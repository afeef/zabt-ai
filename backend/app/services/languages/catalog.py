# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Read-only access to the system-seeded language_entry catalog."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.base import LanguageEntry


def list_entries(session: Session) -> list[LanguageEntry]:
    return list(session.exec(select(LanguageEntry).order_by(LanguageEntry.display_name)))


def get_entry(session: Session, code: str) -> LanguageEntry | None:
    return session.get(LanguageEntry, code)


def code_exists(session: Session, code: str) -> bool:
    return get_entry(session, code) is not None


def default_codes(session: Session) -> list[str]:
    rows = session.exec(
        select(LanguageEntry.code).where(LanguageEntry.is_default.is_(True))
    ).all()
    return list(rows)


def transliteration_target_for(
    session: Session, source_code: str
) -> LanguageEntry | None:
    """Return the entry that has transliterate_from = source_code, or None."""
    return session.exec(
        select(LanguageEntry).where(LanguageEntry.transliterate_from == source_code)
    ).first()
