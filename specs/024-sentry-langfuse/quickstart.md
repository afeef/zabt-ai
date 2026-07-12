# Quickstart: Observability Upgrade (Sentry + Langfuse)

## Prerequisites

### Sentry Setup

1. Create a Sentry account at [sentry.io](https://sentry.io)
2. Create a new project (Platform: Python, Framework: FastAPI)
3. Copy the **DSN** from Settings → Client Keys

### Langfuse Setup

1. Create a Langfuse account at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project
3. Go to Settings → API Keys and copy:
   - **Public Key**
   - **Secret Key**
   - **Host** (default: `https://cloud.langfuse.com`)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | No | `""` | Sentry project DSN. If empty, error/performance monitoring is disabled. |
| `SENTRY_ENVIRONMENT` | No | `"production"` | Environment tag in Sentry (e.g., `production`, `staging`, `local`). |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `1.0` | Fraction of transactions to trace (0.0–1.0). Use 1.0 at low scale. |
| `LANGFUSE_PUBLIC_KEY` | No | `""` | Langfuse public key. If empty, LLM tracing is disabled. |
| `LANGFUSE_SECRET_KEY` | No | `""` | Langfuse secret key. If empty, LLM tracing is disabled. |
| `LANGFUSE_HOST` | No | `"https://cloud.langfuse.com"` | Langfuse API host. Change for self-hosted instances. |

### Removed Variables

| Variable | Status | Notes |
|----------|--------|-------|
| `LOGFIRE_TOKEN` | **Removed** | No longer used. Can be deleted from `.env` and docker-compose. |

## Add to VPS `.env`

```bash
# Sentry APM
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=production

# Langfuse LLM Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Verification

1. **Sentry**: Deploy, trigger any API request. Check Sentry dashboard → Performance for the request trace.
2. **Langfuse**: Trigger a meeting summarization. Check Langfuse dashboard → Traces for the LLM call with prompt, completion, tokens, and cost.

## Disabling

- Remove or clear `SENTRY_DSN` to disable Sentry.
- Remove or clear `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY` to disable Langfuse.
- No code changes needed — both SDKs gracefully no-op when unconfigured.
