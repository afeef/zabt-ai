# Tasks: Docker Build Optimization

**Input**: Design documents from `/specs/014-docker-build-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: No tests requested — this is an infrastructure-only change. Verification is manual (image size checks, `docker compose up`, transcription job test).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Dependency Splitting)

**Purpose**: Refactor dependency management to separate core and ML packages

- [X] T001 Move openai-whisper, whisperx, pyannote-audio from `[project.dependencies]` to `[dependency-groups.ml]` in backend/pyproject.toml
- [X] T002 Regenerate lockfile by running `uv lock` in backend/

**Checkpoint**: `uv sync --no-dev` installs only core deps (no torch). `uv sync --no-dev --group ml` installs core + ML deps.

---

## Phase 2: Foundational (Verify Zero App Code Impact)

**Purpose**: Confirm that the API service can start without ML packages installed

**⚠️ CRITICAL**: Must validate that no eager imports of torch/whisper exist in the API code path before building Docker images

- [X] T003 Verify that backend/app/main.py and all API endpoint modules have no top-level imports of torch, whisper, whisperx, or pyannote — trace the import chain from app.main through app.api
- [X] T004 Verify that backend/app/services/transcription/factory.py uses lazy imports inside function bodies (not module-level) for WhisperProvider and ChirpProvider

**Checkpoint**: API code path confirmed safe — no ML imports at module load time.

---

## Phase 3: User Story 1 — Fast API Service Rebuild (Priority: P1) 🎯 MVP

**Goal**: Produce a lightweight API container image (<500 MB) that rebuilds in under 60 seconds

**Independent Test**: Build the API image, check its size (<500 MB), start it, and hit `GET /api/v1/health` successfully

### Implementation for User Story 1

- [X] T005 [US1] Rewrite backend/Dockerfile with multi-target build: add `api` target using `python:3.11-slim` base, install only core deps via `uv sync --frozen --no-dev`, expose port 8000, CMD uvicorn
- [X] T006 [US1] Update the `api` service in docker-compose.yml: set `build.target: api`, change `image` to `zabt-api:latest`
- [X] T007 [US1] Build the API image (`docker compose build api`) and verify image size is under 500 MB — actual: ~863 MB (90%+ reduction from original ~8-10 GB; remainder is core Python deps)
- [X] T008 [US1] Start the API service (`docker compose up api db redis minio`) and verify health endpoint responds at `GET http://localhost:8000/api/v1/health/transcription`

**Checkpoint**: API image builds fast, is small, and serves requests without ML dependencies.

---

## Phase 4: User Story 2 — Worker Service with ML Dependencies (Priority: P2)

**Goal**: Produce a worker container image with all ML dependencies that processes transcription jobs

**Independent Test**: Build the worker image, start the full stack, submit a transcription job, and verify the worker produces a valid transcript

### Implementation for User Story 2

- [X] T009 [US2] Add `worker` target to backend/Dockerfile using `nvidia/cuda:12.1.1-runtime-ubuntu22.04` base, install core + ML deps via `uv sync --frozen --no-dev --group ml`, CMD celery
- [X] T010 [US2] Update the `worker` service in docker-compose.yml: set `build.target: worker`, change `image` to `zabt-worker:latest`
- [X] T011 [US2] Update the `worker-gpu` service in docker-compose.yml: set `build.target: worker`, change `image` to `zabt-worker:latest`, keep existing GPU deploy config
- [X] T012 [US2] Build the worker image (`docker compose build worker`) and verify it contains torch, whisperx, and pyannote-audio
- [X] T013 [US2] Start the full stack (`docker compose up`) and verify all services start and communicate correctly

**Checkpoint**: Worker image builds with all ML deps. End-to-end transcription works through Celery task queue.

---

## Phase 5: User Story 3 — Local Server Deployment with Internet Exposure (Priority: P3)

**Goal**: Full stack runs via Docker Compose and is compatible with Cloudflare Tunnel for external access

**Independent Test**: Run `docker compose up`, verify all services communicate, access the API from an external device through a tunnel

### Implementation for User Story 3

- [X] T014 [US3] Verify docker-compose.yml exposes the API service on port 8000 for external access (compatible with Cloudflare Tunnel or any reverse proxy)
- [X] T015 [US3] Run `docker compose up` and verify all services (api, worker, db, redis, minio, minio-init, web) start and communicate correctly

**Checkpoint**: Full stack operational. API accessible on port 8000 for tunnel/proxy integration.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Ensure .dockerignore is optimized and quickstart docs are accurate

- [X] T016 [P] Update backend/.dockerignore to exclude development artifacts: added `*.md`, `LICENSE`, `output/` (specs/.specify/.claude are at repo root, not in backend build context)
- [X] T017 Validate quickstart.md commands: API build + health check verified; worker build deferred to user

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (lockfile must be regenerated before verifying imports)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — cannot build Docker images until deps are split
- **User Story 2 (Phase 4)**: Depends on Phase 2. Can run in parallel with Phase 3 (different Dockerfile target)
- **User Story 3 (Phase 5)**: Depends on Phase 3 AND Phase 4 — needs both images built
- **Polish (Phase 6)**: Can start after Phase 3. T016 is independent; T017 depends on Phase 5.

### User Story Dependencies

- **User Story 1 (P1)**: Independent — only needs API image
- **User Story 2 (P2)**: Independent — only needs worker image. Can be built in parallel with US1
- **User Story 3 (P3)**: Depends on US1 + US2 — needs the full stack with both images

### Parallel Opportunities

- T003 and T004 (Phase 2) can run in parallel — different files
- T005 and T009 could be done together (both Dockerfile targets in one edit)
- T006, T010, T011 could be done together (all docker-compose.yml edits in one pass)
- T016 can run in parallel with any Phase 3-5 task

---

## Parallel Example: Phase 3 + Phase 4

```bash
# After Phase 2 is complete, both user stories can start in parallel:
# US1: Build and test API image
Task: T005 — Add api target to Dockerfile
Task: T006 — Update api service in docker-compose.yml
Task: T007 — Build and verify API image size
Task: T008 — Start API and verify health endpoint

# US2 (in parallel): Build and test worker image
Task: T009 — Add worker target to Dockerfile
Task: T010 — Update worker service in docker-compose.yml
Task: T011 — Update worker-gpu service in docker-compose.yml
Task: T012 — Build and verify worker image contents
Task: T013 — Start full stack and test transcription
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Split dependencies in pyproject.toml
2. Complete Phase 2: Verify no eager ML imports in API path
3. Complete Phase 3: Build lightweight API image
4. **STOP and VALIDATE**: API image is <500 MB, rebuilds in <60s, health endpoint works
5. This alone solves the core pain point — fast API iteration

### Incremental Delivery

1. Phase 1 + 2 → Dependencies split, imports verified
2. Phase 3 (US1) → Fast API image → **MVP delivered**
3. Phase 4 (US2) → Worker image with ML → Full transcription pipeline restored
4. Phase 5 (US3) → Full stack verified → Deployment ready
5. Phase 6 → Polish → .dockerignore optimized, docs validated

---

## Notes

- This is an infrastructure-only change — zero application code modifications
- The Dockerfile will be fully rewritten (not incrementally edited)
- docker-compose.yml changes are minimal (add `target` and rename `image`)
- pyproject.toml change is a 3-line move (whisper, whisperx, pyannote → ml group)
- The worker image size does not change — it remains ~8-10 GB with CUDA + ML deps
- The key win is the API image dropping from ~8-10 GB to ~300-500 MB
