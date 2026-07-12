# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pathlib import Path

from zabt_vision.pipeline.extract_frames import extract_frames


def test_extract_frames_at_2fps(tmp_path: Path, fixtures_dir: Path):
    video = fixtures_dir / "sample.mp4"
    out_dir = tmp_path / "frames"

    frames = extract_frames(video_path=video, out_dir=out_dir, fps=2)

    # 4 second video at 2fps = 8 frames
    assert len(frames) == 8
    for f in frames:
        assert f.path.exists()
        assert f.path.suffix == ".jpg"
        assert f.timestamp_s >= 0.0
    # Timestamps should be roughly 0.0, 0.5, 1.0, 1.5, ... 3.5
    assert frames[0].timestamp_s == 0.0
    assert abs(frames[-1].timestamp_s - 3.5) < 0.1


def test_extract_frames_at_1fps(tmp_path: Path, fixtures_dir: Path):
    video = fixtures_dir / "sample.mp4"
    out_dir = tmp_path / "frames"
    frames = extract_frames(video_path=video, out_dir=out_dir, fps=1)
    assert len(frames) == 4
