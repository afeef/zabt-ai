# Tasks: Logout Button

**Input**: Design documents from `/specs/015-logout-button/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: E2E test included per constitution requirement (Principle VI — user-facing flow).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed. All infrastructure (Supabase client, auth helpers, sidebar component) already exists. This phase is empty.

**Checkpoint**: Proceed directly to User Story 1.

---

## Phase 2: User Story 1 — Logout from Sidebar (Priority: P1) 🎯 MVP

**Goal**: Authenticated user can click the profile section in the sidebar, see a dropdown menu, and click "Logout" to end their session and be redirected to the login page.

**Independent Test**: Log in → click profile in sidebar → dropdown appears → click Logout → session terminated → redirected to `/login` → cannot access protected pages.

### Implementation for User Story 1

- [x] T001 [P] [US1] Create ProfileMenu dropdown component in `frontend-2/app/components/profile-menu.tsx` — includes: click-outside-to-close handler, menu items with icons (placeholder items for future: Account Settings, Help Center), divider, and Logout item styled with `text-red-600 hover:bg-red-50`. Logout calls `clearToken()` from `frontend-2/app/lib/api.ts` with try/catch, then `router.push("/login")` as fallback (dashboard layout `onAuthStateChange` is the primary redirect mechanism). Container uses design system tokens: `bg-white border border-stone-200 rounded-lg`, no shadows.
- [x] T002 [P] [US1] Update sidebar profile section in `frontend-2/app/components/sidebar.tsx` — make the profile area (avatar + name + email) a clickable button that toggles the ProfileMenu dropdown. Add a chevron indicator that rotates when the menu is open. Import and render `<ProfileMenu>` anchored below the profile section. Pass `userName`, `userEmail`, and `initials` as props.
- [x] T003 [US1] Verify desktop and mobile logout flow works end-to-end — on mobile, the dropdown opens inside the off-canvas sidebar drawer (no special handling needed per research R6). Ensure the sidebar `onNavClick` prop closes the mobile sidebar when logout redirects.

**Checkpoint**: User Story 1 is fully functional. Users can log out from both desktop and mobile. This is the MVP.

---

## Phase 3: User Story 2 — Logout Confirmation (Priority: P2)

**Goal**: When the user clicks "Logout" in the profile dropdown, an inline confirmation prompt appears (within the dropdown) asking "Confirm logout?" with Confirm and Cancel buttons. This prevents accidental logouts.

**Independent Test**: Click profile → dropdown opens → click Logout → dropdown transforms to show "Confirm logout?" with Confirm/Cancel → click Cancel → returns to normal menu → click Logout again → click Confirm → session terminated.

### Implementation for User Story 2

- [x] T004 [US2] Add inline confirmation state to ProfileMenu in `frontend-2/app/components/profile-menu.tsx` — add `confirmingLogout` state (`useState<boolean>`). When Logout is clicked, set `confirmingLogout = true` which replaces the menu items with a "Confirm logout?" message and two buttons: "Confirm" (`bg-red-600 text-white hover:bg-red-700 rounded-lg text-sm`) and "Cancel" (`bg-stone-100 text-stone-800 hover:bg-stone-200 rounded-lg text-sm`). "Confirm" calls the actual logout logic. "Cancel" resets `confirmingLogout = false`. Reset confirmation state when dropdown closes.

**Checkpoint**: Both user stories complete. Logout has full confirmation flow.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Design system documentation and E2E testing.

- [x] T005 [P] Document the ProfileMenu dropdown pattern in `.interface-design/system.md` — add a `### ProfileMenu` subsection under Components describing: container styles (`bg-white border border-stone-200 rounded-lg`), menu item styles (`px-3 py-2 text-sm text-stone-700 hover:bg-stone-100 rounded-lg`), icon styles (`w-4 h-4 text-stone-400`), danger item (`text-red-600 hover:bg-red-50`), divider (`border-t border-stone-100`), inline confirmation pattern.
- [x] T006 [P] Create E2E test for logout flow in `tests/e2e/test_logout.py` — Playwright/Python test covering: (1) login → click profile → verify dropdown visible → click Logout → verify confirmation prompt → click Confirm → verify redirected to `/login`, (2) login → click profile → click Logout → click Cancel → verify still logged in, (3) after logout → navigate to protected route → verify redirected to `/login`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 2 (US1)**: No prerequisites — can start immediately
- **Phase 3 (US2)**: Depends on T001 (ProfileMenu component must exist)
- **Phase 4 (Polish)**: Depends on Phase 3 completion (both stories must be done)

### User Story Dependencies

- **User Story 1 (P1)**: Independent — can start immediately. T001 and T002 are parallel (different files). T003 depends on both T001 and T002.
- **User Story 2 (P2)**: Depends on US1's T001 (modifies the same ProfileMenu component created in T001).

### Within Each User Story

- US1: T001 ∥ T002 → T003
- US2: T004 (single task, depends on T001)
- Polish: T005 ∥ T006

### Parallel Opportunities

- T001 and T002 can run in parallel (different files: `profile-menu.tsx` vs `sidebar.tsx`)
- T005 and T006 can run in parallel (different files: `system.md` vs `test_logout.py`)

---

## Parallel Example: User Story 1

```text
# Launch in parallel (different files):
Task T001: "Create ProfileMenu component in frontend-2/app/components/profile-menu.tsx"
Task T002: "Update sidebar profile section in frontend-2/app/components/sidebar.tsx"

# Then sequentially:
Task T003: "Verify desktop and mobile logout flow" (depends on T001 + T002)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 + T002 in parallel → ProfileMenu exists, sidebar triggers it
2. Complete T003 → Verify end-to-end flow
3. **STOP and VALIDATE**: Log in, click profile, click Logout → redirected to /login
4. Deploy if ready — users can log out

### Incremental Delivery

1. US1 (T001-T003) → Users can log out → Deploy (MVP!)
2. US2 (T004) → Logout has confirmation → Deploy
3. Polish (T005-T006) → Design system documented, E2E tests in place → Deploy

---

## Notes

- No backend changes required — this is entirely frontend
- `clearToken()` in `api.ts` already wraps `supabase.auth.signOut()` — no new auth logic needed
- Dashboard layout's `onAuthStateChange` listener handles redirect on session loss automatically
- Design system compliance: no shadows, `rounded-lg`, `border-stone-200`, `indigo-600` accent, `red-600` for danger
- Total tasks: 6 | US1: 3 tasks | US2: 1 task | Polish: 2 tasks
