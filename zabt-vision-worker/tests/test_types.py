# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import pytest

from zabt_vision.types import JobInput, JobResult, VisualSegment


def test_visual_segment_valid():
    seg = VisualSegment(
        id="abc123",
        sequence=0,
        start_time=0.0,
        end_time=10.0,
        screenshot_s3_key="users/u/meetings/m/visual/abc123.jpg",
        caption="A login page",
        confidence=0.85,
    )
    assert seg.end_time > seg.start_time


def test_visual_segment_rejects_inverted_times():
    with pytest.raises(ValueError):
        VisualSegment(
            id="x",
            sequence=0,
            start_time=10.0,
            end_time=5.0,
            screenshot_s3_key="k",
            caption="c",
            confidence=0.5,
        )


def test_job_input_parses():
    payload = {
        "video_url": "https://example.com/v.mp4",
        "owner_id": "owner-1",
        "meeting_id": "meet-1",
        "transcript": [{"speaker": "SPEAKER_00", "text": "hello", "start": 0.0, "end": 1.5}],
        "params": {"fps": 2},
    }
    job = JobInput.model_validate(payload)
    assert job.transcript[0].text == "hello"
    assert job.params["fps"] == 2


def test_job_result_includes_stage_metrics():
    result = JobResult(
        status="completed",
        segments=[],
        raw_output_s3_key="k",
        model="qwen3-vl:8b-thinking",
        params={},
        stage_metrics={"extract_frames": {"duration_ms": 1000}},
    )
    assert result.stage_metrics["extract_frames"]["duration_ms"] == 1000
