# Implementation Plan: Observability Upgrade (Sentry + Langfuse)

**Branch**: `024-sentry-langfuse` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-sentry-langfuse/spec.md`

## Summary

Replace Logfire instrumentation with Sentry (APM: errors, performance, slow queries, Celery) and Langfuse (LLM observability: prompt/completion tracing, token/cost tracking). Logfire logging calls (`logfire.info`, `logfire.exception`) are replaced with standard Python `logging`. No frontend changes, no schema changes.

## Technical Context

**Language/Version**: Python 3.11 (backend only)
**Primary Dependencies**: FastAPI, Celery, SQLAlchemy, sentry-sdk (new), langfuse (new)
**Storage**: N/A — no schema changes
**Testing**: pytest
**Target Platform**: Linux server (Docker)
**Project Type**: Web service (backend modification)
**Performance Goals**: < 5ms p99 latency overhead from instrumentation
**Constraints**: All monitoring best-effort; failures never impact user flows
**Scale/Scope**: 1 new file (core/logging.py), 4 files to modify (main.py, worker.py, ai_agent.py, email.py), 1 file to remove logfire dep (pyproject.toml), config + docker-compose updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes |
| API Contract | No | N/A | No endpoint changes |
| Auth/Security | Yes | PASS | Sentry DSN and Langfuse keys stored as env vars; no secrets in code |
| Env Config | Yes | PASS | SENTRY_DSN, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST documented in quickstart.md |
| Scope Boundary | Yes | PASS | Backend-only; replace existing instrumentation, no new features |
| E2E Testing | No | N/A | No user-facing flow changes |
| Repository Pattern | No | N/A | No data access changes |
| CLI/Typer | No | N/A | No CLI changes |
| Provider Abstraction | No | N/A | Sentry and Langfuse are infrastructure, not business-logic providers |
| Cost Awareness | Yes | PASS | Both services have free tiers; Langfuse Cloud free tier: 50k observations/mo |
| Migration Safety | No | N/A | Logfire is being removed, not retained behind a toggle — it's infrastructure, not a business provider |
| DB Migration | No | N/A | No schema changes |
| shadcn/ui Components | No | N/A | No frontend changes |

## Project Structure

### Documentation (this feature)

```text
specs/024-sentry-langfuse/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   ├── config.py              # Replace LOGFIRE_TOKEN with SENTRY_DSN, LANGFUSE_* vars
│   │   └── logging.py             # NEW: centralized get_logger() with console handler + Sentry auto-capture
│   ├── main.py                    # Replace logfire.configure/instrument with sentry_sdk.init
│   ├── worker.py                  # Replace logfire.configure/instrument with sentry_sdk.init; use get_logger()
│   └── services/
│       ├── ai_agent.py            # Replace logfire.instrument_openai + logfire.span with Langfuse observe()
│       └── email.py               # Replace logfire calls with get_logger()
├── pyproject.toml                 # Remove logfire, add sentry-sdk + langfuse
docker-compose.yml                 # Replace LOGFIRE_TOKEN with SENTRY_DSN + LANGFUSE_* env vars
```

**Structure Decision**: Backend-only. One new file (`core/logging.py`) centralizes logger configuration following the user's existing pattern from prior projects. All other changes are modifications to existing files.

## Complexity Tracking

> No constitution violations. All gates pass.
