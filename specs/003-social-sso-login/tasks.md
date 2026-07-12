---
description: "Task list for 003-social-sso-login"
---

# Tasks: Social Login & SSO for Login Page

**Input**: Design documents from `/specs/003-social-sso-login/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/auth.md ✅ quickstart.md ✅

**Tests**: No test runner in project — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

---

## Phase 1: Setup

**Purpose**: Environment and directory preparation

- [x] T001 Confirm `NEXT_PUBLIC_API_URL` is set and add `NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000` to `frontend-2/.env.local` (create file if absent); both variables are required per `specs/003-social-sso-login/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend `frontend-2/app/lib/api.ts` with the types and helper functions required
by all three user stories. These four tasks touch the same file — complete them sequentially.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Add `OAuthProvider`, `SSOLookupRequest`, and `SSOLookupResponse` TypeScript types to `frontend-2/app/lib/api.ts` after the existing `AuthToken` interface (see `specs/003-social-sso-login/data-model.md` for exact shapes)

- [x] T003 Add `socialLoginUrl(provider: OAuthProvider, state: string): string` function to `frontend-2/app/lib/api.ts` — constructs and returns `${API_URL}/auth/oauth/${provider}/authorize?redirect_uri=${encodeURIComponent(frontendUrl+"/auth/callback/"+provider)}&state=${state}` where `frontendUrl` reads from `process.env.NEXT_PUBLIC_FRONTEND_URL`

- [x] T004 Add `ssoLookup(email: string): Promise<SSOLookupResponse>` function to `frontend-2/app/lib/api.ts` — calls `POST /auth/sso/lookup` via `apiClient`; on any network error, timeout, or 5xx response, catches the error and returns `{ sso_enabled: false, redirect_url: null, organisation_name: null }` (never throws)

- [x] T005 Add `loginWithRememberMe(email: string, password: string, rememberMe: boolean): Promise<void>` function to `frontend-2/app/lib/api.ts` — mirrors existing `login()` but appends `&remember_me=true` to the form body when `rememberMe` is true; stores token via `setToken()`

**Checkpoint**: `api.ts` now exports `socialLoginUrl`, `ssoLookup`, `loginWithRememberMe`, and the three new types. Foundation ready — user story phases can now begin.

---

## Phase 3: User Story 1 — Social Login (Priority: P1) 🎯 MVP

**Goal**: User can sign in with Google, Microsoft, or Apple via backend-redirected OAuth2

**Independent Test**: Click "Sign in with Google" on `/login` → browser navigates to `{API_URL}/auth/oauth/google/authorize?...`. Visit `/auth/callback/google?token=<valid-jwt>` → token stored in localStorage, redirected to `/`. Visit `/auth/callback/google?error=email_conflict` → conflict message with /login link shown.

### Implementation for User Story 1

- [x] T006 [P] [US1] Create `frontend-2/app/components/ui/social-button.tsx` — a full-width button component accepting `provider: OAuthProvider`, `label: string`, and `onClick: () => void` props. Design: `w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg border border-stone-200 bg-white text-stone-800 text-sm font-medium hover:bg-stone-50 transition-colors`. Include inline SVG icons for each provider: Google (G multicolour logo, 20×20), Microsoft (four-colour 2×2 grid, 20×20), Apple (Apple logo, 20×20).

- [x] T007 [P] [US1] Create `frontend-2/app/auth/callback/[provider]/page.tsx` — "use client" component. On mount, read `provider` from `use(params)` and query params via `useSearchParams()`. Logic: (1) if `?token=` present: call `setToken(token)`, then `router.replace("/")`. (2) if `?error=email_conflict`: render error banner "An account with this email already exists. Sign in with your password instead." with a link to `/login`. (3) if `?error=` other: render generic error "Sign in failed. Please try again." with link to `/login`. (4) neither: `router.replace("/login")`. Design: `bg-stone-50` page, centred white `rounded-lg border border-stone-200 p-8` card.

