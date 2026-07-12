from zabt_vision.settings import Settings


def test_settings_loads_defaults(monkeypatch):
    monkeypatch.delenv("VISION_INFERENCE_BACKEND", raising=False)
    monkeypatch.delenv("VISION_JUDGE_MODEL", raising=False)
    s = Settings()
    assert s.vision_inference_backend == "ollama"
    assert s.vision_judge_model == "qwen3-vl:8b-thinking"
    assert s.fps == 2
    assert s.phash_threshold == 8
    assert s.confidence_threshold == 0.7
    assert s.ensemble_min_signals == 2


def test_settings_overrides_from_env(monkeypatch):
    monkeypatch.setenv("VISION_INFERENCE_BACKEND", "transformers")
    monkeypatch.setenv("VISION_JUDGE_MODEL", "qwen3-vl-32b-thinking")
    s = Settings()
    assert s.vision_inference_backend == "transformers"
    assert s.vision_judge_model == "qwen3-vl-32b-thinking"
