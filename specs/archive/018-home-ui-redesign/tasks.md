# Tasks: Home Page UI Redesign

**Input**: Design documents from `/specs/018-home-ui-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/ui-contracts.md

**Tests**: Not included — no test tasks were explicitly requested in the feature specification.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — this is a frontend-only modification within the existing `frontend-2/` Next.js app. No new dependencies or configuration required.

*(No tasks — all infrastructure already exists)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking work needed. All existing components (`meeting-feed.tsx`, `sidebar.tsx`, `right-panel.tsx`, home `page.tsx`) and the API layer (`api.ts` with `getMeetings`, `Meeting` type) are already in place. User stories can begin immediately.

*(No tasks — existing codebase provides all prerequisites)*

---

## Phase 3: User Story 1 — Richer Meeting List Cards (Priority: P1) MVP

**Goal**: Redesign each meeting card on the home page to show a title heading, time + duration + speaker metadata line, and a truncated summary preview (2-3 lines with "Show more") for completed meetings. Date groups become collapsible.

**Independent Test**: Load the home page with existing meetings. Verify each completed meeting card shows title, time, duration, speaker, and a summary preview. Processing/queued cards show only status badge — no empty summary area. Date headers have a clickable chevron to collapse/expand.

### Implementation

- [X] T001 [US1] Redesign `MeetingFeedCard` in `frontend-2/app/components/meeting-feed.tsx` — update card layout to show: title as `text-sm font-semibold text-stone-900` heading, metadata subtitle line (time of day + duration + speaker name in `text-xs text-stone-500`), and a 2-3 line summary preview (`line-clamp-3 text-sm text-stone-700 leading-relaxed`) with a "Show more" text affordance (`text-xs text-indigo-600 font-medium`) when truncated. For non-completed meetings, show only title + metadata + StatusBadge — no summary area. Use the `Meeting` type fields: `created_at` (format as time), `duration_seconds` (format as "X min"), `summary_text`, `status`.
- [X] T002 [US1] Add collapsible date group headers in `frontend-2/app/components/meeting-feed.tsx` — wrap each date group in a collapsible section. The date label (`text-sm font-medium text-stone-500`) gets a chevron icon (lucide-react `ChevronDown`) that rotates on toggle. Use React `useState` per group. Default state: expanded. Chevron styling: `w-4 h-4 text-stone-400 transition-transform`.
- [X] T003 [US1] Handle edge cases in `frontend-2/app/components/meeting-feed.tsx` — meetings with no summary and no status (legacy data) fall back to showing only title and file name. Meetings with a very long summary are truncated to 3 lines via `line-clamp-3`. The "Show more" text is only rendered if `summary_text` exceeds ~200 characters.

**Checkpoint**: Home page meeting cards now show rich information. Each card is scannable without clicking into it.

---

## Phase 4: User Story 2 — Top Action Bar (Priority: P2)

**Goal**: Add a top action bar with Meeting URL, Import, and Record buttons above the meeting feed on the home page. Import opens the existing upload modal; the other two show "Coming soon".

**Independent Test**: Load the home page. Verify three action buttons appear between the AI query bar and the meeting feed. Click "Import" — upload modal opens. Hover "Meeting URL" and "Record" — "Coming soon" tooltip appears.

### Implementation

- [X] T004 [P] [US2] Create `ActionBar` component in `frontend-2/app/components/action-bar.tsx` — new component with props `onImportClick: () => void`. Renders three buttons in a `flex items-center gap-2 justify-end` container: (1) Meeting URL — icon-only button with `Video` icon from lucide-react, secondary/outlined style (`border border-stone-200 bg-white text-stone-700 hover:bg-stone-50 rounded-lg p-2`), `title="Coming soon"`, `cursor-default opacity-60`; (2) Import — text button, secondary style (`bg-stone-100 text-stone-800 hover:bg-stone-200 rounded-lg px-4 py-2 text-sm font-medium`), calls `onImportClick`; (3) Record — primary red button with `Mic` icon from lucide-react (`bg-red-600 text-white hover:bg-red-700 rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2`), `title="Coming soon"`, `cursor-default opacity-80`.
- [X] T005 [US2] Integrate `ActionBar` into home page in `frontend-2/app/(dashboard)/page.tsx` — import ActionBar and render it between the AI query bar section and the MeetingFeed. Pass `onImportClick={() => setUploadModalOpen(true)}`. Layout: `flex items-center justify-between mb-6` wrapper containing a section heading ("Your meetings" or similar in `text-lg font-semibold text-stone-800`) on the left and ActionBar on the right.

**Checkpoint**: Users can initiate an import in 1 click from the home page action bar. Meeting URL and Record buttons are visible placeholders.

---

## Phase 5: User Story 3 — Remove Meetings Nav Item and Page (Priority: P3)

**Goal**: Remove the standalone Meetings page and sidebar nav item. Redirect `/meetings` to `/`. Meeting detail pages (`/meetings/[id]`) remain unchanged.

**Independent Test**: Verify the sidebar shows Home, AI Chat, Integrations (no "Meetings"). Navigate to `/meetings` — should redirect to `/`. Navigate to `/meetings/123` — should still load the meeting detail page.

### Implementation

- [X] T006 [P] [US3] Remove "Meetings" from sidebar nav in `frontend-2/app/components/sidebar.tsx` — remove the `{ href: "/meetings", label: "Meetings", icon: <MeetingsIcon /> }` entry from the `NAV_LINKS` array. The resulting array should be: Home, AI Chat, Integrations.
- [X] T007 [P] [US3] Replace meetings list page with redirect in `frontend-2/app/(dashboard)/meetings/page.tsx` — replace the entire page component with a `redirect("/")` call using Next.js `redirect` from `next/navigation`. Remove all existing imports and state. Keep this as a server component (remove `"use client"` if present). The file at `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` MUST remain untouched.

**Checkpoint**: Navigation is simplified to 3 items. No duplicate meeting views exist. Meeting detail pages still work.

---

## Phase 6: User Story 4 — Updated Right Panel Quick Actions (Priority: P4)

**Goal**: Relabel the right panel's primary button from "Upload a meeting" to "Import" for consistency with the new action bar.

**Independent Test**: View the right panel on desktop. The primary button reads "Import" and opens the upload modal.

### Implementation

- [X] T008 [US4] Relabel right panel button in `frontend-2/app/components/right-panel.tsx` — change the primary Button's text content from "Upload a meeting" to "Import". Keep the same `onClick` handler (`window.dispatchEvent(new Event('open-upload-modal'))`), icon, and styling. Also update the icon to use a generic import/download icon instead of the video camera icon for consistency with the "Import" label.

**Checkpoint**: Right panel button label matches the top action bar terminology.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency pass and cleanup

- [X] T009 Remove unused `MeetingCard` component import from `frontend-2/app/(dashboard)/meetings/page.tsx` (now a redirect — verify no dead imports remain)
- [X] T010 Remove unused imports in `frontend-2/app/(dashboard)/meetings/page.tsx` — since the page is now a redirect, delete any leftover `FileUploadZone`, `uploadMeeting`, `Button`, `MeetingCard`, `getMeetings`, `deleteMeeting`, `isActiveMeeting`, `useRouter`, `useState`, `useEffect`, `useRef` imports
- [X] T011 Verify build passes — run `cd frontend-2 && npx next build` and confirm no TypeScript or lint errors
- [X] T012 Verify meeting detail page still works — navigate to `/meetings/[id]` for an existing meeting and confirm the detail page renders correctly with transcript viewer and media player

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A — no setup needed
- **Foundational (Phase 2)**: N/A — no foundational work needed
- **User Story 1 (Phase 3)**: Can start immediately — no dependencies
- **User Story 2 (Phase 4)**: Can start immediately — independent of US1 (different files)
- **User Story 3 (Phase 5)**: Can start immediately — independent of US1/US2
- **User Story 4 (Phase 6)**: Can start immediately — independent of other stories
- **Polish (Phase 7)**: Depends on US3 completion (T007 must be done before T009/T010)

### User Story Dependencies

- **US1 (P1)**: Independent — modifies `meeting-feed.tsx` only
- **US2 (P2)**: Independent — creates new `action-bar.tsx` and modifies `page.tsx`
- **US3 (P3)**: Independent — modifies `sidebar.tsx` and `meetings/page.tsx`
- **US4 (P4)**: Independent — modifies `right-panel.tsx` only

### Within Each User Story

- US1: T001 → T002 → T003 (sequential — all in same file)
- US2: T004 ∥ (then T005 depends on T004)
- US3: T006 ∥ T007 (parallel — different files)
- US4: T008 (single task)

### Parallel Opportunities

All four user stories touch different files and can run fully in parallel:

```
US1 (meeting-feed.tsx) ─────────────────────┐
US2 (action-bar.tsx + page.tsx) ────────────┼── All in parallel
US3 (sidebar.tsx + meetings/page.tsx) ──────┤
US4 (right-panel.tsx) ─────────────────────┘
```

---

## Parallel Example: All User Stories

```bash
# All four stories can launch simultaneously:
Agent A: T001 → T002 → T003  (US1: meeting-feed.tsx)
Agent B: T004 → T005          (US2: action-bar.tsx → page.tsx)
Agent C: T006 ∥ T007          (US3: sidebar.tsx ∥ meetings/page.tsx)
Agent D: T008                  (US4: right-panel.tsx)

# After all complete:
Agent A: T009 → T010 → T011 → T012  (Polish)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T003 (richer meeting cards)
2. **STOP and VALIDATE**: Home page cards show rich information
3. Deploy — users immediately benefit from better meeting scanning

### Incremental Delivery

1. US1: Richer cards → Deploy (MVP)
2. US2: Action bar → Deploy (adds quick import access)
3. US3: Remove meetings page → Deploy (simplified navigation)
4. US4: Right panel relabel → Deploy (terminology consistency)
5. Polish: Cleanup → Final deploy

### Single Developer Strategy

Execute in priority order: US1 → US2 → US3 → US4 → Polish. Each story is a self-contained commit.

---

## Notes

- All changes are frontend-only — no backend modifications needed
- The existing `Meeting` type in `api.ts` already provides all fields needed (`summary_text`, `duration_seconds`, `created_at`, `status`, `sub_status`)
- Design system compliance: stone/indigo palette, borders only (no shadows), `rounded-lg`, 4px spacing grid
- Meeting detail page (`/meetings/[id]`) must remain functional throughout all changes
- "Coming soon" buttons use `title` attribute tooltip + muted opacity — no toast/notification system needed
