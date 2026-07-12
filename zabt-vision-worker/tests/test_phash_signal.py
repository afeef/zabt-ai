from PIL import Image, ImageDraw

from zabt_vision.pipeline.signals.phash import compute_phash_signal


def _pattern_a() -> Image.Image:
    """Diagonal stripes in the upper-left quadrant — strong low-frequency content."""
    img = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(img)
    for i in range(0, 256, 16):
        draw.line([(0, i), (i, 0)], fill="black", width=4)
    return img


def _pattern_b() -> Image.Image:
    """Grid of filled circles — very different spatial layout from pattern_a."""
    img = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(img)
    for x in range(32, 256, 64):
        for y in range(32, 256, 64):
            draw.ellipse([x - 20, y - 20, x + 20, y + 20], fill="black")
    return img


def test_phash_detects_change_between_distinct_patterns():
    # Two of pattern A, then two of pattern B. pHash should see a clear jump
    # at the boundary. Solid colors won't work — pHash is DCT-based and all
    # uniform images hash identically, so we use real spatial content.
    frames = [_pattern_a(), _pattern_a(), _pattern_b(), _pattern_b()]
    distances = compute_phash_signal(frames)
    assert len(distances) == 3
    # Same pattern → 0
    assert distances[0] == 0
    # Distinct patterns → meaningful distance (>> identity, on the order of
    # our production phash_threshold of 8)
    assert distances[1] >= 8
    # Same pattern → 0
    assert distances[2] == 0


def test_phash_handles_single_frame():
    distances = compute_phash_signal([_pattern_a()])
    assert distances == []
