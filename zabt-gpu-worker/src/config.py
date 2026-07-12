# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODE: str = "runpod"  # "runpod" or "local"
    WHISPER_MODEL: str = "large-v3"
    MEDASR_MODEL: str = "google/medasr"
    DIARIZATION_MODEL: str = "pyannote/speaker-diarization-3.1"
    HF_TOKEN: str = ""
    DIARIZATION_MIN_SPEAKERS: int = 1
    DIARIZATION_MAX_SPEAKERS: int = 10
    COST_PER_MINUTE: float = 0.0046
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    LOGFIRE_TOKEN: str = ""
    PORT: int = 8001

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
