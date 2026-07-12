# Data Model: Transcription Type Selection

## Modified Entities

### Meeting (existing table)

**New field:**

| Field | Type | Default | Nullable | Description |
|-------|------|---------|----------|-------------|
| `transcription_type` | VARCHAR | `"general"` | No | Which transcription model was used: `"general"` (WhisperX) or `"medical"` (MedASR) |

**Migration**: Alembic migration adds column with `server_default="normal"`. All existing rows get `"general"` automatically.

## Modified Data Transfer Objects

### MeetingCreateWithKey (request body for POST /meetings/)

**New field:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `transcription_type` | string | No | `"general"` | User's selected transcription type |

### YouTubeIngestRequest (request body for POST /meetings/youtube)

**New field:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `transcription_type` | string | No | `"general"` | User's selected transcription type |

### MeetingRead (response body)

**New field:**

| Field | Type | Description |
|-------|------|-------------|
| `transcription_type` | string | The transcription type used for this meeting |

## GPU Worker Job Input (modified)

**New field in job payload:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `transcription_type` | string | No | `"general"` | Routes to WhisperX (`"general"`) or MedASR (`"medical"`) |
