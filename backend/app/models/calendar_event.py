# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ConferencingPlatform(str, Enum):
    TEAMS = "teams"
    MEET = "meet"
    ZOOM = "zoom"


class BotStatus(str, Enum):
    IDLE = "IDLE"
    SCHEDULED = "SCHEDULED"
    JOINING = "JOINING"
    RECORDING = "RECORDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CalendarEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    integration_id: int = Field(foreign_key="integration.id", index=True)
    provider: str
    external_event_id: str = Field(index=True)
    title: str
    start_time: datetime
    end_time: datetime
    conferencing_platform: Optional[ConferencingPlatform] = None
    join_url: Optional[str] = None
    organizer_email: Optional[str] = None
    attendees: List[dict] = Field(default_factory=list, sa_column=Column(JSONB))
    auto_join: bool = Field(default=False)
    bot_status: BotStatus = Field(default=BotStatus.IDLE)
    meeting_id: Optional[int] = Field(default=None, foreign_key="meeting.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CalendarEventRead(SQLModel):
    id: int
    provider: str
    external_event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    conferencing_platform: Optional[str] = None
    join_url: Optional[str] = None
    organizer_email: Optional[str] = None
    attendees: List[dict] = []
    auto_join: bool = False
    bot_status: str = "IDLE"
    meeting_id: Optional[int] = None


class CalendarEventUpdate(SQLModel):
    auto_join: Optional[bool] = None
