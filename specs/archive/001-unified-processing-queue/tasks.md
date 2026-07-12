# Tasks: Unified Processing Queue

**Input**: Design documents from `/specs/001-unified-processing-queue/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-contracts.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the shared processing queue infrastructure (context, types, provider)

- [X] T001 Create the `contexts/` directory and processing queue context with QueueItem type, QueueState, reducer actions (ADD_ITEM, UPDATE_STAGE, SET_COLLAPSED, SET_VISIBLE, CLEAR), and ProcessingQueueProvider component with per-item polling logic (3s interval using `getMeeting` + `getUserStage`) and 10s auto-hide timer in `frontend-2/app/contexts/processing-queue-context.tsx`
- [X] T002 Create the ProcessingQueue floating panel component using shadcn/ui Card and Collapsible — renders queue items when visible, supports collapsed mode showing active item count pill, fixed position bottom-right (`fixed bottom-4 right-4 w-80 z-50`), header with "Processing" title and collapse/expand button in `frontend-2/app/components/processing-queue.tsx`
- [X] T003 Create the ProcessingQueueItem component — displays item name, source icon (upload/YouTube), current stage via STAGE_LABELS, ProgressSteps component for processing items, green checkmark for done (clickable → navigates to `/meetings/{meetingId}`), red X with error message for failed items in `frontend-2/app/components/processing-queue-item.tsx`

**Checkpoint**: Queue infrastructure ready — context provider, panel, and item components exist but are not yet wired to any dialog.

---

## Phase 2: Foundational

**Purpose**: Wire the ProcessingQueueProvider into the dashboard page layout

- [X] T004 Wrap dashboard page content with `<ProcessingQueueProvider>` and render `<ProcessingQueue />` as a sibling to the existing UploadModal and YouTubeUrlDialog in `frontend-2/app/(dashboard)/page.tsx`

**Checkpoint**: Provider active on dashboard — `useProcessingQueue()` is available to all child components. Queue panel renders (empty) when items exist.

---

## Phase 3: User Story 1 — File Upload Worker Progress in Queue (Priority: P1) 🎯 MVP

**Goal**: After a file upload completes in the import dialog, the processing queue panel shows worker stage progress (transcribing → aligning → diarizing → summarizing → done).

**Independent Test**: Upload a file, close the import dialog after upload, verify the queue panel appears with live worker stage updates.

### Implementation for User Story 1

- [X] T005 [US1] Modify upload-modal.tsx to call `useProcessingQueue().addItem(meetingId, file.name, "upload")` after a successful upload (when status transitions to "success" and meetingId is available). Import the hook from processing-queue-context in `frontend-2/app/components/upload-modal.tsx`
- [X] T006 [US1] Remove post-upload polling from upload-modal.tsx — delete the `pollTimers` ref, the `useEffect` that creates per-item poll intervals, the `processingStage` field from the UploadItem interface, the ProgressSteps rendering for completed uploads, and the STAGE_LABELS subtitle display. Retain all upload byte progress, cancellation, file selection, and quota footer logic in `frontend-2/app/components/upload-modal.tsx`

**Checkpoint**: File uploads push items to the queue after upload completes. Import dialog no longer shows worker stages. Queue panel shows live stage progress.

---

## Phase 4: User Story 2 — YouTube URL Worker Progress in Queue (Priority: P1)

**Goal**: After a YouTube URL is submitted and accepted, the processing queue panel shows worker stage progress (downloading → transcribing → aligning → diarizing → summarizing → done).

**Independent Test**: Submit a YouTube URL, verify the queue panel appears with live worker stage updates after the dialog closes.

### Implementation for User Story 2

- [X] T007 [US2] Modify youtube-url-dialog.tsx to call `useProcessingQueue().addItem(meeting.id, meeting.youtube_title || trimmed, "youtube")` after a successful `submitYoutubeUrl()` call (before calling `onOpenChange(false)`). Import the hook from processing-queue-context in `frontend-2/app/components/youtube-url-dialog.tsx`

**Checkpoint**: YouTube URL submissions push items to the queue. Queue panel shows live stage progress for both upload and YouTube items.

---

## Phase 5: User Story 3 — Queue Management (Priority: P2)

**Goal**: Multiple items track independently, queue auto-hides after completion, collapsible/expandable, completed items are clickable to navigate to meeting detail.

**Independent Test**: Submit multiple items (mix of uploads and YouTube URLs), verify independent tracking, collapse/expand, auto-hide after 10s, and click-through navigation.

### Implementation for User Story 3

- [X] T008 [US3] Verify and refine auto-hide timer logic in the context provider — ensure the 10s timer starts only when ALL items are in terminal state (done or failed), cancels if a new item is added during countdown, and sets `isVisible: false` when elapsed. Test with multiple items completing at different times in `frontend-2/app/contexts/processing-queue-context.tsx`
- [X] T009 [US3] Add click-to-navigate behavior on completed queue items — when a done item is clicked, call `router.push("/meetings/{meetingId}")` using Next.js router. Add cursor-pointer styling and hover state for done items only in `frontend-2/app/components/processing-queue-item.tsx`
- [X] T010 [US3] Add scrollable overflow to the queue panel item list when more than 4 items — apply `max-h-64 overflow-y-auto` to the items container. Verify the header and collapse controls stay fixed above the scroll area in `frontend-2/app/components/processing-queue.tsx`

**Checkpoint**: Full queue management works — multi-item, auto-hide, collapse, navigation.

---

## Phase 6: User Story 4 — Import Dialog Refactoring (Priority: P2)

**Goal**: Verify the import dialog no longer displays any worker stage tracking after upload completes. Upload byte progress and cancellation remain intact.

**Independent Test**: Upload a file, keep the dialog open, verify NO transcribing/aligning/summarizing indicators appear after upload finishes.

### Implementation for User Story 4

- [X] T011 [US4] Clean up any remaining references to ProgressSteps import, STAGE_LABELS import, or processingStage-related rendering in upload-modal.tsx that were not fully removed in T006. Verify the modal only shows upload status (uploading/success/error/cancelled) and never displays worker pipeline stages in `frontend-2/app/components/upload-modal.tsx`

**Checkpoint**: Import dialog is clean — upload-only, no worker stage tracking.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: E2E tests, design system compliance, analytics

- [X] T012 Create E2E test file with tests covering: queue panel appears after file upload completes (mocked API), queue panel appears after YouTube URL submission (mocked API), queue shows stage progress updates, queue auto-hides after completion, queue collapse/expand, completed item click navigates to meeting detail page, and failed item shows error message in `tests/e2e/test_processing_queue.py`
- [X] T013 Add PostHog analytics events to the processing queue — capture `processing_queue_item_added` (with source_type), `processing_queue_item_completed` (with source_type, duration), `processing_queue_item_failed` (with source_type, error), `processing_queue_collapsed`, `processing_queue_expanded` in `frontend-2/app/contexts/processing-queue-context.tsx` and `frontend-2/app/components/processing-queue.tsx`
- [X] T014 Document the floating queue panel pattern in the design system file — position, dimensions, z-index, surface treatment, collapse behavior in `.interface-design/system.md`
- [X] T015 Run quickstart.md validation — verify all manual test scenarios from `specs/001-unified-processing-queue/quickstart.md` can be executed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (context exists)
- **US1 (Phase 3)**: Depends on Phase 2 (provider wired to dashboard)
- **US2 (Phase 4)**: Depends on Phase 2 (provider wired to dashboard) — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 3 or Phase 4 (needs items in queue to test)
- **US4 (Phase 6)**: Depends on T006 from Phase 3 (removal already done there; this is verification)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Independent — requires only foundational phase
- **US2 (P1)**: Independent — requires only foundational phase, can run parallel with US1
- **US3 (P2)**: Depends on US1 or US2 being complete (needs queue items to test management features)
- **US4 (P2)**: Effectively done as part of US1 (T006); Phase 6 is verification only

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, both depend on T001)
- T005 and T007 can run in parallel after Phase 2 (different files: upload-modal vs youtube-dialog)
- T008, T009, T010 can run in parallel (different files within US3)

---

## Parallel Example: Phase 1

```bash
# After T001 completes, launch T002 and T003 together:
Task T002: "Create ProcessingQueue panel in frontend-2/app/components/processing-queue.tsx"
Task T003: "Create ProcessingQueueItem in frontend-2/app/components/processing-queue-item.tsx"
```

## Parallel Example: US1 + US2

```bash
# After Phase 2 (T004) completes, launch US1 and US2 together:
Task T005: "Wire upload-modal.tsx to addItem()"
Task T007: "Wire youtube-url-dialog.tsx to addItem()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004)
3. Complete Phase 3: US1 (T005–T006)
4. **STOP and VALIDATE**: Upload a file, close dialog, verify queue shows worker stages
5. Deploy if ready — file upload progress in queue is the primary use case

### Incremental Delivery

1. Setup + Foundational → Queue infrastructure ready
2. US1 → File upload worker progress in queue (MVP!)
3. US2 → YouTube URL worker progress in queue
4. US3 → Multi-item management, auto-hide, collapse, navigation
5. US4 → Verification pass on import dialog cleanup
6. Polish → E2E tests, analytics, design system docs

---

## Notes

- This is a frontend-only feature — no backend changes required
- The queue reuses existing `getMeeting()` API and `getUserStage()` mapping
- Session-only state — no persistence across page refreshes
- Maximum 5 concurrent queue items
- ProgressSteps component is reused as-is from `frontend-2/app/components/ui/progress-steps.tsx`
