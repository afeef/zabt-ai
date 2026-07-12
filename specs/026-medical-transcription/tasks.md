# Tasks: Transcription Type Selection (Normal + Medical)

**Input**: Design documents from `/specs/026-medical-transcription/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story. All three stories are P1 but have natural dependencies: US3 (UI) and US1 (Medical GPU) both depend on US2 (Backend/DB foundation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Prepare dependencies and model infrastructure

- [x] T001 Add `google/medasr` to `zabt-gpu-worker/scripts/download_models.py` — download MedASR model at build time alongside WhisperX and pyannote models
- [x] T002 Add `nemo_toolkit[asr]` dependency to `zabt-gpu-worker/pyproject.toml` (or requirements file) for MedASR inference
- [x] T003 Update `zabt-gpu-worker/Dockerfile` to include MedASR model download step and nemo dependency installation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema and backend model changes shared across all stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `transcription_type` field to `Meeting` model in `backend/app/models.py` — string field with default `"normal"`, valid values `"normal"` and `"medical"`
- [x] T005 Generate Alembic migration for `transcription_type` column in `backend/alembic/versions/` — add column with `server_default="normal"` for zero-downtime deployment
- [x] T006 [P] Add `transcription_type` to `MeetingCreateWithKey` request schema in `backend/app/models.py` — optional string field with default `"normal"`
- [x] T007 [P] Add `transcription_type` to `YouTubeIngestRequest` request schema in `backend/app/models.py` — optional string field with default `"normal"`
- [x] T008 [P] Add `transcription_type` to `MeetingRead` response schema in `backend/app/models.py`

**Checkpoint**: Database and schemas ready for all stories

---

## Phase 3: User Story 2 — Normal Transcription (Default Behavior) (Priority: P1)

**Goal**: Ensure backward compatibility — existing upload flow works unchanged with `transcription_type` defaulting to `"normal"`

**Independent Test**: Upload a file without changing the selector and verify transcript is produced identically to pre-feature behavior

- [x] T009 [US2] Update `create_meeting` endpoint in `backend/app/api/v1/endpoints/meetings.py` to accept and store `transcription_type` from request body (defaults to `"normal"`)
- [x] T010 [US2] Update `ingest_youtube_url` endpoint in `backend/app/api/v1/endpoints/meetings.py` to accept and store `transcription_type` from request body (defaults to `"normal"`)
- [x] T011 [US2] Update `GpuTranscriptionClient._submit()` in `backend/app/services/transcription/gpu_client.py` to include `transcription_type` in the job input payload
- [x] T012 [US2] Update `stage_transcribe` in `backend/app/worker.py` to pass `transcription_type` from the meeting record through to the transcription client

**Checkpoint**: Normal upload flow works with `transcription_type="normal"` passed through to GPU worker (GPU worker ignores unknown fields, so no GPU changes needed yet)

---

## Phase 4: User Story 1 — Medical Transcription Upload (Priority: P1)

**Goal**: GPU worker routes to MedASR when `transcription_type="medical"`, producing identical output format

**Independent Test**: Submit a job to GPU worker with `transcription_type="medical"` and verify transcript JSON matches WhisperX output schema

- [x] T013 [US1] Add `MEDASR_MODEL` setting to `zabt-gpu-worker/src/config.py` — default `"google/medasr"`
- [x] T014 [US1] Add `transcription_type` field to `PipelineConfig` in `zabt-gpu-worker/src/pipeline.py` — string field, default `"normal"`
- [x] T015 [US1] Implement MedASR transcription function in `zabt-gpu-worker/src/pipeline.py` — load MedASR model via NeMo, transcribe audio, return segments in same format as WhisperX
- [x] T016 [US1] Add model routing in `run_pipeline()` in `zabt-gpu-worker/src/pipeline.py` — if `transcription_type=="medical"` use MedASR transcription, else use WhisperX. Both paths feed into same alignment and diarization stages
- [x] T017 [US1] Update `handler.py` in `zabt-gpu-worker/src/handler.py` to read `transcription_type` from job input and pass to `PipelineConfig`
- [x] T018 [US1] Update `server.py` in `zabt-gpu-worker/src/server.py` to read `transcription_type` from request body and pass to `PipelineConfig`
- [x] T019 [US1] Pre-load MedASR model at worker startup in `zabt-gpu-worker/src/handler.py` and `zabt-gpu-worker/src/server.py` alongside WhisperX model to avoid per-request loading

**Checkpoint**: GPU worker can process both normal and medical transcriptions with identical output format

---

## Phase 5: User Story 3 — Transcription Type Selection UI (Priority: P1)

**Goal**: Users can select transcription type in the upload modal and YouTube URL dialog

**Independent Test**: Open upload modal, verify selector defaults to "Normal", switch to "Medical", upload a file, verify meeting detail shows "Medical"

- [x] T020 [US3] Add transcription type RadioGroup (shadcn/ui) to `frontend-2/app/components/upload-modal.tsx` — two options: "Normal" (default) and "Medical". Pass selected value through upload flow to `POST /meetings/` request body
- [x] T021 [US3] Add transcription type RadioGroup (shadcn/ui) to `frontend-2/app/components/youtube-url-dialog.tsx` — same selector, pass value to `POST /meetings/youtube` request body
- [x] T022 [US3] Update `createMeeting()` and `submitYoutubeUrl()` in `frontend-2/app/lib/api.ts` to accept and send `transcription_type` parameter
- [x] T023 [US3] Display transcription type badge on meeting detail page in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — show "Normal" or "Medical" badge near meeting title/metadata

**Checkpoint**: Full end-to-end flow works — user selects type, uploads, sees type on detail page, correct model processes the audio

---

## Phase 6: Docker Build Restructuring

**Goal**: Restructure GPU worker to use uv/pyproject.toml and multi-stage Docker build with base image on Docker Hub

- [x] T024 Initialize `zabt-gpu-worker` as a uv project with `pyproject.toml` — run `uv init` and add all current dependencies (torch, whisperx, pyannote-audio, nemo_toolkit[asr], runpod, fastapi, uvicorn, httpx, sentry-sdk, pydantic-settings) in `zabt-gpu-worker/pyproject.toml`
- [x] T025 Generate `uv.lock` lockfile in `zabt-gpu-worker/` by running `uv lock`
- [x] T026 Create `zabt-gpu-worker/Dockerfile.base` — FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04, install Python 3.11, uv, PyTorch (CUDA 12.8 index). This image rebuilds rarely.
- [x] T027 Refactor `zabt-gpu-worker/Dockerfile` — FROM the base image, copy pyproject.toml/uv.lock, run `uv sync --frozen`, copy src/ and scripts/, run download_models.py. Source-only changes rebuild in seconds.
- [x] T028 ~~Build and push base image~~ — OBSOLETE: Dockerfile.base eliminated, single-stage Dockerfile uses pytorch/pytorch base directly
- [x] T029 Update `docker-compose.yml` worker-gpu service to add `MEDASR_MODEL` env var
- [x] T030 Verify local build: GPU worker Docker image built successfully

## Phase 7: Enum Rename & Cleanup

**Goal**: Rename "normal" to "general" across the codebase using TranscriptionType enum

- [x] T031 Rename `TranscriptionType` enum values in `backend/app/models.py` — `GENERAL = "general"`, `MEDICAL = "medical"` (already done)
- [x] T032 Update `TranscriptionConfig.transcription_type` default to `TranscriptionType.GENERAL` in `backend/app/services/transcription/types.py` (already done)
- [x] T033 Update `MeetingService.update_transcription_type()` parameter type to `TranscriptionType` in `backend/app/services/meeting.py` (already done)
- [x] T034 Update worker.py to use `TranscriptionType.GENERAL` default in `backend/app/worker.py` (already done)
- [x] T035 Update `gpu_client.py` to serialize enum with `.value` at JSON boundary in `backend/app/services/transcription/gpu_client.py` (already done)
- [x] T036 Update Alembic migration server_default from `"normal"` to `"general"` in `backend/alembic/versions/f7a8b9c0d1e2_add_transcription_type_to_meeting.py`
- [x] T037 Update frontend upload-modal.tsx to use `"general"` instead of `"normal"` for default value in `frontend-2/app/components/upload-modal.tsx`
- [x] T038 Update frontend api.ts Meeting type to use `"general" | "medical"` in `frontend-2/app/lib/api.ts`

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T039 E2E test for medical transcription upload flow in `tests/e2e/test_medical_transcription.py` — upload with "Medical" selected, verify meeting record has `transcription_type="medical"`, verify detail page shows badge
- [ ] T040 Rebuild GPU worker Docker image and verify both models load at startup without OOM on RTX 3090
- [ ] T041 Run quickstart.md test scenarios (all 4 scenarios) on VPS to validate end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: No dependency on Phase 1 (different projects)
- **US2 (Phase 3)**: Depends on Phase 2 (schemas must exist)
- **US1 (Phase 4)**: Depends on Phase 1 (MedASR model baked in) + can run parallel to Phase 3
- **US3 (Phase 5)**: Depends on Phase 2 (API accepts `transcription_type`) + Phase 3 (endpoints updated)
- **Docker Build (Phase 6)**: Independent — can run anytime
- **Enum Rename (Phase 7)**: Depends on Phase 2 (models exist)
- **Polish (Phase 8)**: Depends on all stories + Docker build complete

### User Story Dependencies

- **US2 (Normal/Backend)**: Foundation only — no story dependencies
- **US1 (Medical/GPU)**: Independent of US2 and US3 — only needs Phase 1 setup
- **US3 (UI)**: Needs US2 backend changes to send `transcription_type` to API

### Parallel Opportunities

```
Phase 1 (GPU setup) ──────────── → Phase 4 (US1: Medical GPU)
                                                                  → Phase 6 (Polish)
