"""Tests for markdown converter."""

from datetime import datetime

import pytest

from gong_to_github.markdown_converter import (
    call_to_markdown,
    format_duration,
    format_participant,
    format_timestamp,
    generate_client_folder_name,
    generate_client_index,
    generate_filename,
    get_speaker_name,
    slugify,
)
from gong_to_github.models import Affiliation, Call, CallMetadata, Participant


class TestSlugify:
    """Tests for slugify function."""

    def test_simple_text(self) -> None:
        """Test slugifying simple text."""
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self) -> None:
        """Test slugifying text with special characters."""
        assert slugify("Acme Corp - Discovery Call!") == "acme-corp-discovery-call"

    def test_multiple_spaces(self) -> None:
        """Test slugifying text with multiple spaces."""
        assert slugify("Hello    World") == "hello-world"

    def test_leading_trailing_dashes(self) -> None:
        """Test slugifying removes leading/trailing dashes."""
        assert slugify("--Hello World--") == "hello-world"

    def test_unicode_characters(self) -> None:
        """Test slugifying text with unicode (preserves accented chars)."""
        assert slugify("Café Company") == "café-company"

    def test_empty_string(self) -> None:
        """Test slugifying empty string."""
        assert slugify("") == ""


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_zero_ms(self) -> None:
        """Test formatting zero milliseconds."""
        assert format_timestamp(0) == "[00:00]"

    def test_seconds_only(self) -> None:
        """Test formatting seconds only."""
        assert format_timestamp(30000) == "[00:30]"

    def test_minutes_and_seconds(self) -> None:
        """Test formatting minutes and seconds."""
        assert format_timestamp(90000) == "[01:30]"

    def test_hours(self) -> None:
        """Test formatting with hours."""
        assert format_timestamp(3661000) == "[01:01:01]"

    def test_large_value(self) -> None:
        """Test formatting large value."""
        assert format_timestamp(7200000) == "[02:00:00]"


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_minutes_only(self) -> None:
        """Test formatting duration with minutes only."""
        assert format_duration(1800) == "30 min"

    def test_hours_and_minutes(self) -> None:
        """Test formatting duration with hours and minutes."""
        assert format_duration(5400) == "1h 30min"

    def test_exact_hour(self) -> None:
        """Test formatting exact hour."""
        assert format_duration(3600) == "1h 0min"

    def test_zero(self) -> None:
        """Test formatting zero duration."""
        assert format_duration(0) == "0 min"


class TestGetSpeakerName:
    """Tests for get_speaker_name function."""

    def test_found_speaker(
        self,
        sample_internal_participant: Participant,
        sample_external_participant: Participant,
    ) -> None:
        """Test finding speaker by ID."""
        parties = [sample_internal_participant, sample_external_participant]
        name, affiliation = get_speaker_name("speaker-1", parties)
        assert name == "John Doe"
        assert affiliation == Affiliation.INTERNAL

    def test_external_speaker(
        self,
        sample_internal_participant: Participant,
        sample_external_participant: Participant,
    ) -> None:
        """Test finding external speaker."""
        parties = [sample_internal_participant, sample_external_participant]
        name, affiliation = get_speaker_name("speaker-2", parties)
        assert name == "Jane Smith"
        assert affiliation == Affiliation.EXTERNAL

    def test_unknown_speaker(self) -> None:
        """Test unknown speaker returns truncated ID."""
        name, affiliation = get_speaker_name("unknown-speaker-id", [])
        assert name == "Speaker unknown-"
        assert affiliation is None

    def test_speaker_without_name_uses_email(self) -> None:
        """Test speaker without name falls back to email."""
        participant = Participant(
            id="party-1",
            emailAddress="test@test.com",
            speakerId="speaker-1",
            affiliation=Affiliation.INTERNAL,
        )
        name, affiliation = get_speaker_name("speaker-1", [participant])
        assert name == "test@test.com"


class TestFormatParticipant:
    """Tests for format_participant function."""

    def test_full_participant(self, sample_internal_participant: Participant) -> None:
        """Test formatting participant with all fields."""
        result = format_participant(sample_internal_participant)
        assert result == "John Doe (Internal) - Account Executive"

    def test_external_participant(self, sample_external_participant: Participant) -> None:
        """Test formatting external participant."""
        result = format_participant(sample_external_participant)
        assert result == "Jane Smith (External) - VP of Sales"

    def test_participant_without_title(self) -> None:
        """Test formatting participant without title."""
        participant = Participant(
            id="party-1",
            name="John Doe",
            affiliation=Affiliation.INTERNAL,
        )
        result = format_participant(participant)
        assert result == "John Doe (Internal)"

    def test_participant_with_email_only(self) -> None:
        """Test formatting participant with email only."""
        participant = Participant(
            id="party-1",
            emailAddress="john@company.com",
            affiliation=Affiliation.INTERNAL,
        )
        result = format_participant(participant)
        assert result == "john@company.com (Internal)"


