"""CLI for Gong to GitHub sync."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from .gong_client import GongClient
from .github_sync import GitHubSync, LocalSync
from .markdown_converter import (
    call_to_markdown,
    generate_client_folder_name,
    generate_client_index,
    generate_filename,
)
from .state import SyncState, load_state, save_state, update_last_sync

load_dotenv()


@click.group()
@click.option(
    "--gong-access-key",
    envvar="GONG_ACCESS_KEY",
    required=True,
    help="Gong API access key",
)
@click.option(
    "--gong-secret-key",
    envvar="GONG_SECRET_KEY",
    required=True,
    help="Gong API secret key",
)
@click.option(
    "--gong-api-url",
    envvar="GONG_API_URL",
    default=None,
    help="Gong API base URL (e.g., https://us-67600.api.gong.io)",
)
@click.pass_context
def cli(ctx: click.Context, gong_access_key: str, gong_secret_key: str, gong_api_url: str | None) -> None:
    """Sync Gong call transcripts to GitHub as Markdown files."""
    ctx.ensure_object(dict)
    ctx.obj["gong_client"] = GongClient(gong_access_key, gong_secret_key, gong_api_url)


@cli.command()
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("./output"),
    help="Output directory for markdown files",
)
@click.option(
    "--state-file",
    type=click.Path(path_type=Path),
    default=Path("./.gong-sync-state.json"),
    help="State file for incremental sync",
)
@click.option(
    "--full-sync",
    is_flag=True,
    help="Ignore state and sync all calls",
)
@click.option(
    "--update-existing",
    is_flag=True,
    help="Update existing files",
)
@click.pass_context
def sync_local(
    ctx: click.Context,
    from_date: datetime | None,
    to_date: datetime | None,
    output_dir: Path,
    state_file: Path,
    full_sync: bool,
    update_existing: bool,
) -> None:
    """Sync transcripts to local directory."""
    gong_client: GongClient = ctx.obj["gong_client"]
    local_sync = LocalSync(output_dir)

    # Load state
    state = SyncState() if full_sync else load_state(state_file)

    # Use last sync timestamp if no from_date specified
    if not from_date and state.last_sync_timestamp and not full_sync:
        from_date = state.last_sync_timestamp
        click.echo(f"Resuming from last sync: {from_date}")

    click.echo("Fetching calls from Gong...")

    # Group calls by client
    calls_by_client: dict[str, list] = defaultdict(list)
    call_count = 0

    with click.progressbar(
        gong_client.get_full_calls(from_date=from_date, to_date=to_date),
        label="Processing calls",
    ) as calls:
        for call in calls:
            call_count += 1
            client_folder = generate_client_folder_name(call)
            calls_by_client[client_folder].append(call)

    click.echo(f"\nFound {call_count} calls for {len(calls_by_client)} clients")

    # Sync calls
    synced_count = 0
    skipped_count = 0
    for client_folder, client_calls in calls_by_client.items():
        click.echo(f"\n[{client_folder}] Syncing {len(client_calls)} calls...")

        for call in client_calls:
            filename = generate_filename(call)
            content = call_to_markdown(call)

            if local_sync.sync_transcript(
                client_folder=client_folder,
                filename=filename,
                content=content,
                update_existing=update_existing,
            ):
                synced_count += 1
                click.echo(f"  + {filename}")
            else:
                skipped_count += 1
                click.echo(f"  = {filename} (exists)")

        # Generate client index
        client_name = client_folder.replace("-", " ").title()
        index_content = generate_client_index(client_name, client_calls)
        local_sync.sync_client_index(client_folder, index_content)

    # Update state
    update_last_sync(state)
    save_state(state, state_file)

    click.echo(f"\nSynced {synced_count} new, {skipped_count} already existed → {output_dir}")


@cli.command()
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    required=True,
    help="GitHub personal access token",
)
@click.option(
    "--repo",
    envvar="GITHUB_REPO",
    required=True,
    help="GitHub repository (owner/repo)",
)
@click.option(
    "--branch",
    default="main",
    help="GitHub branch",
)
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--state-file",
    type=click.Path(path_type=Path),
    default=Path("./.gong-sync-state.json"),
    help="State file for incremental sync",
)
@click.option(
    "--full-sync",
    is_flag=True,
    help="Ignore state and sync all calls",
)
@click.option(
    "--update-existing",
    is_flag=True,
    help="Update existing files",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without pushing to GitHub",
)
@click.pass_context
def sync_github(
    ctx: click.Context,
    github_token: str,
    repo: str,
    branch: str,
    from_date: datetime | None,
    to_date: datetime | None,
    state_file: Path,
    full_sync: bool,
    update_existing: bool,
    dry_run: bool,
) -> None:
    """Sync transcripts to GitHub repository."""
    gong_client: GongClient = ctx.obj["gong_client"]

    if dry_run:
        click.echo("[DRY RUN] No changes will be pushed to GitHub")

    github_sync = GitHubSync(github_token, repo, branch)

    # Load state
    state = SyncState() if full_sync else load_state(state_file)

    # Use last sync timestamp if no from_date specified
    if not from_date and state.last_sync_timestamp and not full_sync:
        from_date = state.last_sync_timestamp
        click.echo(f"Resuming from last sync: {from_date}")

    click.echo("Fetching calls from Gong...")

    # Group calls by client
    calls_by_client: dict[str, list] = defaultdict(list)
    call_count = 0

    for call in gong_client.get_full_calls(from_date=from_date, to_date=to_date):
        call_count += 1
        client_folder = generate_client_folder_name(call)
        calls_by_client[client_folder].append(call)

        if call_count % 10 == 0:
            click.echo(f"  Fetched {call_count} calls...")

    click.echo(f"\nFound {call_count} calls for {len(calls_by_client)} clients")

    # Sync calls
    synced_count = 0
    skipped_count = 0
    for client_folder, client_calls in calls_by_client.items():
        click.echo(f"\n[{client_folder}] Syncing {len(client_calls)} calls...")

        for call in client_calls:
            filename = generate_filename(call)
            content = call_to_markdown(call)

            if dry_run:
                click.echo(f"  [DRY] Would sync: {filename}")
                synced_count += 1
                continue

            if github_sync.sync_transcript(
                client_folder=client_folder,
                filename=filename,
                content=content,
                update_existing=update_existing,
            ):
                synced_count += 1
                click.echo(f"  + {filename}")
            else:
                skipped_count += 1
                click.echo(f"  = {filename} (exists)")

        # Generate client index
        if not dry_run:
            client_name = client_folder.replace("-", " ").title()
            index_content = generate_client_index(client_name, client_calls)
            github_sync.sync_client_index(client_folder, index_content)

    # Update state
    if not dry_run:
        update_last_sync(state)
        save_state(state, state_file)

    click.echo(f"\nSynced {synced_count} new, {skipped_count} already existed → {repo}")


@cli.command()
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--client",
    help="Filter by client name (case-insensitive, partial match)",
)
@click.pass_context
def list_calls(
    ctx: click.Context,
    from_date: datetime | None,
    to_date: datetime | None,
    client: str | None,
) -> None:
    """List available calls from Gong."""
    gong_client: GongClient = ctx.obj["gong_client"]

    click.echo("Fetching calls from Gong...")

    calls_by_client: dict[str, list] = defaultdict(list)
    client_filter = client.lower() if client else None

    for call in gong_client.get_full_calls(from_date=from_date, to_date=to_date):
        client_folder = generate_client_folder_name(call)
        # Apply client filter if specified
        if client_filter and client_filter not in client_folder.lower():
            continue
        calls_by_client[client_folder].append(call)

    click.echo(f"\nFound {sum(len(c) for c in calls_by_client.values())} external calls\n")

    for client_folder in sorted(calls_by_client.keys()):
        client_calls = calls_by_client[client_folder]
        click.echo(f"[{client_folder}] {len(client_calls)} calls")

        for call in sorted(client_calls, key=lambda c: c.metadata.started or datetime.min):
            date_str = "N/A"
            if call.metadata.started:
                date_str = call.metadata.started.strftime("%Y-%m-%d")

            title = call.metadata.title or "Untitled"
            click.echo(f"  - {date_str}: {title}")


@cli.command()
@click.pass_context
def list_users(ctx: click.Context) -> None:
    """List all Gong users."""
    gong_client: GongClient = ctx.obj["gong_client"]

    click.echo("Fetching users from Gong...")

    users = gong_client.get_users()

    click.echo(f"\nFound {len(users)} users\n")

    for user in sorted(users, key=lambda u: u.full_name):
        status = "active" if user.active else "inactive"
        click.echo(f"  - {user.full_name} ({user.email_address}) [{status}]")


if __name__ == "__main__":
    cli()
