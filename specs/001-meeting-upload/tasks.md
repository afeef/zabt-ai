---
description: "Task list for 001-meeting-upload — Meeting Upload Progress Modal"
---

# Tasks: Meeting Upload Progress

**Input**: Design documents from `/specs/001-meeting-upload/`  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅  
**Branch**: `001-meeting-upload`  
**Tech**: TypeScript 5 / Next.js 16 App Router, Axios, shadcn/ui, Tailwind CSS v4

**Tests**: Playwright E2E tests are REQUIRED per constitution (Principle VI) — included below.

---

## Phase 1: Setup

**Purpose**: Establish the new component files and boilerplate imports before wiring them together.

- [x] T001 Create `frontend-2/app/components/upload-modal.tsx` skeleton — standard functional React component exporting `UploadModal` via shadcn/ui Dialog.
- [x] T002 [P] Create `tests/e2e/test_meeting_upload.py` skeleton — Playwright E2E test file with standard login helper and imports.

**Checkpoint**: Component exists and runs without type errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Set up the core modal container on the dashboard page so feature work has a place to live.

- [x] T003 Update `frontend-2/app/(dashboard)/page.tsx` — Add `isUploadModalOpen` state and `setUploadModalOpen` function. Import `<UploadModal>` and render it at the bottom of the page, passing the open state via props.
- [x] T004 Update `frontend-2/app/components/right-panel.tsx` — Expose an `onUploadClick` prop from `RightPanel`.
- [x] T005 Update `frontend-2/app/components/meeting-feed.tsx` — Expose an `onUploadClick` prop from the empty state layout.
- [x] T006 Wire the triggers in `frontend-2/app/(dashboard)/page.tsx` — Pass `() => setUploadModalOpen(true)` into the `RightPanel` and `MeetingFeed` components.

**Checkpoint**: Clicking "Upload a meeting" from the dashboard right panel or feed empty state immediately toggles `isUploadModalOpen` state to true.

---

## Phase 3: User Story 1 — Meeting File Upload Modal (MVP Priority: P1)

**Goal**: Users can open the modal, see the shadcn/ui architecture, and access a native file picker.

**Independent Test**: Click "Upload", see the styled modal, click "Browse files", and select a file.

### E2E Test
- [x] T007 [P] [US1] Write E2E test `test_upload_modal_opens` in `test_meeting_upload.py` — Login, click "Upload a meeting", assert the "Transcribe audio and video" modal heading is visible.

### Implementation
- [x] T008 [P] [US1] Implement shadcn/ui Dialog structure in `upload-modal.tsx` — Use `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` components. Ensure standard styling (`bg-white border-stone-200 rounded-lg no-shadows`).
- [x] T009 [P] [US1] Implement visually hidden file input in `upload-modal.tsx` — `<input type="file" accept="audio/*,video/*" className="hidden" />` alongside a specialized `useRef` to trigger it.
- [x] T010 [US1] Implement "Browse files" button in `upload-modal.tsx` — Central large blue button (`bg-indigo-600`) that forwards clicks to the hidden file input.
- [x] T011 [US1] Add file selection handler in `upload-modal.tsx` — Read `e.target.files`, filter out anything over 2GB, and store locally in a temporary `selectedFiles` React state.

**Checkpoint**: Clicking "Browse files" opens the OS picker, and selecting a valid A/V file suppresses errors.

---

## Phase 4: User Story 2 — Real-time Upload Progress (Priority: P1)

**Goal**: When a file is selected, it immediately starts uploading via Axios with real-time UI progress feedback.

**Independent Test**: Select a large test video file and watch the progress bar accurately scale 1% → 100%.

### E2E Test
- [x] T012 [P] [US2] Write null-route E2E test `test_upload_progress_flow` in `test_meeting_upload.py` — using Playwright's route interception to mock a 5-second slow network response for `/upload`, assert the progress bar appears and eventually completes.

