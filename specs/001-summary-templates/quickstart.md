# Quickstart: Summary Templates

**Feature**: `001-summary-templates`
**Date**: 2026-03-04

---

## New Environment Variables

No new environment variables are required. This feature uses the existing `OPENAI_API_KEY`, `OPENAI_MODEL`, and database connection settings.

---

## Database Migration

This feature requires a database schema migration to:
1. Create the `summarytemplate` table
2. Add `default_template_id` to the `user` table
3. Add `template_id` and `template_name` to the `meeting` table

Run migrations with Alembic:

```bash
cd backend
uv run alembic revision --autogenerate -m "add summary templates"
uv run alembic upgrade head
```

---

## Built-in Template Seeding

Built-in templates are automatically seeded at application startup via the lifespan hook in `main.py`. The seed is idempotent — templates are only inserted if they do not already exist.

To manually trigger seeding (e.g., after a fresh DB setup):

```bash
cd backend
uv run python -c "from app.services.template_seed import seed_built_in_templates; seed_built_in_templates()"
```

---

## Running the Application

No changes to existing startup commands:

```bash
# Backend
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend-2 && npm run dev

# Celery worker (required for async summarization)
cd backend && uv run celery -A app.worker.celery_app worker --loglevel=info
```

---

## Running E2E Tests

```bash
cd tests/e2e
uv run pytest test_summary_templates.py -v
```

Ensure the full stack (backend, frontend, Celery worker) is running before executing E2E tests.

---

## New API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/templates/` | List all templates (built-in + user's custom) |
| POST | `/api/v1/templates/` | Create a custom template |
| GET | `/api/v1/templates/{id}` | Get template details |
| PUT | `/api/v1/templates/{id}` | Update a custom template |
| DELETE | `/api/v1/templates/{id}` | Delete a custom template |
| POST | `/api/v1/templates/{id}/set-default` | Set personal default template |
| POST | `/api/v1/meetings/{id}/summarize` | Re-summarize with specified template |

---

## New Frontend Routes

| Path | Description |
|------|-------------|
| `/templates` | Templates management page (list, create, edit, delete, set default) |

The summary tab on `/meetings/[id]` gains a template picker dropdown (no new route).
