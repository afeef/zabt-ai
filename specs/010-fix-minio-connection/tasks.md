# Tasks: Fix MinIO Connection & Direct Upload

**Input**: Design documents from `/specs/010-fix-minio-connection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Initialize feature branch (Completed via script)
- [x] T002 Verify Docker environment status (`docker compose ps`)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 [P] Add `MINIO_ENDPOINT=minio:9000` to `api` service in `docker-compose.yml`
- [x] T004 [P] Add `MINIO_ENDPOINT=minio:9000` to `worker` service in `docker-compose.yml`
- [x] T005 [P] Add `MINIO_ENDPOINT=minio:9000` to `worker-gpu` service in `docker-compose.yml`
- [x] T005b Fix `TypeError` in `app/services/ai_agent.py` by updating `OpenAIModel` initialization
- [x] T005c Fix `ImportError` in API by adding `whisper_service` alias in `transcription.py`

## Phase 3: User Story 1 & 2 - Validation (Priority: P1)

- [x] T006 Restart Docker containers (`docker compose up -d --profile gpu`)
- [x] T007 [US1] Verify worker logs for successful initialization (`docker compose logs worker`)
- [x] T008 [US2] Verify API logs for connectivity (`docker compose logs api`)

## Phase 4: Polish

- [x] T009 Verify `quickstart.md` is accurate and easy to follow
- [x] T010 [P] Finalize walkthrough and close feature

## Phase 5: Direct Upload Fix (Debugging 405)

- [x] T011 [P] Add `upload_file` to `S3StorageService` in `storage.py`
- [x] T012 [P] Implement `POST /upload` in `meetings.py` (v1)
- [x] T013 [P] Verify upload flow end-to-end