"""Tests for GitHub sync module."""

from pathlib import Path

import pytest

from gong_to_github.github_sync import LocalSync


class TestLocalSync:
    """Tests for LocalSync class."""

    @pytest.fixture
    def local_sync(self, tmp_path: Path) -> LocalSync:
        """Create a LocalSync instance with temp directory."""
        return LocalSync(tmp_path)

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Test that init creates the output directory."""
        output_dir = tmp_path / "new_output"
        LocalSync(output_dir)
        assert output_dir.exists()

    def test_sync_transcript_creates_file(self, local_sync: LocalSync) -> None:
        """Test syncing a transcript creates the file."""
        result = local_sync.sync_transcript(
            client_folder="acme-corp",
            filename="2025-01-04-discovery.md",
            content="# Test Call\n\nContent here",
        )

        assert result is True
        file_path = local_sync.output_dir / "transcripts" / "acme-corp" / "2025-01-04-discovery.md"
        assert file_path.exists()
        assert file_path.read_text() == "# Test Call\n\nContent here"

    def test_sync_transcript_creates_nested_dirs(self, local_sync: LocalSync) -> None:
        """Test that sync creates necessary directories."""
        local_sync.sync_transcript(
            client_folder="new-client",
            filename="call.md",
            content="Content",
        )

        folder = local_sync.output_dir / "transcripts" / "new-client"
        assert folder.exists()
        assert folder.is_dir()

    def test_sync_transcript_skip_existing(self, local_sync: LocalSync) -> None:
        """Test that sync skips existing files by default."""
        # Create first file
        local_sync.sync_transcript(
            client_folder="acme",
            filename="call.md",
            content="Original content",
        )

        # Try to create again
        result = local_sync.sync_transcript(
            client_folder="acme",
            filename="call.md",
            content="New content",
            update_existing=False,
        )

        assert result is False
        file_path = local_sync.output_dir / "transcripts" / "acme" / "call.md"
        assert file_path.read_text() == "Original content"

    def test_sync_transcript_update_existing(self, local_sync: LocalSync) -> None:
        """Test that sync can update existing files."""
        # Create first file
        local_sync.sync_transcript(
            client_folder="acme",
            filename="call.md",
            content="Original content",
        )

        # Update
        result = local_sync.sync_transcript(
            client_folder="acme",
            filename="call.md",
            content="Updated content",
            update_existing=True,
        )

        assert result is True
        file_path = local_sync.output_dir / "transcripts" / "acme" / "call.md"
        assert file_path.read_text() == "Updated content"

    def test_sync_client_index(self, local_sync: LocalSync) -> None:
        """Test syncing client index."""
        result = local_sync.sync_client_index(
            client_folder="acme",
            content="# Acme - Call History\n\nIndex content",
        )

        assert result is True
        file_path = local_sync.output_dir / "transcripts" / "acme" / "README.md"
        assert file_path.exists()
        assert "Call History" in file_path.read_text()

    def test_sync_client_index_always_updates(self, local_sync: LocalSync) -> None:
        """Test that client index is always updated."""
        # Create initial index
        local_sync.sync_client_index("acme", "Initial")

        # Update index
        local_sync.sync_client_index("acme", "Updated")

        file_path = local_sync.output_dir / "transcripts" / "acme" / "README.md"
        assert file_path.read_text() == "Updated"

    def test_list_existing_transcripts_empty(self, local_sync: LocalSync) -> None:
        """Test listing transcripts for nonexistent folder."""
        result = local_sync.list_existing_transcripts("nonexistent")
        assert result == []

    def test_list_existing_transcripts(self, local_sync: LocalSync) -> None:
        """Test listing existing transcripts."""
        # Create some files
        local_sync.sync_transcript("acme", "call-1.md", "content")
        local_sync.sync_transcript("acme", "call-2.md", "content")
        local_sync.sync_client_index("acme", "index")

        result = local_sync.list_existing_transcripts("acme")

        assert len(result) == 2
        assert "call-1.md" in result
        assert "call-2.md" in result
        assert "README.md" not in result  # Index excluded

    def test_multiple_clients(self, local_sync: LocalSync) -> None:
        """Test syncing multiple clients."""
        local_sync.sync_transcript("acme", "call.md", "Acme content")
        local_sync.sync_transcript("bigcorp", "call.md", "BigCorp content")

        acme_path = local_sync.output_dir / "transcripts" / "acme" / "call.md"
        bigcorp_path = local_sync.output_dir / "transcripts" / "bigcorp" / "call.md"

        assert acme_path.exists()
        assert bigcorp_path.exists()
        assert acme_path.read_text() == "Acme content"
        assert bigcorp_path.read_text() == "BigCorp content"
