# Gong to GitHub - Technical Specification

## Overview

**gong-to-github** synchronizes call transcripts from Gong.io to a GitHub repository as Markdown files, organized by client.

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│    Gong API     │      │   gong-to-github     │      │     GitHub      │
│                 │      │                      │      │                 │
│  /v2/calls      │─────▶│  GongClient          │      │  transcripts/   │
│  /v2/extensive  │      │    ↓                 │      │   ├── acme/     │
│  /v2/transcript │      │  MarkdownConverter   │─────▶│   │   └── *.md  │
│  /v2/users      │      │    ↓                 │      │   └── bigcorp/  │
│                 │      │  GitHubSync/LocalSync│      │       └── *.md  │
└─────────────────┘      └──────────────────────┘      └─────────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │  .gong-sync-state │
                         │      (JSON)       │
                         └───────────────────┘
```

## Components

### 1. GongClient (`gong_client.py`)

**Responsibility:** Interact with Gong API with rate limiting and pagination.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_users()` | `GET /v2/users` | Fetch all Gong users (cached) |
| `list_calls()` | `POST /v2/calls` | List calls with date/scope filters |
| `get_calls_extensive()` | `POST /v2/calls/extensive` | Get call metadata + participants |
| `get_transcripts()` | `POST /v2/calls/transcript` | Get transcript text |
| `get_full_calls()` | (composite) | Combine metadata + participants + transcript |

**Rate Limiting:**
- 3 requests/second max
- 10,000 requests/day
- Automatic retry on HTTP 429 with exponential backoff

**Batching:**
- Calls are processed in batches of 50
- API requests batch up to 100 call IDs per request

### 2. Models (`models.py`)

```python
Participant     # Call participant (internal/external)
CallMetadata    # Call info (title, date, duration, system)
Sentence        # Single transcript sentence with timestamps
TranscriptSegment  # Speaker segment containing sentences
Call            # Complete call with metadata, parties, transcript
User            # Gong user
SyncState       # Sync progress tracking
```

**Key Properties:**
- `Call.client_name` → Extracts client name from Salesforce context or email domain
- `Call.external_participants` → Filters external (client) participants
- `Call.internal_participants` → Filters internal (team) participants

### 3. MarkdownConverter (`markdown_converter.py`)

**Functions:**

| Function | Input | Output |
|----------|-------|--------|
| `call_to_markdown(call)` | `Call` | Markdown string |
| `generate_filename(call)` | `Call` | `2025-01-04-discovery-call.md` |
| `generate_client_folder_name(call)` | `Call` | `acme-corp` |
| `generate_client_index(name, calls)` | client + calls | Index markdown |

**Markdown Format:**
```markdown
# {title}

**Date:** {YYYY-MM-DD HH:MM}
**Duration:** {X min}

**Participants:**
- {name} (Internal) - {title}
- {name} (External) - {title}

**System:** {Zoom} | **Type:** {External}

[View in Gong]({url})

---

## Transcript

**[MM:SS] {Speaker}:**
{text}
```

### 4. GitHubSync / LocalSync (`github_sync.py`)

**GitHubSync** (production):
- Uses PyGithub to create/update files via GitHub API
- Creates one commit per file
- Checks file existence before creating

**LocalSync** (development/preview):
- Writes files to local filesystem
- Same interface as GitHubSync

**Output Structure:**
```
transcripts/
├── {client-slug}/
│   ├── README.md                    # Client index
│   ├── {date}-{title-slug}.md       # Call transcript
│   └── ...
└── {another-client}/
    └── ...
```

### 5. State Management (`state.py`)

**SyncState Schema:**
```json
{
  "last_sync_timestamp": "2025-01-04T14:00:00",
  "synced_call_ids": ["call-1", "call-2", "call-3"]
}
```

**Functions:**
- `load_state(path)` → Load from JSON file
- `save_state(state, path)` → Persist to JSON file
- `mark_call_synced(state, call_id)` → Add call to synced list
- `is_call_synced(state, call_id)` → Check if already synced
- `update_last_sync(state)` → Update timestamp

### 6. CLI (`cli.py`)

**Commands:**

| Command | Description |
|---------|-------------|
| `list-users` | Show all Gong users |
| `list-calls` | Show calls grouped by client |
| `sync-local` | Sync to local directory |
| `sync-github` | Sync to GitHub repository |

**Global Options:**
- `--gong-access-key` / `GONG_ACCESS_KEY`
- `--gong-secret-key` / `GONG_SECRET_KEY`

**Sync Options:**
- `--from-date` / `--to-date` → Date range filter
- `--full-sync` → Ignore state, sync everything
- `--update-existing` → Overwrite existing files
- `--dry-run` → Preview without changes (GitHub only)

## Data Flow

### Sync Process

```
1. Load SyncState from .gong-sync-state.json
   └── If no from-date and state exists, use last_sync_timestamp

2. Fetch calls from Gong API
   ├── POST /v2/calls (with date filter, scope=External)
   ├── Batch call IDs (50 at a time)
   ├── POST /v2/calls/extensive (get participants)
   └── POST /v2/calls/transcript (get transcript)

3. For each call:
   ├── Skip if call_id in synced_call_ids (unless --full-sync)
   ├── Extract client name (Salesforce context or email domain)
   ├── Convert to Markdown
   └── Group by client folder

4. For each client:
   ├── Create/update transcript files
   └── Generate README.md index

5. Update SyncState
   ├── Add synced call IDs
   ├── Update last_sync_timestamp
   └── Save to .gong-sync-state.json
```

### Speaker Resolution

```
Transcript provides: speakerId
Extensive provides:  parties[].speakerId, parties[].name, parties[].affiliation

Resolution:
  transcript.speakerId → find in parties → get name + affiliation

Display:
  Internal: "John Doe"
  External: "Jane Smith (Client)"
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/users` | GET | List users for speaker mapping |
| `/v2/calls` | POST | List calls with filters |
| `/v2/calls/extensive` | POST | Get call details + participants |
| `/v2/calls/transcript` | POST | Get transcript text |

## Error Handling

| Error | Handling |
|-------|----------|
| HTTP 429 (Rate Limit) | Retry with exponential backoff (tenacity) |
| HTTP 4xx/5xx | Raise `GongAPIError` with details |
| Missing transcript | Skip call, continue processing |
| Invalid JSON state | Return empty state, start fresh |

## Configuration

**Environment Variables:**
```bash
GONG_ACCESS_KEY=xxx      # Gong API access key
GONG_SECRET_KEY=xxx      # Gong API secret key
GITHUB_TOKEN=xxx         # GitHub personal access token
GITHUB_REPO=owner/repo   # Target repository
```

## Dependencies

| Package | Purpose |
|---------|---------|
| httpx | HTTP client |
| click | CLI framework |
| pydantic | Data validation |
| tenacity | Retry logic |
| pygithub | GitHub API |
| python-dotenv | Environment loading |
