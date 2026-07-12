# Tasks: S3/MinIO Storage Provider Switch

**Input**: Design documents from `/specs/020-s3-storage-switch/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No automated tests — backend infrastructure refactor validated manually.

**Organization**: Tasks are grouped by user story to enable independent validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new configuration settings and prepare the storage abstraction

- [x] T001 Add `STORAGE_PROVIDER` and `S3_*` settings to `backend/app/core/config.py`
- [x] T002 Refactor `backend/app/services/storage.py` — define `StorageProvider` Protocol with methods: `generate_presigned_upload_url`, `get_presigned_download_url`, `upload_file`, `delete_file`, `provider_name`
- [x] T003 Implement `MinioStorage` class in `backend/app/services/storage.py` (extract from current `S3StorageService`, uses existing `MINIO_*` settings)
- [x] T004 Implement `S3Storage` class in `backend/app/services/storage.py` (uses new `S3_*` settings, boto3 client pointed at `S3_ENDPOINT_URL`)
- [x] T005 Implement `create_storage()` factory function in `backend/app/services/storage.py` that returns `MinioStorage` or `S3Storage` based on `settings.STORAGE_PROVIDER`
- [x] T006 Replace global `storage = S3StorageService()` with `storage = create_storage()` in `backend/app/services/storage.py`

**Checkpoint**: Storage abstraction is in place. Both implementations exist. Default (`minio`) works identically to before.

---

## Phase 2: Foundational (Pipeline Trigger)

**Purpose**: Add the confirm-upload endpoint so S3/R2 mode can trigger the transcription pipeline

- [x] T007 Add `POST /api/v1/meetings/{meeting_id}/confirm-upload` endpoint in `backend/app/api/v1/endpoints/meetings.py` per contract in `specs/020-s3-storage-switch/contracts/confirm-upload.md`
- [x] T008 Verify existing MinIO webhook handler in `backend/app/api/v1/endpoints/webhooks.py` still works unchanged (no modifications needed)

**Checkpoint**: Both pipeline trigger paths exist — MinIO webhook (existing) and confirm-upload endpoint (new).

---

## Phase 3: User Story 1 - S3/R2 Storage on Production VPS (Priority: P1) MVP

**Goal**: System uses S3/R2 for file storage when `STORAGE_PROVIDER=s3` is set.

**Independent Test**: Set `STORAGE_PROVIDER=s3` with R2 credentials, upload a file through frontend, verify it lands in R2 bucket, verify transcription pipeline completes.

### Implementation for User Story 1

- [x] T009 [US1] Add `S3_*` environment variables to `api` service in `docker-compose.yml`
- [x] T010 [US1] Add `S3_*` environment variables to `worker` and `worker-gpu` services in `docker-compose.yml`
- [ ] T011 [US1] Verify presigned upload URL generation works with R2 endpoint (test with `STORAGE_PROVIDER=s3` locally using R2 credentials)
- [ ] T012 [US1] Verify worker can download files from R2 via presigned download URL
- [ ] T013 [US1] Verify full pipeline: upload → confirm-upload → transcribe → summarize with S3/R2

**Checkpoint**: Full end-to-end flow works with S3/R2. MinIO is not needed.

---

## Phase 4: User Story 2 - MinIO Continues Working for Local Development (Priority: P1)

**Goal**: Local dev with MinIO works identically after refactor.

**Independent Test**: Run `docker compose up` with default `.env` (no `STORAGE_PROVIDER` set), upload a file, verify MinIO webhook triggers pipeline.

### Implementation for User Story 2

- [ ] T014 [US2] Verify `STORAGE_PROVIDER` defaults to `minio` when not set in `backend/app/core/config.py`
- [ ] T015 [US2] Verify local `docker compose up` starts MinIO and all services work as before
- [ ] T016 [US2] Verify MinIO webhook triggers transcription pipeline (unchanged behavior)

**Checkpoint**: Local development is identical to before the refactor.

---

## Phase 5: User Story 3 - Pipeline Trigger Without MinIO Webhook (Priority: P1)

**Goal**: Frontend calls confirm-upload endpoint after S3/R2 upload; pipeline triggers without MinIO webhook.

**Independent Test**: With `STORAGE_PROVIDER=s3`, create a meeting, upload file to R2, call `POST /meetings/{id}/confirm-upload`, verify meeting transitions to `queued` and pipeline dispatches.

### Implementation for User Story 3

- [x] T017 [US3] Update frontend upload flow in `frontend-2/` to call `POST /api/v1/meetings/{meeting_id}/confirm-upload` after successful presigned PUT upload (only when using S3/R2 — detect from presigned URL domain or add config)
- [ ] T018 [US3] Verify confirm-upload endpoint correctly calls `meeting_service.initiate_processing()` and meeting status transitions from `pending_upload` → `queued`
- [ ] T019 [US3] Verify confirm-upload returns 400 if meeting is not in `pending_upload` status
- [ ] T020 [US3] Verify confirm-upload returns 403 if user doesn't own the meeting

**Checkpoint**: S3/R2 pipeline trigger works end-to-end via confirm-upload endpoint.

---

## Phase 6: User Story 4 - Public File Access via Presigned URLs (Priority: P2)

**Goal**: Presigned URLs for S3/R2 point directly to the cloud provider; browsers can access files without Kong proxy.

**Independent Test**: Generate a presigned download URL with `STORAGE_PROVIDER=s3`, open it in a browser, verify file downloads.

### Implementation for User Story 4

- [ ] T021 [US4] Verify `S3Storage.generate_presigned_upload_url()` returns URLs pointing to `S3_ENDPOINT_URL` (not Kong/MinIO)
- [ ] T022 [US4] Verify `S3Storage.get_presigned_download_url()` returns URLs pointing to `S3_PUBLIC_URL` for browser access
- [ ] T023 [US4] Verify CORS configuration on R2 bucket allows PUT from frontend domain

**Checkpoint**: Browser can upload to and download from S3/R2 directly via presigned URLs.

---

## Phase 7: Docker Compose & Infrastructure

**Purpose**: Make MinIO optional in docker-compose for S3/R2 deployments

- [x] T024 Add `profiles: ["minio"]` to `minio` service in `docker-compose.yml`
- [x] T025 Add `profiles: ["minio"]` to `minio-init` service in `docker-compose.yml`
- [x] T026 Remove hard `depends_on: minio` from `api`, `worker`, `worker-gpu`, and `kong` services in `docker-compose.yml` (make conditional or remove)
- [ ] T027 Verify `COMPOSE_PROFILES=minio,cpu docker compose up -d` starts all services including MinIO (local dev)
- [ ] T028 Verify `COMPOSE_PROFILES=cpu docker compose up -d` starts without MinIO (VPS with S3/R2)

**Checkpoint**: MinIO is optional — only starts when minio profile is active.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and cleanup

- [x] T029 [P] Update `backend/app/services/storage.py` to implement `delete_file()` method on both `MinioStorage` and `S3Storage` (currently missing)
- [x] T030 [P] Add startup validation in `create_storage()` — fail fast if `STORAGE_PROVIDER=s3` but `S3_ENDPOINT_URL` is empty
- [x] T031 [P] Update `.env.example` with new `STORAGE_PROVIDER` and `S3_*` variables
- [x] T032 [P] Update `README.md` with S3/R2 configuration section
- [ ] T033 Run full quickstart.md validation: test both MinIO (local) and S3/R2 (VPS) paths end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — storage abstraction refactor
- **Foundational (Phase 2)**: Depends on Phase 1 (storage Protocol must exist for confirm-upload to use)
- **US1 (Phase 3)**: Depends on Phase 1 + Phase 2
- **US2 (Phase 4)**: Depends on Phase 1 only (MinIO path, no confirm-upload needed)
- **US3 (Phase 5)**: Depends on Phase 2 (confirm-upload endpoint must exist)
- **US4 (Phase 6)**: Depends on Phase 1 (S3Storage implementation)
- **Docker (Phase 7)**: Depends on Phase 1 (to verify both paths work)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (S3/R2 on VPS)**: Requires storage abstraction (Phase 1) + confirm-upload (Phase 2)
- **US2 (MinIO local dev)**: Requires storage abstraction (Phase 1) — can run in parallel with US1
- **US3 (Pipeline trigger)**: Requires confirm-upload endpoint (Phase 2) — can run in parallel with US1/US2
- **US4 (Presigned URLs)**: Requires S3Storage implementation (Phase 1) — can run in parallel with others

### Parallel Opportunities

- T003 and T004 (MinioStorage + S3Storage) can run in parallel
- US1, US2, US3, US4 can all run in parallel after their dependencies are met
- T029, T030, T031, T032 (polish tasks) can all run in parallel

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2 + US1)

1. Complete Phase 1: Storage abstraction refactor
2. Complete Phase 2: Confirm-upload endpoint
3. Complete Phase 3: US1 — S3/R2 works on VPS
4. **STOP and VALIDATE**: Can upload and transcribe with R2?
5. If yes: proceed to remaining stories

### Incremental Delivery

1. Phase 1 + Phase 2 → Abstraction + trigger endpoint ready
2. US1 → S3/R2 on VPS works → Validate end-to-end
3. US2 → MinIO local dev unchanged → Validate no regressions
4. US3 → Frontend confirm-upload integration → Validate trigger path
5. US4 → Presigned URLs → Validate browser access
6. Phase 7 → Docker profiles → MinIO optional
7. Polish → delete_file, validation, docs

---

## Notes

- The existing `S3StorageService` already uses boto3 — this is a refactor, not a rewrite
- Both MinIO and S3/R2 speak the S3 API, so the implementations are very similar
- The main behavioral difference is the pipeline trigger: MinIO webhook vs. confirm-upload endpoint
- Frontend change (T017) may need a way to detect which storage provider is active — consider adding provider info to the presigned-upload response or a frontend env var
