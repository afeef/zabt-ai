# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(SQLModel, table=True):
    """Registered mobile device for push notifications."""

    __table_args__ = (
        UniqueConstraint("user_id", "expo_push_token", name="uq_device_user_token"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    expo_push_token: str = Field(index=True)
    platform: str  # "ios" | "android"
    created_at: datetime = Field(default_factory=_utcnow)
    last_seen_at: datetime = Field(default_factory=_utcnow)


class DeviceCreate(SQLModel):
    """POST /devices request body."""

    expo_push_token: str
    platform: str  # "ios" | "android"


class DeviceRead(SQLModel):
    """Device API response."""

    id: int
    user_id: int
    expo_push_token: str
    platform: str
    created_at: datetime
    last_seen_at: datetime
