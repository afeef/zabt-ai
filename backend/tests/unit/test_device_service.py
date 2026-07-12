# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""DeviceService unit tests — upsert + query behavior."""

import uuid

import pytest
from sqlmodel import Session

from app.models import User, UserTier
from app.services.device import DeviceService


@pytest.fixture
def user(db: Session) -> User:
    suffix = uuid.uuid4().hex[:8]
    u = User(
        email=f"test-{suffix}@example.com",
        supabase_id=f"sb_test_user_{suffix}",
        tier=UserTier.FREE,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_register_new_device(db: Session, user: User):
    svc = DeviceService(db)
    device = svc.upsert(user.id, expo_push_token="ExpoPushToken[abc123]", platform="ios")
    assert device.id is not None
    assert device.user_id == user.id
    assert device.platform == "ios"


def test_register_same_device_twice_is_idempotent(db: Session, user: User):
    svc = DeviceService(db)
    first = svc.upsert(user.id, expo_push_token="ExpoPushToken[abc]", platform="ios")
    first_id = first.id
    first_last_seen = first.last_seen_at
    second = svc.upsert(user.id, expo_push_token="ExpoPushToken[abc]", platform="ios")
    assert first_id == second.id
    assert second.last_seen_at >= first_last_seen


def test_get_user_devices_returns_only_that_user(db: Session, user: User):
    suffix = uuid.uuid4().hex[:8]
    other = User(email=f"other-{suffix}@example.com", supabase_id=f"sb_other_{suffix}")
    db.add(other)
    db.commit()
    db.refresh(other)

    svc = DeviceService(db)
    svc.upsert(user.id, expo_push_token="ExpoPushToken[a]", platform="ios")
    svc.upsert(other.id, expo_push_token="ExpoPushToken[b]", platform="android")

    user_devices = svc.get_user_devices(user.id)
    assert len(user_devices) == 1
    assert user_devices[0].expo_push_token == "ExpoPushToken[a]"


def test_delete_by_id_removes_user_device(db: Session, user: User):
    svc = DeviceService(db)
    device = svc.upsert(user.id, expo_push_token="ExpoPushToken[delete-me]", platform="ios")
    deleted = svc.delete_by_id(device.id, user.id)
    assert deleted is True
    assert svc.get_user_devices(user.id) == []


def test_delete_by_id_returns_false_for_other_users_device(db: Session, user: User):
    suffix = uuid.uuid4().hex[:8]
    other = User(email=f"other2-{suffix}@example.com", supabase_id=f"sb_other2_{suffix}")
    db.add(other)
    db.commit()
    db.refresh(other)

    svc = DeviceService(db)
    device = svc.upsert(other.id, expo_push_token="ExpoPushToken[other]", platform="ios")
    # `user` tries to delete `other`'s device — must fail
    deleted = svc.delete_by_id(device.id, user.id)
    assert deleted is False
