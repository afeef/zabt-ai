# Implementation Plan: Supabase DB Migration

**Branch**: `022-supabase-db-migration` | **Date**: 2026-03-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/022-supabase-db-migration/spec.md`

## Summary

Migrate the production PostgreSQL database from a self-hosted Docker container on the VPS to Supabase managed Postgres. The migration involves: (1) dumping the VPS database, (2) restoring to Supabase, (3) updating the application configuration to point at Supabase, (4) restricting the Postgres Docker service to the "local" profile only. No schema changes, no new code — this is a configuration and operations task.

## Technical Context

**Language/Version**: Python 3.11 (backend), YAML (Docker Compose)
**Primary Dependencies**: FastAPI, SQLModel, Celery, asyncpg, Alembic
**Storage**: PostgreSQL (migrating from self-hosted → Supabase managed); MinIO/S3 (unchanged)
**Testing**: Manual verification (row count comparison, feature smoke test)
**Target Platform**: Linux VPS (Contabo 6c/12GB), Supabase Cloud
**Project Type**: Web service (backend API + worker)
**Performance Goals**: N/A — no performance-impacting changes; connection latency to Supabase should be comparable
**Constraints**: <10 minute cutover downtime; zero data loss; SSL required for Supabase connection
**Scale/Scope**: Small database, single VPS, 2 services (API + worker)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes |
| API Contract | No | N/A | No endpoint changes |
| Auth/Security | Yes | PASS | No auth changes; DATABASE_URL is env var; SSL enforced |
| Env Config | Yes | PASS | DATABASE_URL already exists; `sslmode=require` added to connection string value (not a new env var) |
| Scope Boundary | Yes | PASS | Only docker-compose.yml and .env changes; no new code |
| E2E Testing | No | N/A | No user-facing flow changes |
| Repository Pattern | No | N/A | No data access changes |
| CLI/Typer | No | N/A | No CLI involved |
| Provider Abstraction | No | N/A | No external API integration changes |
| Cost Awareness | No | N/A | Supabase free tier; no paid API calls |
| Migration Safety | Yes | PASS | VPS Postgres container + data volume preserved as rollback; rollback = revert DATABASE_URL |
| DB Migration | Yes | PASS | Alembic `upgrade head` run on Supabase after restore; no new migration files needed |
| shadcn/ui Components | No | N/A | No UI changes |

## Project Structure

### Documentation (this feature)

```text
specs/022-supabase-db-migration/
├── plan.md              # This file
├── research.md          # Phase 0: migration approach research
├── quickstart.md        # Phase 1: env var documentation
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

Note: `data-model.md` and `contracts/` are skipped — this feature introduces no new data models or API contracts.

### Source Code (repository root)

```text
docker-compose.yml       # Modified: db service gets profiles: ["local"]
                         # Modified: api/worker depends_on conditional
```

**Structure Decision**: No new source files. This feature only modifies `docker-compose.yml` and the `.env` file on the VPS. All other changes are operational (SSH commands on the VPS).

## Step-by-Step Migration Instructions

### Phase 1: Preparation (before maintenance window)

**1.1 — Get the Supabase connection string**

From the Supabase dashboard → Project Settings → Database, copy the **direct connection** string (port 5432). It will look like:

```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

For asyncpg, modify it to:

```
postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
```

**1.2 — Test connectivity from the VPS**

SSH into the VPS and verify the connection works:

```bash
# Install psql if not available
sudo apt-get install -y postgresql-client

# Test connection (use the direct connection string WITHOUT +asyncpg)
psql "postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" -c "SELECT 1;"
```

If this fails, check:
- UFW outbound is allowed (already confirmed: `Default: allow (outgoing)`)
- Supabase network restrictions (Project Settings → Database → Network Restrictions)

### Phase 2: Database Dump & Restore (maintenance window)

**2.1 — Enter maintenance mode**

Stop the API and worker to prevent writes during migration:

```bash
cd /path/to/zabt-ai
docker compose stop api worker
```

**2.2 — Dump the VPS database**

```bash
# Dump from the running Postgres container
docker compose exec db pg_dump -U app -d zabt \
  --no-owner --no-privileges --clean --if-exists \
  -F custom -f /tmp/zabt-dump.backup

# Copy dump out of the container
docker compose cp db:/tmp/zabt-dump.backup ./zabt-dump.backup
```

Flags explained:
- `--no-owner --no-privileges`: Supabase has different roles; skip ownership/grants
- `--clean --if-exists`: Drop and recreate objects on restore (safe for empty target)
- `-F custom`: Binary format for faster restore with `pg_restore`

**2.3 — Restore to Supabase**

```bash
# Restore using pg_restore (installed with postgresql-client)
pg_restore \
  --no-owner --no-privileges \
  --dbname="postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" \
  ./zabt-dump.backup
```

If you see errors about Supabase system schemas (e.g., `auth`, `storage`, `extensions`), they are safe to ignore — those are managed by Supabase.

**2.4 — Run Alembic migrations on Supabase**

```bash
# From the backend directory, set DATABASE_URL temporarily
DATABASE_URL="postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" \
  docker compose run --rm api alembic current

# If not at HEAD, run upgrade
DATABASE_URL="postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" \
  docker compose run --rm api alembic upgrade head
```

**2.5 — Validate data integrity**

```bash
# Compare row counts between VPS and Supabase
# On VPS (local):
docker compose exec db psql -U app -d zabt -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY relname;
"

# On Supabase (remote):
psql "postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY relname;
"
```

Verify every table has matching row counts.

### Phase 3: Cutover

**3.1 — Update .env on the VPS**

Edit the `.env` file on the VPS:

```bash
# Replace the DATABASE_URL line
DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
```

**3.2 — Restart services**

```bash
docker compose up -d api worker
```

**3.3 — Smoke test**

Verify all features work:
1. Open the app in a browser — confirm meetings load
2. Upload a test file — confirm it processes
3. Check a meeting detail page — confirm transcript and summary render
4. Download a PDF — confirm export works

### Phase 4: Docker Compose Cleanup (after verification)

**4.1 — Modify docker-compose.yml**

Add `profiles: ["local"]` to the `db` service so it only starts in local development:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: always
    profiles: ["local"]          # ← ADD THIS LINE
    environment:
      # ... unchanged
    ports:
      - "5433:5432"
    volumes:
      # ... unchanged
```

**4.2 — Update depends_on for api and worker services**

Remove `db` from `depends_on` in the `api` and `worker` services (they now connect to Supabase, not the local container). Keep `depends_on` for `redis` only:

For `api` service:
```yaml
    depends_on:
      - redis
      # Remove: - db
```

For `worker` service (vps profile):
```yaml
    depends_on:
      - redis
      # Remove: - db
```

The `worker-gpu` service (local profile) should keep `depends_on: [db, redis]` since it runs locally.

**4.3 — Deploy the docker-compose change**

```bash
# On the VPS
docker compose down
docker compose up -d
```

Verify no Postgres container starts:
```bash
docker compose ps | grep db
# Should return nothing
```

**4.4 — Preserve rollback capability**

Do NOT remove the `postgres_data` Docker volume. It contains the original database and can be used to rollback:

```bash
# Verify volume still exists
docker volume ls | grep postgres_data
```

To rollback: revert `.env` DATABASE_URL to `postgresql+asyncpg://app:app@db:5432/zabt`, remove `profiles: ["local"]` from db service, restore `depends_on`, and `docker compose up -d`.

## Complexity Tracking

No constitution violations. This feature is a pure configuration/operations change with no new code.
