"""Pytest fixtures for gong-to-github tests."""

from datetime import datetime

import pytest

from gong_to_github.models import (
    Affiliation,
    Call,
    CallMetadata,
    CallTranscript,
    Participant,
    Sentence,
    TranscriptSegment,
    User,
)
from gong_to_github.state import SyncState


@pytest.fixture
def sample_user() -> User:
    """Create a sample Gong user."""
    return User(
        id="user-123",
        emailAddress="john.doe@company.com",
        firstName="John",
        lastName="Doe",
        active=True,
    )


@pytest.fixture
def sample_internal_participant() -> Participant:
    """Create a sample internal participant."""
    return Participant(
        id="party-internal-1",
        emailAddress="john.doe@company.com",
        name="John Doe",
        title="Account Executive",
        speakerId="speaker-1",
        affiliation=Affiliation.INTERNAL,
        userId="user-123",
    )


@pytest.fixture
def sample_external_participant() -> Participant:
    """Create a sample external participant."""
    return Participant(
        id="party-external-1",
        emailAddress="jane.smith@acme.com",
        name="Jane Smith",
        title="VP of Sales",
        speakerId="speaker-2",
        affiliation=Affiliation.EXTERNAL,
    )


@pytest.fixture
def sample_transcript_segments() -> list[TranscriptSegment]:
    """Create sample transcript segments."""
    return [
        TranscriptSegment(
            speakerId="speaker-1",
            sentences=[
                Sentence(startMs=0, endMs=5000, text="Hi Jane, thanks for joining today!"),
                Sentence(startMs=5500, endMs=10000, text="How are things at Acme?"),
            ],
        ),
        TranscriptSegment(
            speakerId="speaker-2",
            sentences=[
                Sentence(startMs=11000, endMs=18000, text="Hi John! Things are great, we're growing fast."),
            ],
        ),
        TranscriptSegment(
            speakerId="speaker-1",
            sentences=[
                Sentence(startMs=19000, endMs=25000, text="That's wonderful to hear!"),
            ],
        ),
    ]


@pytest.fixture
def sample_call_metadata() -> CallMetadata:
    """Create sample call metadata."""
    return CallMetadata(
        id="call-123",
        url="https://app.gong.io/call?id=call-123",
        title="Acme Corp - Discovery Call",
        scheduled=datetime(2025, 1, 4, 14, 0, 0),
        started=datetime(2025, 1, 4, 14, 3, 0),
        duration=1800,  # 30 minutes
        direction="Conference",
        system="Zoom",
        scope="External",
        media="Video",
        language="eng",
        primaryUserId="user-123",
    )


@pytest.fixture
def sample_call(
    sample_call_metadata: CallMetadata,
    sample_internal_participant: Participant,
    sample_external_participant: Participant,
    sample_transcript_segments: list[TranscriptSegment],
) -> Call:
    """Create a sample complete call."""
    return Call(
        metaData=sample_call_metadata,
        parties=[sample_internal_participant, sample_external_participant],
        transcript=sample_transcript_segments,
        context=[
            {
                "system": "Salesforce",
                "objects": [
                    {
                        "objectType": "Account",
                        "objectId": "acc-123",
                        "fields": [
                            {"name": "Name", "value": "Acme Corporation"},
                            {"name": "Industry", "value": "Technology"},
                        ],
                    }
                ],
            }
        ],
    )


@pytest.fixture
def sample_call_without_salesforce(
    sample_call_metadata: CallMetadata,
    sample_internal_participant: Participant,
    sample_external_participant: Participant,
    sample_transcript_segments: list[TranscriptSegment],
) -> Call:
    """Create a sample call without Salesforce context."""
    return Call(
        metaData=sample_call_metadata,
        parties=[sample_internal_participant, sample_external_participant],
        transcript=sample_transcript_segments,
        context=[],
    )


