from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image, ImageDraw

from zabt_vision.pipeline.cross_validate import JudgedKeyframe
from zabt_vision.pipeline.refine_boundaries import refine_boundaries


def _patterned(seed: int) -> Image.Image:
    """Generate a structured PIL image whose pHash differs by seed.

    Solid colors all hash identically under DCT-based pHash, so we draw a
    diagonal line whose position depends on `seed` to give the image
    spatial frequency content."""
    img = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(img)
    draw.line([(0, seed * 4 % 64), (64, (seed * 4 + 32) % 64)], fill="black", width=8)
    return img


def test_refines_to_pHash_first_jump_in_window(tmp_path: Path):
    # Build a fake "video" of frames at high fps around a boundary.
    # 4 frames pattern A, then 4 frames pattern B, sampled at 4fps means
    # timestamps 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75 (jump at index 4 i.e. 1.0s)
    frames = [_patterned(0)] * 4 + [_patterned(7)] * 4
    timestamps = [i * 0.25 for i in range(8)]

    # The judge said boundary is at 1.4s (off by ~0.4s)
    keyframes = [JudgedKeyframe(timestamp_s=1.4, caption="C", confidence=0.9, reasoning="r")]

    # Mock the rescan to return our prepared frames
    rescan = MagicMock(return_value=list(zip(timestamps, frames, strict=False)))

    refined = refine_boundaries(
        keyframes=keyframes,
        rescan_window=lambda center, window, fps: rescan(center, window, fps),
        window_seconds=2.0,
        fps=4,
    )
    assert len(refined) == 1
    # True transition is at 1.0s
    assert abs(refined[0].timestamp_s - 1.0) < 0.3


def test_keeps_original_timestamp_when_no_jump_in_window():
    keyframes = [JudgedKeyframe(timestamp_s=5.0, caption="C", confidence=0.9, reasoning="r")]
    # All frames in rescan look identical
    frames = [_patterned(0)] * 8
    timestamps = [4.0 + i * 0.25 for i in range(8)]
    rescan = MagicMock(return_value=list(zip(timestamps, frames, strict=False)))

    refined = refine_boundaries(
        keyframes=keyframes,
        rescan_window=lambda c, w, f: rescan(c, w, f),
        window_seconds=2.0,
        fps=4,
    )
    assert refined[0].timestamp_s == 5.0
