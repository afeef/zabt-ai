# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from collections.abc import Callable
from dataclasses import replace

import imagehash
from PIL import Image

from zabt_vision.pipeline.cross_validate import JudgedKeyframe

RescanFn = Callable[[float, float, int], list[tuple[float, Image.Image]]]
"""rescan(center_s, window_seconds, fps) -> list of (timestamp_s, frame)"""


def _largest_phash_jump(frames: list[tuple[float, Image.Image]]) -> tuple[float, int] | None:
    """Returns (timestamp_of_post_jump_frame, distance) for the largest pHash
    distance in the sequence, or None if the sequence has < 2 frames."""
    if len(frames) < 2:
        return None
    hashes = [imagehash.phash(f) for _, f in frames]
    best_distance = -1
    best_idx = 1
    for i in range(len(hashes) - 1):
        d = int(hashes[i + 1] - hashes[i])
        if d > best_distance:
            best_distance = d
            best_idx = i + 1
    return frames[best_idx][0], best_distance


def refine_boundaries(
    keyframes: list[JudgedKeyframe],
    rescan_window: RescanFn,
    window_seconds: float,
    fps: int,
    min_jump: int = 5,
) -> list[JudgedKeyframe]:
    """For each keyframe, rescan a tight window at higher fps and snap the
    timestamp to the largest pHash jump in that window.

    If the largest jump is below `min_jump`, keep the original timestamp."""
    refined: list[JudgedKeyframe] = []
    for kf in keyframes:
        try:
            window_frames = rescan_window(kf.timestamp_s, window_seconds, fps)
        except Exception:
            refined.append(kf)
            continue
        result = _largest_phash_jump(window_frames)
        if result is None:
            refined.append(kf)
            continue
        new_ts, distance = result
        if distance >= min_jump:
            refined.append(replace(kf, timestamp_s=new_ts))
        else:
            refined.append(kf)
    return refined
