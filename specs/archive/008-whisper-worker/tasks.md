---
description: "Task list for WhisperX Transcription Backend"
---

# Tasks: WhisperX Transcription Backend

**Input**: Design documents from `/specs/008-whisper-worker/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.yaml

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic dependencies

- [x] T000 Add `docker-compose.yml` defining the FastAPI, Redis, MinIO, and Celery worker services with `deploy.resources.reservations.devices` for NVIDIA GPU access
- [x] T001 Add `whisperx`, `boto3`, `pyannote-audio`, `whisper`, and `celery` dependencies to `backend/pyproject.toml`
- [x] T002 Add `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME`, `WHISPER_MODEL`, and `HF_AUTH_TOKEN` settings to `backend/app/core/config.py`
- [x] T003 [P] Configure the Celery application and Redis broker connection within `backend/app/worker.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004 [P] Update `Meeting` SQLModel in `backend/app/models.py` including `status`, `sub_status`, and `file_path`
- [ ] T005 [P] Create `TranscriptSegment` SQLModel in `backend/app/models.py` with JSONB word-arrays and relationships
- [x] T006 Generate and apply Alembic migration for the new SQLModel database schemas

**Checkpoint**: Foundation ready - Database schema matches the new Media/Whisper needs.

---

## Phase 3: User Story 1 - High-Quality Audio Transcription & Diarization (Priority: P1) 🎯 MVP

**Goal**: Automatically transcribe uploaded audio and accurately identify different speakers.

**Independent Test**: Trigger a hardcoded meeting record directly via Celery and verify it outputs accurately to the database.

### Implementation for User Story 1

- [x] T007 [US1] Create `S3StorageService` in `backend/app/services/storage.py` handling Presigned Upload URL generation and downloading
- [x] T008 [US1] Implement `TranscriptionService` class in `backend/app/services/transcription.py` detailing the WhisperX setup
- [x] T009 [US1] Update `process_meeting` Celery task in `backend/app/worker.py` to download the S3 file, process via `TranscriptionService`, and persist structured segments to PostgreSQL
- [x] T010 [P] [US1] Implement `POST /api/v1/meetings/presigned-upload` endpoint in `backend/app/api/endpoints/meetings.py` for UI S3 uploads
- [x] T011 [P] [US1] Implement `POST /api/v1/meetings/` endpoint in `backend/app/api/endpoints/meetings.py` to commit the record and enqueue the async Celery job

**Checkpoint**: At this point, User Story 1 is functionally complete, capable of streaming generic transcribed chunks back to the API.

---

## Phase 4: User Story 2 - Real-Time Granular Progress Tracking (Priority: P2)

**Goal**: Push real-time status updates of the transcription job so the UI stays updated.

**Independent Test**: Trigger an upload and verify the DB rapidly transitions between transcribing, aligning, and diarizing.

### Implementation for User Story 2

- [x] T012 [P] [US2] Expose callback hooks in `TranscriptionService` (`backend/app/services/transcription.py`) for pipeline stage transitions
- [x] T013 [US2] Update `backend/app/worker.py` Celery task to bind to the hooks and write synchronous DB `sub_status` updates

---

## Phase 5: User Story 3 - Resilient Hardware Degradation (Priority: P3)

**Goal**: Use GPU natively if available, fallback gracefully to CPU if CUDA is missing.

**Independent Test**: Rip out the GPU context or run on bare metal and verify int8 CPU transcribes cleanly.

### Implementation for User Story 3

- [x] T014 [US3] Incorporate the PyTorch `torch.cuda.is_available()` hardware detection logic directly inside `backend/app/services/transcription.py`, managing `compute_type` and batch sizing appropriately

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T015 [P] Add E2E tests for the meeting upload flow in `tests/e2e/test_whisper_upload_flow.py` via Playwright
- [x] T016 Write unit tests testing the CPU fallback logic without requiring real Audio in `backend/tests/test_transcription_service.py`
- [x] T017 Update frontend API logic `frontend-2/app/lib/api.ts` to request Presigned URLs, securely upload the media file directly to MinIO, and then send the `file_key` back to the Backend API.

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete
