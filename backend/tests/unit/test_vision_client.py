# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Tests for VisionClient — HTTP local mode (mocked httpx)."""
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.visual_breakdown.types import VisionWorkerResult
from app.services.visual_breakdown.vision_client import VisionClient


def _make_client_with_mocked_httpx(post_response: dict | Exception):
    """Returns (client, mock_post) tuple. post_response is either a dict to
    return as JSON, or an Exception to raise from .post()."""
    fake_resp = MagicMock()
    if isinstance(post_response, Exception):
        post_method = MagicMock(side_effect=post_response)
    else:
        fake_resp.raise_for_status = MagicMock()
        fake_resp.json.return_value = post_response
        post_method = MagicMock(return_value=fake_resp)

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(post=post_method))
    cm.__exit__ = MagicMock(return_value=False)

    return cm, post_method


def test_submit_and_wait_local_returns_parsed_result():
    cm, post_method = _make_client_with_mocked_httpx({
        "status": "completed",
        "segments": [],
        "raw_output_s3_key": "k",
        "model": "qwen3-vl:8b-thinking",
        "params": {"fps": 2},
        "stage_metrics": {"extract_frames": {"duration_ms": 100}},
    })
    with patch("app.services.visual_breakdown.vision_client.httpx.Client", return_value=cm):
        client = VisionClient(backend="local", local_url="http://worker:8003", timeout=1800)
        result = client.submit_and_wait({
            "video_url": "x", "owner_id": "u", "meeting_id": "m",
        })

    assert isinstance(result, VisionWorkerResult)
    assert result.status == "completed"
    assert result.model == "qwen3-vl:8b-thinking"
    post_method.assert_called_once()
    args, kwargs = post_method.call_args
    assert args[0] == "http://worker:8003/run"
    assert kwargs["timeout"] == 1800


def test_submit_and_wait_local_raises_on_timeout():
    cm, _ = _make_client_with_mocked_httpx(httpx.TimeoutException("timeout"))
    with patch("app.services.visual_breakdown.vision_client.httpx.Client", return_value=cm):
        client = VisionClient(backend="local", local_url="http://worker:8003", timeout=10)
        with pytest.raises(httpx.TimeoutException):
            client.submit_and_wait({"video_url": "x", "owner_id": "u", "meeting_id": "m"})


def test_submit_and_wait_local_returns_failed_status_when_worker_says_so():
    cm, _ = _make_client_with_mocked_httpx({
        "status": "failed",
        "segments": [],
        "model": "qwen3-vl:8b-thinking",
        "params": {},
        "stage_metrics": {},
        "error": "ffmpeg blew up",
        "failed_stage": "extract_frames",
    })
    with patch("app.services.visual_breakdown.vision_client.httpx.Client", return_value=cm):
        client = VisionClient(backend="local", local_url="http://worker:8003")
        result = client.submit_and_wait({"video_url": "x", "owner_id": "u", "meeting_id": "m"})

    assert result.status == "failed"
    assert result.failed_stage == "extract_frames"
    assert "ffmpeg" in result.error


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        VisionClient(backend="bogus")
