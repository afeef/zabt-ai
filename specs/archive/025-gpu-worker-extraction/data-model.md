# Data Model: GPU Worker Extraction

No new database entities. This feature is a code extraction — no schema changes.

## In-Memory Types (API Contract)

### TranscriptionJobRequest (main worker → GPU service)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| audio_url | string (URL) | Yes | Presigned S3/MinIO download URL for the audio file |
| language | string | No | ISO 639-1 language code (e.g., "en"). Auto-detect if omitted |
| min_speakers | int | No | Minimum expected speakers for diarization (default: 1) |
| max_speakers | int | No | Maximum expected speakers for diarization (default: 10) |

### TranscriptionJobStatus

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique job identifier |
| status | enum | `QUEUED`, `IN_PROGRESS`, `COMPLETED`, `FAILED` |
| output | TranscriptionResult | Present only when status is `COMPLETED` |
| error | string | Present only when status is `FAILED` |

### TranscriptionResult (GPU service → main worker)

| Field | Type | Description |
|-------|------|-------------|
| text | string | Full transcript text with speaker labels |
| language | string | Detected or specified language code |
| segments | list[ResultSegment] | Transcript segments with timing |
| provider_name | string | e.g., "whisperx-runpod" or "whisperx-local" |
| audio_duration_seconds | float | Total audio duration |
| estimated_cost | float | Processing cost estimate |

### ResultSegment

| Field | Type | Description |
|-------|------|-------------|
| start | float | Segment start time (seconds) |
| end | float | Segment end time (seconds) |
| text | string | Segment text content |
| speaker | string | Speaker label (e.g., "SPEAKER_00") |
| words | list[WordTimestamp] | Word-level timestamps |

### WordTimestamp

| Field | Type | Description |
|-------|------|-------------|
| word | string | Individual word |
| start | float | Word start time (seconds) |
| end | float | Word end time (seconds) |
| speaker_label | string | Assigned speaker |
| confidence | float | Recognition confidence (0-1) |
