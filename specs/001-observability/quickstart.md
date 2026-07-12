# Quickstart: Monitoring and Observability

**Feature**: 001-observability
**Platform**: Logfire Cloud (logfire.pydantic.dev)

---

## Prerequisites

1. Create a Logfire account at [logfire.pydantic.dev](https://logfire.pydantic.dev)
2. Create a new project (e.g. `zabt`)
3. Go to **Settings → Write Tokens** and create a token
4. Copy the token value (starts with `pylf_...`)

---

## Environment Variables

Add to `.env` (root) and to Vercel/deployment secrets for backend:

```env
# --- Logfire Observability ---
LOGFIRE_TOKEN=pylf_<your-token-here>
```

The following are set in code and do not need to be in `.env`:
- `LOGFIRE_SERVICE_NAME` — set per-service via `service_name=` in `logfire.configure()`

---

## Docker Compose Wiring

The following services receive `LOGFIRE_TOKEN` in `docker-compose.yml`:

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

## Validation Scenarios

### Scenario 1: FastAPI request trace appears

1. Start the backend: `docker compose up api`
2. Make any API request (e.g. `GET /api/v1/meetings`)
3. Open Logfire → **Live** view
4. ✅ A trace appears with service `zabt-api`, showing method, path, status code, and duration

### Scenario 2: Celery worker task trace appears

1. Upload a meeting file via the frontend
2. Open Logfire → **Live** view
3. ✅ Three task spans appear: `stage_download`, `stage_transcribe`, `stage_summarize`
4. ✅ Each task span shows duration and success/failure status

### Scenario 3: Database query spans visible

1. Make an API request that reads from the database (e.g. list meetings)
2. Open the trace in Logfire
3. ✅ Child spans show SQL statements (e.g. `SELECT meeting...`) with duration

### Scenario 4: LLM call traced with token counts

1. Trigger a meeting summarization
2. Open the `stage_summarize` task trace in Logfire
3. ✅ A child span shows the OpenAI API call with:
   - `gen_ai.request.model` (e.g. `google/gemini-flash-lite`)
   - `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens`
   - Request duration

### Scenario 5: Error appears in traces

1. Upload a malformed audio file to trigger a processing failure
2. Open Logfire → **Live** view
3. ✅ The failed task span shows as an error with the exception type and stack trace

---

## Development Without a Token

When `LOGFIRE_TOKEN` is not set, Logfire runs in no-op mode (`send_to_logfire="if-token-present"`). The application starts and runs normally with no trace data sent. No error is thrown.

To verify no-op mode: start the API without `LOGFIRE_TOKEN` set — the app must start cleanly and serve requests normally.
