---
description: "Task list for 005-home-redesign — authenticated shell layout redesign"
---

# Tasks: Home Page Redesign

**Input**: Design documents from `/specs/005-home-redesign/`  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅  
**Branch**: `005-home-redesign`  
**Tech**: TypeScript 5 / Next.js 15 App Router, Tailwind CSS v4, Supabase JS, Axios

**Tests**: E2E tests in Playwright/Python are REQUIRED per constitution (Principle VI) — included below.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the route group folder structure and move existing files into the new layout hierarchy before any new component work begins.

- [x] T001 Create `frontend-2/app/(dashboard)/` route group directory structure per plan.md
- [x] T002 Move `frontend-2/app/meetings/page.tsx` → `frontend-2/app/(dashboard)/meetings/page.tsx`
- [x] T003 Move `frontend-2/app/meetings/[id]/page.tsx` → `frontend-2/app/(dashboard)/meetings/[id]/page.tsx`
- [x] T004 [P] Verify existing login/register/forgot-password/auth routes remain at app root (no move required — confirm by inspection)

**Checkpoint**: Route group exists; existing meeting routes functional at same URLs via the new folder hierarchy

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared components and the authenticated layout shell that ALL user story phases depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `frontend-2/app/components/app-shell.tsx` — three-column flex layout wrapper (`bg-stone-50`, sidebar slot + `<main>` slot + right-panel slot; responsive: right panel hidden below `md` breakpoint)
- [x] T006 [P] Create `frontend-2/app/(dashboard)/layout.tsx` — authenticated shell layout: imports `AppShell`, checks Supabase session client-side, redirects to `/login` if no session; wraps `{children}` in the shell
- [x] T007 [P] Update `frontend-2/app/layout.tsx` — remove old top-level `<nav>` that currently wraps `{children}`; root layout becomes a bare HTML/body shell (login/register pages will have their own nav)

**Checkpoint**: Authenticated shell renders; visiting `/` with a valid session shows the three-column frame; without a session redirects to `/login`

---

## Phase 3: User Story 1 — Authenticated Dashboard Shell (Priority: P1) 🎯 MVP

**Goal**: All authenticated routes show the persistent three-column layout with a working sidebar and right panel.

**Independent Test**: Log in → navigate to `/` → verify sidebar (logo, nav links, user profile), main area header, and right panel all render; click a nav link and confirm sidebar does not remount.

### E2E Test for User Story 1 ⚠️ (REQUIRED — constitution Principle VI)

- [x] T008 [P] [US1] Write E2E test `tests/e2e/test_home_layout.py` — happy path: log in with test credentials, assert three-column layout is present, assert sidebar contains "Zabt AI" logo and "Home" nav link is active, assert no horizontal scroll (Playwright/Python)

### Implementation for User Story 1

- [x] T009 [P] [US1] Create `frontend-2/app/components/sidebar.tsx` — left sidebar with: Zabt logo mark, collapsible sections (Channels, DMs, Folders), primary nav links (Home, AI Chat, Meetings, Integrations) with Heroicon-style inline SVGs, active-route highlight (`bg-indigo-50 text-indigo-700`), user avatar initials + display name + email from Supabase `getUser()`, plan usage bar at bottom — all tokens from `system.md` (stone palette, `border-stone-200`, `rounded-lg`, no shadows)
- [x] T010 [P] [US1] Create `frontend-2/app/components/right-panel.tsx` — right panel with: "Upload a meeting" primary CTA button (routes to `/meetings`), "Connect a calendar" secondary CTA (placeholder), empty-state copy for upcoming events; `bg-white border-l border-stone-200` per design system
- [x] T011 [US1] Wire `Sidebar` and `RightPanel` into `app-shell.tsx` — import both, compose `flex h-screen overflow-hidden` outer wrapper; sidebar fixed-width (`220px`), main area `flex-1 overflow-y-auto`, right panel fixed-width (`280px`, hidden on `< md`)
- [x] T012 [US1] Update `.interface-design/system.md` — append Sidebar pattern (bg, border, active state token, section label style) and RightPanel pattern (border-l, width, responsive collapse rule) to Components section

