# Configuration reference

All configuration is via environment variables in `.env` (copied from
[`.env.example`](../.env.example), the authoritative source). This page groups the variables
and notes which are required. Values marked **REQUIRED** must be set for a working deployment.

## Compose profiles

| Variable | Default | Notes |
|----------|---------|-------|
| `COMPOSE_PROFILES` | `local` | `local` = bundled db+minio+gpu+web. Add `bot`/`vision` for add-ons. Empty for the cloud split. |

## Database

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://app:app@db:5432/zabt` | **REQUIRED.** Local default targets the bundled `db`. Use your managed Postgres URL otherwise. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `app` / `app` / `zabt` | Credentials for the bundled Postgres (profile `local`). |

## Auth (Supabase)

| Variable | Notes |
|----------|-------|
| `SUPABASE_URL` | **REQUIRED.** Your Supabase project URL. |
| `SUPABASE_JWT_SECRET` | **REQUIRED.** Project Settings → API → JWT. Verifies user tokens. |
| `NEXT_PUBLIC_SUPABASE_URL` | **REQUIRED.** Same as `SUPABASE_URL` (browser-side). |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **REQUIRED.** Anon/publishable key. |

## URLs

| Variable | Default | Notes |
|----------|---------|-------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Browser → API base URL. |
| `NEXT_PUBLIC_FRONTEND_URL` | `http://localhost:3000` | |
| `APP_URL` | `http://localhost:3000` | Used in email deep-links. |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins. |

## LLM (summarization)

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` | Any OpenAI-compatible endpoint. |
| `OPENAI_API_KEY` | — | **REQUIRED.** |
| `OPENAI_MODEL` | `google/gemini-3.1-flash-lite-preview` | Model id understood by your endpoint. |

## Object storage

| Variable | Default | Notes |
|----------|---------|-------|
| `STORAGE_PROVIDER` | `minio` | `minio` (bundled) or `s3`. |
| `MINIO_ENDPOINT` | `minio:9000` | In-cluster endpoint. |
| `MINIO_PUBLIC_ENDPOINT` | `http://localhost:9000` | Browser-reachable endpoint for presigned URLs. |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` | Change for anything internet-facing. |
| `MINIO_BUCKET_NAME` | `zabt-ai-bucket` | |
| `MINIO_SECURE` | `false` | `true` if MinIO is served over HTTPS. |
| `MINIO_WEBHOOK_SECRET` | `change-me-in-production` | Shared secret for the MinIO→API upload webhook. |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` / `S3_BUCKET_NAME` / `S3_PUBLIC_URL` / `S3_REGION` | — | Used when `STORAGE_PROVIDER=s3`. |

## Transcription

| Variable | Default | Notes |
|----------|---------|-------|
| `TRANSCRIPTION_BACKEND` | `gpu-local` | `gpu-local` (bundled worker) or `runpod`. |
| `GPU_SERVICE_URL` | `http://worker-gpu:8001` | Local GPU worker URL. |
| `WHISPER_MODEL` | `large-v3` | `tiny`/`base`/`small`/`medium`/`large-v3`. Smaller = faster/less VRAM. |
| `DIARIZATION_MODEL` | `pyannote/speaker-diarization-3.1` | Gated on HF — accept terms. |
| `MEDASR_MODEL` | `google/medasr` | Optional medical ASR model. |
| `HF_TOKEN` | — | **REQUIRED for diarization.** Accept the pyannote gate first. |
| `DIARIZATION_MIN_SPEAKERS` / `DIARIZATION_MAX_SPEAKERS` | `1` / `10` | Speaker-count bounds. |
| `RUNPOD_API_KEY` / `RUNPOD_ENDPOINT_ID` | — | Used when `TRANSCRIPTION_BACKEND=runpod`. |
| `RUNPOD_POLL_INTERVAL` / `RUNPOD_TIMEOUT` | `5` / `1800` | Poll cadence / job timeout (s). |

## Visual breakdown (optional; profile `vision`)

| Variable | Default | Notes |
|----------|---------|-------|
| `VISION_BACKEND` | `local` | `local` or `runpod`. |
| `VISION_LOCAL_URL` | `http://zabt-vision-worker:8003` | |
| `VISION_JUDGE_MODEL` | `qwen3-vl:8b-thinking` | Served via Ollama. |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama endpoint. |
| `VISION_RUNPOD_API_KEY` / `VISION_RUNPOD_ENDPOINT_ID` / `VISION_POLL_INTERVAL` / `VISION_TIMEOUT` | — | RunPod vision path. |

## Integrations & notifications (optional)

| Variable | Notes |
|----------|-------|
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` / `MICROSOFT_TENANT_ID` / `MICROSOFT_REDIRECT_URI` | Microsoft/Teams OAuth. |
| `TOKEN_ENCRYPTION_KEY` | Fernet key encrypting stored OAuth tokens. **Required if you enable integrations.** Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `BOT_DISPLAY_NAME` / `BOT_WORKER_URL` | Teams meeting bot (profile `bot`). |
| `RESEND_API_KEY` / `RESEND_FROM_EMAIL` | Transactional email (Resend). |
| `NOTIFICATION_PROVIDER` / `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Notifications. |

## Observability (all optional)

| Variable | Notes |
|----------|-------|
| `SENTRY_DSN` / `SENTRY_ENVIRONMENT` / `SENTRY_TRACES_SAMPLE_RATE` | Backend error tracking. |
| `NEXT_PUBLIC_SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | Frontend error tracking. |
| `LOGFIRE_TOKEN` | Logfire tracing. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | LLM observability. |
| `POSTHOG_API_KEY` / `POSTHOG_HOST` / `NEXT_PUBLIC_POSTHOG_KEY` / `NEXT_PUBLIC_POSTHOG_HOST` | Product analytics. |

## Mobile app (optional)

`EXPO_ACCESS_TOKEN`, `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_SUPABASE_URL`,
`EXPO_PUBLIC_SUPABASE_ANON_KEY` — only needed if you build the Expo mobile app.

> This table is kept in sync with `.env.example`. If you add a variable to the code, add it to
> both.
