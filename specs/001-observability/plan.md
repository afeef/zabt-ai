# Implementation Plan: Monitoring and Observability

**Branch**: `001-observability` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-observability/spec.md`

---

## Summary

Add unified observability to the Zabt backend using Logfire (Pydantic) as the single platform. Every FastAPI request, Celery worker task (download → transcribe → summarize), and OpenAI LLM call will produce structured traces with child spans, visible in a single Logfire Cloud dashboard. Logfire is already in `pyproject.toml` — this feature adds extras, configuration, and instrumentation calls only. No database schema changes or new API endpoints are required.

---

## Technical Context

**Language/Version**: Python 3.11 (backend only — no frontend changes)
**Primary Dependencies**: FastAPI 0.129+, Celery 5.6+, SQLModel 0.0.37, OpenAI SDK 2.21+, Logfire 4.25.0 (already installed)
**Storage**: PostgreSQL via SQLModel (unchanged)
**Testing**: No automated tests (observability is validated via Logfire Live view — see quickstart.md)
**Target Platform**: Linux (Docker Compose local, Cloudflare tunnel for external access)
**Project Type**: Web service backend + async worker
**Performance Goals**: Instrumentation overhead < 5% on API response time (FR per spec SC-004)
**Constraints**: Fail-silent — `LOGFIRE_TOKEN` absent must not crash the app; `send_to_logfire="if-token-present"` handles this
**Scale/Scope**: Single developer; free tier Logfire Cloud; 7 files modified, 0 new files

---

## Constitution Check

| Gate | Applies | Status | Notes |
|------|---------|--------|-------|
| Design System | No UI changes | SKIP | Backend-only |
| API Contract | No new endpoints | SKIP | Pure instrumentation |
| Auth/Security | New env var `LOGFIRE_TOKEN` | PASS | Documented in quickstart.md; never hardcoded |
| Env Config | `LOGFIRE_TOKEN` introduced | PASS | Listed in quickstart.md; added to docker-compose.yml |
| Scope Boundary | Backend instrumentation only | PASS | No frontend, no new endpoints |
| E2E Testing | No user-facing flow | SKIP | Validation via Logfire Live view |
| Repository Pattern | No new data access | SKIP | No DB changes |
| CLI/Typer | No CLI changes | SKIP | |
| Provider Abstraction | Logfire is external service | **DEVIATION** | Justified — see Complexity Tracking |
| Cost Awareness | Logfire free tier | PASS | No paid API calls added |
| Migration Safety | No provider replacement | SKIP | |

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Provider Abstraction (Principle IX) — Logfire instrumented directly without abstract interface | Logfire auto-instrumentation hooks into FastAPI's ASGI layer, SQLAlchemy's event system, and Celery's signals. These hooks are framework-internal and cannot be called through an abstract interface. | An `ObservabilityProvider` abstraction would prevent auto-instrumentation from working; all spans would need to be created manually, defeating the purpose. Same justification as PostHog in `001-product-analytics`. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-observability/
├── plan.md         ← this file
├── research.md     ← Phase 0 output
├── quickstart.md   ← Phase 1 output
└── tasks.md        ← Phase 2 output (/speckit.tasks)
```

No contracts/ directory — this feature adds no new API endpoints.
No data-model.md — this feature adds no new database entities.

### Source Code Changes

```text
backend/
├── pyproject.toml                        # Add logfire extras
├── app/
│   ├── core/
│   │   └── config.py                     # Add LOGFIRE_TOKEN setting
│   ├── main.py                           # logfire.configure() + instrument_fastapi/sqlalchemy/httpx/celery/openai
│   ├── worker.py                         # logfire.configure() + instrument_celery()
│   └── services/
│       └── ai_agent.py                   # logfire.instrument_openai(_client)
.env                                      # Add LOGFIRE_TOKEN (local dev)
docker-compose.yml                        # Add LOGFIRE_TOKEN to api/worker/worker-gpu
```

---

## Implementation Details

### 1. pyproject.toml — Add Logfire Extras

```toml
# Change from:
"logfire>=4.25.0",
# To:
"logfire[fastapi,sqlalchemy,httpx,celery]>=4.25.0",
```

Note: `instrument_openai` is built into the logfire core package — no extra required.

---