**Checkpoint**: US1 fully functional — refresh any authenticated route and the shell renders with sidebar, user name, nav links, and right panel; nav links route correctly; right panel CTAs are visible

---

## Phase 4: User Story 2 — AI Query Bar (Priority: P2)

**Goal**: The home page central area contains an AI query bar; submitting it routes to `/meetings?q=<query>`.

**Independent Test**: From the home page, type "What were my last meeting action items?" in the query bar → press Enter → confirm URL changes to `/meetings?q=What+were+my+last+meeting+action+items%3F`.

### E2E Test for User Story 2 ⚠️ (REQUIRED — constitution Principle VI)

- [x] T013 [P] [US2] Write E2E test `tests/e2e/test_home_ai_query.py` — assert query bar is present on home page, type a query, press Enter, assert URL navigates to `/meetings` with `q` param, assert empty query does not navigate (Playwright/Python)

### Implementation for User Story 2

- [x] T014 [P] [US2] Create `frontend-2/app/components/ai-query-bar.tsx` — styled pill input: `bg-white border border-stone-200 rounded-lg flex items-center gap-2 px-4 py-3`; sparkle icon (inline SVG) on left; controlled `<input>` with placeholder "Ask Zabt anything about your meetings…"; "Advanced" text toggle (stone-400, toggles `advanced` boolean state); submit arrow button (`bg-indigo-600 text-white rounded-lg`); `onSubmit` prop defaults to routing to `/meetings?q=<query>`; no submit on empty input
- [x] T015 [US2] Create `frontend-2/app/(dashboard)/page.tsx` — home dashboard page: personalized greeting (`"Good morning/afternoon/evening, [firstName]"` keyed by `new Date().getHours()`), renders `<AiQueryBar />` below greeting, renders `<MeetingFeed />` below query bar (data fetched here); page wrapped in `px-6 py-8 max-w-none`

**Checkpoint**: US2 functional — home page shows greeting and query bar; submitting a query navigates to meetings with `q` param; empty submit does nothing

---

## Phase 5: User Story 3 — Meeting Activity Feed (Priority: P3)

**Goal**: The central area below the query bar shows recent meetings grouped by date; clicking a card navigates to the meeting detail.

**Independent Test**: Upload at least one meeting → return to home page → confirm meeting appears as a card in the feed under the correct date group; click the card → confirm navigation to `/meetings/[id]`.

### E2E Test for User Story 3 ⚠️ (REQUIRED — constitution Principle VI)

- [x] T016 [P] [US3] Write E2E test `tests/e2e/test_home_feed.py` — scenario A: no meetings → assert empty-state text and upload CTA are visible; scenario B: meetings exist → assert at least one feed card with title and date group header is present; assert clicking a card navigates to `/meetings/[id]` (Playwright/Python)

### Implementation for User Story 3

- [x] T017 [P] [US3] Create `frontend-2/app/components/meeting-feed.tsx` — exports `MeetingFeed` (client component); fetches `getMeetings()` on mount; groups meetings by `created_at` date into `{ label: string, meetings: Meeting[] }[]` using `formatDateLabel()` helper (Today/Yesterday/Weekday logic per data-model.md); renders `DateGroupHeader` (`text-sm font-medium text-stone-500`) and `MeetingFeedCard` per item; shows skeleton placeholder divs (`bg-stone-100 rounded-lg animate-pulse h-16`) while loading; shows empty-state `<p>` with upload CTA button when no meetings
- [x] T018 [US3] Create `MeetingFeedCard` sub-component inside `meeting-feed.tsx` — `bg-white rounded-lg border border-stone-200 p-4 flex gap-3 hover:bg-stone-50 transition-colors cursor-pointer`; avatar circle with initials (stone-100/700); title `text-sm font-medium text-stone-900`; summary preview first 150 chars of `summary_text` as `text-xs text-stone-500`; `StatusBadge` for `status`; wraps in Next.js `<Link href="/meetings/[id]">`
- [x] T019 [US3] Wire `MeetingFeed` into `page.tsx` (T015) — import and render below `<AiQueryBar />`; pass no props (feed fetches its own data internally)

