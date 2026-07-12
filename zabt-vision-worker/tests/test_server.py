# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from zabt_vision.server import app
from zabt_vision.types import JobResult, VisualSegment


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_synchronous_run_endpoint(client):
    fake_result = JobResult(
        status="completed",
        segments=[
            VisualSegment(
                id="s1",
                sequence=0,
                start_time=0.0,
                end_time=10.0,
                screenshot_s3_key="k",
                caption="X",
                confidence=0.9,
            )
        ],
        raw_output_s3_key="raw",
        model="qwen3-vl:8b-thinking",
        params={"fps": 2},
        stage_metrics={"extract_frames": {"duration_ms": 100}},
    )
    with (
        patch("zabt_vision.server.run_pipeline", return_value=fake_result),
        patch("zabt_vision.server.make_inference", return_value=MagicMock()),
        patch("zabt_vision.server.make_s3_client", return_value=MagicMock()),
    ):
        r = client.post(
            "/run",
            json={
                "video_url": "file:///tmp/x.mp4",
                "owner_id": "u1",
                "meeting_id": "m1",
                "transcript": [],
                "params": {},
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert len(body["segments"]) == 1


def test_run_returns_failed_status_on_exception(client):
    with (
        patch("zabt_vision.server.run_pipeline", side_effect=RuntimeError("ffmpeg blew up")),
        patch("zabt_vision.server.make_inference", return_value=MagicMock()),
        patch("zabt_vision.server.make_s3_client", return_value=MagicMock()),
    ):
        r = client.post(
            "/run",
            json={
                "video_url": "x",
                "owner_id": "u",
                "meeting_id": "m",
                "transcript": [],
                "params": {},
            },
        )
    assert r.status_code == 200  # surface failure in body, not HTTP
    body = r.json()
    assert body["status"] == "failed"
    assert "ffmpeg" in body["error"]
