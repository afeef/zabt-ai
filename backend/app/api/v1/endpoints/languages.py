# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Language catalog and user preference endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.models.base import LanguageEntryRead, User
from app.services import analytics
from app.services.languages import catalog, preferences

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/languages", response_model=list[LanguageEntryRead])
def list_languages(db: Session = Depends(get_db)) -> list[LanguageEntryRead]:
    return [LanguageEntryRead.model_validate(e, from_attributes=True)
            for e in catalog.list_entries(db)]


class LanguagePreferencesRead(BaseModel):
    codes: list[str]


class LanguagePreferencesUpdate(BaseModel):
    codes: list[str]


@router.get(
    "/users/me/language-preferences", response_model=LanguagePreferencesRead
)
def get_user_language_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LanguagePreferencesRead:
    return LanguagePreferencesRead(codes=preferences.get_preferences(db, user.id))


@router.put(
    "/users/me/language-preferences", response_model=LanguagePreferencesRead
)
def update_user_language_preferences(
    payload: LanguagePreferencesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LanguagePreferencesRead:
    try:
        codes = preferences.set_preferences(db, user.id, payload.codes)
    except preferences.InvalidLanguageCode as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        analytics.capture(
            user.id,
            "language_preferences_updated",
            {"codes": codes},
        )
    except Exception:
        logger.warning("Failed to capture language_preferences_updated", exc_info=True)

    return LanguagePreferencesRead(codes=codes)
