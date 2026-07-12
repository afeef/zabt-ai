from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

from zabt_vision.pipeline.video_native import NativeDetection, detect_screen_changes_native


def test_detect_returns_parsed_detections(tmp_path: Path):
    fake_inference = MagicMock()
    # Pretend the model finds two screen changes per chunk
    fake_inference.generate.return_value = (
        '{"detections": ['
        '{"timestamp_ms": 5000, "caption": "Login page", "reasoning": "first screen"},'
        '{"timestamp_ms": 35000, "caption": "Pricing page", "reasoning": "switched"}'
        "]}"
    )

    chunks = [
        (0.0, 60.0, [Image.new("RGB", (10, 10), "red") for _ in range(8)]),
    ]
    out = detect_screen_changes_native(chunks=chunks, inference=fake_inference)

    assert len(out) == 2
    assert isinstance(out[0], NativeDetection)
    assert out[0].timestamp_s == 5.0
    assert out[0].caption == "Login page"
    assert out[1].timestamp_s == 35.0


def test_detect_offsets_chunk2_timestamps(tmp_path: Path):
    fake_inference = MagicMock()
    fake_inference.generate.side_effect = [
        '{"detections": [{"timestamp_ms": 1000, "caption": "A", "reasoning": "r"}]}',
        '{"detections": [{"timestamp_ms": 2000, "caption": "B", "reasoning": "r"}]}',
    ]
    chunks = [
        (0.0, 30.0, []),
        (30.0, 60.0, []),
    ]
    out = detect_screen_changes_native(chunks=chunks, inference=fake_inference)

    assert out[0].timestamp_s == 1.0  # chunk 1: 0.0 + 1.0
    assert out[1].timestamp_s == 32.0  # chunk 2: 30.0 + 2.0


def test_handles_malformed_response_gracefully():
    fake_inference = MagicMock()
    fake_inference.generate.return_value = "not json at all"
    chunks = [(0.0, 10.0, [])]
    out = detect_screen_changes_native(chunks=chunks, inference=fake_inference)
    assert out == []
