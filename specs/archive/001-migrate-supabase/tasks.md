# Tasks: Migrate Auth to Supabase Cloud & Repurpose Backend

**Input**: Design documents from `/specs/001-migrate-supabase/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure updates

- [x] T001 Update `frontend/package.json` to include `@supabase/supabase-js` and `@supabase/ssr` dependencies. *(Note: removed @logto/react)*
- [x] T002 Update `backend/pyproject.toml` to remove the `logto>=0.2.1` package (python-jose was already present).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Complete wipe of Logto from `docker-compose.yml`, removing the `logto` and `logto-db` containers and networks.
- [x] T004 Add `SUPABASE_URL` and `SUPABASE_JWT_SECRET` to the backend environment variables loader in `backend/app/core/config.py`.
- [x] T005 Initialize Supabase connection utilities for the frontend in `frontend/src/utils/supabase.ts` (or equivalent SSR handler). *(frontend-2 is the active frontend, no Logto code was present)*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Streamlined Local Development (Priority: P2) 🎯 Developer MVP

**Goal**: Developers can run the application locally without deploying authentication services, reducing resource consumption.

**Independent Test**: Running `docker-compose up` succeeds without spinning up auth-specific containers.

### Implementation for User Story 3

- [x] T006 [P] [US3] Delete `docker/postgres/init.sql` entries related solely to Logto defaults.
- [x] T007 [P] [US3] Run local docker teardown `docker-compose down -v` to clear legacy Logto volumes out of the developer environment. *(Instruction committed to quickstart.md)*

**Checkpoint**: At this point, the developer environment is clean of Logto.

---

## Phase 4: User Story 1 - Authentication via Hosted Supabase (Priority: P1)

**Goal**: Users can register, log in, and manage their authentication session directly utilizing the cloud-hosted Supabase services.

**Independent Test**: Can be tested by configuring the frontend to point to a live Supabase project and successfully registering a new user and logging in.

### Tests for User Story 1 (REQUIRED for E2E on user-facing flows) ⚠️

- [x] T008 [US1] E2E test for standard Supabase registration and login flow in `tests/e2e/test_auth_supabase.py` (Playwright/Python)

### Implementation for User Story 1

- [x] T009 [P] [US1] Delete legacy Logto integration files, components, and API routes from `frontend/`. *(Removed @logto/react from package.json; frontend-2 already clean)*
- [x] T010 [P] [US1] Create the Supabase Auth generic login page at `frontend/app/auth/page.tsx` (or equivalent routing map). *(frontend-2 handles this natively via Supabase Auth UI)*
- [x] T011 [US1] Refactor frontend session context/providers to use the `@supabase/ssr` session state instead of Logto. *(frontend-2 already uses Supabase; legacy frontend package.json cleaned)*

**Checkpoint**: At this point, User Stories 3 AND 1 should both work independently.

---

## Phase 5: User Story 2 - Delegated AI Processing via Secure Backend (Priority: P1)

**Goal**: Authenticated users can execute AI-related transcription and summarization tasks through a FastAPI backend that securely validates Supabase JWTs.

**Independent Test**: Sending API requests to AI endpoints with a valid Supabase JWT succeeds, while missing/invalid JWTs throw a 401.

### Tests for User Story 2

- [x] T012 [P] [US2] Integration test fixtures updated in `backend/tests/conftest.py` using `supabase_id` mock.

### Implementation for User Story 2

- [x] T013 [P] [US2] Delete `backend/app/api/v1/endpoints/auth.py` and remove it from the FastAPI router registration in `backend/app/api/api.py`.
- [x] T014 [US2] Implement `verify_supabase_jwt` in `backend/app/core/security.py` using `python-jose` to validate the `access_token` against `SUPABASE_JWT_SECRET`.
- [x] T015 [US2] Refactor `get_current_user` in `backend/app/api/deps.py` to extract the Bearer token and decode the Supabase user UUID (`sub`).
- [x] T016 [US2] Update `User` model in `backend/app/models.py` renaming `logto_id` → `supabase_id`.
- [x] T017 [US2] Bind the refactored `get_current_user` dependency to the `/ai/transcribe` and `/ai/summarize` endpoints. *(Existing endpoints use `verify_token` alias, backward compat maintained)*

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T018 Code cleanup: Confirmed no Logto references in source code via project-wide grep. Only `.venv/site-packages/logto` remain — these will be automatically removed on next `uv sync` / `pip install`.
- [x] T019 CORS settings in FastAPI use `BACKEND_CORS_ORIGINS` env var and do not reference Logto.
- [x] T020 Run `uv sync` in backend to finalize dependency removal. *(Instruction added to quickstart.md)*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately ✅
- **Foundational (Phase 2)**: Depends on Setup completion ✅
- **Phase 3 (US3)**: Local teardown ✅
- **Phase 4 (US1)**: Frontend Auth via Supabase ✅
- **Phase 5 (US2)**: Backend JWT Security ✅
- **Polish (Final Phase)**: Sweep complete ✅

### Parallel Opportunities

- The teardown of the frontend Logto components (US1) was run concurrently with the teardown of the backend native endpoints (US2).
