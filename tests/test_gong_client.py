"""Tests for Gong API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from gong_to_github.gong_client import (
    GongAPIError,
    GongClient,
    GongRateLimitError,
)
from gong_to_github.models import CallMetadata, User


class TestGongRateLimitError:
    """Tests for GongRateLimitError."""

    def test_error_message(self) -> None:
        """Test error message contains retry info."""
        error = GongRateLimitError(retry_after=30)
        assert error.retry_after == 30
        assert "30 seconds" in str(error)


class TestGongClient:
    """Tests for GongClient."""

    @pytest.fixture
    def client(self) -> GongClient:
        """Create a GongClient instance."""
        return GongClient(access_key="test-key", secret_key="test-secret")

    def test_init(self, client: GongClient) -> None:
        """Test client initialization."""
        assert client.base_url == "https://api.gong.io"
        assert isinstance(client.auth, httpx.BasicAuth)

    @patch("gong_to_github.gong_client.httpx.Client")
    def test_request_success(
        self, mock_client_class: MagicMock, client: GongClient
    ) -> None:
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = client._request("GET", "/test")
        assert result == {"data": "test"}

    @patch("gong_to_github.gong_client.httpx.Client")
    def test_request_rate_limited(
        self, mock_client_class: MagicMock, client: GongClient
    ) -> None:
        """Test rate limit handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        with pytest.raises(GongRateLimitError) as exc_info:
            # Disable retry for test
            client._request.__wrapped__(client, "GET", "/test")

        assert exc_info.value.retry_after == 30

    @patch("gong_to_github.gong_client.httpx.Client")
    def test_request_api_error(
        self, mock_client_class: MagicMock, client: GongClient
    ) -> None:
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        with pytest.raises(GongAPIError) as exc_info:
            client._request.__wrapped__(client, "GET", "/test")

        assert "400" in str(exc_info.value)
        assert "Bad Request" in str(exc_info.value)

    @patch.object(GongClient, "_request")
    def test_get_users(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_users_response: dict
    ) -> None:
        """Test getting users."""
        mock_request.return_value = sample_gong_api_users_response

        users = client.get_users()

        assert len(users) == 2
        assert all(isinstance(u, User) for u in users)
        assert users[0].id == "user-1"
        assert users[0].full_name == "John Doe"

    @patch.object(GongClient, "_request")
    def test_get_users_caches_results(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_users_response: dict
    ) -> None:
        """Test that users are cached."""
        mock_request.return_value = sample_gong_api_users_response

        # First call
        client.get_users()
        # Second call should use cache
        client.get_users()

        # Should only call API once
        assert mock_request.call_count == 1

    @patch.object(GongClient, "_request")
    def test_get_user_by_id(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_users_response: dict
    ) -> None:
        """Test getting user by ID."""
        mock_request.return_value = sample_gong_api_users_response

        user = client.get_user_by_id("user-1")
        assert user is not None
        assert user.id == "user-1"

    @patch.object(GongClient, "_request")
    def test_get_user_by_id_not_found(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_users_response: dict
    ) -> None:
        """Test getting nonexistent user."""
        mock_request.return_value = sample_gong_api_users_response

        user = client.get_user_by_id("nonexistent")
        assert user is None

    @patch.object(GongClient, "_paginate_get")
    def test_list_calls(
        self, mock_paginate_get: MagicMock, client: GongClient
    ) -> None:
        """Test listing calls."""
        mock_paginate_get.return_value = iter([
            {
                "id": "call-1",
                "title": "Test Call",
                "scope": "External",
            },
            {
                "id": "call-2",
                "title": "Internal Call",
                "scope": "Internal",
            },
        ])

        calls = list(client.list_calls(scope="External"))

        # Only external calls should be returned
        assert len(calls) == 1
        assert calls[0].id == "call-1"

    @patch.object(GongClient, "_paginate_get")
    def test_list_calls_no_scope_filter(
        self, mock_paginate_get: MagicMock, client: GongClient
    ) -> None:
        """Test listing calls without scope filter."""
        mock_paginate_get.return_value = iter([
            {"id": "call-1", "scope": "External"},
            {"id": "call-2", "scope": "Internal"},
        ])

        calls = list(client.list_calls(scope=None))

        assert len(calls) == 2

    @patch.object(GongClient, "_request")
    def test_get_calls_extensive(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_extensive_response: dict
    ) -> None:
        """Test getting extensive call data."""
        mock_request.return_value = sample_gong_api_extensive_response

        result = client.get_calls_extensive(["call-123"])

        assert "call-123" in result
        assert "parties" in result["call-123"]
        assert len(result["call-123"]["parties"]) == 2

    @patch.object(GongClient, "_request")
    def test_get_calls_extensive_empty_list(
        self, mock_request: MagicMock, client: GongClient
    ) -> None:
        """Test getting extensive data with empty list."""
        result = client.get_calls_extensive([])

        assert result == {}
        mock_request.assert_not_called()

    @patch.object(GongClient, "_request")
    def test_get_calls_extensive_batching(
        self, mock_request: MagicMock, client: GongClient
    ) -> None:
        """Test that calls are batched in groups of 100."""
        # Create 150 call IDs
        call_ids = [f"call-{i}" for i in range(150)]

        mock_request.return_value = {"calls": []}

        client.get_calls_extensive(call_ids)

        # Should make 2 requests (100 + 50)
        assert mock_request.call_count == 2

    @patch.object(GongClient, "_request")
    def test_get_transcripts(
        self, mock_request: MagicMock, client: GongClient, sample_gong_api_transcript_response: dict
    ) -> None:
        """Test getting transcripts."""
        mock_request.return_value = sample_gong_api_transcript_response

        result = client.get_transcripts(["call-123"])

        assert "call-123" in result
        assert len(result["call-123"].transcript) == 2

    @patch.object(GongClient, "_request")
    def test_get_transcripts_empty_list(
        self, mock_request: MagicMock, client: GongClient
    ) -> None:
        """Test getting transcripts with empty list."""
        result = client.get_transcripts([])

        assert result == {}
        mock_request.assert_not_called()


class TestGongClientThrottling:
    """Tests for rate limit throttling."""

    @patch("gong_to_github.gong_client.time.sleep")
    @patch("gong_to_github.gong_client.time.time")
    def test_throttle_waits_when_needed(
        self, mock_time: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test that throttle waits when requests are too fast."""
        client = GongClient("key", "secret")

        # Simulate time: first call at 0, second call at 0.1 (too fast)
        # MIN_REQUEST_INTERVAL = 1/3 = 0.333... seconds
        mock_time.side_effect = [0.1, 0.5]  # current_time, after sleep

        client._last_request_time = 0.0
        client._throttle()

        # Should have slept for ~0.233 seconds (0.333 - 0.1)
        mock_sleep.assert_called_once()
        sleep_time = mock_sleep.call_args[0][0]
        assert 0.2 < sleep_time < 0.35

    @patch("gong_to_github.gong_client.time.sleep")
    @patch("gong_to_github.gong_client.time.time")
    def test_throttle_no_wait_when_slow(
        self, mock_time: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test that throttle doesn't wait when requests are slow enough."""
        client = GongClient("key", "secret")

        # Simulate time: enough time has passed
        mock_time.return_value = 1.0

        client._last_request_time = 0.0
        client._throttle()

        mock_sleep.assert_not_called()
