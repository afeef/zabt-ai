# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class MeetingHighlight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    highlight_type: str  # "action_item", "key_question", "topic", "chapter"
    content: str
    speaker: Optional[str] = None
    timestamp_start: float
    timestamp_end: Optional[float] = None
    ai_answer: Optional[str] = None
    extra_metadata: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSONB))
    sort_order: int = Field(default=0)


class MeetingHighlightRead(SQLModel):
    id: int
    meeting_id: int
    highlight_type: str
    content: str
    speaker: Optional[str]
    timestamp_start: float
    timestamp_end: Optional[float]
    ai_answer: Optional[str]
    extra_metadata: Optional[dict]
    sort_order: int
