# Data Model: Observability Upgrade (Sentry + Langfuse)

## Overview

This feature introduces **no database tables or schema changes**. All observability data is sent to external services (Sentry, Langfuse) via their SDKs.

## Entities

No new entities. The feature modifies infrastructure instrumentation only.

## Logfire Removal Inventory

The following Logfire touchpoints are removed and replaced:

| File | Logfire Usage | Replacement |
|------|--------------|-------------|
| `app/main.py` | `logfire.configure()`, `instrument_fastapi/sqlalchemy/httpx/celery` | `sentry_sdk.init()` with auto-integrations |
| `app/worker.py` | `logfire.configure()`, `instrument_celery`, 16x `logfire.info/warning/exception` | `sentry_sdk.init()`, standard `logging` |
| `app/services/ai_agent.py` | `logfire.instrument_openai()`, `logfire.span()` | `langfuse.openai.OpenAI` wrapper, `@observe()` decorator |
| `app/services/email.py` | 6x `logfire.info/exception` | Standard `logging` |
| `app/core/config.py` | `LOGFIRE_TOKEN` setting | `SENTRY_DSN`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` |
| `pyproject.toml` | `logfire[fastapi,sqlalchemy,httpx,celery]` dependency | `sentry-sdk[fastapi,celery,sqlalchemy]`, `langfuse` |
| `docker-compose.yml` | `LOGFIRE_TOKEN` in api/worker/worker-gpu | `SENTRY_DSN`, `LANGFUSE_*` in api/worker/worker-gpu |
