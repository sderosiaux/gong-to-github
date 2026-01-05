"""Tests for CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gong_to_github.cli import cli


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_cli_requires_credentials(self, runner: CliRunner) -> None:
        """Test that CLI requires Gong credentials."""
        # Clear environment variables to ensure test isolation
        result = runner.invoke(
            cli,
            ["list-users"],
            env={"GONG_ACCESS_KEY": "", "GONG_SECRET_KEY": "", "GONG_API_URL": ""},
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @patch("gong_to_github.cli.GongClient")
    def test_cli_accepts_credentials(
        self, mock_client_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test that CLI accepts credentials."""
        mock_client = MagicMock()
        mock_client.get_users.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            cli,
            [
                "--gong-access-key", "test-key",
                "--gong-secret-key", "test-secret",
                "list-users",
            ],
            env={"GONG_API_URL": ""},
        )

        mock_client_class.assert_called_once_with("test-key", "test-secret", None)

    @patch("gong_to_github.cli.GongClient")
    def test_cli_credentials_from_env(
        self, mock_client_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test that CLI reads credentials from environment."""
        mock_client = MagicMock()
        mock_client.get_users.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            cli,
            ["list-users"],
            env={
                "GONG_ACCESS_KEY": "env-key",
                "GONG_SECRET_KEY": "env-secret",
                "GONG_API_URL": "",
            },
        )

        mock_client_class.assert_called_once_with("env-key", "env-secret", None)


class TestListUsersCommand:
    """Tests for list-users command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @patch("gong_to_github.cli.GongClient")
    def test_list_users(self, mock_client_class: MagicMock, runner: CliRunner) -> None:
        """Test list-users command."""
        from gong_to_github.models import User

        mock_client = MagicMock()
        mock_client.get_users.return_value = [
            User(id="1", emailAddress="john@test.com", firstName="John", lastName="Doe"),
            User(id="2", emailAddress="jane@test.com", firstName="Jane", lastName="Roe"),
        ]
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            cli,
            ["--gong-access-key", "key", "--gong-secret-key", "secret", "list-users"],
        )

        assert result.exit_code == 0
        assert "John Doe" in result.output
        assert "Jane Roe" in result.output
        assert "2 users" in result.output


class TestListCallsCommand:
    """Tests for list-calls command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @patch("gong_to_github.cli.GongClient")
    def test_list_calls_empty(
        self, mock_client_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test list-calls with no calls."""
        mock_client = MagicMock()
        mock_client.get_full_calls.return_value = iter([])
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            cli,
            ["--gong-access-key", "key", "--gong-secret-key", "secret", "list-calls"],
        )

        assert result.exit_code == 0
        assert "0 external calls" in result.output


class TestSyncLocalCommand:
    """Tests for sync-local command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @patch("gong_to_github.cli.GongClient")
    def test_sync_local_creates_output(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        sample_call,
        tmp_path: Path,
    ) -> None:
        """Test sync-local creates files."""
        mock_client = MagicMock()
        mock_client.get_full_calls.return_value = iter([sample_call])
        mock_client_class.return_value = mock_client

        output_dir = tmp_path / "output"
        state_file = tmp_path / "state.json"

        result = runner.invoke(
            cli,
            [
                "--gong-access-key", "key",
                "--gong-secret-key", "secret",
                "sync-local",
                "--output-dir", str(output_dir),
                "--state-file", str(state_file),
            ],
        )

        assert result.exit_code == 0
        assert "Synced" in result.output

        # Check files were created
        transcripts_dir = output_dir / "transcripts"
        assert transcripts_dir.exists()

    @patch("gong_to_github.cli.GongClient")
    def test_sync_local_full_sync_flag(
        self,
        mock_client_class: MagicMock,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test sync-local with --full-sync flag."""
        mock_client = MagicMock()
        mock_client.get_full_calls.return_value = iter([])
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            cli,
            [
                "--gong-access-key", "key",
                "--gong-secret-key", "secret",
                "sync-local",
                "--output-dir", str(tmp_path / "output"),
                "--state-file", str(tmp_path / "state.json"),
                "--full-sync",
            ],
        )

        assert result.exit_code == 0


class TestSyncGithubCommand:
    """Tests for sync-github command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_sync_github_requires_token(self, runner: CliRunner) -> None:
        """Test sync-github requires GitHub token."""
        result = runner.invoke(
            cli,
            [
                "--gong-access-key", "key",
                "--gong-secret-key", "secret",
                "sync-github",
            ],
        )

        assert result.exit_code != 0

    @patch("gong_to_github.cli.GitHubSync")
    @patch("gong_to_github.cli.GongClient")
    def test_sync_github_dry_run(
        self,
        mock_gong_class: MagicMock,
        mock_github_class: MagicMock,
        runner: CliRunner,
        sample_call,
        tmp_path: Path,
    ) -> None:
        """Test sync-github with dry-run."""
        mock_gong = MagicMock()
        mock_gong.get_full_calls.return_value = iter([sample_call])
        mock_gong_class.return_value = mock_gong

        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        result = runner.invoke(
            cli,
            [
                "--gong-access-key", "key",
                "--gong-secret-key", "secret",
                "sync-github",
                "--github-token", "gh-token",
                "--repo", "owner/repo",
                "--state-file", str(tmp_path / "state.json"),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output
        # GitHub sync methods should not be called in dry-run
        mock_github.sync_transcript.assert_not_called()