- [x] T008 [US1] Replace `frontend-2/app/login/page.tsx` entirely with the new design layout. Structure (top to bottom): (a) centred `<main>` on `bg-stone-50`; (b) white `rounded-xl border border-stone-200 p-8 w-full max-w-md` card; (c) logo row: Meetily wordmark in `text-xl font-bold text-stone-900`; (d) `text-2xl font-bold text-stone-900` "Welcome back" heading; (e) `text-sm text-stone-500` subtitle "Please enter your details to sign in."; (f) 3 `SocialButton` components for google/microsoft/apple — each `onClick` calls `window.location.href = socialLoginUrl(provider, crypto.randomUUID())`; (g) `<div>` separator: `flex items-center gap-3` with `<hr>` lines and `text-xs text-stone-400` "or sign in with email" text; (h) email input (label "Email address", placeholder "name@company.com"); (i) password input (label "Password", placeholder "••••••••"); (j) full-width `<Button>` "Sign in" calling `login()` from `api.ts` (SSO logic added in T009); (k) "Don't have an account?" with `text-indigo-600` Register link to `/register`. Keep existing `loading`, `error` state and `useRouter` redirect logic from the old page.

**Checkpoint**: US1 is independently functional. Social login buttons navigate to the OAuth flow. Callback page handles token and error states. Email/password login still works as before.

---

## Phase 4: User Story 2 — SSO Login (Priority: P2)

**Goal**: Enterprise users entering a work email are redirected to their IdP on Sign In click

**Independent Test**: Enter a work email and click Sign In → `POST /auth/sso/lookup` called → if `sso_enabled: true`, browser redirects to `redirect_url`. Enter a personal email → lookup returns `sso_enabled: false` → email/password auth proceeds. Point `NEXT_PUBLIC_API_URL` to unreachable host → lookup times out → email/password auth still proceeds (no block).

### Implementation for User Story 2

- [x] T009 [US2] Update the Sign In submit handler in `frontend-2/app/login/page.tsx` to: (1) set a new `checkingSso` loading state; (2) call `ssoLookup(email)` from `api.ts`; (3) if `sso_enabled: true`, do `window.location.href = result.redirect_url` and return; (4) if `sso_enabled: false` or the call throws, proceed to call `loginWithRememberMe(email, password, false)` (rememberMe wired in T011). Replace the direct `login()` call with `loginWithRememberMe(email, password, false)` as the fallthrough path. Keep existing error handling.

**Checkpoint**: US1 and US2 are both independently functional. SSO detection intercepts work-email sign-in attempts; personal emails fall through to password auth; lookup failures are transparent to the user.

---

## Phase 5: User Story 3 — Email/Password Enhanced UI (Priority: P3)

**Goal**: Show/hide toggle on password field, "Remember me" checkbox, "Forgot password?" stub link, and `/forgot-password` placeholder page

**Independent Test**: (a) Click eye icon on password field → password text revealed; click again → re-masked. (b) Check "Remember me" and sign in → `loginWithRememberMe()` called with `rememberMe: true`. (c) Click "Forgot password?" → navigates to `/forgot-password` → placeholder message shown, no API call made.

### Implementation for User Story 3

- [x] T010 [US3] Add show/hide password toggle to the password `<input>` in `frontend-2/app/login/page.tsx`: add `showPassword` boolean state (default false); set input `type={showPassword ? "text" : "password"}`; wrap input in a relative `<div>`; render `<button type="button">` absolutely positioned inside right edge containing `<Eye>` or `<EyeOff>` from `lucide-react` (16×16, `text-stone-400`); clicking toggles `showPassword`.

