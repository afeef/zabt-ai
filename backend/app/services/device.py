"""Device service — upsert-on-register pattern, query by user."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from sqlmodel import Session, select

from app.models import Device
from app.services.base import BaseService


class DeviceService(BaseService):
    """Manages registered mobile devices for push notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, user_id: int, expo_push_token: str, platform: str) -> Device:
        """Register or refresh a device. Idempotent on (user_id, expo_push_token)."""
        existing = self.db.exec(
            select(Device).where(
                Device.user_id == user_id,
                Device.expo_push_token == expo_push_token,
            )
        ).first()

        if existing:
            existing.last_seen_at = datetime.now(timezone.utc)
            existing.platform = platform  # platform may change if user reinstalls
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        device = Device(
            user_id=user_id,
            expo_push_token=expo_push_token,
            platform=platform,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_user_devices(self, user_id: int) -> Sequence[Device]:
        """Return all registered devices for a user."""
        return self.db.exec(
            select(Device).where(Device.user_id == user_id)
        ).all()

    def delete_by_id(self, device_id: int, user_id: int) -> bool:
        """Delete a device owned by the given user. Returns True if deleted."""
        device = self.db.exec(
            select(Device).where(
                Device.id == device_id,
                Device.user_id == user_id,
            )
        ).first()
        if not device:
            return False
        self.db.delete(device)
        self.db.commit()
        return True
