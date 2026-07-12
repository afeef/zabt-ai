# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Tests for stage_visual_breakdown Celery task orchestration."""
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.db.engine import engine
from app.models import Meeting, User, VisualSegment
from app.services.visual_breakdown.types import VisualSegmentResponse, VisionWorkerResult
from app.worker import stage_visual_breakdown


@pytest.fixture
def meeting_with_file(db: Session):
    """Create a throw-away meeting (user already created by create_test_user fixture)
    with a valid file_path, and yield meeting_id. Cleans up after test."""
    m = Meeting(owner_id=1, title="VB test mtg", file_path="users/1/meetings/X/audio.mp4")
    db.add(m)
    db.commit()
    db.refresh(m)
    mid = m.id
    yield mid
    with Session(engine) as session:
        obj = session.get(Meeting, mid)
        if obj is not None:
            session.delete(obj)
            session.commit()


def _completed_worker_result() -> VisionWorkerResult:
    return VisionWorkerResult(
        status="completed",
        segments=[
            VisualSegmentResponse(
                id="w-1", sequence=0, start_time=0.0, end_time=5.0,
                screenshot_s3_key="users/1/meetings/X/visual/w-1.jpg",
                caption="Login page", confidence=0.9,
            ),
            VisualSegmentResponse(
                id="w-2", sequence=1, start_time=5.0, end_time=10.0,
                screenshot_s3_key="users/1/meetings/X/visual/w-2.jpg",
                caption="Dashboard", confidence=0.85,
            ),
        ],
        raw_output_s3_key="users/1/meetings/X/visual/raw_output.json",
        model="qwen3-vl:8b-thinking",
        params={"fps": 2},
        stage_metrics={
            "extract_frames": {"duration_ms": 1000, "frame_count": 40},
            "compute_signals": {"duration_ms": 500, "candidate_count": 6},
        },
    )


def test_happy_path_completes_meeting_and_persists_segments(meeting_with_file):
    meeting_id = meeting_with_file
    worker_result = _completed_worker_result()

    with (
        patch("app.services.visual_breakdown.vision_client.VisionClient") as mock_cls,
        patch("app.services.storage.storage.get_presigned_download_url", return_value="https://signed/"),
        patch("app.services.analytics.capture") as mock_capture,
        patch("app.worker.notify") as mock_notify,
    ):
        mock_client = MagicMock()
        mock_client.submit_and_wait.return_value = worker_result
        mock_cls.return_value = mock_client

        out = stage_visual_breakdown(meeting_id)

    assert out == {"status": "completed", "segment_count": 2}

    # Meeting fields updated
    with Session(engine) as session:
        m = session.get(Meeting, meeting_id)
        assert m.visual_breakdown_status == "completed"
        assert m.visual_breakdown_completed_at is not None
        assert m.visual_raw_output_s3_key == "users/1/meetings/X/visual/raw_output.json"
        assert m.visual_breakdown_model == "qwen3-vl:8b-thinking"
        assert m.visual_breakdown_run_count == 1

    # Segments persisted
    from sqlmodel import select as sql_select
    with Session(engine) as session:
        segs = list(session.exec(
            sql_select(VisualSegment).where(VisualSegment.meeting_id == meeting_id)
        ))
        assert len(segs) == 2
        assert {s.caption for s in segs} == {"Login page", "Dashboard"}

    # Analytics: 1 completion event + 2 per-stage events
    event_names = [c.args[1] for c in mock_capture.call_args_list]
    assert "visual_breakdown_completed" in event_names
    assert event_names.count("visual_breakdown_stage_completed") == 2

    # Notify called once with the right event type
    mock_notify.assert_called_once()
    assert mock_notify.call_args.args[0] == "visual_breakdown_completed"


def test_worker_returns_failed_marks_meeting_failed(meeting_with_file):
    meeting_id = meeting_with_file
    failed_result = VisionWorkerResult(
        status="failed", segments=[], model="qwen3-vl:8b-thinking", params={},
        stage_metrics={}, error="ffmpeg blew up", failed_stage="extract_frames",
    )

    with (
        patch("app.services.visual_breakdown.vision_client.VisionClient") as mock_cls,
        patch("app.services.storage.storage.get_presigned_download_url", return_value="https://signed/"),
        patch("app.services.analytics.capture") as mock_capture,
        patch("app.services.notifications.notify"),
    ):
        mock_cls.return_value.submit_and_wait.return_value = failed_result

        out = stage_visual_breakdown(meeting_id)

    assert out == {"status": "failed", "failed_stage": "extract_frames"}

    with Session(engine) as session:
        m = session.get(Meeting, meeting_id)
        assert m.visual_breakdown_status == "failed"
        assert "ffmpeg" in (m.visual_breakdown_error or "")

    event_names = [c.args[1] for c in mock_capture.call_args_list]
    assert "visual_breakdown_failed" in event_names
    assert "visual_breakdown_completed" not in event_names


def test_client_exception_marks_failed_and_reraises(meeting_with_file):
    meeting_id = meeting_with_file

    with (
        patch("app.services.visual_breakdown.vision_client.VisionClient") as mock_cls,
        patch("app.services.storage.storage.get_presigned_download_url", return_value="https://signed/"),
        patch("app.services.analytics.capture"),
        patch("app.services.notifications.notify"),
    ):
        mock_cls.return_value.submit_and_wait.side_effect = RuntimeError("connection refused")

        with pytest.raises(RuntimeError, match="connection refused"):
            stage_visual_breakdown(meeting_id)

    with Session(engine) as session:
        m = session.get(Meeting, meeting_id)
        assert m.visual_breakdown_status == "failed"


def test_missing_file_path_fails_fast(meeting_with_file, db: Session):
    meeting_id = meeting_with_file
    # Clear file_path before test
    m = db.get(Meeting, meeting_id)
    m.file_path = None
    db.add(m)
    db.commit()

    with (
        patch("app.services.visual_breakdown.vision_client.VisionClient") as mock_cls,
        patch("app.services.storage.storage.get_presigned_download_url"),
        patch("app.services.analytics.capture"),
        patch("app.services.notifications.notify"),
    ):
        out = stage_visual_breakdown(meeting_id)

    assert out == {"status": "failed", "reason": "no_video_file"}
    # Worker was never called
    mock_cls.assert_not_called()

    with Session(engine) as session:
        m = session.get(Meeting, meeting_id)
        assert m.visual_breakdown_status == "failed"
        assert m.visual_breakdown_error == "no_video_file"
