---
description: "Task list for 001-logto-register"
---

# Tasks: Logto-Based User Registration

**Input**: Design documents from `/specs/001-logto-register/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/auth.md ✅ quickstart.md ✅

**Tests**: E2E tests in Playwright/Python are REQUIRED per constitution (feature has user-facing flows).

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths are included in every task description

---

## Phase 1: Setup

**Purpose**: Environment configuration — these values must exist before any implementation compiles.

- [x] T001 Add `NEXT_PUBLIC_LOGTO_ENDPOINT=http://localhost:3001` and `NEXT_PUBLIC_LOGTO_APP_ID=<your-logto-app-id>` to `frontend-2/.env.local` — these public env vars are already in `docker-compose.yml` for the container but are absent from `.env.local` for local dev; `socialLoginUrl()` will read them
- [x] T002 Add `LOGTO_M2M_APP_ID: str = "change_me_in_env"` and `LOGTO_M2M_APP_SECRET: str = "change_me_in_env"` to the `Settings` class in `backend/app/core/config.py` — required by the new `POST /auth/register` endpoint for Management API authentication

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Create the backend auth router that US1 and US2 both depend on. No user story work
can begin until this phase is complete.

⚠️ **CRITICAL**: US1 (email/password) and US2 (social callback) both need the auth router registered.

- [x] T003 Create `backend/app/api/v1/endpoints/auth.py` with a FastAPI `APIRouter` and implement `POST /register` — the endpoint must: (1) fetch an M2M access token from `{settings.LOGTO_ENDPOINT}/oidc/token` using `grant_type=client_credentials`, `client_id=settings.LOGTO_M2M_APP_ID`, `client_secret=settings.LOGTO_M2M_APP_SECRET`, `scope=all`, `resource=https://default.logto.app/api`; (2) create the user in Logto via `POST {settings.LOGTO_ENDPOINT}/api/users` using that M2M token with body `{primaryEmail: email, password: password, name: full_name}`; (3) exchange for a user JWT via `POST {settings.LOGTO_ENDPOINT}/oidc/token` using `grant_type=password`, `client_id=settings.LOGTO_APP_ID`, `username=email`, `password=password`, `scope=openid email profile`, `resource=settings.LOGTO_AUDIENCE`; (4) return `{access_token, token_type: "bearer"}`. Error handling: 400 with `"Email already registered"` if Logto returns a 422/conflict; 503 with `"Identity service unavailable"` for any httpx/network error. Use `httpx.AsyncClient` (already a dependency).

- [x] T004 Register the auth router in `backend/app/api/api.py` — add `from app.api.v1.endpoints import auth` and `api_router.include_router(auth.router, prefix="/auth", tags=["auth"])` so `POST /api/v1/auth/register` is live

**Checkpoint**: `POST /api/v1/auth/register` returns `{access_token, token_type}` for a fresh email and 400 for a duplicate. Foundation ready — user story phases can begin.

---

## Phase 3: User Story 1 — Email/Password Registration (Priority: P1) 🎯 MVP

**Goal**: Submitting the registration form creates a Logto identity, signs the user in, and redirects to `/`

**Independent Test**: Visit `/register` → fill Full Name, fresh email, password ≥ 8 chars → click Sign up → land on `/` authenticated. Repeat with same email → "Email already registered" error shown inline. Stop Logto container → submit form → see "service unavailable" message (not "email already registered").

### E2E Tests for User Story 1 (required per constitution)

- [x] T005 [P] [US1] Write Playwright/Python E2E tests for email/password registration in `tests/e2e/test_registration.py` — cover 3 scenarios from `specs/001-logto-register/quickstart.md`: (1) happy path: new email → Sign up → lands on `/`; (2) duplicate email → sees "already registered" message; (3) service unavailable → sees error that is NOT "email already registered". Use `playwright.sync_api` with `page.goto`, `page.fill`, `page.click`, `page.wait_for_url`, `page.locator`. Assume frontend at `http://localhost:3000`, Logto at `http://localhost:3001`.

### Implementation for User Story 1

- [x] T006 [US1] Update `register()` in `frontend-2/app/lib/api.ts` — change endpoint from `"/users/"` to `"/auth/register"`, change return type from `Promise<User>` to `Promise<void>`, remove `return res.data`, add `setToken(res.data.access_token)` after the post call (token is stored before returning so the caller can redirect immediately)

