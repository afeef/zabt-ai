from pathlib import Path

from zabt_vision.pipeline.signals.scene_detect import compute_scene_signal


def test_scene_signal_detects_red_to_blue_cut(fixtures_dir: Path):
    video = fixtures_dir / "sample.mp4"
    boundaries = compute_scene_signal(video, threshold=27.0)
    # The synthetic fixture is 2s red + 2s blue → expect a cut at ~2.0s.
    assert len(boundaries) >= 1
    assert any(1.5 < b < 2.5 for b in boundaries)


def test_scene_signal_returns_list_of_seconds(fixtures_dir: Path):
    video = fixtures_dir / "sample.mp4"
    boundaries = compute_scene_signal(video, threshold=27.0)
    for b in boundaries:
        assert isinstance(b, float)
