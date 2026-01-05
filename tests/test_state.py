"""Tests for state management."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from gong_to_github.state import (
    SyncState,
    load_state,
    save_state,
    update_last_sync,
)


class TestLoadState:
    """Tests for load_state function."""

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from nonexistent file returns empty state."""
        state_file = tmp_path / "nonexistent.json"
        state = load_state(state_file)

        assert state.last_sync_timestamp is None

    def test_load_valid_state(self, tmp_path: Path) -> None:
        """Test loading valid state file."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            json.dumps({"last_sync_timestamp": "2025-01-01T00:00:00"})
        )

        state = load_state(state_file)
        assert state.last_sync_timestamp == datetime(2025, 1, 1, 0, 0, 0)

    def test_load_corrupted_json(self, tmp_path: Path) -> None:
        """Test loading corrupted JSON returns empty state."""
        state_file = tmp_path / "corrupted.json"
        state_file.write_text("not valid json {{{")

        state = load_state(state_file)
        assert state.last_sync_timestamp is None

    def test_load_invalid_schema(self, tmp_path: Path) -> None:
        """Test loading invalid schema returns empty state."""
        state_file = tmp_path / "invalid.json"
        state_file.write_text(json.dumps({"unknown_field": "value"}))

        state = load_state(state_file)
        # Should still work with defaults
        assert state.last_sync_timestamp is None


class TestSaveState:
    """Tests for save_state function."""

    def test_save_state(self, tmp_path: Path) -> None:
        """Test saving state to file."""
        state = SyncState(last_sync_timestamp=datetime(2025, 1, 1, 12, 0, 0))
        state_file = tmp_path / "state.json"
        save_state(state, state_file)

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert "last_sync_timestamp" in data

    def test_save_state_creates_directory(self, tmp_path: Path) -> None:
        """Test save_state creates parent directories."""
        state_file = tmp_path / "subdir" / "nested" / "state.json"
        state = SyncState()
        save_state(state, state_file)

        assert state_file.exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Test saving and loading preserves data."""
        state_file = tmp_path / "state.json"
        original = SyncState(last_sync_timestamp=datetime(2025, 1, 15, 10, 30, 0))

        save_state(original, state_file)
        loaded = load_state(state_file)

        assert loaded.last_sync_timestamp == original.last_sync_timestamp


class TestUpdateLastSync:
    """Tests for update_last_sync function."""

    def test_update_with_timestamp(self) -> None:
        """Test updating with specific timestamp."""
        state = SyncState()
        timestamp = datetime(2025, 6, 15, 12, 0, 0)
        update_last_sync(state, timestamp)
        assert state.last_sync_timestamp == timestamp

    def test_update_without_timestamp(self) -> None:
        """Test updating without timestamp uses current time."""
        state = SyncState()
        before = datetime.now()
        update_last_sync(state)
        after = datetime.now()

        assert state.last_sync_timestamp is not None
        assert before <= state.last_sync_timestamp <= after
