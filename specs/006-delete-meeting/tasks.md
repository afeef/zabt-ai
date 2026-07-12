---
description: "Task list for 006-delete-meeting — Meeting Delete Option"
---

# Tasks: Meeting Delete Option

**Input**: Design documents from `/specs/006-delete-meeting/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅
**Branch**: `006-delete-meeting`
**Tech**: TypeScript 5 / Next.js 16 App Router, Python 3.11 / FastAPI, Supabase, Playwright
**Tests**: Playwright E2E tests are REQUIRED per constitution (Principle VI).

---

## Phase 1: Setup

**Purpose**: Test scaffolding and initial boilerplate.

- [x] T001 Create `tests/e2e/test_meeting_delete.py` skeleton — Playwright E2E test file with standard login helper and imports.

**Checkpoint**: E2E skeleton runs without import errors.

---

## Phase 2: Foundational (Backend API)

**Purpose**: Build the `DELETE` endpoint required by the frontend.

- [x] T002 Implement `DELETE /upload` or `DELETE /{meeting_id}` in `backend/app/api/v1/endpoints/meetings.py` — Must verify `current_user.id == meeting.owner_id`.
- [x] T003 Add validation in the delete endpoint — If `meeting.status` is `processing` or `queued`, raise `400 HTTPException`.
- [x] T004 Implement storage garbage collection in the delete endpoint — Call `storage.delete_file(meeting.file_path)` (or equivalent OS remove logic) before removing the DB record.
- [x] T005 Implement DB deletion — Delete the `Meeting` record using `Session.delete(meeting)` and `Session.commit()`.

**Checkpoint**: The backend endpoint exists, rejects active processing requests, and cleanly deletes records and files when correctly authenticated.

---

## Phase 3: User Story 1 — Delete a Meeting UI (Priority: P1)

**Goal**: Users can open a 3-dot menu on a meeting, click delete, confirm the prompt, and see the meeting disappear immediately.

### E2E Test

- [x] T006 [P] [US1] Write E2E test `test_meeting_delete_flow` in `test_meeting_delete.py` — Login, upload a mock meeting (so we have one to delete), wait for success status, click the 3-dot menu, click "Delete", confirm the browser dialog, and assert the meeting disappears from the feed.

### Implementation

- [x] T007 [P] [US1] Add `deleteMeeting` API wrapper in `frontend-2/app/lib/api.ts` — `export const deleteMeeting = async (id: number): Promise<void> => { await apiClient.delete('/meetings/' + id); };` (if not already existing/matching the right path).
- [x] T008 [US1] Update `MeetingFeedCard` in `frontend-2/app/components/meeting-feed.tsx` — Add a 3-dot vertical menu icon button aligned to the right. Use a simple React state or `<details>` dropdown to show a "Delete" button.
- [x] T009 [US1] Add processing state guard in `MeetingFeedCard` — Hide or disable the 3-dot menu/delete button if `meeting.status === 'processing'` or `'queued'`.
- [x] T010 [US1] Implement optimistic deletion flow in `MeetingFeedCard` — On delete click, call `window.confirm("Are you sure you want to permanently delete this meeting?")`. If yes, invoke `deleteMeeting(meeting.id)`.
- [x] T011 [US1] Propagate deletion to `MeetingFeed` parent — Add an `onDelete(id: number)` prop to `MeetingFeedCard`. In `MeetingFeed`, filter out the deleted ID from the `meetings` state array (`setMeetings(prev => prev.filter(m => m.id !== id))`) to update the UI instantly without a refresh.

**Checkpoint**: The UI allows safe deletion, confirms the action, hits the new Python backend endpoint, and seamlessly removes the item from the feed visually.

---

## Phase 4: Polish & Validation

**Purpose**: E2E test execution and design system compliance.

- [x] T012 Run `/interface-design:audit` — Ensure the new 3-dot menu complies with `.interface-design/system.md` (e.g., uses `border-stone-200`, `bg-white` surface if dropdown).
- [x] T013 Execute full E2E test locally (`pytest tests/e2e/test_meeting_delete.py`) to confirm the front-to-back deletion flow works via Chromium.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Backend)**: Blocks frontend execution (needs the API to actually delete things).
- **Phase 3 (Frontend/US1)**: Integrates the UI with the Phase 2 backend.
- **Phase 4 (Polish)**: Final validation run.

### Parallel Opportunities

Tasks marked with `[P]` can be executed simultaneously:
- T006 (E2E Test) can be written concurrently with T007 (API Wrapper).
