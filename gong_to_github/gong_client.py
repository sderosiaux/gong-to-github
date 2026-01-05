"""Gong API client with rate limiting and pagination support."""

import time
from datetime import datetime
from typing import Any, Generator

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .models import (
    Call,
    CallMetadata,
    CallTranscript,
    Participant,
    TranscriptSegment,
    User,
)


class GongRateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds.")


class GongAPIError(Exception):
    """Raised when API returns an error."""

    pass


class GongClient:
    """Client for the Gong API with rate limiting and pagination."""

    DEFAULT_BASE_URL = "https://api.gong.io"
    RATE_LIMIT_REQUESTS_PER_SECOND = 3
    MIN_REQUEST_INTERVAL = 1.0 / RATE_LIMIT_REQUESTS_PER_SECOND

    def __init__(self, access_key: str, secret_key: str, base_url: str | None = None):
        self.auth = httpx.BasicAuth(access_key, secret_key)
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._last_request_time = 0.0
        self._users_cache: dict[str, User] = {}

    def _throttle(self) -> None:
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type(GongRateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Gong API with rate limiting."""
        self._throttle()

        url = f"{self.base_url}/v2{endpoint}"

        with httpx.Client(auth=self.auth, timeout=30.0) as client:
            response = client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise GongRateLimitError(retry_after)

        if response.status_code >= 400:
            raise GongAPIError(f"API error {response.status_code}: {response.text}")

        return response.json()

    def _paginate_post(
        self,
        endpoint: str,
        json_body: dict[str, Any] | None = None,
        data_key: str = "records",
    ) -> Generator[dict[str, Any], None, None]:
        """Paginate through API results using POST with cursor in body."""
        cursor = None

        while True:
            body = json_body.copy() if json_body else {}
            if cursor:
                body["cursor"] = cursor

            result = self._request("POST", endpoint, json=body)

            # Yield items from the response
            items = result.get(data_key, [])
            for item in items:
                yield item

            # Check for next page
            records_info = result.get("records", {})
            cursor = records_info.get("cursor") if isinstance(records_info, dict) else None

            if not cursor:
                # Also check top-level cursor
                cursor = result.get("cursor")

            if not cursor:
                break

    def _paginate_get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data_key: str = "records",
    ) -> Generator[dict[str, Any], None, None]:
        """Paginate through API results using GET with cursor in query params."""
        cursor = None

        while True:
            request_params = params.copy() if params else {}
            if cursor:
                request_params["cursor"] = cursor

            result = self._request("GET", endpoint, params=request_params)

            # Yield items from the response
            items = result.get(data_key, [])
            for item in items:
                yield item

            # Check for next page - Gong uses records.cursor structure
            records_info = result.get("records", {})
            cursor = records_info.get("cursor") if isinstance(records_info, dict) else None

            if not cursor:
                # Also check top-level cursor
                cursor = result.get("cursor")

            if not cursor:
                break

    def _paginate(
        self,
        method: str,
        endpoint: str,
        json_body: dict[str, Any] | None = None,
        data_key: str = "records",
    ) -> Generator[dict[str, Any], None, None]:
        """Paginate through API results (backward compatibility wrapper)."""
        if method == "GET":
            yield from self._paginate_get(endpoint, data_key=data_key)
        else:
            yield from self._paginate_post(endpoint, json_body=json_body, data_key=data_key)

    def get_users(self) -> list[User]:
        """Get all users from Gong."""
        if self._users_cache:
            return list(self._users_cache.values())

        users = []
        for user_data in self._paginate("GET", "/users", data_key="users"):
            user = User.model_validate(user_data)
            users.append(user)
            self._users_cache[user.id] = user

        return users

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID, using cache."""
        if not self._users_cache:
            self.get_users()
        return self._users_cache.get(user_id)

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for Gong API (ISO 8601 with timezone)."""
        # Gong requires timezone-aware datetime, append Z if naive
        iso = dt.isoformat()
        if dt.tzinfo is None:
            return iso + "Z"
        return iso

    def list_calls(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        scope: str | None = "External",
    ) -> Generator[CallMetadata, None, None]:
        """List calls with optional filters."""
        params: dict[str, str] = {}

        if from_date:
            params["fromDateTime"] = self._format_datetime(from_date)
        if to_date:
            params["toDateTime"] = self._format_datetime(to_date)

        for call_data in self._paginate_get("/calls", params=params, data_key="calls"):
            # Filter by scope if specified
            if scope and call_data.get("scope") != scope:
                continue
            yield CallMetadata.model_validate(call_data)

    def get_calls_extensive(self, call_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Get extensive call data including participants."""
        if not call_ids:
            return {}

        # API allows max 100 calls per request
        result = {}
        for i in range(0, len(call_ids), 100):
            batch_ids = call_ids[i : i + 100]

            response = self._request(
                "POST",
                "/calls/extensive",
                json={
                    "filter": {"callIds": batch_ids},
                    "contentSelector": {
                        "exposedFields": {
                            "parties": True,
                            "content": {"trackers": True},
                            "collaboration": {"publicComments": True},
                        }
                    },
                },
            )

            for call_data in response.get("calls", []):
                call_id = call_data.get("metaData", {}).get("id")
                if call_id:
                    result[call_id] = call_data

        return result

    def get_transcripts(self, call_ids: list[str]) -> dict[str, CallTranscript]:
        """Get transcripts for multiple calls."""
        if not call_ids:
            return {}

        result = {}

        # API allows max 100 calls per request
        for i in range(0, len(call_ids), 100):
            batch_ids = call_ids[i : i + 100]

            response = self._request(
                "POST",
                "/calls/transcript",
                json={"filter": {"callIds": batch_ids}},
            )

            for transcript_data in response.get("callTranscripts", []):
                call_id = transcript_data.get("callId")
                if call_id:
                    result[call_id] = CallTranscript.model_validate(transcript_data)

        return result

    def get_full_calls(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        scope: str | None = "External",
    ) -> Generator[Call, None, None]:
        """Get full call data with participants and transcripts."""
        # Collect call IDs in batches
        call_batch: list[str] = []
        batch_size = 50

        for call_meta in self.list_calls(from_date=from_date, to_date=to_date, scope=scope):
            call_batch.append(call_meta.id)

            if len(call_batch) >= batch_size:
                yield from self._process_call_batch(call_batch)
                call_batch = []

        # Process remaining calls
        if call_batch:
            yield from self._process_call_batch(call_batch)

    def _process_call_batch(self, call_ids: list[str]) -> Generator[Call, None, None]:
        """Process a batch of calls."""
        # Get extensive data and transcripts
        extensive_data = self.get_calls_extensive(call_ids)
        transcripts = self.get_transcripts(call_ids)

        for call_id in call_ids:
            ext_data = extensive_data.get(call_id, {})
            transcript = transcripts.get(call_id)

            if not ext_data:
                continue

            # Build the Call object
            metadata = CallMetadata.model_validate(ext_data.get("metaData", {}))

            parties = [
                Participant.model_validate(p) for p in ext_data.get("parties", [])
            ]

            transcript_segments: list[TranscriptSegment] = []
            if transcript:
                transcript_segments = transcript.transcript

            call = Call(
                metaData=metadata,
                parties=parties,
                transcript=transcript_segments,
                context=ext_data.get("context", []),
            )

            yield call
