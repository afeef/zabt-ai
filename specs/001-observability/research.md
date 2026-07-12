# Research: Monitoring and Observability

**Feature**: 001-observability
**Date**: 2026-03-05
**Status**: Complete

---

## Decision 1: Unified Observability Platform

**Decision**: Logfire (by Pydantic) as the single platform for API traces, worker task traces, and LLM call traces.

**Rationale**: Logfire has native auto-instrumentation for FastAPI, SQLAlchemy, Celery, httpx, and OpenAI — all in the same dashboard. The user explicitly chose this over a split Logfire + Langfuse approach (see spec Clarifications section). It is already present in `pyproject.toml` at `>=4.25.0`.

**Alternatives considered**: Langfuse (LLM-only, no API/worker traces), Sentry (error tracking only, no LLM traces), OpenTelemetry + Grafana (powerful but heavy self-hosting burden).

---

## Decision 2: LLM Instrumentation — `instrument_openai` (not `instrument_pydantic_ai`)

**Decision**: Use `logfire.instrument_openai(client)` to capture LLM call traces.

**Rationale**: The codebase uses the OpenAI SDK client directly in `backend/app/services/ai_agent.py` (`from openai import OpenAI`). Despite `pydantic-ai` appearing in `pyproject.toml`, it is **not imported or used anywhere** in the codebase. `logfire.instrument_openai()` is built into core logfire (no extra required) and captures model name, prompt, completion, token counts (input/output), and latency as LLM-specific OTel attributes.

**Alternatives considered**: `logfire.instrument_pydantic_ai()` — not applicable (pydantic-ai unused); `logfire.instrument_httpx()` — would capture the outgoing HTTP call to OpenRouter but without LLM-specific attributes (no token counts, no prompt content).

---

## Decision 3: Celery Instrumentation — `logfire[celery]` extra + dual-side call

**Decision**: Add `logfire[celery]` extra and call `logfire.instrument_celery()` in **both** `main.py` (producer side) and `worker.py` (consumer side).

**Rationale**: The Celery OTel instrumentation (`opentelemetry-instrumentation-celery`) automatically propagates W3C `traceparent` headers through Celery task headers. When called on both sides, the worker task appears as a linked trace to the originating API request. Auto-instrumentation creates task spans via signals (`task_prerun`, `task_postrun`, `task_failure`) — no manual span wrappers needed inside task bodies.

**Key finding**: The `logfire.instrument_celery()` docstring explicitly states: *"For distributed tracing to work correctly, this must be called in both the worker processes and the application that enqueues tasks."*

---

## Decision 4: FastAPI Instrumentation — `logfire[fastapi]` extra

**Decision**: `logfire.instrument_fastapi(app)` called after `app = FastAPI(...)` and before `add_middleware()`.

**Rationale**: Auto-captures HTTP method, route, status code, URL, duration, validation errors, and unhandled exceptions on every request. The `send_to_logfire="if-token-present"` parameter is used so the app starts without error when `LOGFIRE_TOKEN` is not set (local dev without Logfire account).

---

## Decision 5: Database Instrumentation — `logfire[sqlalchemy]`

**Decision**: `logfire.instrument_sqlalchemy(engine=engine)` using the existing sync SQLModel engine from `backend/app/db/engine.py`.

**Rationale**: The app uses a SQLModel sync engine (`create_engine(DATABASE_URL.replace("+asyncpg", ""))`) for all DDL and a session-per-request pattern via BaseService. SQLAlchemy instrumentation captures `db.statement` (SQL text), table name, and duration as child spans within the parent request span. `instrument_asyncpg()` is not needed since raw asyncpg is not used.

---

## Decision 6: Outbound HTTP Instrumentation — `logfire[httpx]`

**Decision**: `logfire.instrument_httpx()` called globally at startup (instruments all httpx client instances).

**Rationale**: The app uses httpx for outbound calls (`"httpx>=0.28.1"` in dependencies). Global instrumentation covers all httpx clients, including any created by third-party libraries. Captures method, URL, status code, duration as child spans.

---

## Decision 7: logfire.configure() Placement and env var

**Decision**: Call `logfire.configure(service_name=..., send_to_logfire="if-token-present")` as the very first statement in both `main.py` and `worker.py`, before any instrumentation calls or app creation. Token is read automatically from `LOGFIRE_TOKEN` env var.

**Rationale**: Logfire must be configured before any instrumentation calls. `send_to_logfire="if-token-present"` is safe for development — Logfire is a no-op when the token is absent. `service_name` differentiates traces from the API vs. the worker in the Logfire UI.

**New env vars**:
- `LOGFIRE_TOKEN` — required for production; get from logfire.pydantic.dev → Settings → Write Tokens
- `LOGFIRE_SERVICE_NAME` — optional override; code sets it explicitly via `service_name=`

---

## Decision 8: Provider Abstraction Deviation (Justified)

**Decision**: Logfire is instrumented directly without an abstract `ObservabilityProvider` interface (deviates from Constitution Principle IX).

**Rationale**: Observability instrumentation is cross-cutting infrastructure, not a swappable business logic provider like transcription or LLM summarization. Logfire's auto-instrumentation hooks directly into FastAPI's ASGI layer, SQLAlchemy's event system, and Celery's signals — an abstract interface would prevent these from working. If the observability platform is ever replaced, it would be a configuration change (remove `logfire`, add `opentelemetry-exporter-*`), not a provider implementation change. This is the same justified deviation applied in the `001-product-analytics` feature for PostHog.

---

## Key Integration Points in Existing Code

| File | Integration Point | Change Required |
|------|-------------------|-----------------|
| `backend/pyproject.toml` | Add logfire extras | `logfire[fastapi,sqlalchemy,httpx,celery]` |
| `backend/app/main.py` | App startup | `logfire.configure()`, `instrument_fastapi()`, `instrument_sqlalchemy()`, `instrument_httpx()`, `instrument_celery()` |
| `backend/app/worker.py` | Worker startup | `logfire.configure()`, `instrument_celery()` |
| `backend/app/services/ai_agent.py` | OpenAI client creation | `logfire.instrument_openai(_client)` after `_client = OpenAI(...)` |
| `backend/app/core/config.py` | Settings | Add `LOGFIRE_TOKEN: str = ""` |
| `.env` | Local dev | Add `LOGFIRE_TOKEN=<your-token>` |
| `docker-compose.yml` | Container env | Add `LOGFIRE_TOKEN` to `api`, `worker`, `worker-gpu` services |
