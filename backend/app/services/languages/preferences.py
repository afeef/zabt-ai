# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Read/write user language preferences."""

from __future__ import annotations

from sqlmodel import Session

from app.models.base import User
from app.services.languages.catalog import (
    code_exists, default_codes, get_entry,
)


class InvalidLanguageCode(ValueError):
    """Raised when a user submits a language code not in the catalog."""


def get_preferences(session: Session, user_id: int) -> list[str]:
    user = session.get(User, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    if user.language_preferences:
        return list(user.language_preferences)
    return default_codes(session)


def set_preferences(
    session: Session, user_id: int, codes: list[str]
) -> list[str]:
    if not codes:
        raise InvalidLanguageCode("language_preferences cannot be empty")
    for code in codes:
        if not code_exists(session, code):
            raise InvalidLanguageCode(f"Unknown language code: {code}")
    user = session.get(User, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.language_preferences = codes
    session.add(user)
    session.commit()
    return codes


def get_primary_code(session: Session, user_id: int) -> str:
    return get_preferences(session, user_id)[0]


def get_allowed_whisper_langs(session: Session, user_id: int) -> set[str]:
    """Resolve the user's preferences into the set of whisper_lang codes
    we'll accept from auto-detection."""
    codes = get_preferences(session, user_id)
    langs: set[str] = set()
    for code in codes:
        entry = get_entry(session, code)
        if entry:
            langs.add(entry.whisper_lang)
    return langs