class TestCallToMarkdown:
    """Tests for call_to_markdown function."""

    def test_full_call(self, sample_call: Call) -> None:
        """Test converting full call to markdown."""
        md = call_to_markdown(sample_call)

        # Check title
        assert "# Acme Corp - Discovery Call" in md

        # Check metadata
        assert "**Date:** 2025-01-04 14:03" in md
        assert "**Duration:** 30 min" in md

        # Check participants
        assert "**Participants:**" in md
        assert "John Doe (Internal) - Account Executive" in md
        assert "Jane Smith (External) - VP of Sales" in md

        # Check system info
        assert "**System:** Zoom" in md
        assert "**Type:** External" in md

        # Check Gong URL
        assert "[View in Gong](https://app.gong.io/call?id=call-123)" in md

        # Check transcript
        assert "## Transcript" in md
        assert "Hi Jane, thanks for joining today!" in md
        assert "(Client)" in md  # External speaker indicator

    def test_minimal_call(self, sample_call_minimal: Call) -> None:
        """Test converting minimal call to markdown."""
        md = call_to_markdown(sample_call_minimal)
        assert "# Untitled Call" in md
        assert "## Transcript" not in md  # No transcript

    def test_call_without_transcript(
        self,
        sample_call_metadata: CallMetadata,
        sample_internal_participant: Participant,
    ) -> None:
        """Test call without transcript."""
        call = Call(
            metaData=sample_call_metadata,
            parties=[sample_internal_participant],
            transcript=[],
            context=[],
        )
        md = call_to_markdown(call)
        assert "## Transcript" not in md


class TestGenerateFilename:
    """Tests for generate_filename function."""

    def test_filename_with_date_and_title(self, sample_call: Call) -> None:
        """Test generating filename with date and title."""
        filename = generate_filename(sample_call)
        assert filename == "2025-01-04-acme-corp-discovery-call.md"

    def test_filename_without_date(self, sample_call_minimal: Call) -> None:
        """Test generating filename without date."""
        filename = generate_filename(sample_call_minimal)
        assert filename.startswith("unknown-date-")
        assert filename.endswith(".md")

    def test_filename_long_title_truncated(self) -> None:
        """Test that long titles are truncated."""
        call = Call(
            metaData=CallMetadata(
                id="call-1",
                title="This is a very long title that should be truncated because it exceeds the maximum allowed length for filenames",
                started=datetime(2025, 1, 1),
            ),
            parties=[],
            transcript=[],
            context=[],
        )
        filename = generate_filename(call)
        # Title slug should be truncated to 50 chars
        assert len(filename) <= len("2025-01-01-") + 50 + len(".md")


class TestGenerateClientFolderName:
    """Tests for generate_client_folder_name function."""

    def test_from_salesforce_context(self, sample_call: Call) -> None:
        """Test folder name from Salesforce context."""
        folder = generate_client_folder_name(sample_call)
        assert folder == "acme-corporation"

    def test_from_email_domain(self, sample_call_without_salesforce: Call) -> None:
        """Test folder name from email domain."""
        folder = generate_client_folder_name(sample_call_without_salesforce)
        assert folder == "acme"

    def test_unknown_client(self, sample_call_minimal: Call) -> None:
        """Test folder name for unknown client."""
        folder = generate_client_folder_name(sample_call_minimal)
        assert folder == "unknown-client"


class TestGenerateClientIndex:
    """Tests for generate_client_index function."""

    def test_index_content(self, sample_call: Call) -> None:
        """Test generating client index."""
        index = generate_client_index("Acme Corporation", [sample_call])

        assert "# Acme Corporation - Call History" in index
        assert "Total calls: 1" in index
        assert "## Calls" in index
        assert "| Date | Title | Duration | Participants |" in index
        assert "2025-01-04" in index
        assert "Acme Corp - Discovery Call" in index
        assert "30 min" in index

    def test_index_multiple_calls(self, sample_call: Call) -> None:
        """Test index with multiple calls."""
        # Create a second call with different date
        call2 = Call(
            metaData=CallMetadata(
                id="call-2",
                title="Follow-up Call",
                started=datetime(2025, 1, 10, 10, 0, 0),
                duration=900,
            ),
            parties=[],
            transcript=[],
            context=[],
        )

        index = generate_client_index("Acme", [sample_call, call2])
        assert "Total calls: 2" in index
        # Newest first
        assert index.index("2025-01-10") < index.index("2025-01-04")
