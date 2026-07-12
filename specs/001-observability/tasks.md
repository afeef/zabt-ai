# Tasks: Monitoring and Observability

**Input**: Design documents from `/specs/001-observability/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

**Tests**: Not requested — validation is done via Logfire Live view (see quickstart.md).

**Organization**: Tasks are grouped by user story. US1 (API & Worker Traces) is the MVP — US2 and US3 build on top.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Logfire extras, env var, and environment wiring.

- [X] T001 Update `logfire>=4.25.0` to `logfire[fastapi,sqlalchemy,httpx,celery]>=4.25.0` in `backend/pyproject.toml`
- [X] T002 Add `LOGFIRE_TOKEN: str = ""` setting to the Settings class in `backend/app/core/config.py`
- [X] T003 [P] Add `LOGFIRE_TOKEN=` placeholder to the Logfire section in `.env`
- [X] T004 [P] Add `LOGFIRE_TOKEN: ${LOGFIRE_TOKEN}` to the `api`, `worker`, and `worker-gpu` services in `docker-compose.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Call `logfire.configure()` in both the API process and the worker process before any instrumentation can work.

**⚠️ CRITICAL**: All instrumentation calls (instrument_fastapi, instrument_celery, etc.) require `logfire.configure()` to be called first in the same process.

- [X] T005 Add `import logfire` and `logfire.configure(service_name="zabt-api", send_to_logfire="if-token-present")` as the first statements (before `app = FastAPI(...)`) in `backend/app/main.py`
- [X] T006 Add `import logfire` and `logfire.configure(service_name="zabt-worker", send_to_logfire="if-token-present")` as the first statements (before the Celery app creation) in `backend/app/worker.py`

**Checkpoint**: Foundation ready — `uv run uvicorn` and `celery` must both start cleanly with or without `LOGFIRE_TOKEN` set.

---

## Phase 3: User Story 1 — API & Worker Traces (Priority: P1) 🎯 MVP

**Goal**: Every FastAPI request and every Celery task (stage_download, stage_transcribe, stage_summarize) produces a visible trace in Logfire with duration, status, and DB query child spans.

**Independent Test**: Make an API request, then upload a file and wait for processing. Open Logfire → Live. Verify traces for both appear with correct service names (`zabt-api` and `zabt-worker`).

- [X] T007 [US1] Call `logfire.instrument_fastapi(app)` immediately after `app = FastAPI(...)` (before `add_middleware`) in `backend/app/main.py`
- [X] T008 [US1] Call `logfire.instrument_sqlalchemy(engine=engine)` after the `logfire.configure()` call (import `engine` from `app.db.engine`) in `backend/app/main.py`
- [X] T009 [US1] Call `logfire.instrument_httpx()` after `logfire.configure()` in `backend/app/main.py`
- [X] T010 [US1] Call `logfire.instrument_celery()` after `logfire.instrument_httpx()` in `backend/app/main.py` (producer side — links dispatch traces to worker)
- [X] T011 [US1] Call `logfire.instrument_celery()` after `logfire.configure()` in `backend/app/worker.py` (consumer side — creates task spans for stage_download, stage_transcribe, stage_summarize)

**Checkpoint**: US1 complete — API traces and Celery task traces visible in Logfire Live. DB query spans appear as children of API request spans. Worker task chain appears as linked traces.

---

## Phase 4: User Story 2 — LLM Call Traces (Priority: P2)

**Goal**: Every OpenAI API call made during meeting summarization appears as a traced child span in Logfire, showing model name, input/output token counts, and latency. Traces are tagged with the summary template ID used (FR-007).

**Independent Test**: Trigger a meeting summarization and open the `stage_summarize` task trace in Logfire. Verify a child span shows `gen_ai.request.model`, `gen_ai.usage.input_tokens`, and `gen_ai.usage.output_tokens`.

- [X] T012 [US2] Add `import logfire` and call `logfire.instrument_openai(_client)` immediately after `_client = OpenAI(...)` in `backend/app/services/ai_agent.py`
- [X] T013 [US2] In the `summarize_transcript()` function in `backend/app/services/ai_agent.py`, wrap the `_client.chat.completions.create(...)` call with `with logfire.span("summarize_transcript", template_id=template_id or "default") as span:` and call `span.set_attribute("model", settings.OPENAI_MODEL)` — add `template_id: str | None = None` parameter to the function signature to receive the template ID from the caller in `backend/app/worker.py`

