from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class EmailShareStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"


class EmailShare(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id", index=True)
    sender_user_id: int = Field(foreign_key="user.id", index=True)
    integration_id: int = Field(foreign_key="integration.id")
    recipients: List[dict] = Field(default_factory=list, sa_column=Column(JSONB))  # [{email, name, status}]
    status: EmailShareStatus = Field(default=EmailShareStatus.PENDING)
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EmailShareRead(SQLModel):
    id: int
    meeting_id: int
    recipients: List[dict] = []
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime


class EmailShareCreate(SQLModel):
    recipient_emails: List[str]