Phase 2 (DB/schemas) → Phase 3 (US2: Backend) → Phase 5 (US3: UI)
```

- T006, T007, T008 can run in parallel (different schema files)
- Phase 1 and Phase 2 can run in parallel (different projects)
- Phase 4 (GPU worker) and Phase 3 (backend) can run in parallel

---

## Implementation Strategy

### MVP First

1. Phase 2: DB migration + schemas
2. Phase 3: Backend passes `transcription_type` through (US2)
3. Phase 5: Frontend selector (US3)
4. **VALIDATE**: Normal uploads still work with new selector
5. Phase 1: GPU worker MedASR setup
6. Phase 4: GPU worker routing (US1)
7. **VALIDATE**: Medical upload produces accurate transcript

### Incremental Delivery

1. Deploy backend + frontend changes first (selector visible, "Normal" works)
2. Deploy GPU worker with MedASR second (medical option becomes functional)
3. Each deployment is independently safe — medical selection without GPU support will fail gracefully with error message (FR-008)

---

## Notes

- MedASR uses NeMo Conformer architecture — verify `nemo_toolkit[asr]` version compatibility with existing CUDA/PyTorch in GPU worker
- MedASR is 105M params vs WhisperX 1.5B — should fit comfortably on RTX 3090 alongside WhisperX
- MedASR outputs CTC-based word timestamps — may need different alignment approach than WhisperX (which uses wav2vec2 alignment)
- Both models share the same pyannote diarization pipeline