- [x] T007 [US1] Update the form submit handler in `frontend-2/app/register/page.tsx` — change `router.push("/login")` to `router.push("/")` (since `register()` now stores the token internally and user is immediately authenticated); update the catch block to distinguish HTTP errors: check `error.response?.status === 400` to show `"This email is already registered. Try signing in instead."`, and show `"Registration is temporarily unavailable. Please try again."` for any other error (503 or network failure). Remove the hardcoded single-message error string.

**Checkpoint**: US1 independently functional. Fresh email → `/` signed in. Duplicate → correct error. Service down → correct error. Social buttons unaffected.

---

## Phase 4: User Story 2 — Social Provider Registration (Priority: P2)

**Goal**: Social sign-up buttons navigate directly to the correct OAuth provider via Logto's OIDC authorize URL; the callback exchanges the code for a JWT and signs the user in

**Independent Test**: Visit `/register` → click "Sign up with Google" → browser goes directly to Google OAuth (not to Logto's hosted page first) → complete auth → land on `/` signed in. The same flow works for Microsoft and Apple.

### E2E Tests for User Story 2 (required per constitution)

- [x] T008 [P] [US2] Add social registration E2E tests (Scenarios 4, 5, 6 from `specs/001-logto-register/quickstart.md`) to `tests/e2e/test_registration.py` — test that clicking each social button (`Sign up with Google`, `Sign up with Microsoft`, `Sign up with Apple`) navigates to the correct provider domain (google.com, microsoft.com, apple.com). Use `page.expect_navigation()` or check `page.url` after click to confirm the redirect target without completing the full OAuth flow (which requires live provider credentials).

### Implementation for User Story 2

- [x] T009 [US2] Add `GET /social/callback` endpoint to `backend/app/api/v1/endpoints/auth.py` — accepts query params `code: str` and `redirect_uri: str`; uses `httpx.AsyncClient` to call `POST {settings.LOGTO_ENDPOINT}/oidc/token` with `grant_type=authorization_code`, `client_id=settings.LOGTO_APP_ID`, `client_secret=settings.LOGTO_APP_SECRET`, `code=code`, `redirect_uri=redirect_uri`; returns `{access_token, token_type: "bearer"}`. Error handling: 400 for invalid/expired code, 503 for Logto unreachable.

- [x] T010 [US2] Update `socialLoginUrl()` in `frontend-2/app/lib/api.ts` — replace the broken backend-proxy URL with a direct Logto OIDC authorize URL. Add two new constants at the top of the file: `const LOGTO_ENDPOINT = process.env.NEXT_PUBLIC_LOGTO_ENDPOINT || "http://localhost:3001"` and `const LOGTO_APP_ID = process.env.NEXT_PUBLIC_LOGTO_APP_ID || ""`. Add a connector ID mapping: `google→"google-universal"`, `microsoft→"azure-ad"`, `apple→"apple-universal"`. Build and return the URL: `${LOGTO_ENDPOINT}/oidc/auth?client_id=${LOGTO_APP_ID}&redirect_uri=${redirectUri}&response_type=code&scope=openid%20email%20profile&state=${state}&direct_sign_in=social%3A${connectorId}`. Keep the existing function signature `socialLoginUrl(provider: OAuthProvider, state: string): string` unchanged so all callers (register/page.tsx and login/page.tsx) continue to work without modification.

- [x] T011 [US2] Update `frontend-2/app/auth/callback/[provider]/page.tsx` — replace the current `?token=` / `?error=` URL reading with `?code=` / `?error=` handling. When `code` is present: call `GET /api/v1/auth/social/callback?code={code}&redirect_uri={encodeURIComponent(callbackUrl)}` via `apiClient`, call `setToken(res.data.access_token)`, then `router.replace("/")`. When `error` is present: show an error message with a "Return to sign in" link to `/login`. When neither: redirect to `/login`. Remove the old `email_conflict` special-case (that error came from the old backend flow, not the new Logto OIDC flow). The `callbackUrl` passed as `redirect_uri` must exactly match the value used in `socialLoginUrl()` — i.e., `${process.env.NEXT_PUBLIC_FRONTEND_URL}/auth/callback/${provider}`.

**Checkpoint**: Both user stories independently functional. Email/password registration → `/` signed in. Social buttons → correct OAuth provider → callback → `/` signed in.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Dead code removal and final validation

- [x] T012 Delete `backend/app/api/login.py` — dead code: the router is not mounted in `api.py`, and the endpoint references `security.verify_password` and `user.hashed_password` which do not exist in the current codebase. Deleting prevents future confusion.

- [x] T013 Delete `backend/app/api/users.py` — dead code: not mounted in `api.py`; references `security.get_password_hash` (doesn't exist) and attempts to create a `User` without `logto_id` (required non-nullable field). Superseded by `POST /auth/register`.

- [x] T014 [P] Manually trace all 6 test scenarios from `specs/001-logto-register/quickstart.md` against the implemented routes — confirm: (1) fresh email → `/` signed in; (2) duplicate email → correct error; (3) Logto down → service unavailable error; (4) Google button → Google OAuth page; (5) Microsoft button → Microsoft OAuth page; (6) Apple button → Apple OAuth page.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately (T001, T002 are independent)
- **Foundational (Phase 2)**: Depends on T002 (config must have M2M fields before auth.py can read them) — BLOCKS both user stories
- **US1 (Phase 3)**: Depends on Foundational (T003+T004 must be complete — POST /auth/register must exist)
- **US2 (Phase 4)**: Depends on Foundational (T003+T004) for T009; depends on US1 completion for T010+T011 (same api.ts file)
- **Polish (Phase N)**: Depends on both user story phases complete

### Within Phase Dependencies

- T001 and T002 are independent — can run in parallel
- T003 must complete before T004 (can't register a router that doesn't exist yet)
- T005 (E2E test skeleton) can be written in parallel with T006+T007 (different files)
- T006 must complete before T007 (T007 changes the page that calls `register()` which T006 updates)
- T008 (E2E social tests) can run in parallel with T009+T010+T011 (different concerns)
- T009 must complete before T011 (T011 calls the endpoint T009 creates)
- T010 must complete before T011 (T011's callback URL must match the redirect_uri T010 constructs)
- T012 and T013 are independent of each other — can run in parallel

### Parallel Opportunities

```bash
# Phase 1 — run together:
Task: "T001 — Add NEXT_PUBLIC_LOGTO_* vars to frontend-2/.env.local"
Task: "T002 — Add LOGTO_M2M_* to backend/app/core/config.py"

# Phase 3 — E2E skeleton and implementation can start in parallel:
Task: "T005 — Write E2E tests for email/password registration in tests/e2e/test_registration.py"
Task: "T006 — Update register() in frontend-2/app/lib/api.ts"

# Phase N — parallel cleanup:
Task: "T012 — Delete backend/app/api/login.py"
Task: "T013 — Delete backend/app/api/users.py"
Task: "T014 — Trace quickstart.md scenarios"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001, T002 in parallel)
2. Complete Phase 2: Foundational (T003 → T004)
3. Complete Phase 3: User Story 1 (T005 ∥ T006 → T007)
4. **STOP and VALIDATE**: Fresh email → `/` signed in; duplicate → correct error
5. Ship MVP — email/password registration is live

### Incremental Delivery

1. T001+T002 → T003 → T004 → **backend ready**
2. T006 → T007 → **US1 done** (email/password registration fixed)
3. T009 → T010 → T011 → **US2 done** (social sign-up buttons fixed)
4. T012 → T013 → T014 → **Polish done**

### Total Tasks: 14

| Phase | Tasks | Count |
|-------|-------|-------|
| Setup | T001–T002 | 2 |
| Foundational | T003–T004 | 2 |
| US1 — Email Registration | T005–T007 | 3 |
| US2 — Social Registration | T008–T011 | 4 |
| Polish | T012–T014 | 3 |

---

## Notes

- `[P]` tasks = different files or concerns, no in-phase dependencies
- `[USn]` label maps each task to its user story for traceability
- T005 and T008 (E2E tests) should be written before implementation where possible — the constitution requires E2E tests; writing them first reveals any ambiguity in the acceptance scenarios
- The `socialLoginUrl()` function change (T010) affects both `register/page.tsx` AND `login/page.tsx` — both use social buttons. This is intentional: fixing the social URL helper fixes social login everywhere at once.
- The ROPC grant (`grant_type=password`) in T003 requires it to be enabled in Logto Console — see `specs/001-logto-register/quickstart.md` Step 1a for configuration instructions. If ROPC is unavailable for the configured app type, the backend can fall back to redirecting to `/login` (FR-003 would be partially violated, but registration itself would still work).
- Connector IDs in T010 (`google-universal`, `azure-ad`, `apple-universal`) are Logto defaults — verify against actual Logto Console configuration before finalizing
