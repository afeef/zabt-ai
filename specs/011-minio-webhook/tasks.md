# Tasks: MinIO Webhook Trigger & API Refactoring

**Input**: Design documents from `/specs/011-minio-webhook/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Tests are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the shared configuration that both user stories depend on.

- [x] T001 Add `MINIO_WEBHOOK_SECRET` setting to backend/app/core/config.py with default `"change-me-in-production"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Change Meeting model status default that affects all downstream work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Change `Meeting.status` default from `"queued"` to `"pending_upload"` in backend/app/models.py

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Event-Driven Transcription (Priority: P1) MVP

**Goal**: MinIO automatically triggers Celery transcription when a file lands in the bucket via a webhook endpoint.

**Independent Test**: Drop a file into the MinIO bucket via `mc cp` or the MinIO console (`localhost:9001`). Verify the webhook fires, a meeting record transitions to `"queued"`, and a Celery task is enqueued.

### Implementation for User Story 1

- [x] T003 [P] [US1] Add `initiate_processing(file_key: str)` method to `MeetingService` in backend/app/services/meeting.py — query Meeting by `file_path` where `status == "pending_upload"`, update status to `"queued"`, call `process_meeting.delay(meeting.id)`, return meeting or None for idempotency
- [x] T004 [P] [US1] Configure MinIO webhook in docker-compose.yml: add `MINIO_NOTIFY_WEBHOOK_*` env vars to `minio` service, add `MINIO_WEBHOOK_SECRET` env var to `api` service, add `minio-init` one-shot service (image: `minio/mc`) that runs `mc event add myminio/zabt-media arn:minio:sqs::PRIMARY:webhook --event s3:ObjectCreated:Put`
- [x] T005 [US1] Create webhook endpoint in backend/app/api/v1/endpoints/webhooks.py: define S3 event Pydantic DTOs (`S3EventNotification`, `S3EventRecord`, `S3Info`, `S3Object`, `S3Bucket`, `WebhookResponse`), implement `HEAD /` returning 200 (MinIO health check, no auth), implement `POST /` that validates `Authorization: Bearer {MINIO_WEBHOOK_SECRET}`, parses `Records[0].s3.object.key` (URL-decode with `urllib.parse.unquote_plus`), calls `meeting_service.initiate_processing(file_key)`, returns `WebhookResponse`
- [x] T006 [US1] Register webhook router with prefix `/webhooks` in backend/app/api/api.py

**Checkpoint**: Webhook endpoint is live. Files uploaded to MinIO trigger Celery processing automatically.

---

## Phase 4: User Story 2 — Unified Meeting API (Priority: P2)

**Goal**: Consolidate duplicate meeting creation logic. Single upload path via presigned URLs. No direct multipart upload.

**Independent Test**: Verify the codebase has zero duplicate `process_meeting.delay()` calls outside of `MeetingService.initiate_processing()`. Verify `POST /meetings/upload` returns 410. Verify `POST /meetings/` creates a record with `status=pending_upload` and does not trigger Celery.

### Backend Implementation

- [x] T007 [US2] Refactor backend/app/api/v1/endpoints/meetings.py: remove the entire `upload_meeting` endpoint (lines 129–165) and its `uuid`/`UploadFile`/`File` imports, remove the `process_meeting.delay()` call from `create_meeting` (lines 33–35)

### Frontend Implementation

- [x] T008 [P] [US2] Reorder `uploadMeeting()` in frontend-2/app/lib/api.ts: move `POST /meetings/` call (step 3) before the `PUT` to MinIO (step 2), so the meeting record exists before the file upload triggers the webhook. The function should: (1) get presigned URL, (2) create meeting record via POST, (3) upload file to MinIO. Return the meeting from step 2.
- [x] T009 [P] [US2] Refactor upload modal `startUpload()` in frontend-2/app/components/upload-modal.tsx: replace `apiClient.post("/meetings/upload", formData)` with presigned URL flow — call `apiClient.post("/meetings/presigned-upload", ...)` to get `upload_url` and `file_key`, then call `apiClient.post("/meetings/", ...)` to create meeting record, then `axios.put(upload_url, file, ...)` with `onUploadProgress` for progress tracking

**Checkpoint**: Single upload path. No duplicate logic. Frontend creates meeting before upload.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate the end-to-end flow works as documented.

- [x] T010 Verify end-to-end flow matches quickstart.md: confirm `MINIO_WEBHOOK_SECRET` is in `.env.example` (or `.env`), run `docker compose up -d`, check `minio-init` logs for successful event subscription, upload a file via frontend, confirm webhook triggers processing within 5 seconds (SC-001)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — T003 and T004 are parallel, T005 depends on T003, T006 depends on T005
- **US2 (Phase 4)**: Depends on Phase 2 — T007 (backend) can start independently; T008 and T009 are parallel (different files); T008/T009 do not depend on T007
- **Polish (Phase 5)**: Depends on Phase 3 + Phase 4

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2. No dependencies on US2.
- **User Story 2 (P2)**: Can start after Phase 2. No dependencies on US1. However, the full end-to-end flow requires both US1 and US2 to be complete.

### Within Each User Story

- US1: T003 ‖ T004 → T005 → T006
- US2: T007 ‖ T008 ‖ T009 (all independent — different files)

### Parallel Opportunities

- T003 and T004 can run in parallel (backend/app/services/meeting.py vs docker-compose.yml)
- T008 and T009 can run in parallel (api.ts vs upload-modal.tsx)
- US1 and US2 can be worked on in parallel after Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch parallel tasks for US1:
Task: "Add initiate_processing() to MeetingService in backend/app/services/meeting.py"
Task: "Configure MinIO webhook in docker-compose.yml"

# Then sequential:
Task: "Create webhook endpoint in backend/app/api/v1/endpoints/webhooks.py"
Task: "Register webhook router in backend/app/api/api.py"
```

## Parallel Example: User Story 2

```bash
# All three tasks can run in parallel (different files):
Task: "Refactor meetings.py — remove upload_meeting and Celery trigger"
Task: "Reorder uploadMeeting() in frontend-2/app/lib/api.ts"
Task: "Refactor upload modal in frontend-2/app/components/upload-modal.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003–T006)
4. **STOP and VALIDATE**: Upload a file to MinIO directly; verify webhook triggers Celery
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test webhook independently → MVP!
3. Add User Story 2 → Test unified API → Full feature complete
4. Polish → Validate quickstart.md → Done

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No new pip dependencies required
- Frontend changes (T008, T009) are API call reordering only — no new UI components
- The `minio-init` service is idempotent — re-running `mc event add` on an existing subscription is a no-op
