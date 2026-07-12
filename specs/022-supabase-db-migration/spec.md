# Feature Specification: Migrate VPS Postgres to Supabase Managed Postgres

**Feature Branch**: `022-supabase-db-migration`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "Let's use the supabase postgres as the database. Let's take the dump of the current db and restore on supabase and then reconnect the supabase with the application. The application is running in prod mode and the migration should be seamless. After the migration is successful, remove the postgres container from the vps profile of docker-compose and only run postgres when the docker compose profile is 'local'."

## User Scenarios & Testing

### User Story 1 - Zero-downtime database migration (Priority: P1)

As the system operator, I need to migrate the production PostgreSQL database from a self-hosted Docker container on the VPS to Supabase managed Postgres without any data loss and with minimal service disruption.

**Why this priority**: This is the core deliverable. Without a successful data migration, nothing else matters. The production application is live and serving users — data integrity is non-negotiable.

**Independent Test**: Can be fully tested by dumping the VPS database, restoring it to Supabase, and verifying all tables, rows, and relationships match exactly. Delivers the actual migration outcome.

**Acceptance Scenarios**:

1. **Given** the production database is running in a Docker container on the VPS, **When** a full database dump is taken and restored to Supabase Postgres, **Then** all tables, rows, indexes, sequences, and constraints are present and identical on Supabase.
2. **Given** the dump has been restored to Supabase, **When** a row count comparison is run across all tables, **Then** every table has the same number of rows on both the VPS and Supabase instances.
3. **Given** the migration is in progress, **When** the application switches its DATABASE_URL to Supabase, **Then** all existing application features (login, upload, transcription, summary, PDF export) continue to work without errors.

---

### User Story 2 - Application reconnection to Supabase Postgres (Priority: P1)

As the system operator, I need to update the application configuration so that both the API server and Celery worker connect to the Supabase Postgres instance instead of the local Docker container.

**Why this priority**: Equal to the migration itself — the app must be reconfigured to use the new database for the migration to have any effect.

**Independent Test**: Can be tested by updating the DATABASE_URL environment variable in docker-compose and restarting the services, then verifying API responses return real data from Supabase.

**Acceptance Scenarios**:

1. **Given** the Supabase Postgres connection string is configured, **When** the API service starts, **Then** it connects successfully and serves requests using the Supabase database.
2. **Given** the Supabase Postgres connection string is configured, **When** the Celery worker starts, **Then** it connects successfully and can read/write meeting and transcription data.
3. **Given** Alembic migrations have been applied to Supabase, **When** the migration state is checked against the Supabase database, **Then** it reports the latest migration revision as HEAD.

---

### User Story 3 - Remove Postgres container from VPS deployment (Priority: P2)

As the system operator, I need the Postgres Docker container to only run when using the "local" Docker Compose profile, so it is no longer part of the VPS production deployment.

**Why this priority**: This is a cleanup step that should only happen after the migration is verified successful. It reduces VPS resource usage and eliminates the exposed-port security risk.

**Independent Test**: Can be tested by running docker compose with and without profiles and verifying Postgres container presence matches expectations.

**Acceptance Scenarios**:

1. **Given** the migration to Supabase is complete and verified, **When** docker compose is run with the "vps" profile, **Then** no Postgres container is started.
2. **Given** a developer needs a local database, **When** docker compose is run with the "local" profile, **Then** the Postgres container starts as before on port 5433.
3. **Given** the Postgres container is removed from VPS deployment, **When** VPS resource usage is checked, **Then** memory and CPU usage decrease by the amount previously consumed by Postgres.

---

### Edge Cases

- What happens if the Supabase connection is temporarily unavailable? The application should surface connection errors through standard error handling — no special retry logic needed beyond what the database driver already provides.
- What happens if schema differences exist between the VPS dump and Supabase? Alembic migrations are the source of truth — run migrations on Supabase after restore to ensure schema consistency.
- What happens if the VPS database receives writes during the migration window? A brief maintenance window (application paused) should be used to prevent data drift between dump and cutover.
- What happens if Supabase Postgres uses a different version than the VPS container (Postgres 16)? Supabase currently runs Postgres 15. The pg_dump format is forward-compatible; verify no Postgres 16-specific features are in use (none identified in the current schema).

## Clarifications

### Session 2026-03-14

- Q: Supabase connection mode — direct (port 5432) vs Supavisor pooler (port 6543)? → A: Direct connection (port 5432). API and worker are long-running processes with their own connection pools; direct is simpler and avoids pooler quirks.

## Requirements

### Functional Requirements

- **FR-001**: Operator MUST be able to create a complete backup dump of the VPS Postgres database including all schemas, tables, data, indexes, sequences, and constraints.
- **FR-002**: Operator MUST be able to restore the dump into the Supabase Postgres instance with all data intact.
- **FR-003**: Operator MUST validate data integrity post-restore by comparing row counts across all tables between source and destination.
- **FR-004**: System MUST accept a Supabase Postgres connection string via the existing DATABASE_URL environment variable for both the API service and Celery worker.
- **FR-005**: System MUST ensure database migrations are at the latest revision on the Supabase database after restore.
- **FR-006**: System MUST modify docker-compose.yml so the Postgres (`db`) service only starts under the "local" profile, not the default or "vps" profile.
- **FR-007**: System MUST update service dependency configuration so that services do not require the `db` service when running without the "local" profile.
- **FR-008**: System MUST preserve the VPS Postgres container and its data volume as a rollback option until the migration is confirmed stable.

### Assumptions

- The Supabase project is already provisioned and the operator has the Postgres connection string (host, port, user, password, database).
- Connection uses Supabase direct mode (port 5432), not the Supavisor pooler — the API and worker are long-running processes with their own asyncpg connection pools, so direct connections are simpler and avoid pooler-specific quirks.
- The current database size is small enough to dump and restore within a reasonable maintenance window (under 30 minutes).
- SSL connections to Supabase Postgres are required (standard for Supabase); the DATABASE_URL must include `sslmode=require`.
- The operator has SSH access to the VPS to run dump/restore commands.
- VPS UFW firewall allows all outbound traffic by default (`Default: allow (outgoing)`), so no firewall rule changes are needed for the application to reach Supabase Postgres.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All production data is present on Supabase with zero row count discrepancies across all tables.
- **SC-002**: Application downtime during cutover is under 10 minutes.
- **SC-003**: All existing features (user auth, file upload, transcription, summary generation, PDF export) work correctly against the Supabase database within the first hour after migration.
- **SC-004**: VPS memory usage decreases after removing the Postgres container from the production stack.
- **SC-005**: Local development workflow continues to work with the local Postgres container unchanged.