@pytest.fixture
def sample_call_minimal() -> Call:
    """Create a minimal call with only required fields."""
    return Call(
        metaData=CallMetadata(id="call-minimal"),
        parties=[],
        transcript=[],
        context=[],
    )


@pytest.fixture
def sample_sync_state() -> SyncState:
    """Create a sample sync state."""
    return SyncState(
        last_sync_timestamp=datetime(2025, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def empty_sync_state() -> SyncState:
    """Create an empty sync state."""
    return SyncState()


@pytest.fixture
def sample_gong_api_calls_response() -> dict:
    """Sample response from Gong /v2/calls endpoint."""
    return {
        "requestId": "req-123",
        "records": {
            "totalRecords": 2,
            "currentPageSize": 2,
            "currentPageNumber": 0,
        },
        "calls": [
            {
                "id": "call-123",
                "url": "https://app.gong.io/call?id=call-123",
                "title": "Discovery Call",
                "scheduled": "2025-01-04T14:00:00Z",
                "started": "2025-01-04T14:03:00Z",
                "duration": 1800,
                "direction": "Conference",
                "system": "Zoom",
                "scope": "External",
                "media": "Video",
                "language": "eng",
            },
            {
                "id": "call-456",
                "url": "https://app.gong.io/call?id=call-456",
                "title": "Demo Call",
                "scheduled": "2025-01-05T10:00:00Z",
                "started": "2025-01-05T10:02:00Z",
                "duration": 2700,
                "direction": "Conference",
                "system": "Zoom",
                "scope": "External",
                "media": "Video",
                "language": "eng",
            },
        ],
    }


@pytest.fixture
def sample_gong_api_transcript_response() -> dict:
    """Sample response from Gong /v2/calls/transcript endpoint."""
    return {
        "requestId": "req-456",
        "callTranscripts": [
            {
                "callId": "call-123",
                "transcript": [
                    {
                        "speakerId": "speaker-1",
                        "sentences": [
                            {"startMs": 0, "endMs": 5000, "text": "Hello!"},
                            {"startMs": 5500, "endMs": 10000, "text": "How are you?"},
                        ],
                    },
                    {
                        "speakerId": "speaker-2",
                        "sentences": [
                            {"startMs": 11000, "endMs": 15000, "text": "I'm doing great!"},
                        ],
                    },
                ],
            }
        ],
    }


@pytest.fixture
def sample_gong_api_extensive_response() -> dict:
    """Sample response from Gong /v2/calls/extensive endpoint."""
    return {
        "requestId": "req-789",
        "calls": [
            {
                "metaData": {
                    "id": "call-123",
                    "url": "https://app.gong.io/call?id=call-123",
                    "title": "Discovery Call",
                    "started": "2025-01-04T14:03:00Z",
                    "duration": 1800,
                    "system": "Zoom",
                    "scope": "External",
                    "media": "Video",
                },
                "parties": [
                    {
                        "id": "party-1",
                        "emailAddress": "john@company.com",
                        "name": "John Doe",
                        "title": "AE",
                        "speakerId": "speaker-1",
                        "affiliation": "Internal",
                    },
                    {
                        "id": "party-2",
                        "emailAddress": "jane@acme.com",
                        "name": "Jane Smith",
                        "title": "VP Sales",
                        "speakerId": "speaker-2",
                        "affiliation": "External",
                    },
                ],
                "context": [],
            }
        ],
    }


@pytest.fixture
def sample_gong_api_users_response() -> dict:
    """Sample response from Gong /v2/users endpoint."""
    return {
        "requestId": "req-users",
        "records": {
            "totalRecords": 2,
            "currentPageSize": 2,
            "currentPageNumber": 0,
        },
        "users": [
            {
                "id": "user-1",
                "emailAddress": "john@company.com",
                "firstName": "John",
                "lastName": "Doe",
                "active": True,
            },
            {
                "id": "user-2",
                "emailAddress": "jane@company.com",
                "firstName": "Jane",
                "lastName": "Roe",
                "active": True,
            },
        ],
    }