**Checkpoint**: US2 complete — LLM traces appear in the same Logfire dashboard as API and worker traces. Token counts visible. Template ID attribute present on summarization spans.

---

## Phase 5: User Story 3 — Structured Logs (Priority: P3)

**Goal**: Explicit structured log events with `meeting_id`, `user_id`, and task context are emitted at key pipeline milestones, searchable in Logfire by these fields. Exceptions in tasks are captured with full stack traces.

**Independent Test**: Trigger a file upload and processing. In Logfire → Logs, search for `meeting_id=<id>`. Verify log entries appear for download start, transcription complete, summarization complete, and any errors.

- [X] T014 [US3] In `backend/app/worker.py`, add `logfire.info()`/`logfire.exception()` calls at key milestones inside `stage_download`, `stage_transcribe`, and `stage_summarize` task bodies with structured fields: `meeting_id=meeting_id`, `owner_id=meeting.owner_id` (where available). Wrap exception handling blocks with `logfire.exception("Stage failed", meeting_id=meeting_id)` to capture stack traces (FR-005, FR-009). Pass `template_id` from stage_summarize to `summarize_transcript()` to satisfy the updated signature from T013.

**Checkpoint**: US3 complete — structured log events searchable by meeting_id in Logfire. Exception stack traces captured automatically.

---

## Phase 6: Polish & Validation

**Purpose**: End-to-end validation against quickstart.md scenarios.

- [ ] T015 Restart the backend without `LOGFIRE_TOKEN` set and verify the app starts cleanly with no errors (validates FR-008 fail-silent requirement from `send_to_logfire="if-token-present"`)
- [ ] T016 Run all 5 validation scenarios from `specs/001-observability/quickstart.md` with `LOGFIRE_TOKEN` set and confirm each passes in Logfire Live view


---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T003 and T004 can run in parallel
- **Foundational (Phase 2)**: Requires T001 (extras installed) — BLOCKS all user stories
- **US1 (Phase 3)**: Requires Phase 2 complete — T007–T011 run sequentially (same files)
- **US2 (Phase 4)**: Requires Phase 3 complete (needs Logfire configured and running)
- **US3 (Phase 5)**: Requires Phase 4 complete (T013 changes summarize_transcript signature)
- **Polish (Phase 6)**: Requires all user story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 — no other story dependencies
- **US2 (P2)**: Depends on US1 (Logfire must be configured in the process first)
- **US3 (P3)**: Depends on US2 (T014 calls updated `summarize_transcript()` from T013)

### Within Each User Story

- All instrumentation calls in main.py (T007–T010) are sequential (same file, ordered)
- T011 in worker.py is independent of T007–T010 but must come after T006

### Parallel Opportunities

- **T003 and T004** can run in parallel (different files: `.env` and `docker-compose.yml`)
- **T005 and T006** can run in parallel (different files: `main.py` and `worker.py`)

---

## Parallel Example: Phase 1 Setup

```
In parallel:
  Task T003: Add LOGFIRE_TOKEN to .env
  Task T004: Add LOGFIRE_TOKEN to docker-compose.yml

Then in parallel:
  Task T005: logfire.configure() in main.py
  Task T006: logfire.configure() in worker.py
```

---

## Implementation Strategy

### MVP (US1 Only — API & Worker Traces)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T006)
3. Complete Phase 3: US1 (T007–T011)
4. **STOP and VALIDATE**: Make an API request and process a file → verify traces in Logfire
5. MVP delivered — engineers can see request and task traces

### Incremental Delivery

1. Setup + Foundational → Logfire configured, no-op in dev
2. US1 → API + worker traces visible (MVP)
3. US2 → LLM token counts and model info added to traces
4. US3 → Structured logs searchable by meeting_id
5. Polish → All quickstart scenarios validated

---

## Notes

- `instrument_celery()` MUST be called in BOTH `main.py` (producer) AND `worker.py` (consumer) for trace context propagation to work
- `instrument_fastapi(app)` MUST be called AFTER `app = FastAPI(...)` and BEFORE `add_middleware()`
- `logfire.configure()` MUST be the very first logfire call in each process
- `send_to_logfire="if-token-present"` ensures all tasks pass even without a Logfire account
- No new files are created — all changes are modifications to existing files
