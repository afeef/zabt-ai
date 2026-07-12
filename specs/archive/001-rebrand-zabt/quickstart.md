# Quickstart: Zabt Rebranding

**Feature**: `001-rebrand-zabt`
**Date**: 2026-02-22

---

## Environment Variables

No new environment variables are introduced. The following existing variables must be updated to reflect the new project name:

### Root `.env` (docker-compose)

```bash
# Change this:
POSTGRES_DB=pareto_ai
# To this:
POSTGRES_DB=zabt
```

All other variables remain the same.

---

## Running After the Rename

Because the Postgres database name is changing, you must destroy the old volume before starting:

```bash
# 1. Stop containers and destroy the old pareto_ai volume
docker-compose down -v

# 2. Start fresh — Postgres will create the 'zabt' database
docker-compose up
```

> ⚠️ Running `docker-compose down -v` **destroys all local data**. This is expected for a development environment rename. Back up any data you need before running this.

---

## Verification

After startup, confirm the rename is fully applied by checking:

```bash
# No "pareto" references in tracked files
grep -ri "pareto" . --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.sql" --include="*.md" --include="*.env" 2>/dev/null | grep -v ".git/"

# No "logto" references in tracked files
grep -ri "logto" . --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.sql" --include="*.md" 2>/dev/null | grep -v ".git/" | grep -v ".venv/"
```

Both commands should return **no output** when the rename is complete.
