# Implementation Plan: Fix MinIO Connection & Direct Upload

Resolve the `ConnectionRefusedError` for MinIO in Docker and implement a missing direct upload endpoint for meetings. This ensures reliable internal networking and provides a straightforward multipart upload path for the frontend.

## Proposed Changes

### [Backend Infrastructure]

#### [MODIFY] [docker-compose.yml](file:///path/to/zabt-ai/docker-compose.yml)
- Set `MINIO_ENDPOINT=minio:9000` for `api`, `worker`, and `worker-gpu`.

### [Service Layer]

#### [MODIFY] [app/services/storage.py](file:///path/to/zabt-ai/backend/app/services/storage.py)
- Implement `upload_file(file_data: bytes, object_key: str, content_type: str)` using `boto3`.

#### [MODIFY] [app/services/ai_agent.py](file:///path/to/zabt-ai/backend/app/services/ai_agent.py)
- Revert to minimal `OpenAIModel` and `Agent` initialization using `output_type`.

#### [MODIFY] [app/services/transcription.py](file:///path/to/zabt-ai/backend/app/services/transcription.py)
- Implement `transcribe_audio_chunk(data: bytes)` for real-time API support.

### [API Layer]

#### [MODIFY] [app/api/v1/endpoints/meetings.py](file:///path/to/zabt-ai/backend/app/api/v1/endpoints/meetings.py)
- Implement `POST /upload` endpoint:
  - Validate multipart file.
  - Upload to MinIO via `storage.upload_file`.
  - Create `Meeting` record via `meeting_service`.
  - Trigger `process_meeting` Celery task.

## Constitution Check

| Gate | Applies When | Check |
|------|-------------|-------|
| API Contract | Adds/modifies endpoints | `specs/010-fix-minio-connection/contracts/` will define `POST /upload`. |
| Auth/Security | Handles user data | User ownership enforced via `current_user` dependency. |
| Env Config | New variables | `MINIO_ENDPOINT` verified. |
| Repository Pattern | Data access | All DB operations via `meeting_service`. |

## Verification Plan

### Automated Tests
- **Integration Test**: Mock file upload to `/api/v1/meetings/upload` and verify S3 state and DB record.

### Manual Verification
1. **Connectivity**: Verify no connection errors in backend logs.
2. **Upload**: Verify file arrives in MinIO and Celery picks it up.
