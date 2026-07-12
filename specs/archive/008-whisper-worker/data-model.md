# Data Model: WhisperX Transcription Backend

**Feature Branch**: `008-whisper-worker`

## 1. Entities

### 1.1 `TranscriptSegment`
Represents a block of transcribed logic associated with a specific identified speaker and bounded by precise Float timestamps.
- `id` (Integer, Primary Key)
- `meeting_id` (Integer, Foreign Key to `meeting.id`, Indexed)
- `start_time` (Float, e.g., `12.541`)
- `end_time` (Float, e.g., `15.902`)
- `text` (String)
- `speaker` (String, e.g., `"SPEAKER_00"`)

### 1.2 `TranscriptWord` 
*(Note: A JSONB array inside the `TranscriptSegment` OR a distinct table, but for Phase 1 Performance, this will be represented as a JSONB array column on `TranscriptSegment` to prevent 10,000+ row inserts per hour of meeting)*
- `word` (String)
- `start` (Float)
- `end` (Float)

### 1.3 `Meeting` (Modifications)
The existing meeting model requires fields to track the async job progress and state.
- `status` (String, enum: `queued`, `processing`, `completed`, `failed`)
- `sub_status` (String, null ok, enum: `transcribing`, `aligning`, `diarizing`)
- `file_path` (String) -> Will now store the generic S3 URI, e.g., `s3://zabt-media/user_12/meeting_45.mp3`

## 2. Validation Rules
- `start_time` on a segment MUST NEVER be greater than `end_time`.
- `speaker` MUST be assigned. If diarization fails or the speaker cannot be clustered, the database should gracefully fall back to `"SPEAKER_UNKNOWN"`.
- `file_path` MUST NOT be processed if the payload is zero bytes or if the suffix fails an internal `allowed_extensions` MIME/magic byte check.

## 3. Storage Keys
The system relies on AWS S3/MinIO for blob storage.
The `file_path` on the `Meeting` model will store the object key.
- **Bucket**: `zabt-media` (or dynamic via env)
- **Key Pattern**: `users/{user_id}/meetings/{uuid}_{filename_safe}`
- The FastAPI server negotiates a Presigned Upload URL with MinIO, enabling the Frontend to bypass the backend RAM by streaming `multipart/form-data` directly into the bucket.
- The Celery worker then negotiates a Presigned Download URL with MinIO to stream the audio binary into memory or tempfs for WhisperX.
