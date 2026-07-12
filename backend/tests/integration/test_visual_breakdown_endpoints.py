# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Integration tests for visual-breakdown endpoints."""
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.engine import engine
from app.models import Meeting, User


def _ensure_user(session: Session, user_id: int) -> None:
    """Create user if not already present (FK requirement)."""
    if not session.get(User, user_id):
        session.add(User(id=user_id, email=f"user{user_id}@test.com", supabase_id=f"supabase_{user_id}"))
        session.commit()


def _make_meeting(owner_id: int = 1, file_path: str | None = "users/1/meetings/X/audio.mp4") -> int:
    with Session(engine) as s:
        _ensure_user(s, owner_id)
        m = Meeting(owner_id=owner_id, title="VB endpoint test", file_path=file_path)
        s.add(m)
        s.commit()
        s.refresh(m)
        return m.id


def _delete_meeting(meeting_id: int) -> None:
    with Session(engine) as s:
        m = s.get(Meeting, meeting_id)
        if m:
            s.delete(m)
            s.commit()


def test_post_visual_breakdown_returns_202_and_enqueues_task(client: TestClient, normal_user_token_headers):
    meeting_id = _make_meeting()
    try:
        with patch("app.worker.stage_visual_breakdown.apply_async") as mock_apply:
            r = client.post(
                f"/api/v1/meetings/{meeting_id}/visual-breakdown",
                headers=normal_user_token_headers,
            )
        assert r.status_code == 202, r.text
        body = r.json()
        assert body["meeting_id"] == meeting_id
        assert body["visual_breakdown_status"] == "queued"
        mock_apply.assert_called_once_with(args=[meeting_id])

        # DB updated to queued
        with Session(engine) as session:
            m = session.get(Meeting, meeting_id)
            assert m.visual_breakdown_status == "queued"
    finally:
        _delete_meeting(meeting_id)


def test_post_visual_breakdown_409_when_already_running(client: TestClient, normal_user_token_headers):
    meeting_id = _make_meeting()
    try:
        with Session(engine) as session:
            m = session.get(Meeting, meeting_id)
            m.visual_breakdown_status = "processing"
            session.add(m)
            session.commit()

        with patch("app.worker.stage_visual_breakdown.apply_async") as mock_apply:
            r = client.post(
                f"/api/v1/meetings/{meeting_id}/visual-breakdown",
                headers=normal_user_token_headers,
            )
        assert r.status_code == 409
        mock_apply.assert_not_called()
    finally:
        _delete_meeting(meeting_id)


def test_post_visual_breakdown_400_when_no_video_file(client: TestClient, normal_user_token_headers):
    meeting_id = _make_meeting(file_path=None)
    try:
        with patch("app.worker.stage_visual_breakdown.apply_async") as mock_apply:
            r = client.post(
                f"/api/v1/meetings/{meeting_id}/visual-breakdown",
                headers=normal_user_token_headers,
            )
        assert r.status_code == 400
        mock_apply.assert_not_called()
    finally:
        _delete_meeting(meeting_id)


def test_post_visual_breakdown_404_when_meeting_missing(client: TestClient, normal_user_token_headers):
    with patch("app.worker.stage_visual_breakdown.apply_async") as mock_apply:
        r = client.post(
            "/api/v1/meetings/999999/visual-breakdown",
            headers=normal_user_token_headers,
        )
    assert r.status_code == 404
    mock_apply.assert_not_called()


# ---------------------------------------------------------------------------
# GET /meetings/{meeting_id}/visual-segments
# ---------------------------------------------------------------------------

def test_get_visual_segments_returns_empty_when_no_breakdown(
    client: TestClient, normal_user_token_headers
):
    meeting_id = _make_meeting()
    try:
        r = client.get(
            f"/api/v1/meetings/{meeting_id}/visual-segments",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["meeting_id"] == meeting_id
        assert body["visual_breakdown_status"] is None
        assert body["visual_segments"] == []
    finally:
        _delete_meeting(meeting_id)


def test_get_visual_segments_returns_aligned_segments(
    client: TestClient, normal_user_token_headers
):
    from datetime import datetime
    from app.models import TranscriptSegment, VisualSegment

    meeting_id = _make_meeting()
    try:
        # Seed two visual segments + a transcript line
        with Session(engine) as session:
            m = session.get(Meeting, meeting_id)
            m.visual_breakdown_status = "completed"
            m.visual_breakdown_completed_at = datetime.utcnow()
            session.add(m)

            session.add(VisualSegment(
                meeting_id=meeting_id, sequence=0,
                start_time=0.0, end_time=5.0,
                screenshot_s3_key="users/1/meetings/X/visual/a.jpg",
                caption="Login page", confidence=0.9,
            ))
            session.add(VisualSegment(
                meeting_id=meeting_id, sequence=1,
                start_time=5.0, end_time=10.0,
                screenshot_s3_key="users/1/meetings/X/visual/b.jpg",
                caption="Dashboard", confidence=0.85,
            ))
            session.add(TranscriptSegment(
                meeting_id=meeting_id, speaker="A", text="hi from login",
                start_time=1.0, end_time=2.0,
            ))
            session.commit()

        with patch("app.services.storage.storage.get_presigned_download_url",
                   side_effect=lambda key, expiration: f"https://signed/{key}"):
            r = client.get(
                f"/api/v1/meetings/{meeting_id}/visual-segments",
                headers=normal_user_token_headers,
            )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["visual_breakdown_status"] == "completed"
        assert len(body["visual_segments"]) == 2
        assert body["visual_segments"][0]["caption"] == "Login page"
        assert body["visual_segments"][0]["screenshot_url"].startswith("https://signed/")
        assert body["visual_segments"][0]["transcript_lines"][0]["text"] == "hi from login"
        # Segment 1 has no transcript lines (only one line at t=1.0 which falls in segment 0)
        assert body["visual_segments"][1]["transcript_lines"] == []
    finally:
        _delete_meeting(meeting_id)


def test_get_visual_segments_404_when_meeting_missing(
    client: TestClient, normal_user_token_headers
):
    r = client.get(
        "/api/v1/meetings/999999/visual-segments",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
