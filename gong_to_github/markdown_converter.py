"""Convert Gong calls to Markdown format."""

import re
from datetime import datetime

from .models import Affiliation, Call, Participant, TranscriptSegment


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def format_timestamp(ms: int) -> str:
    """Format milliseconds as [HH:MM:SS] or [MM:SS]."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
    return f"[{minutes:02d}:{seconds:02d}]"


def format_duration(seconds: int) -> str:
    """Format duration in a human-readable way."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{minutes} min"


def get_speaker_name(
    speaker_id: str,
    parties: list[Participant],
) -> tuple[str, Affiliation | None]:
    """Resolve speaker ID to name and affiliation."""
    for party in parties:
        if party.speaker_id == speaker_id:
            name = party.name or party.email_address or f"Speaker {speaker_id[:8]}"
            return name, party.affiliation

    return f"Speaker {speaker_id[:8]}", None


def format_participant(participant: Participant) -> str:
    """Format a participant for display."""
    parts = []

    name = participant.name or participant.email_address or "Unknown"
    parts.append(name)

    affiliation = "Internal" if participant.affiliation == Affiliation.INTERNAL else "External"
    parts.append(f"({affiliation})")

    if participant.title:
        parts.append(f"- {participant.title}")

    return " ".join(parts)


def call_to_markdown(call: Call) -> str:
    """Convert a Call to Markdown format."""
    lines: list[str] = []

    # YAML Frontmatter
    lines.append("---")
    lines.append(f"gong_id: {call.metadata.id}")
    if call.metadata.started:
        lines.append(f"date: {call.metadata.started.isoformat()}")
    if call.metadata.duration:
        lines.append(f"duration_seconds: {call.metadata.duration}")
    if call.metadata.title:
        # Escape quotes in title for YAML
        safe_title = call.metadata.title.replace('"', '\\"')
        lines.append(f'title: "{safe_title}"')
    if call.client_name:
        lines.append(f"client: {call.client_name}")
    if call.metadata.url:
        lines.append(f"gong_url: {call.metadata.url}")
    if call.metadata.scope:
        lines.append(f"scope: {call.metadata.scope}")
    if call.metadata.system:
        lines.append(f"system: {call.metadata.system}")

    # Participant emails
    internal_emails = [p.email_address for p in call.internal_participants if p.email_address]
    external_emails = [p.email_address for p in call.external_participants if p.email_address]
    if internal_emails:
        lines.append(f"internal_participants: {internal_emails}")
    if external_emails:
        lines.append(f"external_participants: {external_emails}")

    lines.append("---")
    lines.append("")

    # Title
    title = call.metadata.title or "Untitled Call"
    lines.append(f"# {title}")
    lines.append("")

    # Metadata
    if call.metadata.started:
        date_str = call.metadata.started.strftime("%Y-%m-%d %H:%M")
        lines.append(f"**Date:** {date_str}")

    if call.metadata.duration:
        lines.append(f"**Duration:** {format_duration(call.metadata.duration)}")

    # Participants
    if call.parties:
        lines.append("")
        lines.append("**Participants:**")

        # Internal first, then external
        for participant in call.internal_participants:
            lines.append(f"- {format_participant(participant)}")

        for participant in call.external_participants:
            lines.append(f"- {format_participant(participant)}")

    # System info
    meta_parts = []
    if call.metadata.system:
        meta_parts.append(f"**System:** {call.metadata.system}")
    if call.metadata.scope:
        meta_parts.append(f"**Type:** {call.metadata.scope}")
    if call.metadata.media:
        meta_parts.append(f"**Media:** {call.metadata.media}")

    if meta_parts:
        lines.append("")
        lines.append(" | ".join(meta_parts))

    # Gong URL
    if call.metadata.url:
        lines.append("")
        lines.append(f"[View in Gong]({call.metadata.url})")

    # Transcript
    if call.transcript:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Transcript")
        lines.append("")

        for segment in call.transcript:
            speaker_name, affiliation = get_speaker_name(segment.speaker_id, call.parties)

            # Add affiliation indicator
            if affiliation == Affiliation.EXTERNAL:
                speaker_display = f"{speaker_name} (Client)"
            else:
                speaker_display = speaker_name

            for sentence in segment.sentences:
                timestamp = format_timestamp(sentence.start_ms)
                lines.append(f"**{timestamp} {speaker_display}:**")
                lines.append(sentence.text)
                lines.append("")

    return "\n".join(lines)


def generate_filename(call: Call) -> str:
    """Generate a filename for the call markdown file."""
    # Format: YYYY-MM-DD-[title-slug].md
    date_prefix = "unknown-date"
    if call.metadata.started:
        date_prefix = call.metadata.started.strftime("%Y-%m-%d")

    title = call.metadata.title or call.metadata.id
    title_slug = slugify(title)[:50]  # Limit length

    return f"{date_prefix}-{title_slug}.md"


def generate_client_folder_name(call: Call) -> str:
    """Generate a folder name for the client."""
    client_name = call.client_name

    if not client_name:
        # Try to extract from external participants
        for party in call.external_participants:
            if party.email_address:
                domain = party.email_address.split("@")[-1]
                client_name = domain.split(".")[0].title()
                break

    if not client_name:
        client_name = "Unknown-Client"

    return slugify(client_name)


def generate_client_index(client_name: str, calls: list[Call]) -> str:
    """Generate an index markdown file for a client."""
    lines: list[str] = []

    lines.append(f"# {client_name} - Call History")
    lines.append("")
    lines.append(f"Total calls: {len(calls)}")
    lines.append("")

    # Sort calls by date (newest first)
    sorted_calls = sorted(
        calls,
        key=lambda c: c.metadata.started or datetime.min,
        reverse=True,
    )

    lines.append("## Calls")
    lines.append("")
    lines.append("| Date | Title | Duration | Participants |")
    lines.append("|------|-------|----------|--------------|")

    for call in sorted_calls:
        date_str = "N/A"
        if call.metadata.started:
            date_str = call.metadata.started.strftime("%Y-%m-%d")

        title = call.metadata.title or "Untitled"
        filename = generate_filename(call)

        duration = "N/A"
        if call.metadata.duration:
            duration = format_duration(call.metadata.duration)

        participants = len(call.parties)

        lines.append(f"| {date_str} | [{title}](./{filename}) | {duration} | {participants} |")

    return "\n".join(lines)
