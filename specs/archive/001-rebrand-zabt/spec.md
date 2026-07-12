# Feature Specification: Zabt Rebranding & Logto Removal

**Feature Branch**: `001-rebrand-zabt`
**Created**: 2026-02-22
**Status**: Draft
**Input**: User description: "Remove the logto and pareto mentions from the project and rename both with zabt. Also, remove all logto services, environment variables and rest of the things from the project. We are not using them anymore"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project Renamed to Zabt (Priority: P1)

Any developer or end user who opens the application, reads the repository README, or inspects the codebase should see "Zabt" everywhere that previously said "Pareto", "Pareto AI", or "Meetily". The name change must be consistent across all user-visible surfaces: app titles, package names, Docker service names, database names, and in-code comments/strings.

**Why this priority**: This is the highest-impact change. Every other piece of work builds on a clean, correctly-named project baseline. Inconsistent naming creates confusion for contributors, deployment pipelines, and end users.

**Independent Test**: A developer cloning the repository should find zero occurrences of "pareto" or "Pareto" in any source file, configuration file, or documentation — and the application title displayed in the browser tab should read "Zabt".

**Acceptance Scenarios**:

1. **Given** the project is running, **When** a user opens the application in a browser, **Then** the page title, logo text, and any branding copy reads "Zabt" — not "Pareto", "Pareto AI", or "Meetily".
2. **Given** a developer inspects `package.json` in any project directory, **When** they read the `name` field, **Then** it contains "zabt" (not "pareto" or "frontend" or "backend" with no context).
3. **Given** the project's Docker Compose file, **When** a developer reads service names and image tags, **Then** no service is named after or references "pareto".

---

### User Story 2 - All Logto Artifacts Completely Removed (Priority: P1)

Every remaining artifact of the Logto identity-provider integration — environment variable names, configuration keys, import statements, commented-out code, Docker volumes, SQL statements, and dead code paths — must be deleted from the repository. The project must have no references to Logto anywhere, including hidden configuration files, CI/CD scripts, or spec documentation.

**Why this priority**: Equal to P1 with rebranding. Leftover Logto references break developer onboarding ("what is this?"), cause false positive search results, and could lead to accidental use of removed functionality.

**Independent Test**: A full-text search of the repository for the word "logto" (case-insensitive) returns no results in any file tracked by version control (excluding git history).

**Acceptance Scenarios**:

1. **Given** the project repository, **When** a developer runs a case-insensitive search for "logto" across all tracked source and configuration files, **Then** zero matches are returned.
2. **Given** the `.env` file at the project root, **When** a developer reads it, **Then** no variable begins with `LOGTO_` and no value references a Logto endpoint.
3. **Given** all spec documents, checklists, and planning artifacts under `specs/`, **When** a developer reads them, **Then** references to Logto describe its removal (historical) rather than active usage.

---

### User Story 3 - Database and Infrastructure Renamed (Priority: P2)

The local development database, Docker volumes, and any infrastructure configuration that references "pareto_ai" as a database name or project identifier must be renamed to "zabt".

**Why this priority**: Lower-risk than P1 because it mainly affects local development setup. However, mismatched database names between `.env` configuration and actual Docker volumes causes broken local environments.

**Independent Test**: Running `docker-compose up` from a clean state creates a database named "zabt" and all services start without error.

**Acceptance Scenarios**:

1. **Given** the `docker-compose.yml` and root `.env` files, **When** a developer reads the `POSTGRES_DB` variable, **Then** its value is "zabt" (not "pareto_ai").
2. **Given** the application connects to the database on startup, **When** the backend initializes, **Then** it connects to the "zabt" database without manual reconfiguration.

---

## Functional Requirements

- **FR-001**: All user-visible text instances of "Pareto", "Pareto AI", and "Meetily" MUST be replaced with "Zabt".
- **FR-002**: The `name` field in all `package.json` files MUST be updated to reflect "zabt".
- **FR-003**: The `PROJECT_NAME` value in the backend configuration MUST be "Zabt".
- **FR-004**: The Docker Compose `POSTGRES_DB` environment variable and corresponding backend `DATABASE_URL` MUST reference the database name "zabt".
- **FR-005**: All environment variable names beginning with `LOGTO_` or `NEXT_PUBLIC_LOGTO_` MUST be deleted from the codebase, `.env` files, configuration modules, and Docker Compose files.
- **FR-006**: All import statements, function calls, or references to any `logto` package, SDK, or library MUST be removed from all source files.
- **FR-007**: All specification and planning documents under `specs/` that describe Logto as an active component (not historical removal context) MUST be updated or removed.
- **FR-008**: All Docker volume names, service names, and container labels that reference "pareto" MUST be renamed to "zabt".

---

### Key Entities

- **Project Identity**: The brand name, appearing in UI, configs, package metadata, and documentation.
- **Database Name**: The Postgres database name used by both Docker Compose and the backend connection string.
- **Logto Artifacts**: Any remaining file, string, variable, or comment that references the Logto identity provider.

---

## Success Criteria

- A case-insensitive full-text search for "logto" across all version-controlled files returns **zero** results.
- A case-insensitive full-text search for "pareto" across all version-controlled files returns **zero** results (excluding git history and this spec's historical context).
- The application renders "Zabt" as the brand name on every user-facing page on first load.
- `docker-compose up` succeeds from a clean environment without any manual renaming steps.
- All environment variables in `.env` and `docker-compose.yml` use "zabt" identifiers wherever a project name is required.

---

## Assumptions

- The rename is a pure find-and-replace brand exercise; no new features are introduced.
- "Meetily" (found in some UI copy) is also a legacy name to be replaced by "Zabt".
- The Postgres database volume will need to be destroyed and recreated (`docker-compose down -v`) to pick up the new database name — this is acceptable for local development.
- Logto references inside git history are out of scope; only tracked working-tree files require cleaning.
- Spec documents that document the *removal* of Logto (like `specs/001-migrate-supabase/`) are kept for historical context but must not imply Logto is still active.

---

## Constraints & Non-Goals

- Git history rewriting is explicitly out of scope.
- No functional changes to the application's behavior — this is purely a rename/cleanup operation.
- Third-party packages whose internal source code mentions "logto" (e.g., `.venv/site-packages/logto`) are out of scope; they will be removed naturally by the dependency cleanup already done in `001-migrate-supabase`.
