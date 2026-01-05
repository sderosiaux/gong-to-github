"""State management for incremental sync."""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SyncState(BaseModel):
    """State for incremental sync."""

    model_config = ConfigDict(populate_by_name=True)

    last_sync_timestamp: datetime | None = None


def load_state(state_file: Path) -> SyncState:
    """Load sync state from file."""
    if not state_file.exists():
        return SyncState()

    try:
        data = json.loads(state_file.read_text())
        return SyncState.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return SyncState()


def save_state(state: SyncState, state_file: Path) -> None:
    """Save sync state to file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)

    data = state.model_dump(mode="json")
    state_file.write_text(json.dumps(data, indent=2, default=str))


def update_last_sync(state: SyncState, timestamp: datetime | None = None) -> None:
    """Update the last sync timestamp."""
    state.last_sync_timestamp = timestamp or datetime.now()