- [x] T011 [US3] Add "Remember me" and "Forgot password?" row to `frontend-2/app/login/page.tsx` between the password field and Sign In button: `<div className="flex items-center justify-between">` containing a `<label>` with `<input type="checkbox">` and "Remember me" text (`text-sm text-stone-700`) on the left, and a `<Link href="/forgot-password">` "Forgot password?" (`text-sm text-indigo-600`) on the right. Add `rememberMe` boolean state; pass it to `loginWithRememberMe(email, password, rememberMe)` in the submit handler (updating T009's call).

- [x] T012 [P] [US3] Create `frontend-2/app/forgot-password/page.tsx` — static placeholder page. Layout: `bg-stone-50` main, centred `max-w-sm` white `rounded-lg border border-stone-200 p-8` card, `text-xl font-semibold text-stone-800` heading "Reset your password", `text-sm text-stone-500 mt-2` body "Password reset is coming soon.", `text-sm text-indigo-600` link back to `/login` "← Back to sign in". No form, no API call.

**Checkpoint**: All three user stories are independently functional. The enhanced form is complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Design system documentation, audit, and quickstart validation

- [x] T013 Add `SocialButton` component pattern to `.interface-design/system.md` under the Components section — document the full-width border style, 48px height (`py-3`), inline SVG icon sizing (20×20), and the three provider variants

- [x] T014 [P] Run `/interface-design:audit` on `frontend-2/app/login/page.tsx`, `frontend-2/app/auth/callback/[provider]/page.tsx`, and `frontend-2/app/forgot-password/page.tsx` — fix any spacing, shadow, rounding, or colour violations found against `.interface-design/system.md`

- [x] T015 [P] Manually trace each test path from `specs/003-social-sso-login/quickstart.md` against the implemented routes and confirm: social callback mock works, SSO fallthrough works, remember me state is passed, forgot-password stub renders

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T002–T005)
- **US2 (Phase 4)**: Depends on US1 (T008 must exist — SSO logic added to same page)
- **US3 (Phase 5)**: Depends on US2 (T009 must exist — remember me updates T009's call)
- **Polish (Phase N)**: Depends on all user story phases complete

### Within Phase Dependencies

- T002 → T003, T004, T005 (types must exist before functions)
- T006 → T008 (SocialButton must exist before login page uses it)
- T007 independent (callback page has no local imports)
- T009 depends on T008 (modifying the page T008 creates)
- T010 depends on T008 (adding to the page T008 creates)
- T011 depends on T009, T010 (replaces loginWithRememberMe call added in T009, adds to form from T010)
- T012 independent (separate file)
- T013 depends on T006 (documents the pattern T006 implements)
- T014 depends on T008–T012 (audits completed UI)

### Parallel Opportunities

Within Phase 2 (sequential — same file):
- T002 → T003 → T004 → T005 (sequential)

Within Phase 3 (parallel available):
- T006 and T007 can run in parallel (different files, no interdependency)
- T008 must wait for T006

Within Phase 5:
- T012 can run in parallel with T010 and T011 (different file)

Within Phase N:
- T014 and T015 can run in parallel (different concerns)

```bash
# Phase 3 parallel launch:
Task: "Create SocialButton component in frontend-2/app/components/ui/social-button.tsx"  # T006
Task: "Create OAuth callback page at frontend-2/app/auth/callback/[provider]/page.tsx"   # T007
# Then T008 after T006 completes

# Phase 5 parallel launch:
Task: "Add show/hide toggle to frontend-2/app/login/page.tsx"        # T010
Task: "Create forgot-password stub at frontend-2/app/forgot-password/page.tsx"  # T012
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T005)
3. Complete Phase 3: User Story 1 (T006–T008)
4. **STOP and VALIDATE**: Confirm social login buttons navigate correctly; callback page handles token and errors; email/password still works
5. Ship MVP — social login is live

### Incremental Delivery

1. T001 → T002–T005 → T006–T008 → **US1 done** (social login)
2. T009 → **US2 done** (SSO detection on submit)
3. T010 → T011 → T012 → **US3 done** (enhanced email form + forgot-password stub)
4. T013 → T014 → T015 → **Polish done**

### Total Tasks: 15

| Phase | Tasks | Count |
|-------|-------|-------|
| Setup | T001 | 1 |
| Foundational | T002–T005 | 4 |
| US1 — Social Login | T006–T008 | 3 |
| US2 — SSO Login | T009 | 1 |
| US3 — Enhanced UI | T010–T012 | 3 |
| Polish | T013–T015 | 3 |

---

## Notes

- `[P]` tasks = different files, no in-phase dependencies
- `[USn]` label maps each task to its user story for traceability
- T006 and T007 are the only two truly parallel tasks in US1 — launch together
- T012 (forgot-password page) can launch in parallel with T010/T011
- Design system compliance is enforced in T014 — do not skip
- All api.ts tasks (T002–T005) touch the same file: do NOT parallelize them
