# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pathlib import Path

from scenedetect import ContentDetector, detect


def compute_scene_signal(video_path: Path, threshold: float = 27.0) -> list[float]:
    """Run PySceneDetect content-aware detection and return scene boundary
    timestamps in seconds.

    The first scene always starts at 0.0 (skipped — that's not a "boundary"
    the way our pipeline thinks of it). Returned values are the start times
    of scenes 2..N.
    """
    scenes = detect(str(video_path), ContentDetector(threshold=threshold))
    boundaries: list[float] = []
    for start, _end in scenes[1:]:
        boundaries.append(start.get_seconds())
    return boundaries
