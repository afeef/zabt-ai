# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pydantic import BaseModel


class BotJobInput(BaseModel):
    join_url: str
    event_id: int
    callback_url: str
    bot_job_id: int | None = None


class BotJobResult(BaseModel):
    event_id: int
    bot_job_id: int | None = None
    audio_url: str = ""
    duration_seconds: int = 0
    speakers_count: int = 0
    attendees: list[dict] = []
    status: str = "completed"
    error_message: str = ""


class BotJobStatus(BaseModel):
    id: str
    status: str  # queued | joining | waiting_lobby | recording | uploading | completed | failed
    result: BotJobResult | None = None
    error: str | None = None
