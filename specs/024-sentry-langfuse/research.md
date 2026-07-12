# Research: Observability Upgrade (Sentry + Langfuse)

## Decision 1: Sentry SDK Integration Pattern

**Decision**: Use `sentry_sdk.init()` with FastAPI, SQLAlchemy, Celery, and httpx integrations auto-enabled.

**Rationale**: Sentry's Python SDK auto-discovers installed frameworks. A single `sentry_sdk.init(dsn=..., traces_sample_rate=1.0)` in `main.py` and `worker.py` replaces all of Logfire's `instrument_*()` calls. Sentry automatically captures:
- FastAPI request/response traces with timing
- SQLAlchemy query spans (with slow query detection via `_experiments={"record_sql_params": True}`)
- Celery task spans and errors
- httpx outbound HTTP call spans

**Alternatives considered**:
- OpenTelemetry direct: More flexible but requires manual exporter setup, more boilerplate. Sentry SDK wraps OTEL internally.
- Datadog: More expensive, overkill for current scale.
- Keep Logfire for APM: Logfire's dashboards are less mature than Sentry for error triage and performance analysis.

## Decision 2: Langfuse Integration Pattern

**Decision**: Use `langfuse.openai.OpenAI` drop-in wrapper to replace the standard OpenAI client, plus `@observe()` decorator for the `summarize_transcript` function.

**Rationale**: Langfuse provides a drop-in replacement for the OpenAI client (`from langfuse.openai import OpenAI`) that automatically traces all chat completion calls with prompt, completion, tokens, cost, and latency. The `@observe()` decorator wraps the parent function to create a trace context. This replaces both `logfire.instrument_openai()` and `logfire.span()` with zero change to the business logic.

**Alternatives considered**:
- Langfuse `generation()` manual API: More control but requires manual start/end calls around every LLM invocation. Drop-in wrapper is simpler and less error-prone.
- Helicone: Proxy-based (route API calls through their endpoint). Adds latency and a network dependency. Langfuse SDK is local.
- LangSmith: LangChain ecosystem lock-in. We don't use LangChain.

## Decision 3: Logfire Replacement Strategy

**Decision**: Remove Logfire entirely. Replace `logfire.info/warning/exception` calls with Python's standard `logging` module.

**Rationale**: With Sentry handling APM/errors and Langfuse handling LLM traces, Logfire adds no unique value. The `logfire.info()` calls are structured logs that map 1:1 to `logger.info()`. Removing Logfire simplifies the dependency tree (logfire pulls in opentelemetry, protobuf, etc.) and eliminates the "which dashboard?" confusion.

**Alternatives considered**:
- Keep Logfire for structured logging only: Adds complexity for marginal benefit. Python's logging with structlog or standard formatting is sufficient.
- Replace with structlog: Adds another dependency. Standard logging is fine for current needs.

## Decision 4: Sentry Environment Configuration

**Decision**: Use `traces_sample_rate=1.0` (100% sampling) initially. Set `environment` from a new `ENVIRONMENT` env var (default: `"production"`).

**Rationale**: At current scale (< 100 meetings/day), 100% sampling is within Sentry's free tier (50k transactions/mo). The environment tag separates local dev from production in the Sentry dashboard.

## Decision 5: Langfuse Hosting

**Decision**: Use Langfuse Cloud (hosted) via `LANGFUSE_HOST` env var.

**Rationale**: Self-hosting Langfuse requires a separate Postgres instance and Docker container — unnecessary overhead for the current team size. Langfuse Cloud has a free tier (50k observations/month) that covers current usage. `LANGFUSE_HOST` defaults to Langfuse Cloud (`https://cloud.langfuse.com`) but can be pointed to a self-hosted instance later.
