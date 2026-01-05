"""Tests for data models."""

from datetime import datetime

import pytest

from gong_to_github.models import (
    Affiliation,
    Call,
    CallMetadata,
    Participant,
    Sentence,
    TranscriptSegment,
    User,
)
from gong_to_github.state import SyncState


class TestUser:
    """Tests for User model."""

    def test_full_name_with_both_names(self, sample_user: User) -> None:
        """Test full_name property with first and last name."""
        assert sample_user.full_name == "John Doe"

    def test_full_name_with_first_name_only(self) -> None:
        """Test full_name property with first name only."""
        user = User(id="1", emailAddress="test@test.com", firstName="John")
        assert user.full_name == "John"

    def test_full_name_with_last_name_only(self) -> None:
        """Test full_name property with last name only."""
        user = User(id="1", emailAddress="test@test.com", lastName="Doe")
        assert user.full_name == "Doe"

    def test_full_name_fallback_to_email(self) -> None:
        """Test full_name property falls back to email."""
        user = User(id="1", emailAddress="test@test.com")
        assert user.full_name == "test@test.com"

    def test_user_from_api_response(self) -> None:
        """Test creating User from API response format."""
        data = {
            "id": "123",
            "emailAddress": "john@company.com",
            "firstName": "John",
            "lastName": "Doe",
            "active": True,
        }
        user = User.model_validate(data)
        assert user.id == "123"
        assert user.email_address == "john@company.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.active is True


class TestParticipant:
    """Tests for Participant model."""

    def test_participant_from_api_response(self) -> None:
        """Test creating Participant from API response format."""
        data = {
            "id": "party-1",
            "emailAddress": "jane@acme.com",
            "name": "Jane Smith",
            "title": "VP Sales",
            "speakerId": "speaker-2",
            "affiliation": "External",
        }
        participant = Participant.model_validate(data)
        assert participant.id == "party-1"
        assert participant.email_address == "jane@acme.com"
        assert participant.name == "Jane Smith"
        assert participant.affiliation == Affiliation.EXTERNAL

    def test_participant_minimal(self) -> None:
        """Test creating Participant with minimal data."""
        data = {"id": "party-1"}
        participant = Participant.model_validate(data)
        assert participant.id == "party-1"
        assert participant.email_address is None
        assert participant.name is None


class TestCallMetadata:
    """Tests for CallMetadata model."""

    def test_call_metadata_from_api_response(self, sample_call_metadata: CallMetadata) -> None:
        """Test CallMetadata fields."""
        assert sample_call_metadata.id == "call-123"
        assert sample_call_metadata.title == "Acme Corp - Discovery Call"
        assert sample_call_metadata.duration == 1800
        assert sample_call_metadata.system == "Zoom"
        assert sample_call_metadata.scope == "External"

    def test_call_metadata_minimal(self) -> None:
        """Test CallMetadata with minimal data."""
        data = {"id": "call-minimal"}
        metadata = CallMetadata.model_validate(data)
        assert metadata.id == "call-minimal"
        assert metadata.title is None
        assert metadata.duration is None


class TestTranscript:
    """Tests for transcript models."""

    def test_sentence_from_api(self) -> None:
        """Test Sentence model from API data."""
        data = {"startMs": 1000, "endMs": 5000, "text": "Hello world"}
        sentence = Sentence.model_validate(data)
        assert sentence.start_ms == 1000
        assert sentence.end_ms == 5000
        assert sentence.text == "Hello world"

    def test_transcript_segment_from_api(self) -> None:
        """Test TranscriptSegment model from API data."""
        data = {
            "speakerId": "speaker-1",
            "sentences": [
                {"startMs": 0, "endMs": 1000, "text": "Hi"},
                {"startMs": 1500, "endMs": 3000, "text": "How are you?"},
            ],
        }
        segment = TranscriptSegment.model_validate(data)
        assert segment.speaker_id == "speaker-1"
        assert len(segment.sentences) == 2
        assert segment.sentences[0].text == "Hi"


class TestCall:
    """Tests for Call model."""

    def test_client_name_from_salesforce(self, sample_call: Call) -> None:
        """Test client_name extraction from Salesforce context."""
        assert sample_call.client_name == "Acme Corporation"

    def test_client_name_from_email_domain(self, sample_call_without_salesforce: Call) -> None:
        """Test client_name extraction from email domain."""
        assert sample_call_without_salesforce.client_name == "Acme"

    def test_client_name_none_when_no_data(self, sample_call_minimal: Call) -> None:
        """Test client_name returns None when no data available."""
        assert sample_call_minimal.client_name is None

    def test_external_participants(self, sample_call: Call) -> None:
        """Test external_participants property."""
        external = sample_call.external_participants
        assert len(external) == 1
        assert external[0].name == "Jane Smith"
        assert external[0].affiliation == Affiliation.EXTERNAL

    def test_internal_participants(self, sample_call: Call) -> None:
        """Test internal_participants property."""
        internal = sample_call.internal_participants
        assert len(internal) == 1
        assert internal[0].name == "John Doe"
        assert internal[0].affiliation == Affiliation.INTERNAL


class TestSyncState:
    """Tests for SyncState model."""

    def test_sync_state_initial(self, empty_sync_state: SyncState) -> None:
        """Test initial sync state."""
        assert empty_sync_state.last_sync_timestamp is None

    def test_sync_state_with_data(self, sample_sync_state: SyncState) -> None:
        """Test sync state with data."""
        assert sample_sync_state.last_sync_timestamp == datetime(2025, 1, 1, 0, 0, 0)

    def test_sync_state_json_serialization(self, sample_sync_state: SyncState) -> None:
        """Test sync state can be serialized to JSON."""
        json_data = sample_sync_state.model_dump(mode="json")
        assert "last_sync_timestamp" in json_data

        # Verify it can be deserialized
        restored = SyncState.model_validate(json_data)
        assert restored.last_sync_timestamp == sample_sync_state.last_sync_timestamp
