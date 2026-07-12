---
description: "Task list for 001-social-register"
---

# Tasks: Social Login & Enhanced Registration Page

**Input**: Design documents from `/specs/001-social-register/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/registration.md ✅ quickstart.md ✅

**Tests**: No test runner in project — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths are included in every task description

---

## Phase 1: Setup

**Purpose**: Environment verification

- [x] T001 Confirm `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_FRONTEND_URL` exist in `frontend-2/.env.local`; these are required for OAuth redirect URI construction and were added in `003-social-sso-login` — create the file if absent with `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` and `NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000`

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Extend `register()` in `frontend-2/app/lib/api.ts` to accept `fullName` — required by User Story 2's form submit.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Update `register(email: string, password: string)` to `register(email: string, password: string, fullName: string): Promise<User>` in `frontend-2/app/lib/api.ts` — add `fullName: string` as a third parameter and include `full_name: fullName` in the JSON body of the `POST /users/` call; the backend already accepts `full_name: str = Body(None)` (confirmed in `backend/app/api/users.py`)

**Checkpoint**: `api.ts` now exports an updated `register()` that forwards `full_name` to the backend. Foundation ready — user story phases can begin.

---

## Phase 3: User Story 1 — Social Sign-Up (Priority: P1) 🎯 MVP

**Goal**: User can create a Meetily account using Google, Microsoft, or Apple via the same backend-redirect OAuth2 flow as the login page

**Independent Test**: Visit `/register` → click "Sign up with Google" → browser navigates to `{API_URL}/auth/oauth/google/authorize?...`. Simulate callback by visiting `/auth/callback/google?token=<valid-jwt>` → token stored → redirected to `/`. Visit `/auth/callback/google?error=email_conflict` → conflict message with /login link shown. Email/password form still submits correctly.

### Implementation for User Story 1

- [x] T003 [US1] Replace `frontend-2/app/register/page.tsx` entirely with the new design layout. Structure (top to bottom): (a) centred `<main>` on `bg-stone-50`; (b) `max-w-md rounded-xl border border-stone-200 p-8` card; (c) Meetily wordmark `text-xl font-bold text-stone-900`; (d) `text-2xl font-bold text-stone-900` "Create your account" heading; (e) `text-sm text-stone-500` subtitle "Please enter your details to sign in."; (f) 3 `SocialButton` components (`frontend-2/app/components/ui/social-button.tsx`) for google/microsoft/apple — labels "Sign up with Google / Microsoft / Apple" — each `onClick` calls `window.location.href = socialLoginUrl(provider, crypto.randomUUID())`; (g) separator `flex items-center gap-3` with `<hr>` lines and `text-xs text-stone-400` "or sign up with email"; (h) email input (label "Email address", placeholder "name@company.com"); (i) password input (label "Password", placeholder "At least 8 characters", `minLength={8}`); (j) full-width `<Button>` "Sign up" — submit handler calls `register(email, password, "")` as a placeholder (Full Name wired in T004); (k) "Already have an account?" with `text-indigo-600` Sign in link to `/login`. Keep existing `loading`, `error` state and `useRouter` redirect to `/login` on success.

**Checkpoint**: US1 is independently functional. Social sign-up buttons navigate to the OAuth flow. Existing OAuth callback page handles token/error states without modification. Email/password registration still works.

---

## Phase 4: User Story 2 — Enhanced Registration Form (Priority: P2)

**Goal**: The email/password form collects Full Name and provides a show/hide toggle on the password field, matching the visual completeness of the new login page

**Independent Test**: (a) Fill in Full Name "Jane Smith", email, password ≥ 8 chars → click Sign up → redirected to `/login`. (b) Leave Full Name blank → form prevents submission. (c) Click eye icon on password → password characters revealed; click again → re-masked.

### Implementation for User Story 2

- [x] T004 [US2] Add Full Name field to `frontend-2/app/register/page.tsx`: add `fullName` string state (default `""`); add a `<div>` with label "Full name", `<input type="text" required placeholder="John Doe">` before the email field; replace `register(email, password, "")` in the submit handler with `register(email, password, fullName)`.

- [x] T005 [US2] Add show/hide password toggle to the password `<input>` in `frontend-2/app/register/page.tsx`: add `showPassword` boolean state (default false); set `type={showPassword ? "text" : "password"}`; wrap input in a `relative <div>`; render `<button type="button">` absolutely positioned at the right edge with `<Eye>` or `<EyeOff>` from `lucide-react` (16×16, `text-stone-400`); clicking toggles `showPassword`.

**Checkpoint**: Both user stories are independently functional. The registration form collects full name, email, and password; social sign-up buttons are fully wired; password show/hide works.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Design system compliance and quickstart validation

- [x] T006 Verify that the register page `rounded-xl` and `max-w-md` card dimensions are already covered by the login card exception documented in `.interface-design/system.md` — no system.md update needed if exception already applies to all auth cards; add a note if the exception was login-only

- [x] T007 [P] Run `/interface-design:audit` on `frontend-2/app/register/page.tsx` — fix any spacing, shadow, rounding, or colour violations found against `.interface-design/system.md`

- [x] T008 [P] Manually trace each test path from `specs/001-social-register/quickstart.md` against the implemented routes and confirm: social callback mock works, duplicate-email error shown, full name required validation works, show/hide toggle works, "Sign in" link navigates to `/login`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T002 must exist — updated `register()` needed for correctness)
- **US2 (Phase 4)**: Depends on US1 (T003 must exist — modifying the page T003 creates)
- **Polish (Phase N)**: Depends on all user story phases complete

### Within Phase Dependencies

- T002 is the only foundational task — no internal dependencies
- T003 depends on T002 (uses updated `register()`)
- T004 depends on T003 (adds to the page T003 creates)
- T005 depends on T004 (adds to the same page; sequential to avoid conflicts)
- T006, T007, T008 are independent of each other — T007 and T008 can run in parallel

### Parallel Opportunities

Within Phase N:
- T007 and T008 can run in parallel (different concerns)

```bash
# Phase N parallel launch:
Task: "Run interface-design:audit on frontend-2/app/register/page.tsx"   # T007
Task: "Trace quickstart.md test paths against implemented routes"         # T008
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003)
4. **STOP and VALIDATE**: Social buttons navigate to OAuth flow; callback page handles token/error; email/password registration still works
5. Ship MVP — social sign-up is live

### Incremental Delivery

1. T001 → T002 → T003 → **US1 done** (social sign-up)
2. T004 → T005 → **US2 done** (full name + show/hide)
3. T006 → T007 → T008 → **Polish done**

### Total Tasks: 8

| Phase | Tasks | Count |
|-------|-------|-------|
| Setup | T001 | 1 |
| Foundational | T002 | 1 |
| US1 — Social Sign-Up | T003 | 1 |
| US2 — Enhanced Form | T004–T005 | 2 |
| Polish | T006–T008 | 3 |

---

## Notes

- `[P]` tasks = different files or concerns, no in-phase dependencies
- `[USn]` label maps each task to its user story for traceability
- No parallel tasks within Phases 2–4 — all touch the same file or depend on the previous task
- `SocialButton`, `socialLoginUrl()`, `OAuthProvider`, and `/auth/callback/[provider]` are all reused from `003-social-sso-login` — no new components to create
- The backend `POST /users/` already accepts `full_name` — confirmed; no backend work required
- T006/T007/T008 can launch in parallel after T005 is complete
