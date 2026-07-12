# Tasks: GPU Worker Extraction

**Input**: Design documents from `/specs/025-gpu-worker-extraction/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/gpu-service-api.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (New Repository)

**Purpose**: Initialize the zabt-gpu-worker repository and project structure

- [x] T001 Create new GitHub repository `zabt-gpu-worker` and clone it locally
- [x] T002 Create `zabt-gpu-worker/pyproject.toml` with dependencies: torch, whisperx, pyannote-audio, runpod, fastapi, uvicorn, httpx, sentry-sdk, pydantic-settings
- [x] T003 [P] Create `zabt-gpu-worker/src/config.py` with settings: MODE, WHISPER_MODEL, DIARIZATION_MODEL, HF_AUTH_TOKEN, SENTRY_DSN, SENTRY_ENVIRONMENT, PORT, COST_PER_MINUTE
- [x] T004 [P] Create `zabt-gpu-worker/src/models.py` with request/response schemas: TranscriptionJobRequest, TranscriptionJobStatus, TranscriptionResult, ResultSegment, WordTimestamp (matching contracts/gpu-service-api.md)

---

## Phase 2: Foundational (GPU Service Core)

**Purpose**: Move the shared pipeline code and set up entry points

- [x] T005 Copy `backend/app/services/transcription/pipeline.py` to `zabt-gpu-worker/src/pipeline.py` and adapt imports to use local config.py and models.py (remove all backend app imports)
- [x] T006 Create `zabt-gpu-worker/scripts/download_models.py` — script that pre-downloads WhisperX model and pyannote diarization model to the local cache directory (runs during Docker build)
- [x] T007 Create `zabt-gpu-worker/Dockerfile` — CUDA 12.8 base, install dependencies, run download_models.py to bake models into image, set entrypoint to `python -m src.main`
- [x] T008 Create `zabt-gpu-worker/src/main.py` — entry point that reads MODE env var and starts either RunPod handler or FastAPI server

**Checkpoint**: GPU service project structure complete, Dockerfile builds with models baked in

---

## Phase 3: User Story 2 - Standalone GPU Service (Priority: P1)

**Goal**: GPU service runs in both RunPod and local HTTP modes with identical output

**Independent Test**: Build image, run in local mode, POST an audio URL, receive transcript JSON

### Implementation

- [x] T009 [US2] Create `zabt-gpu-worker/src/handler.py` — RunPod serverless handler: receives job input (audio_url, language, min/max_speakers), downloads audio, runs pipeline, returns TranscriptionResult, flushes Sentry before return. Migrate from existing `runpod/handler.py`
- [x] T010 [US2] Create `zabt-gpu-worker/src/server.py` — FastAPI local HTTP server with POST /run (accepts TranscriptionJobRequest, spawns background task, returns job_id + QUEUED status) and GET /status/{job_id} (returns TranscriptionJobStatus with QUEUED/IN_PROGRESS/COMPLETED/FAILED). Use in-memory dict for job tracking
- [x] T011 [US2] Initialize Sentry SDK in `zabt-gpu-worker/src/main.py` with environment tag (runpod/local) and flush on handler completion
- [x] T012 [US2] Create `zabt-gpu-worker/.env.example` with all env vars from quickstart.md
- [ ] T013 [US2] Build and test GPU service image locally: `docker build -t zabt-gpu-worker .` and run in local mode with a test audio file

**Checkpoint**: GPU service works standalone in both modes

---

## Phase 4: User Story 3 - Unified Communication Protocol (Priority: P1)

**Goal**: Main worker uses same client code for both RunPod and local GPU service

**Independent Test**: Switch TRANSCRIPTION_PROVIDER between `runpod` and `gpu-local`, verify identical behavior

### Implementation

- [x] T014 [US3] Create `backend/app/services/transcription/gpu_client.py` — unified GpuTranscriptionClient that implements TranscriptionProvider protocol. Two backends: `runpod` (uses RunPod SDK submit/poll) and `gpu-local` (uses httpx to POST /run and GET /status/{job_id}). Exposes `process_audio()` matching the existing provider protocol
- [x] T015 [US3] Update `backend/app/services/transcription/factory.py` — add `gpu-local` provider option that creates GpuTranscriptionClient with local backend. Update `runpod` option to use GpuTranscriptionClient with runpod backend
- [x] T016 [US3] Add `GPU_SERVICE_URL` setting to `backend/app/core/config.py` for local GPU service endpoint
- [x] T017 [US3] Update `backend/.env.example` with GPU_SERVICE_URL variable

**Checkpoint**: Main worker can talk to both RunPod and local GPU service via same code path

---

## Phase 5: User Story 1 - Lightweight Main Worker (Priority: P1)

**Goal**: Main worker has zero GPU/ML dependencies, builds fast

**Independent Test**: Build main worker Docker image, verify < 60s build time, upload audio file, verify full pipeline works via GPU service

### Implementation

- [x] T018 [US1] Remove `whisper_provider.py` from `backend/app/services/transcription/` (moved to GPU service)
- [x] T019 [P] [US1] Remove `pipeline.py` from `backend/app/services/transcription/` (moved to GPU service)
- [x] T020 [P] [US1] Remove old `runpod_provider.py` from `backend/app/services/transcription/` (replaced by gpu_client.py)
- [x] T021 [US1] Remove `ml` dependency group from `backend/pyproject.toml` and remove torch, whisperx, pyannote-audio, openai-whisper from all dependency sections
- [x] T022 [US1] Remove `backend/Dockerfile.worker-base` (no longer needed)
- [x] T023 [US1] Update `backend/Dockerfile` — remove the `worker` target that depends on worker-base. Worker now uses the same lightweight `api` base image. Single target with Celery CMD
- [x] T024 [US1] Update `backend/app/worker.py` — remove local file download logic in stage_download (no longer needed when all transcription goes through GPU service). Clean up imports that reference removed modules
- [x] T025 [US1] Update `docker-compose.yml` — remove model_cache volume, update worker service (vps profile) to use lightweight image, remove GPU-specific env vars (WHISPER_MODEL, DIARIZATION_MODEL, HF_AUTH_TOKEN, CUDA_VISIBLE_DEVICES, OMP_NUM_THREADS, CTRANS2_NUM_THREADS) from worker service. Keep TRANSCRIPTION_PROVIDER, RUNPOD_* vars. Replace the old `worker-gpu` service (local profile) with a new `worker-gpu` service that uses the `zabt-gpu-worker` image in local HTTP mode (MODE=local, port 8001, NVIDIA GPU resources), keeping the service name `worker-gpu`
- [x] T026 [US1] Remove `runpod/` directory from main repo (handler.py, Dockerfile, settings moved to zabt-gpu-worker)
- [x] T027 [US1] Run `uv lock` to regenerate lock file without ML dependencies in `backend/`
- [x] T028 [US1] Build main worker Docker image and verify build time < 60 seconds

**Checkpoint**: Main worker builds fast, no GPU dependencies, full pipeline works via GPU service

---

## Phase 6: User Story 4 - Error Monitoring in GPU Service (Priority: P2)

**Goal**: GPU service errors and performance data visible in Sentry

**Independent Test**: Trigger error with corrupt audio, verify it appears in Sentry dashboard

### Implementation

- [x] T029 [US4] Add Sentry performance spans in `zabt-gpu-worker/src/pipeline.py` for each stage: audio download, transcription, alignment, diarization
- [x] T030 [US4] Add error context (job_id, audio_url, model names) to Sentry captures in `zabt-gpu-worker/src/handler.py` and `zabt-gpu-worker/src/server.py`
- [ ] T031 [US4] Test error reporting: submit job with invalid audio URL, verify error appears in Sentry with full context

**Checkpoint**: All GPU service errors and performance data flow to Sentry

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and documentation

- [ ] T032 Create `zabt-gpu-worker/README.md` with build, run, deploy, and env var documentation
- [ ] T033 Update `ROADMAP.md` in main repo — mark GPU worker extraction as completed
- [x] T034 Remove any remaining dead imports or unused GPU-related code across `backend/app/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (US2 - GPU Service)**: Depends on Phase 2
- **Phase 4 (US3 - Unified Protocol)**: Depends on Phase 2 (can run in parallel with Phase 3)
- **Phase 5 (US1 - Lightweight Worker)**: Depends on Phase 3 AND Phase 4 (needs GPU service running + unified client ready before removing old code)
- **Phase 6 (US4 - Monitoring)**: Depends on Phase 3 (GPU service must exist)
- **Phase 7 (Polish)**: Depends on all previous phases

