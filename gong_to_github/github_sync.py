"""GitHub sync module for pushing transcripts."""

from pathlib import Path

from github import Auth, Github, GithubException


class GitHubSync:
    """Sync markdown files to a GitHub repository."""

    def __init__(self, token: str, repo_name: str, branch: str = "main"):
        """
        Initialize GitHub sync.

        Args:
            token: GitHub personal access token
            repo_name: Repository name in format "owner/repo"
            branch: Branch to push to (default: main)
        """
        auth = Auth.Token(token)
        self.github = Github(auth=auth)
        self.repo = self.github.get_repo(repo_name)
        self.branch = branch

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the repository."""
        try:
            self.repo.get_contents(path, ref=self.branch)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise

    def get_file_sha(self, path: str) -> str | None:
        """Get the SHA of an existing file."""
        try:
            contents = self.repo.get_contents(path, ref=self.branch)
            if isinstance(contents, list):
                return None
            return contents.sha
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def create_or_update_file(
        self,
        path: str,
        content: str,
        commit_message: str,
        update_existing: bool = False,
    ) -> bool:
        """
        Create or update a file in the repository.

        Args:
            path: File path in the repository
            content: File content
            commit_message: Commit message
            update_existing: Whether to update if file exists

        Returns:
            True if file was created/updated, False if skipped
        """
        existing_sha = self.get_file_sha(path)

        if existing_sha and not update_existing:
            return False

        try:
            if existing_sha:
                self.repo.update_file(
                    path=path,
                    message=commit_message,
                    content=content,
                    sha=existing_sha,
                    branch=self.branch,
                )
            else:
                self.repo.create_file(
                    path=path,
                    message=commit_message,
                    content=content,
                    branch=self.branch,
                )
            return True
        except GithubException as e:
            raise RuntimeError(f"Failed to create/update file {path}: {e}")

    def sync_transcript(
        self,
        client_folder: str,
        filename: str,
        content: str,
        update_existing: bool = False,
    ) -> bool:
        """
        Sync a transcript file to the repository.

        Args:
            client_folder: Client folder name (e.g., "acme-corp")
            filename: Markdown filename (e.g., "2025-01-04-discovery-call.md")
            content: Markdown content
            update_existing: Whether to update if file exists

        Returns:
            True if file was synced, False if skipped
        """
        path = f"transcripts/{client_folder}/{filename}"
        commit_message = f"Add transcript: {client_folder}/{filename}"

        return self.create_or_update_file(
            path=path,
            content=content,
            commit_message=commit_message,
            update_existing=update_existing,
        )

    def sync_client_index(
        self,
        client_folder: str,
        content: str,
    ) -> bool:
        """
        Sync or update a client's index file.

        Args:
            client_folder: Client folder name
            content: Index markdown content

        Returns:
            True if file was synced
        """
        path = f"transcripts/{client_folder}/README.md"
        commit_message = f"Update index: {client_folder}"

        return self.create_or_update_file(
            path=path,
            content=content,
            commit_message=commit_message,
            update_existing=True,  # Always update index
        )

    def list_existing_transcripts(self, client_folder: str) -> list[str]:
        """List existing transcript files for a client."""
        path = f"transcripts/{client_folder}"
        try:
            contents = self.repo.get_contents(path, ref=self.branch)
            if isinstance(contents, list):
                return [
                    c.name for c in contents
                    if c.name.endswith(".md") and c.name != "README.md"
                ]
            return []
        except GithubException as e:
            if e.status == 404:
                return []
            raise


class LocalSync:
    """Sync markdown files to a local directory (for testing/preview)."""

    def __init__(self, output_dir: Path):
        """
        Initialize local sync.

        Args:
            output_dir: Base directory for output
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def sync_transcript(
        self,
        client_folder: str,
        filename: str,
        content: str,
        update_existing: bool = False,
    ) -> bool:
        """Sync a transcript file locally."""
        folder = self.output_dir / "transcripts" / client_folder
        folder.mkdir(parents=True, exist_ok=True)

        file_path = folder / filename

        if file_path.exists() and not update_existing:
            return False

        file_path.write_text(content)
        return True

    def sync_client_index(
        self,
        client_folder: str,
        content: str,
    ) -> bool:
        """Sync a client's index file locally."""
        folder = self.output_dir / "transcripts" / client_folder
        folder.mkdir(parents=True, exist_ok=True)

        file_path = folder / "README.md"
        file_path.write_text(content)
        return True

    def list_existing_transcripts(self, client_folder: str) -> list[str]:
        """List existing transcript files for a client."""
        folder = self.output_dir / "transcripts" / client_folder
        if not folder.exists():
            return []

        return [
            f.name for f in folder.iterdir()
            if f.suffix == ".md" and f.name != "README.md"
        ]
