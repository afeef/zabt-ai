# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""End-to-end pipeline integration test.

Runs the FULL pipeline (frame extraction → all four signals → video-native
detection → cross-validation → boundary refinement → S3 mock upload) against
a real screen-recording fixture using a real Ollama-served Qwen3-VL model.

Skips automatically when:
- The fixture `tests/fixtures/demo_short.mp4` is not present (record one
  manually — see `zabt-vision-worker/README.md` Calibration section).
- The env var `OLLAMA_AVAILABLE=1` is not set (so this never runs in CI by
  default — the dev opts in explicitly).

Marker: `integration`. Run with: `uv run pytest -m integration`.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from zabt_vision.inference.factory import make_inference
from zabt_vision.pipeline.run import run_pipeline
from zabt_vision.settings import Settings
from zabt_vision.types import JobInput

pytestmark = pytest.mark.integration


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(work_dir=str(tmp_path))


def test_full_pipeline_with_real_video(fixtures_dir: Path, settings: Settings):
    video = fixtures_dir / "demo_short.mp4"
    if not video.exists():
        pytest.skip(
            f"Fixture {video} not present — record a 30-60s screen recording with "
            "at least 2 distinct screen changes and save it there."
        )

    if os.getenv("OLLAMA_AVAILABLE") != "1":
        pytest.skip(
            "Set OLLAMA_AVAILABLE=1 to run; requires Ollama running locally with "
            f"the model `{settings.vision_judge_model}` pulled."
        )

    fake_s3 = MagicMock()  # don't hit real S3
    inference = make_inference(settings)

    job = JobInput(
        video_url=f"file://{video.absolute()}",
        owner_id="test-user",
        meeting_id="test-meeting",
        transcript=[],
        params={},
    )

    result = run_pipeline(job=job, settings=settings, inference=inference, s3_client=fake_s3)

    assert result.status == "completed"
    # We should detect at least one screen change in a recording with multiple screens.
    assert len(result.segments) >= 1
    for seg in result.segments:
        assert seg.end_time > seg.start_time
        assert seg.confidence >= settings.confidence_threshold
        assert seg.caption.strip() != ""
