# Tasks: Observability Upgrade (Sentry + Langfuse)

**Input**: Design documents from `/specs/024-sentry-langfuse/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Update dependencies and config

- [x] T001 Remove `logfire[fastapi,sqlalchemy,httpx,celery]` and add `sentry-sdk[fastapi,celery,sqlalchemy]` and `langfuse` to `backend/pyproject.toml`
- [x] T002 Replace `LOGFIRE_TOKEN` with `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` in `backend/app/core/config.py`

---

## Phase 2: Foundational (Logging Module)

**Purpose**: Create centralized logging module — MUST complete before user stories

**⚠️ CRITICAL**: All user story tasks depend on this module

- [x] T003 Create `backend/app/core/logging.py` — centralized `get_logger(name)` function following user's existing pattern: console handler with formatted output (`%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s`), log level based on environment (DEBUG for dev, WARNING for production), Sentry auto-captures ERROR+ via `sentry_sdk.init()` (no explicit handler needed). Also create `init_sentry()` helper that calls `sentry_sdk.init()` guarded by `if settings.SENTRY_DSN`.

**Checkpoint**: `get_logger()` and `init_sentry()` available for all modules

---

## Phase 3: User Story 1 — Error and Performance Monitoring (Priority: P1) 🎯 MVP

**Goal**: All errors, slow requests, and slow DB queries captured in Sentry dashboard

**Independent Test**: Deploy with `SENTRY_DSN` set, trigger an API request and a Celery task error, verify both appear in Sentry with full context

### Implementation for User Story 1

- [x] T004 [US1] Replace Logfire with Sentry in `backend/app/main.py` — remove `import logfire`, all `logfire.configure()` and `logfire.instrument_*()` calls; import and call `init_sentry()` from `app.core.logging`; keep `logfire.instrument_openai` removal for US2
- [x] T005 [US1] Replace Logfire with logging in `backend/app/worker.py` — remove `import logfire`, `logfire.configure()`, `logfire.instrument_celery()`; import `init_sentry` and `get_logger` from `app.core.logging`; call `init_sentry()` at module level; replace all `logfire.info/warning/exception()` with `logger.info/warning/exception()`
- [x] T006 [P] [US1] Replace Logfire logging in `backend/app/services/email.py` — remove `import logfire`; import `get_logger` from `app.core.logging`; replace all `logfire.info/exception()` with `logger.info/exception()`
- [x] T007 [US1] Replace `LOGFIRE_TOKEN` with `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `LANGFUSE_*` env vars in `docker-compose.yml` — update api, worker (vps), and worker-gpu (local) services

**Checkpoint**: Sentry captures errors and performance traces for all API requests and Celery tasks. Logfire APM removed.

---

## Phase 4: User Story 2 — LLM Call Tracing (Priority: P1)

**Goal**: Every LLM call traced in Langfuse with prompt, completion, tokens, cost, latency

**Independent Test**: Trigger a meeting summarization, check Langfuse dashboard for the full LLM trace

### Implementation for User Story 2

- [x] T008 [US2] Replace Logfire OpenAI instrumentation with Langfuse in `backend/app/services/ai_agent.py` — remove `import logfire`, `logfire.instrument_openai(_client)`, and `logfire.span()` context manager; change `from openai import OpenAI` to `from langfuse.openai import OpenAI`; add `@observe()` decorator from `langfuse.decorators` to `summarize_transcript()` function; replace any remaining `logfire` calls with `get_logger` from `app.core.logging`

**Checkpoint**: All LLM calls appear in Langfuse dashboard with full trace data.

---

## Phase 5: User Story 3 — Logfire Cleanup (Priority: P2)

**Goal**: No Logfire code or configuration remains; single source of truth per signal

**Independent Test**: Grep codebase for `logfire` — zero matches. Verify no `LOGFIRE_TOKEN` in config or docker-compose.

### Implementation for User Story 3

- [x] T009 [US3] Verify complete Logfire removal — grep entire `backend/` for any remaining `logfire` references; remove any stragglers
- [x] T010 [US3] Update `.env.example` — remove `LOGFIRE_TOKEN`; add `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` entries

**Checkpoint**: Zero Logfire references in codebase. Clean separation: Sentry = APM, Langfuse = LLM.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification

- [x] T011 Verify all env vars are passed through `docker-compose.yml` to api, worker, and worker-gpu services
- [x] T012 Run `uv sync` to verify dependency resolution succeeds with new packages in `backend/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — uses `get_logger()` and `init_sentry()`
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on US1 and US2 — cleanup verifies nothing was missed
- **Polish (Phase 6)**: Depends on all user stories

### Parallel Opportunities

```text
After Phase 2 completes:
  ├── T004 [US1] main.py Sentry init
  │   └── T005 [US1] worker.py Sentry init + logging migration
  ├── T006 [US1] email.py logging migration (parallel — different file)
  ├── T007 [US1] docker-compose env vars
  └── T008 [US2] ai_agent.py Langfuse wrapper (parallel — different file)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004-T007)
4. **STOP and VALIDATE**: Set SENTRY_DSN, deploy, trigger requests and errors
5. Verify Sentry dashboard shows traces

### Incremental Delivery

1. Setup + Foundational → `get_logger()` and `init_sentry()` ready
2. Add US1 (Sentry APM) → Deploy → Verify error/performance monitoring
3. Add US2 (Langfuse LLM) → Deploy → Verify LLM tracing
4. US3 cleanup → Verify no Logfire remnants
5. Polish → Final env var verification

---

## Notes

- Total tasks: 12
- US1: 4 tasks | US2: 1 task | US3: 2 tasks
- Setup: 2 tasks | Foundational: 1 task | Polish: 2 tasks
- T006 and T008 can run in parallel (different files, no dependencies)
- No database migrations needed
- No frontend changes needed
- Suggested MVP: Phase 1 + Phase 2 + Phase 3 (US1) = 7 tasks
