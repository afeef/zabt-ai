# Tasks: Zabt Rebranding & Logto Removal

**Input**: `specs/001-rebrand-zabt/` — research.md, data-model.md, quickstart.md, plan.md, spec.md
**Branch**: `001-rebrand-zabt`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (independent files)
- **[Story]**: User story this task belongs to

---

## Phase 1: Setup

**Purpose**: Establish a clean working state before renaming begins.

- [x] T001 Run `docker-compose down -v` to destroy old `pareto_ai` volume before any config changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update all shared infrastructure config files that other stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Update `POSTGRES_DB` from `pareto_ai` → `zabt` in `.env` (project root)
- [x] T003 Update `POSTGRES_DB` default value and any `pareto_ai` comments in `docker-compose.yml`
- [x] T004 Update `POSTGRES_DB` default and `PROJECT_NAME` from `"Pareto AI"` → `"Zabt"` in `backend/app/core/config.py`

**Checkpoint**: Infrastructure config is consistent — US1, US2, US3 can proceed in parallel.

---

## Phase 3: User Story 1 — Project Renamed to Zabt (Priority: P1) 🎯 MVP

**Goal**: Zero occurrences of "Pareto", "Pareto AI", or "Meetily" in any tracked file.

**Independent Test**: `grep -ri "pareto\|meetily" . --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --include="*.yml" --include="*.md"` returns no output.

- [x] T005 [P] [US1] Rename `name` field from `"backend"` → `"zabt-backend"` in `backend/pyproject.toml`
- [x] T006 [P] [US1] Rename `name` field from `"frontend-2"` → `"zabt-web"` in `frontend-2/package.json`
- [x] T007 [P] [US1] Replace all "Meetily" text with "Zabt" in `frontend-2/app/login/page.tsx`
- [x] T008 [P] [US1] Replace all "Meetily" text with "Zabt" in `frontend-2/app/register/page.tsx`
- [x] T009 [P] [US1] Update "Meetily Constitution" title → "Zabt Constitution" in `.specify/memory/constitution.md`
- [x] T010 [P] [US1] Update any "Pareto AI" project name mention in `CLAUDE.md` → "Zabt"
- [x] T011 [US1] If `README.md` exists at project root: replace all "Pareto", "Pareto AI", "Meetily" with "Zabt"

**Checkpoint**: A full-text search for "pareto" and "meetily" returns zero results.

---

## Phase 4: User Story 2 — All Logto Artifacts Removed (Priority: P1)

**Goal**: Zero occurrences of "logto" (case-insensitive) in any tracked source/config/doc file.

**Independent Test**: `grep -ri "logto" . --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.sql" --include="*.md" | grep -v ".git/" | grep -v ".venv/"` returns no output.

- [x] T012 [P] [US2] Audit and remove all active-tense Logto references from `specs/001-migrate-supabase/spec.md` (update to past-tense "was removed")
- [x] T013 [P] [US2] Audit and remove any "Logto" or "logto" references from `specs/001-migrate-supabase/plan.md` that describe it as currently active
- [x] T014 [P] [US2] Audit and remove any "Logto" or "logto" references from `specs/001-migrate-supabase/research.md` that describe it as currently active
- [x] T015 [P] [US2] Run a project-wide grep for "logto" across all tracked `.py`, `.ts`, `.tsx`, `.json`, `.yml`, `.yaml`, `.sql`, `.md`, `.env` files (excluding `.venv/` and `.git/`); fix any remaining occurrences not already covered

**Checkpoint**: The grep command from the Independent Test above returns no output.

---

## Phase 5: User Story 3 — Database & Infrastructure Renamed (Priority: P2)

**Goal**: `docker-compose up` from a clean state creates a `zabt` database successfully.

**Independent Test**: After `docker-compose up`, run `docker exec <db-container> psql -U app -l` and confirm a database named `zabt` exists (not `pareto_ai`).

- [x] T016 [US3] Verify `DATABASE_URL` in `docker-compose.yml` derives correctly from `POSTGRES_DB=zabt` (no hardcoded `pareto_ai` string in the connection string template)
- [x] T017 [US3] Run `docker-compose up` and confirm the `zabt` database is created and the `api` service starts without errors

**Checkpoint**: Full stack boots cleanly with the `zabt` database.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T018 Run the full verification grep from `quickstart.md` for both "pareto" and "logto" — confirm zero matches
- [x] T019 Run the full verification grep from `quickstart.md` for "meetily" — confirm zero matches
- [x] T020 Update `specs/001-rebrand-zabt/tasks.md` marking all tasks `[x]` complete after implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately
- **Phase 2 (Foundational)**: After Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1)**: After Phase 2 complete — T005–T010 fully parallelizable
- **Phase 4 (US2)**: After Phase 2 complete — T012–T014 fully parallelizable; T015 runs last
- **Phase 5 (US3)**: After Phase 2 + T016 verification
- **Phase 6 (Polish)**: After all user story phases complete

### Parallel Opportunities

```
After Phase 2 completes:
  → T005, T006, T007, T008, T009, T010 (all different files, no deps) — launch in parallel
  → T012, T013, T014 (different spec docs)                            — launch in parallel
```

---

## Implementation Strategy

### MVP (US1 + US2 only)

1. Phase 1: Teardown
2. Phase 2: Config rename
3. Phase 3: Brand rename (UI + package names)
4. Phase 4: Logto sweep
5. **VALIDATE**: Run grep assertions — zero matches for "pareto", "meetily", "logto"

### Full Delivery

After MVP validated, add Phase 5 (DB restart) and Phase 6 (polish sweep).

---

## Notes

- T015 is the safety net — run it last in US2 to catch anything T012–T014 missed
- T017 is a runtime verification, not a code change — it confirms the infrastructure rename is effective
- `.venv/site-packages/logto` is explicitly excluded from the grep scope (out of scope per spec assumptions)
