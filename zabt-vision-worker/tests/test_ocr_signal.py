from unittest.mock import MagicMock

from PIL import Image

from zabt_vision.pipeline.signals.ocr_diff import _jaccard_distance, compute_ocr_signal


def test_jaccard_distance_identical():
    assert _jaccard_distance({"hello", "world"}, {"hello", "world"}) == 0.0


def test_jaccard_distance_disjoint():
    assert _jaccard_distance({"a", "b"}, {"c", "d"}) == 1.0


def test_jaccard_distance_partial():
    # 1 shared / 3 union = 0.667 distance
    d = _jaccard_distance({"a", "b"}, {"b", "c"})
    assert abs(d - (1 - 1 / 3)) < 0.001


def test_compute_ocr_signal_uses_reader():
    fake_reader = MagicMock()
    # Three frames: same text, then different text
    fake_reader.readtext.side_effect = [
        [(None, "Login Page", 0.9)],
        [(None, "Login Page", 0.9)],
        [(None, "Pricing Tiers", 0.9)],
    ]
    img = Image.new("RGB", (10, 10), "white")
    distances = compute_ocr_signal([img, img, img], reader=fake_reader)
    assert len(distances) == 2
    assert distances[0] == 0.0  # identical text
    assert distances[1] > 0.5  # significant change
