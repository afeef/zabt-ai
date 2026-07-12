from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

from app.models import TranscriptionBackend

# Single .env at the repo root (one file per project, not per service).
# This file lives at <repo>/backend/app/core/config.py — three parents up = repo root.
# In Docker, /app/app/core/config.py resolves to /app, where there is no .env;
# Docker provides config via the `environment:` block instead, which is fine.
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"

# Some legacy modules (worker.py, api/upload.py, services/styles.py) read
# directly from os.environ instead of going through this Settings class.
# Eagerly load the root .env into os.environ so those reads succeed when
# `uv run` is invoked from `backend/` for local dev / tests.
if _REPO_ROOT_ENV.exists():
    load_dotenv(_REPO_ROOT_ENV, override=False)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Zabt"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "app"
    POSTGRES_DB: str = "zabt"
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://redis:6379/0"

    # MinIO Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_PUBLIC_ENDPOINT: str = ""  # Browser-accessible endpoint for presigned URLs (defaults to MINIO_ENDPOINT)
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "zabt-media"
    MINIO_SECURE: bool = False
    MINIO_WEBHOOK_SECRET: str = "change-me-in-production"

    # Storage Provider Toggle ("minio" or "s3")
    STORAGE_PROVIDER: str = "minio"

    # S3-compatible Cloud Storage (used when STORAGE_PROVIDER=s3)
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "zabt-ai-bucket"
    S3_PUBLIC_URL: str = ""  # Public URL for browser presigned URLs (defaults to S3_ENDPOINT_URL)
    S3_REGION: str = "auto"

    # Transcription Backend Toggle
    TRANSCRIPTION_BACKEND: TranscriptionBackend = TranscriptionBackend.RUNPOD

    # GPU Service (used when TRANSCRIPTION_BACKEND=gpu-local)
    GPU_SERVICE_URL: str = "http://gpu-worker:8001"

    # RunPod Serverless (used when TRANSCRIPTION_BACKEND=runpod)
    RUNPOD_API_KEY: str = ""
    RUNPOD_ENDPOINT_ID: str = ""
    RUNPOD_POLL_INTERVAL: int = 5
    RUNPOD_TIMEOUT: int = 300

    # Visual breakdown worker (zabt-vision-worker — see Plan 1/2 specs)
    VISION_BACKEND: str = "local"  # "local" | "runpod"
    VISION_LOCAL_URL: str = "http://zabt-vision-worker:8003"
    VISION_RUNPOD_ENDPOINT_ID: Optional[str] = None
    VISION_RUNPOD_API_KEY: Optional[str] = None
    VISION_JUDGE_MODEL: str = "qwen3-vl:8b-thinking"
    VISION_POLL_INTERVAL: float = 5.0  # seconds between RunPod status polls
    VISION_TIMEOUT: int = 1800  # 30 minutes (per spec)

    # Diarization Settings (passed to GPU service via TranscriptionConfig)
    DIARIZATION_MIN_SPEAKERS: int = 1
    DIARIZATION_MAX_SPEAKERS: int = 10

    # Email (Resend)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "no-reply@zabt.ai"
    APP_URL: str = "https://app.zabt.ai"

    # Sentry APM
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    # Logfire Structured Tracing
    LOGFIRE_TOKEN: str = ""

    # Langfuse LLM Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # PostHog Analytics
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"

    # AI Settings (OpenAI-compatible — works with OpenRouter, Together, etc.)
    OPENAI_BASE_URL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""

    # Supabase Settings
    SUPABASE_URL: str = "https://your-project-ref.supabase.co"
    SUPABASE_JWT_SECRET: str = "change_me_in_env"
    SUPABASE_ANON_KEY: str = ""

    # Notifications
    NOTIFICATION_PROVIDER: str = ""  # "telegram" or "" (disabled)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    EXPO_ACCESS_TOKEN: str | None = None

    # Microsoft OAuth (Graph API integration — separate from Supabase login)
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"  # "common" for multi-tenant
    MICROSOFT_REDIRECT_URI: str = ""  # e.g. https://api.zabt.ai/api/v1/integrations/microsoft/callback

    # Token encryption key (Fernet — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    TOKEN_ENCRYPTION_KEY: str = ""

    # Bot Worker
    BOT_WORKER_URL: str = "http://worker-bot:8002"

    # Comma-separated list of allowed CORS origins
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host="db",
            path=f"/{values.get('POSTGRES_DB') or ''}",
        ))

    class Config:
        case_sensitive = True
        env_file = str(_REPO_ROOT_ENV)
        extra = "ignore"

settings = Settings()
