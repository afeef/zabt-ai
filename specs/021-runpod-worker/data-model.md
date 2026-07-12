# Data Model: Transcription Worker Provider Switch

## No New Entities

This feature introduces no new database tables or model changes. The existing models remain unchanged:

- **Meeting**: `transcript_text`, `status`, `sub_status` — written by worker as before
- **TranscriptSegment**: `meeting_id`, `start_time`, `end_time`, `text`, `speaker`, `words` — written by worker as before
- **User**: `minutes_used_this_month` — incremented by worker as before

## In-Memory Types (unchanged)

The existing transcription transport types in `backend/app/services/transcription/types.py` are used by both providers:

- `TranscriptionResult` — returned by both WhisperProvider and RunPodProvider
- `ResultSegment` — individual transcript segments with speaker labels
- `WordTimestamp` — word-level timing and speaker info
- `TranscriptionConfig` — diarization settings passed to providers

## Configuration (new settings in config.py)

New fields on the `Settings` class:

- `TRANSCRIPTION_PROVIDER: str = "local"` — provider toggle
- `RUNPOD_API_KEY: str = ""` — RunPod authentication
- `RUNPOD_ENDPOINT_ID: str = ""` — RunPod Serverless endpoint
- `RUNPOD_POLL_INTERVAL: int = 5` — polling interval in seconds
- `RUNPOD_TIMEOUT: int = 1800` — job timeout in seconds
