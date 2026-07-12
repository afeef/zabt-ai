# Tasks: Transcription Progress Tracking

**Input**: Design documents from `/specs/017-transcription-progress/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: E2E test included per constitution requirement (feature has user-facing flows).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Backend pipeline decomposition and API schema changes that all user stories depend on

- [x] T001 Add `sub_status` field to `MeetingRead` response schema in `backend/app/models.py`
- [x] T002 Add `update_sub_status(meeting_id, sub_status, summary_msg=None)` method to `MeetingService` in `backend/app/services/meeting.py` — updates `sub_status` in DB and publishes to Redis Pub/Sub channel `meeting:{meeting_id}:status` (fire-and-forget)
- [x] T003 Create `on_stage_failure` error callback task in `backend/app/worker.py` — sets `meeting.status = "failed"` and `meeting.summary_text = "[Error: {exc}]"` using `MeetingService`
- [x] T004 Create `stage_download` Celery task in `backend/app/worker.py` — downloads audio from MinIO, validates duration, extracts audio from video. Sets `sub_status` through `downloading` → `validating` → `extracting_audio`. Saves temp file path to a shared location. Returns `meeting_id`. Uses `MeetingService` for all DB operations.
- [x] T005 Create `stage_transcribe` Celery task in `backend/app/worker.py` — calls `provider.process_audio()` with `on_status_change` callback that updates `sub_status` (transcribing → aligning → diarizing). Saves transcript segments to DB. Updates user minutes. Returns `meeting_id`. Uses `MeetingService` for all DB operations.
- [x] T006 Create `stage_summarize` Celery task in `backend/app/worker.py` — runs AI agent for summary + action items. Sets `status = "completed"`, clears `sub_status`. Writes final `summary_text` and `action_items_text`. Uses `MeetingService` for all DB operations.
- [x] T007 Refactor `initiate_processing()` in `backend/app/services/meeting.py` to dispatch a Celery `chain(stage_download.s(meeting_id) | stage_transcribe.s() | stage_summarize.s())` with `link_error=on_stage_failure.s()` on each task, replacing the old `process_meeting.delay(meeting_id)` call
- [x] T008 Remove the old monolithic `process_meeting` task from `backend/app/worker.py` and stop writing `[System: ...]` messages to `summary_text` — sub_status is now the sole progress indicator
- [x] T009 [P] Add `sub_status` field to the `Meeting` TypeScript interface in `frontend-2/app/lib/api.ts`
- [x] T010 [P] Create `stage-utils.ts` in `frontend-2/app/lib/stage-utils.ts` — export `UserStage` type, `getUserStage(meeting)` mapping function, `STAGE_ORDER` array, `STAGE_LABELS` record, and `getStageIndex(stage)` helper per contracts/meetings-api.md

**Checkpoint**: Backend exposes `sub_status` via API, pipeline runs as chained tasks, frontend has stage mapping utilities. Ready for UI implementation.

---

## Phase 2: User Story 1 — Upload Modal Shows Processing Stages (Priority: P1) 🎯 MVP

**Goal**: After file upload completes, the upload modal shows live processing stage updates (Transcribing → Aligning → Diarizing → Done) for each uploaded file.

**Independent Test**: Upload a file, keep the modal open, and verify stage labels cycle through each processing phase in real time.

### Implementation for User Story 1

- [x] T011 [US1] Extend the `UploadItem` interface in `frontend-2/app/components/upload-modal.tsx` — add `meetingId?: number` and `processingStage?: UserStage` fields to track post-upload processing state
- [x] T012 [US1] Update `startUpload()` in `frontend-2/app/components/upload-modal.tsx` — after the `POST /meetings/` call succeeds, store the returned `meeting.id` on the `UploadItem` so polling can target it
- [x] T013 [US1] Add post-upload polling logic to `frontend-2/app/components/upload-modal.tsx` — when an upload item reaches `status: "success"` and has a `meetingId`, start polling `getMeeting(meetingId)` every 3 seconds. Update the item's `processingStage` from the response. Stop polling when `status` is `completed` or `failed`.
- [x] T014 [US1] Update the upload item UI in `frontend-2/app/components/upload-modal.tsx` — below the progress bar, show the current `processingStage` label (from `STAGE_LABELS`) when the file upload is complete and processing has started. Show "Done" with a completion indicator when finished. Show error state on failure.

**Checkpoint**: Upload modal shows live stage progression after file upload completes. User Story 1 is independently testable.

---

## Phase 3: User Story 2 — Meetings List Shows Processing Stages (Priority: P1)

**Goal**: Meeting cards on the meetings list and home feed display specific processing stage labels instead of generic "Processing…", with automatic polling updates.

**Independent Test**: Navigate to the meetings page while a meeting is processing, and verify the meeting card shows a specific stage label that updates live.

### Implementation for User Story 2

- [x] T015 [P] [US2] Update `StatusBadge` in `frontend-2/app/components/ui/status-badge.tsx` — accept an optional `subStatus` prop. When `status === "processing"` and `subStatus` is provided, display the user-visible stage label (via `getUserStage` + `STAGE_LABELS`) instead of generic "Processing…"
- [x] T016 [P] [US2] Update `MeetingFeedCard` in `frontend-2/app/components/meeting-feed.tsx` — pass `meeting.sub_status` to `StatusBadge`. Replace the hardcoded "Transcribing…" placeholder text with the actual stage label from `getUserStage(meeting)`
- [x] T017 [P] [US2] Update `MeetingCard` in `frontend-2/app/components/meeting-card.tsx` — pass `meeting.sub_status` to `StatusBadge`
- [x] T018 [US2] Add polling to `frontend-2/app/components/meeting-feed.tsx` — after initial load, if any meeting has `status` in `["pending_upload", "queued", "processing"]`, poll `getMeetings(0, 20)` every 5 seconds. Stop polling when no active meetings remain. Clean up interval on unmount.
- [x] T019 [US2] Add polling to `frontend-2/app/(dashboard)/meetings/page.tsx` — same logic as T018: poll `getMeetings()` every 5 seconds while any meeting is active. Stop when no active meetings remain. Clean up on unmount.
- [x] T020 [US2] Update meeting detail page `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — show the specific stage label (from `getUserStage` + `STAGE_LABELS`) in the processing banner instead of generic "Processing your meeting…". Add `pending_upload` to `ACTIVE_STATUSES` set.

