# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from sqlmodel import Session

from app.db.engine import engine
from app.models.base import Meeting, User, UserTier
from app.worker import _resolve_meeting_language_for_transcription


def _cleanup(meeting_id: int | None, user_id: int | None) -> None:
    with Session(engine) as s:
        if meeting_id:
            m = s.get(Meeting, meeting_id)
            if m: s.delete(m)
        if user_id:
            u = s.get(User, user_id)
            if u: s.delete(u)
        s.commit()


def test_resolves_to_meeting_requested_language_whisper_code():
    with Session(engine) as s:
        u = User(email="lang-res@example.com", supabase_id="lr-supa", tier=UserTier.FREE,
                 language_preferences=["urdu_arabic", "english"])
        s.add(u); s.commit(); s.refresh(u)
        m = Meeting(title="t", owner_id=u.id, requested_language="urdu_arabic")
        s.add(m); s.commit(); s.refresh(m)
        meeting_id, user_id = m.id, u.id

    try:
        with Session(engine) as s:
            forced, allowed = _resolve_meeting_language_for_transcription(s, meeting_id)
        assert forced == "ur"
        assert allowed == {"ur", "en"}
    finally:
        _cleanup(meeting_id, user_id)


def test_resolves_when_requested_language_is_transliteration_target():
    # urdu_roman is a transliteration target — underlying transcribe should be ur
    with Session(engine) as s:
        u = User(email="lang-res2@example.com", supabase_id="lr2-supa", tier=UserTier.FREE,
                 language_preferences=["urdu_roman", "english"])
        s.add(u); s.commit(); s.refresh(u)
        m = Meeting(title="t", owner_id=u.id, requested_language="urdu_roman")
        s.add(m); s.commit(); s.refresh(m)
        meeting_id, user_id = m.id, u.id

    try:
        with Session(engine) as s:
            forced, allowed = _resolve_meeting_language_for_transcription(s, meeting_id)
        assert forced == "ur"
        assert "ur" in allowed
    finally:
        _cleanup(meeting_id, user_id)


def test_resolves_with_no_requested_language_returns_none_forced():
    with Session(engine) as s:
        u = User(email="lang-res3@example.com", supabase_id="lr3-supa", tier=UserTier.FREE)
        s.add(u); s.commit(); s.refresh(u)
        m = Meeting(title="t", owner_id=u.id, requested_language=None)
        s.add(m); s.commit(); s.refresh(m)
        meeting_id, user_id = m.id, u.id

    try:
        with Session(engine) as s:
            forced, allowed = _resolve_meeting_language_for_transcription(s, meeting_id)
        assert forced is None
        # allowed comes from user's defaults (english + urdu_arabic)
        assert "en" in allowed and "ur" in allowed
    finally:
        _cleanup(meeting_id, user_id)
