"""Notification provider abstraction and event dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable


@dataclass
class NotificationEvent:
    """A single event to be dispatched to notification providers."""

    event_type: str
    emoji: str
    label: str
    user_email: str
    meeting_title: str | None = None
    meeting_id: int | None = None
    extra: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@runtime_checkable
class NotificationProvider(Protocol):
    """Abstract interface for notification delivery channels."""

    def send(self, event: NotificationEvent) -> None:
        """Deliver a notification. Must not raise exceptions."""
        ...