**Checkpoint**: Meetings list, home feed, and detail page all show specific stage labels with live updates. User Story 2 is independently testable.

---

## Phase 4: User Story 3 — Stage Progress Indicator (Priority: P2)

**Goal**: A visual multi-step progress indicator shows completed, active, and pending stages for processing meetings.

**Independent Test**: Observe a processing meeting and verify a stepped indicator highlights completed stages and the active stage.

### Implementation for User Story 3

- [x] T021 [US3] Create `ProgressSteps` component in `frontend-2/app/components/ui/progress-steps.tsx` — horizontal stepped indicator showing 5 stages (Uploaded → Transcribing → Aligning → Diarizing → Done). Each step: circle + label. States: completed (indigo-600 fill + check), active (indigo-600 ring + pulse animation), pending (stone-200 border). Connecting lines: completed (indigo-600), pending (stone-200). Design system compliant: `rounded-full` circles, 4px grid, border-only depth, no shadows.
- [x] T022 [US3] Integrate `ProgressSteps` into `frontend-2/app/components/upload-modal.tsx` — show below each upload item that has entered processing (after file upload succeeds). Pass `currentStage` from the polling data. Hide when `status` is `pending_upload` or `queued`.
- [x] T023 [US3] Integrate `ProgressSteps` into `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — show in the processing banner area when meeting is active. Replace or complement the existing text-only banner.
- [x] T024 [US3] Document the `ProgressSteps` pattern in `.interface-design/system.md` — add entry for the stepped progress indicator pattern with its states, colors, and spacing.

**Checkpoint**: Visual progress indicator shows in upload modal and detail page. All 3 user stories are complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing, cleanup, and verification

- [x] T025 Create E2E test in `tests/e2e/test_transcription_progress.py` — Playwright/Python test covering: upload a file → verify upload modal shows stage labels → navigate to meetings list → verify stage label appears → wait for completion → verify "Completed" status
- [x] T026 Verify that the old `process_meeting` task is fully removed and no references remain across the codebase (grep for `process_meeting` in all backend files)
- [x] T027 Run quickstart.md verification — confirm `sub_status` appears in API response, verify chained tasks are registered in Celery

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup completion (T001–T010)
- **User Story 2 (Phase 3)**: Depends on Setup completion (T001–T010). Can run in parallel with US1.
- **User Story 3 (Phase 4)**: Depends on Setup completion (T001–T010). Can run in parallel with US1/US2, but benefits from US1 being done (to integrate ProgressSteps into upload modal).
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Phase 1 — Integrates into US1's upload modal (T022) and US2's detail page (T023), so complete US1/US2 first for cleanest integration

### Within Each User Story

- Backend schema/service changes (Phase 1) before frontend implementation
- Stage utilities (T010) before any UI task that uses `getUserStage`
- StatusBadge update (T015) before meeting-feed/card updates that pass `subStatus`
- ProgressSteps component (T021) before integration tasks (T022, T023)

### Parallel Opportunities

**Phase 1 parallel group**:
- T009 (frontend type) and T010 (stage-utils) can run in parallel — different files, no dependencies

**Phase 3 parallel group (US2)**:
- T015 (StatusBadge), T016 (meeting-feed), T017 (meeting-card) can all run in parallel — different files

---

## Parallel Example: User Story 2

```bash
# Launch StatusBadge, MeetingFeedCard, and MeetingCard updates together:
Task T015: "Update StatusBadge in frontend-2/app/components/ui/status-badge.tsx"
Task T016: "Update MeetingFeedCard in frontend-2/app/components/meeting-feed.tsx"
Task T017: "Update MeetingCard in frontend-2/app/components/meeting-card.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (backend pipeline + API schema + frontend utilities)
2. Complete Phase 2: User Story 1 (upload modal progress)
3. **STOP and VALIDATE**: Upload a file, keep modal open, verify stages cycle through
4. Deploy/demo if ready — users get immediate value from upload modal feedback

### Incremental Delivery

1. Phase 1 (Setup) → Backend pipeline works, API exposes sub_status
2. + User Story 1 → Upload modal shows stages → Deploy (MVP!)
3. + User Story 2 → Meetings list + home feed show stages → Deploy
4. + User Story 3 → Visual progress indicator → Deploy
5. Each story adds visual polish without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Backend tasks (T001–T008) are sequential — each builds on the previous
- Frontend tasks (T009–T010) can start as soon as the API contract is defined (T001)
- The old `process_meeting` task removal (T008) should happen after all 3 new stage tasks are verified working
- Total: 27 tasks (10 setup, 4 US1, 6 US2, 4 US3, 3 polish)
