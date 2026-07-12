# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Tests for POST /api/v1/meetings/{id}/re-transcribe."""

from unittest.mock import patch
from sqlmodel import Session, select
from app.db.engine import engine
from app.models.base import Meeting, TranscriptSegment, User


def _ensure_user(session: Session, user_id: int) -> None:
    """Create user if not already present (FK requirement)."""
    if not session.get(User, user_id):
        session.add(User(id=user_id, email=f"user{user_id}@test.com", supabase_id=f"supabase_{user_id}"))
        session.commit()


def _make_meeting(owner_id: int = 1, requested_language: str | None = "hindi") -> int:
    with Session(engine) as s:
        _ensure_user(s, owner_id)
        m = Meeting(
            title="t", owner_id=owner_id,
            requested_language=requested_language, status="completed",
            file_path="some/key",
        )
        s.add(m); s.commit(); s.refresh(m)
        return m.id


def _delete_meeting(meeting_id: int) -> None:
    with Session(engine) as s:
        m = s.get(Meeting, meeting_id)
        if m:
            s.delete(m); s.commit()


def test_re_transcribe_updates_language_and_dispatches_job(client):
    meeting_id = _make_meeting(requested_language="hindi")
    try:
        # Patch the dispatch helper at its actual import path.
        with patch("app.api.v1.endpoints.meetings.dispatch_transcription_job") as mock_dispatch:
            resp = client.post(
                f"/api/v1/meetings/{meeting_id}/re-transcribe",
                json={"language": "urdu_arabic"},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["requested_language"] == "urdu_arabic"
        mock_dispatch.assert_called_once_with(meeting_id)

        # Confirm DB persisted
        with Session(engine) as s:
            assert s.get(Meeting, meeting_id).requested_language == "urdu_arabic"
    finally:
        _delete_meeting(meeting_id)


def test_re_transcribe_rejects_unknown_language(client):
    meeting_id = _make_meeting()
    try:
        resp = client.post(
            f"/api/v1/meetings/{meeting_id}/re-transcribe",
            json={"language": "klingon"},
        )
        assert resp.status_code == 400
    finally:
        _delete_meeting(meeting_id)


def test_re_transcribe_404_for_nonexistent_meeting(client):
    resp = client.post(
        "/api/v1/meetings/999999/re-transcribe",
        json={"language": "english"},
    )
    assert resp.status_code == 404


def test_re_transcribe_404_for_other_users_meeting(client):
    meeting_id = _make_meeting(owner_id=42)  # current_user is id=1
    try:
        resp = client.post(
            f"/api/v1/meetings/{meeting_id}/re-transcribe",
            json={"language": "english"},
        )
        assert resp.status_code in (403, 404)
    finally:
        _delete_meeting(meeting_id)


def test_re_transcribe_clears_transliterated_text_and_segments(client):
    with Session(engine) as s:
        _ensure_user(s, 1)
        m = Meeting(
            title="t", owner_id=1,
            requested_language="urdu_arabic", status="completed",
            file_path="k", transliterated_text="yeh urdu hai",
        )
        s.add(m)
        s.commit()
        s.refresh(m)
        meeting_id = m.id
        s.add(TranscriptSegment(
            meeting_id=meeting_id, start_time=0, end_time=1, text="a",
        ))
        s.commit()

    try:
        with patch("app.api.v1.endpoints.meetings.dispatch_transcription_job"):
            resp = client.post(
                f"/api/v1/meetings/{meeting_id}/re-transcribe",
                json={"language": "english"},
            )
        assert resp.status_code == 200
        with Session(engine) as s:
            reloaded = s.get(Meeting, meeting_id)
            assert reloaded.transliterated_text is None
            remaining = s.exec(
                select(TranscriptSegment).where(
                    TranscriptSegment.meeting_id == meeting_id,
                )
            ).all()
            assert remaining == []
    finally:
        with Session(engine) as s:
            m = s.get(Meeting, meeting_id)
            if m:
                s.delete(m)
            s.commit()


def test_meeting_read_exposes_transliterated_text(client):
    with Session(engine) as s:
        _ensure_user(s, 1)
        m = Meeting(
            title="t", owner_id=1,
            transliterated_text="sample roman", file_path="k",
        )
        s.add(m)
        s.commit()
        s.refresh(m)
        meeting_id = m.id

    try:
        resp = client.get(f"/api/v1/meetings/{meeting_id}")
        assert resp.status_code == 200
        assert resp.json().get("transliterated_text") == "sample roman"
    finally:
        with Session(engine) as s:
            m = s.get(Meeting, meeting_id)
            if m:
                s.delete(m)
            s.commit()
