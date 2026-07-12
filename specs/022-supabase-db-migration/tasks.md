# Tasks: Supabase DB Migration

**Input**: Design documents from `/specs/022-supabase-db-migration/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Not requested — this is an operations/configuration feature with manual verification.

**Organization**: Tasks are grouped by user story. US1 and US2 are co-dependent (dump/restore + reconnect happen in sequence). US3 is independent cleanup after verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths and commands in descriptions

---

## Phase 1: Preparation

**Purpose**: Verify prerequisites and establish connectivity before entering the maintenance window.

- [ ] T001 Install postgresql-client on VPS: `sudo apt-get install -y postgresql-client`
- [ ] T002 Obtain Supabase direct connection string from Supabase dashboard (Settings → Database → Connection string → URI, port 5432)
- [ ] T003 Test connectivity from VPS to Supabase: `psql "postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" -c "SELECT 1;"`
- [ ] T004 Construct the asyncpg DATABASE_URL by prepending `+asyncpg` to the scheme and appending `?sslmode=require`: `postgresql+asyncpg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require`

**Checkpoint**: Supabase is reachable from VPS. Ready to enter maintenance window.

---

## Phase 2: User Story 1 — Zero-downtime database migration (Priority: P1) 🎯 MVP

**Goal**: Dump the VPS Postgres database and restore it to Supabase with zero data loss.

**Independent Test**: Compare row counts across all tables between VPS and Supabase — every table must match exactly.

### Implementation for User Story 1

- [ ] T005 [US1] Stop API and worker services to prevent writes: `docker compose stop api worker`
- [ ] T006 [US1] Dump VPS database from container: `docker compose exec db pg_dump -U app -d zabt --no-owner --no-privileges --clean --if-exists -F custom -f /tmp/zabt-dump.backup`
- [ ] T007 [US1] Copy dump file out of the container: `docker compose cp db:/tmp/zabt-dump.backup ./zabt-dump.backup`
- [ ] T008 [US1] Restore dump to Supabase: `pg_restore --no-owner --no-privileges --dbname="postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" ./zabt-dump.backup` (ignore errors about Supabase system schemas like `auth`, `storage`, `extensions`)
- [ ] T009 [US1] Run Alembic migrations on Supabase to ensure schema is at HEAD: `DATABASE_URL="postgresql+asyncpg://..." docker compose run --rm api alembic upgrade head`
- [ ] T010 [US1] Verify Alembic is at HEAD on Supabase: `DATABASE_URL="postgresql+asyncpg://..." docker compose run --rm api alembic current`
- [ ] T011 [US1] Validate data integrity — run row count query on VPS: `docker compose exec db psql -U app -d zabt -c "SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;"`
- [ ] T012 [US1] Validate data integrity — run row count query on Supabase: `psql "postgresql://..." -c "SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;"`
- [ ] T013 [US1] Compare row counts from T011 and T012 — every table must have identical counts

**Checkpoint**: All production data is on Supabase with verified integrity. Services are still stopped.

---

## Phase 3: User Story 2 — Application reconnection (Priority: P1)

**Goal**: Reconnect the API and worker to Supabase and verify all features work.

**Independent Test**: All existing features (login, upload, transcription, summary, PDF export) work against Supabase.

**Depends on**: Phase 2 (US1) complete — data must be on Supabase before reconnecting.

### Implementation for User Story 2

- [ ] T014 [US2] Update DATABASE_URL in `.env` on the VPS to the Supabase asyncpg connection string
- [ ] T015 [US2] Restart API and worker services: `docker compose up -d api worker`
- [ ] T016 [US2] Smoke test — open the app in browser and confirm meetings list loads
- [ ] T017 [US2] Smoke test — open a meeting detail page and confirm transcript and summary render
- [ ] T018 [US2] Smoke test — download a PDF export and confirm it generates correctly
- [ ] T019 [US2] Smoke test — upload a test audio file and confirm processing starts (if RunPod is configured)

**Checkpoint**: Application is running against Supabase. All features verified. Maintenance window ends.

---

## Phase 4: User Story 3 — Remove Postgres from VPS deployment (Priority: P2)

**Goal**: Restrict the Postgres Docker service to the "local" profile only so it no longer runs on the VPS.

**Independent Test**: `docker compose --profile vps up` starts no Postgres container; `docker compose --profile local up` does.

**Depends on**: Phase 3 (US2) complete and verified stable (ideally wait 24-48 hours).

### Implementation for User Story 3

- [x] T020 [US3] Add `profiles: ["local"]` to the `db` service in `docker-compose.yml`
- [x] T021 [US3] Remove `- db` from `depends_on` in the `api` service in `docker-compose.yml` (keep `- redis`)
- [x] T022 [US3] Remove `- db` from `depends_on` in the `worker` service (vps profile) in `docker-compose.yml` (keep `- redis`)
- [x] T023 [US3] Verify `worker-gpu` service (local profile) still has `depends_on: [db, redis]` in `docker-compose.yml`
- [ ] T024 [US3] Deploy updated docker-compose.yml to VPS and restart: `docker compose down && docker compose up -d`
- [ ] T025 [US3] Verify no Postgres container is running: `docker compose ps | grep db` should return nothing
- [ ] T026 [US3] Verify `postgres_data` Docker volume still exists for rollback: `docker volume ls | grep postgres_data`

**Checkpoint**: Postgres container removed from VPS deployment. Volume preserved for rollback.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and documentation.

- [ ] T027 Commit docker-compose.yml changes to the `022-supabase-db-migration` branch
- [x] T028 Update ROADMAP.md to mark feature #6 (DB migration to managed Postgres) as complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Preparation)**: No dependencies — can start immediately
- **Phase 2 (US1 — Dump/Restore)**: Depends on Phase 1 — ENTERS MAINTENANCE WINDOW
- **Phase 3 (US2 — Reconnect)**: Depends on Phase 2 — EXITS MAINTENANCE WINDOW after smoke tests pass
- **Phase 4 (US3 — Docker Cleanup)**: Depends on Phase 3 verified stable (wait 24-48h recommended)
- **Phase 5 (Polish)**: Depends on Phase 4

### User Story Dependencies

- **US1 (P1)**: Must complete before US2 (data must be on Supabase before reconnecting)
- **US2 (P1)**: Must complete before US3 (app must be verified working before removing container)
- **US3 (P2)**: Independent of US1/US2 in terms of code, but operationally gated on US2 stability

### Parallel Opportunities

- T011 and T012 can run in parallel (row count queries on different databases)
- T016, T017, T018, T019 can run in parallel (independent smoke tests)
- T020, T021, T022, T023 can be done as a single docker-compose.yml edit session

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Preparation
2. Complete Phase 2: US1 — Dump & Restore (maintenance window begins)
3. Complete Phase 3: US2 — Reconnect & Verify (maintenance window ends)
4. **STOP and VALIDATE**: Run app for 24-48 hours against Supabase
5. If stable → proceed to Phase 4 (US3)
6. If issues → rollback: revert DATABASE_URL, restart with local Postgres

### Rollback Procedure

1. Revert `DATABASE_URL` in `.env` to `postgresql+asyncpg://app:app@db:5432/zabt`
2. Remove `profiles: ["local"]` from `db` service (if Phase 4 was done)
3. Restore `- db` to `depends_on` in api/worker (if Phase 4 was done)
4. `docker compose up -d`
5. `postgres_data` volume contains the original database — no data loss

---

## Notes

- This feature has NO code changes — only configuration and operational steps
- The maintenance window (Phase 2 + Phase 3) should take under 10 minutes for a small database
- Phase 4 should be deferred until the app has been running against Supabase for at least 24 hours
- The `postgres_data` volume is intentionally NOT deleted — it's the rollback safety net