### Parallel Opportunities

- T003 and T004 can run in parallel (different files in new repo)
- T018, T019, T020 can run in parallel (deleting independent files)
- Phase 3 (GPU service) and Phase 4 (unified client) can start in parallel after Phase 2
- Phase 6 (monitoring) can start as soon as Phase 3 is done

---

## Implementation Strategy

### MVP First (Phases 1-4)

1. Set up new repo with pipeline code and dual-mode entry points (Phases 1-2)
2. Build and validate GPU service works (Phase 3)
3. Create unified client in main worker (Phase 4)
4. **STOP and VALIDATE**: Test end-to-end pipeline with GPU service
5. Only then proceed to remove old code (Phase 5)

### Incremental Delivery

1. GPU service repo created and tested → Phase 3 checkpoint
2. Main worker uses new client → Phase 4 checkpoint
3. Old GPU code removed, lightweight build → Phase 5 checkpoint
4. Monitoring added → Phase 6 checkpoint
5. Each phase adds value without breaking the existing pipeline

---

## Notes

- Phase 5 (removing old code) is intentionally LAST — migration safety requires the GPU service to be validated before removing fallback code
- The `runpod/` directory in the main repo is fully replaced by the new `zabt-gpu-worker` repo
- The worker-gpu Docker Compose service (local profile) will be replaced by running zabt-gpu-worker image directly