### Implementation
- [x] T013 [P] [US2] Define `UploadItem` interface locally in `upload-modal.tsx` — tracking `id`, `file`, `progress`, `status`, and `abortController` per the `data-model.md`. Convert the temporary `selectedFiles` state to an `UploadItem[]` array.
- [x] T014 [US2] Implement upload routine in `upload-modal.tsx` — Create a `startUpload(item: UploadItem)` function. Construct `FormData`, attach an `AbortController`, and call `apiClient.post('/meetings/upload')`.
- [x] T015 [US2] Wire Axios `onUploadProgress` — Inside `startUpload`, listen to `progressEvent`, calculate `Math.round((loaded * 100) / total)`, and `setUploads` state recursively to update the item's progress percentage.
- [x] T016 [US2] Implement active upload UI block in `upload-modal.tsx` — Render each item in the `uploads` array showing: file name, `formatted_size` (MB), percentage text, and a horizontal CSS progress bar keyed to `item.progress`.
- [x] T017 [P] [US2] Add status formatting in `upload-modal.tsx` — when upload finishes (200 OK), transition the item `status` to `'success'`.

**Checkpoint**: Selecting a file natively pushes it over the network to the `/upload` API endpoint, and the UI progress bar smoothly updates all the way to 100%.

---

## Phase 5: User Story 3 — Cancel Uploads (Priority: P2)

**Goal**: Users can cancel long-running uploads immediately terminating the network request.

**Independent Test**: Start a large upload, click "Cancel," and verify the network tab shows the request aborted.

### E2E Test
- [x] T018 [P] [US3] Write E2E test `test_upload_cancellation` in `test_meeting_upload.py` — Mock slow upload, click "Cancel", assert item is removed from view.

### Implementation
- [x] T019 [P] [US3] Add "Cancel" button to the active file UI row in `upload-modal.tsx` — `text-indigo-600` secondary styling.
- [x] T020 [US3] Wire cancellation logic in `upload-modal.tsx` — On click, call `item.abortController.abort()`, wait for Axios to throw an `CanceledError`, and optionally remove the item from the state array or mark it as `'cancelled'`.
- [x] T021 [P] [US3] Add "Cancel all" button to top right of modal in `upload-modal.tsx` — Loops through all active `UploadItem`s and fires their abort controllers.

**Checkpoint**: Clicking "Cancel" on an active 1GB upload instantly terminates the upload stream via the AbortController.

---

## Phase 6: User Story 4 — Import Quota (Priority: P3)

**Goal**: Show a static upgrade CTA and import quota boundary inside the modal footer for MVP.

### Implementation
- [x] T022 [P] [US4] Add static footer to `upload-modal.tsx` — `border-t border-stone-200`, flex layout wrapping "3 of 3 imports left" text and the "Upgrade to Business" secondary button inline.

**Checkpoint**: Footer visually renders per the reference image.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, layout stability, and modal closure safety.

- [x] T023 [P] Implement modal closure guard in `upload-modal.tsx` — If the user clicks outside the modal or hits Escape while `uploads.some(u => u.status === 'uploading')`, use standard browser `window.confirm("Upload in progress. Cancel anyway?")` before closing and wiping state.
- [x] T024 [P] Layout QA in `upload-modal.tsx` — Ensure the list of active uploads scrolls vertically if more than 3 files are queued at once, keeping the modal within standard viewport height limits (`max-h-[80vh]`).
- [x] T025 Run `/interface-design:audit` — Ensure the new Upload Modal complies fully with `.interface-design/system.md`.
- [x] T026 Execute full E2E test suite locally (`pytest tests/e2e/test_meeting_upload.py`) to confirm all coverage passes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1. Blocks all UI work.
- **US1 (Phase 3)**: Depends on Phase 2. The modal must exist in the dashboard to implement the file picker.
- **US2 (Phase 4)**: Depends on US1 file picker logic.
- **US3 (Phase 5)**: Depends on US2 active upload loop.
- **US4 (Phase 6)**: Parallel to US3.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### Parallel Opportunities

Tasks marked with `[P]` can be executed simultaneously:
- T002 (E2E skeleton) can happen alongside T001 (UI skeleton).
- E2E tests (T007, T012, T018) can be written alongside their respective UI tasks.
- US4 (T022 Footer) can be built independently of US2/US3 logic.

### Implementation Strategy

1. **MVP First (Phases 1-3)**: Build the raw modal and connect the file picker. It won't upload yet, but the UI shell will be complete.
2. **Core Feature (Phase 4)**: Integrate Axios `onUploadProgress`. This is the high-risk technical chunk.
3. **Iterative Polish (Phases 5-7)**: Add the cancellation controllers, mock the quotas, and add the exit warnings.
