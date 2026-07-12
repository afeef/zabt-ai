# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class BotJobStatus(str, Enum):
    QUEUED = "queued"
    WAITING_LOBBY = "waiting_lobby"
    JOINING = "joining"
    RECORDING = "recording"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class BotJobInfra(str, Enum):
    LOCAL = "local"
    AZURE_ACI = "azure_aci"


class BotJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    calendar_event_id: int = Field(foreign_key="calendarevent.id", index=True)
    worker_instance_id: Optional[str] = None
    infrastructure: BotJobInfra = Field(default=BotJobInfra.LOCAL)
    status: BotJobStatus = Field(default=BotJobStatus.QUEUED)
    join_url: str
    audio_url: Optional[str] = None
    speakers_count: Optional[int] = None
    duration_seconds: Optional[int] = None
    attendees: List[dict] = Field(default_factory=list, sa_column=Column(JSONB))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BotJobRead(SQLModel):
    id: int
    calendar_event_id: int
    status: str
    infrastructure: str
    join_url: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    speakers_count: Optional[int] = None
    attendees: List[dict] = []
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None
