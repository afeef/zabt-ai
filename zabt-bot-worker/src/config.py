from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # S3 storage for audio uploads
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "zabt-ai-bucket"
    S3_REGION: str = "auto"

    # Worker identity
    WORKER_ID: str = "bot-worker-1"
    BOT_DISPLAY_NAME: str = "Zabt AI Notetaker"

    # Meeting session limits
    MAX_MEETING_DURATION_HOURS: int = 2
    LOBBY_TIMEOUT_SECONDS: int = 300  # 5 minutes

    # Observability
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    LOGFIRE_TOKEN: str = ""
    
    # PostHog analytics
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://app.posthog.com"

    PORT: int = 8002

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