### 2. config.py — Add LOGFIRE_TOKEN Setting

```python
# backend/app/core/config.py — add to Settings class:

# --- Logfire Observability ---
LOGFIRE_TOKEN: str = ""
```

---

### 3. main.py — Configure and Instrument

```python
# backend/app/main.py
import logfire
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.middleware.audit import AuditMiddleware
from app.db.engine import create_db_and_tables, engine

# 1. Configure Logfire FIRST — reads LOGFIRE_TOKEN from env automatically
logfire.configure(
    service_name="zabt-api",
    send_to_logfire="if-token-present",  # no-ops gracefully if token absent
)

# 2. Instrument outbound httpx globally (covers OpenAI SDK, boto3 presigned URLs, etc.)
logfire.instrument_httpx()

# 3. Instrument SQLAlchemy engine (covers all SQLModel queries)
logfire.instrument_sqlalchemy(engine=engine)

# 4. Instrument Celery on the producer side (so dispatch traces link to worker)
logfire.instrument_celery()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    from app.services.template_seed import seed_built_in_templates
    seed_built_in_templates()
    yield
    from app.services.analytics import shutdown as analytics_shutdown
    analytics_shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# 5. Instrument FastAPI — must be AFTER app = FastAPI(...)
logfire.instrument_fastapi(app)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)

from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Zabt API", "docs": "/docs"}
```

---

### 4. worker.py — Configure and Instrument Celery

Add at the top of `worker.py`, before the Celery app creation:

```python
import logfire

# Configure Logfire for the worker process
logfire.configure(
    service_name="zabt-worker",
    send_to_logfire="if-token-present",
)

# Instrument Celery on the consumer side — creates spans for each task execution
logfire.instrument_celery()
```

Context propagation: When `dispatch_pipeline()` is called within a traced FastAPI request, the Celery instrumentation automatically injects the W3C `traceparent` into task headers. The worker extracts it and creates linked/child spans. Both sides must call `instrument_celery()` for this to work.

---

### 5. ai_agent.py — Instrument OpenAI Client

```python
# backend/app/services/ai_agent.py
import logfire
from openai import OpenAI
from app.core.config import settings

_client = OpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)

# Instrument the OpenAI client — captures model, tokens, prompt/completion, latency
logfire.instrument_openai(_client)
```

This captures:
- `gen_ai.request.model` (e.g. `google/gemini-3.1-flash-lite-preview`)
- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`
- Full prompt and completion content (as span attributes)
- Request duration as span duration

---

### 6. .env — Add LOGFIRE_TOKEN

```env
# --- Logfire Observability ---
LOGFIRE_TOKEN=pylf_<your-token-here>
```

---

### 7. docker-compose.yml — Wire LOGFIRE_TOKEN

```yaml
services:
  api:
    environment:
      LOGFIRE_TOKEN: ${LOGFIRE_TOKEN}

  worker:
    environment:
      LOGFIRE_TOKEN: ${LOGFIRE_TOKEN}

  worker-gpu:
    environment:
      LOGFIRE_TOKEN: ${LOGFIRE_TOKEN}
```

---

## Trace Topology

```
HTTP Request (zabt-api)
└── GET /api/v1/meetings/upload [FastAPI span]
    ├── SELECT meeting... [SQLAlchemy span]
    └── dispatch_pipeline() [Celery producer span]

Celery Task Chain (zabt-worker) — linked via traceparent
├── stage_download [Celery task span]
│   └── GET s3://... [httpx span — MinIO presigned URL]
├── stage_transcribe [Celery task span]
│   └── (local Whisper — no HTTP calls)
└── stage_summarize [Celery task span]
    └── POST https://openrouter.ai/... [OpenAI span]
        ├── gen_ai.request.model: "google/gemini-3.1-flash-lite-preview"
        ├── gen_ai.usage.input_tokens: 4821
        └── gen_ai.usage.output_tokens: 412
```

---

## Implementation Strategy

**MVP (minimum to get value)**: Tasks T001–T005 — configure Logfire, add FastAPI and Celery instrumentation. API traces and worker task traces visible in Logfire Live view.

**Full value**: T006–T007 — OpenAI instrumentation added, LLM token counts visible in traces.

All tasks are sequential (no parallelism needed — small scope, single file modifications per task).
