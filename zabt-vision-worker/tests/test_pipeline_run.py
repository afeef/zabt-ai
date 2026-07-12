# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from zabt_vision.pipeline.candidates import Candidate
from zabt_vision.pipeline.cross_validate import JudgedKeyframe
from zabt_vision.pipeline.run import run_pipeline
from zabt_vision.pipeline.video_native import NativeDetection
from zabt_vision.settings import Settings
from zabt_vision.types import JobInput, TranscriptLine


def test_run_pipeline_happy_path(tmp_path: Path):
    """Single real keyframe at 1.0s should produce 2 segments:
    - Implicit opening (0.0 -> 1.0) because the first real boundary is > 0.5s
    - The real segment (1.0 -> 4.0) ending at video duration
    """
    job = JobInput(
        video_url="file:///tmp/fake.mp4",
        owner_id="u1",
        meeting_id="m1",
        transcript=[TranscriptLine(speaker="A", text="hello", start=0.0, end=1.0)],
        params={},
    )
    settings = Settings(work_dir=str(tmp_path))

    fake_inference = MagicMock()
    fake_s3 = MagicMock()

    with (
        patch("zabt_vision.pipeline.run.download_video", return_value=tmp_path / "video.mp4"),
        patch(
            "zabt_vision.pipeline.run.extract_frames",
            return_value=[
                type(
                    "F", (), {"index": i, "timestamp_s": i * 0.5, "path": tmp_path / f"f{i}.jpg"}
                )()
                for i in range(4)
            ],
        ),
        patch(
            "zabt_vision.pipeline.run._load_frames_as_images",
            return_value=[Image.new("RGB", (16, 16), "red") for _ in range(4)],
        ),
        patch("zabt_vision.pipeline.run.compute_phash_signal", return_value=[1, 20, 1]),
        patch("zabt_vision.pipeline.run.compute_ocr_signal", return_value=[0.0, 0.7, 0.0]),
        patch("zabt_vision.pipeline.run.compute_scene_signal", return_value=[]),
        patch("zabt_vision.pipeline.run.compute_transcript_hint_signal", return_value=[]),
        patch(
            "zabt_vision.pipeline.run.generate_candidates",
            return_value=[
                Candidate(timestamp_s=1.0, signals_fired=frozenset({"phash", "ocr"})),
            ],
        ),
        patch(
            "zabt_vision.pipeline.run.detect_screen_changes_native",
            return_value=[
                NativeDetection(timestamp_s=1.0, caption="Login", reasoning="r"),
            ],
        ),
        patch(
            "zabt_vision.pipeline.run.cross_validate",
            return_value=[
                JudgedKeyframe(
                    timestamp_s=1.0, caption="Login page", confidence=0.9, reasoning="r"
                ),
            ],
        ),
        patch(
            "zabt_vision.pipeline.run.refine_boundaries",
            side_effect=lambda keyframes, **_: keyframes,
        ),
        patch(
            "zabt_vision.pipeline.run.upload_keyframe_jpg",
            return_value="users/u1/meetings/m1/visual/X.jpg",
        ),
        patch(
            "zabt_vision.pipeline.run.upload_raw_output_json",
            return_value="users/u1/meetings/m1/visual/raw_output.json",
        ),
        patch("zabt_vision.pipeline.run.video_duration_seconds", return_value=4.0),
    ):
        result = run_pipeline(
            job=job, settings=settings, inference=fake_inference, s3_client=fake_s3
        )

    assert result.status == "completed"
    assert len(result.segments) == 2

    # Opening segment
    opening = result.segments[0]
    assert opening.sequence == 0
    assert opening.start_time == 0.0
    assert opening.end_time == 1.0
    assert "(opening)" in opening.caption

    # Real segment
    real = result.segments[1]
    assert real.sequence == 1
    assert real.start_time == 1.0
    assert real.end_time == 4.0
    assert real.caption == "Login page"

    assert "extract_frames" in result.stage_metrics
    assert "cross_validate" in result.stage_metrics
    assert "boundary_refinement" in result.stage_metrics


def test_run_pipeline_no_opening_segment_when_first_boundary_at_zero(tmp_path: Path):
    """If the first keyframe is already at or near 0, no implicit opening is added."""
    job = JobInput(
        video_url="file:///tmp/fake.mp4",
        owner_id="u1",
        meeting_id="m1",
        transcript=[],
        params={},
    )
    settings = Settings(work_dir=str(tmp_path))

    with (
        patch("zabt_vision.pipeline.run.download_video", return_value=tmp_path / "video.mp4"),
        patch(
            "zabt_vision.pipeline.run.extract_frames",
            return_value=[
                type(
                    "F", (), {"index": i, "timestamp_s": i * 0.5, "path": tmp_path / f"f{i}.jpg"}
                )()
                for i in range(4)
            ],
        ),
        patch(
            "zabt_vision.pipeline.run._load_frames_as_images",
            return_value=[Image.new("RGB", (16, 16), "red") for _ in range(4)],
        ),
        patch("zabt_vision.pipeline.run.compute_phash_signal", return_value=[]),
        patch("zabt_vision.pipeline.run.compute_ocr_signal", return_value=[]),
        patch("zabt_vision.pipeline.run.compute_scene_signal", return_value=[]),
        patch("zabt_vision.pipeline.run.compute_transcript_hint_signal", return_value=[]),
        patch("zabt_vision.pipeline.run.generate_candidates", return_value=[]),
        patch("zabt_vision.pipeline.run.detect_screen_changes_native", return_value=[]),
        patch("zabt_vision.pipeline.run.cross_validate", return_value=[]),
        patch(
            "zabt_vision.pipeline.run.refine_boundaries",
            side_effect=lambda keyframes, **_: keyframes,
        ),
        patch("zabt_vision.pipeline.run.upload_keyframe_jpg", return_value="k"),
        patch("zabt_vision.pipeline.run.upload_raw_output_json", return_value="raw"),
        patch("zabt_vision.pipeline.run.video_duration_seconds", return_value=4.0),
    ):
        result = run_pipeline(
            job=job, settings=settings, inference=MagicMock(), s3_client=MagicMock()
        )

    # No keyframes kept → no segments at all
    assert result.status == "completed"
    assert result.segments == []
