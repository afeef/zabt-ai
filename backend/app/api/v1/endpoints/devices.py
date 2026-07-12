# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Device registration endpoints for mobile push notifications."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.models import DeviceCreate, DeviceRead, User
from app.services.device import DeviceService

router = APIRouter()

ALLOWED_PLATFORMS = {"ios", "android"}


@router.post("", response_model=DeviceRead)
def register_device(
    payload: DeviceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceRead:
    """Register or refresh an Expo push token for the authenticated user.

    Idempotent on (user_id, expo_push_token). Platform may change on reinstall.
    """
    if payload.platform not in ALLOWED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"platform must be one of {sorted(ALLOWED_PLATFORMS)}",
        )

    svc = DeviceService(db)
    device = svc.upsert(
        user_id=user.id,
        expo_push_token=payload.expo_push_token,
        platform=payload.platform,
    )
    return DeviceRead.model_validate(device, from_attributes=True)


@router.delete("/{device_id}", status_code=204, response_class=Response)
def unregister_device(
    device_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a device owned by the current user. Used on signout from mobile."""
    svc = DeviceService(db)
    deleted = svc.delete_by_id(device_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="device not found")
    return Response(status_code=204)
