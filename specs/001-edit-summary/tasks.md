# Tasks: Edit Summary Markdown In-App

**Input**: Design documents from `/specs/001-edit-summary/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/meetings-summary.md, quickstart.md

**Tests**: E2E test included (constitution requirement for user-facing features).

**Organization**: Tasks grouped by user story — US1 (Edit & Save) and US2 (Track Edit History).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install new dependencies and prepare project structure

- [x] T001 Install Tiptap packages in frontend-2/ — run `npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-link tiptap-markdown`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema changes and model extensions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Add `original_summary_text` (Optional[str]) and `summary_edited` (bool, default=False) fields to the Meeting model in backend/app/models.py
- [x] T003 Add `original_summary_text` and `summary_edited` fields to the MeetingRead response model in backend/app/models.py
- [x] T004 Update `_build_meeting_response()` in backend/app/api/v1/endpoints/meetings.py to include `original_summary_text` and `summary_edited` in the MeetingRead response
- [x] T005 Add `original_summary_text` and `summary_edited` fields to the Meeting TypeScript interface in frontend-2/app/lib/api.ts
- [x] T006 Run database migration — execute `ALTER TABLE meeting ADD COLUMN original_summary_text TEXT; ALTER TABLE meeting ADD COLUMN summary_edited BOOLEAN NOT NULL DEFAULT FALSE;`

**Checkpoint**: Foundation ready — model extended on both backend and frontend, DB migrated

---

## Phase 3: User Story 1 — Edit and Save Summary (Priority: P1) 🎯 MVP

**Goal**: Users can click Edit on a completed meeting's summary, make changes in a WYSIWYG markdown editor, and save the updated summary to the server.

**Independent Test**: Navigate to a completed meeting → click Edit → modify text in WYSIWYG editor → click Save → refresh page → verify changes persisted.

### Backend Implementation

- [x] T007 [US1] Create `MeetingSummaryUpdate` request model (with `summary_text: str` field) in backend/app/models.py
- [x] T008 [US1] Add `update_summary(meeting_id, summary_text)` method to MeetingService in backend/app/services/meeting.py — on first edit copy `summary_text` → `original_summary_text`, then set new `summary_text` and `summary_edited = True`
- [x] T009 [US1] Add `PATCH /{meeting_id}/summary` endpoint in backend/app/api/v1/endpoints/meetings.py — validates ownership, checks meeting not processing, calls `meeting_service.update_summary()`, returns updated summary fields per contract

### Frontend Implementation

- [x] T010 [US1] Add `updateMeetingSummary(meetingId, summaryText)` function to frontend-2/app/lib/api.ts — PATCH request to `/meetings/{id}/summary`
- [x] T011 [US1] Create the `SummaryEditor` component in frontend-2/app/components/summary-editor.tsx — Tiptap WYSIWYG editor with toolbar (bold, italic, headings, lists, links), loads markdown content via `tiptap-markdown`, outputs markdown on save. Style with Tailwind: `border border-stone-200 rounded-lg bg-white`, toolbar buttons use `indigo-600` accent, no shadows
- [x] T012 [US1] Integrate `SummaryEditor` into the meeting detail page in frontend-2/app/dashboard/meetings/[id]/page.tsx — add Edit/Cancel/Save buttons next to summary heading, toggle between `react-markdown` read-only view and `SummaryEditor` component, call `updateMeetingSummary()` on save, disable Edit button when meeting is processing
- [x] T013 [US1] Add `beforeunload` event listener in the meeting detail page when editor is active with unsaved changes — warn user before navigating away (frontend-2/app/dashboard/meetings/[id]/page.tsx)

**Checkpoint**: User Story 1 complete — users can edit and save summaries via WYSIWYG editor

---

## Phase 4: User Story 2 — Track Edit History (Priority: P2)

**Goal**: System preserves the original AI-generated summary, shows an "Edited" badge, and allows users to view/restore the original.

**Independent Test**: Edit a summary → verify "Edited" badge appears → click "View Original" → verify original text shown → click "Restore Original" → verify summary reverts and badge disappears.

**Depends on**: Phase 3 (US1) — editing must work before tracking makes sense

### Backend Implementation

- [x] T014 [US2] Add `restore_summary(meeting_id)` method to MeetingService in backend/app/services/meeting.py — copy `original_summary_text` → `summary_text`, set `summary_edited = False`
- [x] T015 [US2] Add `POST /{meeting_id}/summary/restore` endpoint in backend/app/api/v1/endpoints/meetings.py — validates ownership, checks `original_summary_text` is not null, calls `meeting_service.restore_summary()`, returns updated fields per contract

### Frontend Implementation

- [x] T016 [US2] Add `restoreMeetingSummary(meetingId)` function to frontend-2/app/lib/api.ts — POST request to `/meetings/{id}/summary/restore`
- [x] T017 [US2] Add "Edited" badge to the summary section in frontend-2/app/dashboard/meetings/[id]/page.tsx — show when `meeting.summary_edited === true`, use `text-stone-500 bg-stone-100 border border-stone-200 rounded-md text-xs px-2 py-1` styling
- [x] T018 [US2] Add "View Original" / "Restore Original" controls to the meeting detail page in frontend-2/app/dashboard/meetings/[id]/page.tsx — "View Original" shows `original_summary_text` in a read-only panel, "Restore Original" calls `restoreMeetingSummary()` and refreshes meeting data

**Checkpoint**: User Story 2 complete — original summary preserved, badge shown, restore works

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing and final validation

- [x] T019 Write E2E test for edit summary flow in tests/e2e/test_edit_summary.py — Playwright/Python: navigate to completed meeting, enter edit mode, modify summary, save, verify persistence, test cancel discards changes
- [x] T020 Write E2E test for restore original flow in tests/e2e/test_edit_summary.py — edit summary, verify "Edited" badge, restore original, verify badge removed and original text restored
- [x] T021 Verify design system compliance — audit SummaryEditor toolbar and container for: no shadows, border-stone-200, rounded-lg, indigo-600 accent, stone text hierarchy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (npm packages installed)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (model extended, DB migrated)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (edit flow must exist)
- **Polish (Phase 5)**: Depends on Phase 3 + Phase 4

### Within Each User Story

- Backend models/services before endpoints
- Backend endpoints before frontend API functions
- Frontend API functions before UI components
- UI components before page integration

### Parallel Opportunities

**Phase 2**:
- T002 + T005 can run in parallel (backend model + frontend type — different repos)

**Phase 3 (US1)**:
- T007 + T010 cannot parallelize (T010 depends on backend endpoint existing)
- T011 can start in parallel with backend tasks (editor component is self-contained)

**Phase 4 (US2)**:
- T014 + T016 cannot parallelize (frontend depends on backend endpoint)
- T017 can start in parallel with backend tasks (badge is purely frontend state)

---

## Parallel Example: User Story 1

```bash
# Backend (sequential):
T007 → T008 → T009

# Frontend (partially parallel with backend):
T011 (editor component — no backend dependency)
# Then after T009 is done:
T010 → T012 → T013
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Install Tiptap packages
2. Complete Phase 2: Extend Meeting model + migrate DB
3. Complete Phase 3: Build PATCH endpoint + WYSIWYG editor + page integration
4. **STOP and VALIDATE**: Test edit/save flow independently
5. Deploy — users can now edit summaries

### Incremental Delivery

1. Setup + Foundational → Model ready
2. User Story 1 → Edit & Save works → Deploy (MVP!)
3. User Story 2 → Original preserved, badge shown, restore works → Deploy
4. Polish → E2E tests + design audit → Confidence for production

---

## Notes

- Tiptap is headless — all styling is manual Tailwind matching the design system
- The editor outputs markdown (not HTML) via `tiptap-markdown` for compatibility with existing `react-markdown` rendering and PDF export
- `original_summary_text` is set only on first edit — subsequent edits don't overwrite it
- E2E tests are in Playwright/Python per constitution (Principle VI)
- No new environment variables needed