**Checkpoint**: US3 functional — home feed shows date-grouped meeting cards; empty state shows correctly; clicking a card navigates to detail

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Responsive behaviour, edge cases, and final design system update.

- [x] T020 [P] Add mobile sidebar drawer to `app-shell.tsx` — hamburger button in a top `<header>` bar (visible only below `md`); clicking toggles `sidebarOpen` state; sidebar slides in as `fixed inset-y-0 left-0 z-50 w-[220px]` with a semi-transparent backdrop; close on backdrop click or nav link click
- [x] T021 [P] Add `title` truncation and long-name guard to `sidebar.tsx` — ensure `userName` and `userEmail` use `truncate` and `max-w-[140px]` so very long names don't break layout
- [x] T022 [P] Fix `meetings/page.tsx` (after move) — replace old top-level `<nav>` with a page-level `<header>` since the shell nav now handles navigation; update "← Home" button to use `<Link href="/">` instead of `router.push`
- [x] T023 [P] Fix `meetings/[id]/page.tsx` (after move) — same nav header replacement as T022
- [x] T024 Smoke-test full authenticated flow end-to-end: login → home (shell renders) → sidebar nav to meetings → click meeting → detail page (shell renders consistently throughout); confirm no flash of unstyled content

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (route group must exist) — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — AppShell must exist before Sidebar/RightPanel can be wired in
- **US2 (Phase 4)**: Depends on Phase 2 + AppShell (T011 wiring) — can start in parallel with US1 if AiQueryBar file is isolated [P T014 is fully parallel]
- **US3 (Phase 5)**: Depends on US2 page.tsx (T015) existing — MeetingFeed is rendered inside the home page
- **Polish (Phase 6)**: Depends on all story phases complete

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: AppShell + authenticated layout)
    ↓
Phase 3 (US1: Sidebar + RightPanel) ──┐
Phase 4 (US2: AI Query Bar + page.tsx) ←─ T015 page.tsx required by US3
    ↓
Phase 5 (US3: Meeting Feed)
    ↓
Phase 6 (Polish)
```

### Parallel Opportunities

- T002, T003, T004 can run simultaneously (Phase 1)
- T006 and T007 can run simultaneously (Phase 2)
- T008 (E2E test) and T009, T010 (components) can run simultaneously (Phase 3)
- T013 (E2E test) and T014 (component) can run simultaneously (Phase 4)
- T016 (E2E test) and T017, T018 (components) can run simultaneously (Phase 5)
- T020, T021, T022, T023 are fully parallel (Phase 6)

---

## Parallel Example: User Story 1

```bash
# Phase 3 — all [P] tasks can run concurrently:
Task T008: "Write tests/e2e/test_home_layout.py"
Task T009: "Create frontend-2/app/components/sidebar.tsx"
Task T010: "Create frontend-2/app/components/right-panel.tsx"

# Then sequentially (depends on T009 + T010):
Task T011: "Wire Sidebar + RightPanel into app-shell.tsx"
Task T012: "Update .interface-design/system.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Route group setup (T001–T004)
2. Complete Phase 2: AppShell + authenticated layout (T005–T007)
3. Complete Phase 3: Sidebar + RightPanel (T008–T012)
4. **STOP and VALIDATE**: Log in → confirm three-column shell → run `pytest tests/e2e/test_home_layout.py`
5. Demo-ready MVP: authenticated shell on all post-login pages

### Incremental Delivery

1. Phases 1–2 → Authenticated shell frame (no content yet)
2. Phase 3 (US1) → Shell with sidebar + nav + right panel → Demo/validate
3. Phase 4 (US2) → Home page with greeting + AI query bar → Demo/validate
4. Phase 5 (US3) → Meeting feed on home page → Demo/validate
5. Phase 6 → Polish + mobile → Ship

---

## Notes

- `[P]` tasks = different files, no shared state dependencies, can run in parallel
- `[USn]` label maps task to spec.md user story for traceability
- All new components MUST use stone/indigo palette and `border-stone-200` borders — no shadows
- E2E tests (T008, T013, T016) MUST be written before implementation; verify they fail first
- Commit after each checkpoint to enable clean rollback
- After completing T012, run `/interface-design:audit` to verify design system compliance
