def test_transcription_config_has_allowed_languages():
    from app.services.transcription.types import TranscriptionConfig
    cfg = TranscriptionConfig(language="ur", allowed_languages={"ur", "en"})
    assert cfg.language == "ur"
    assert cfg.allowed_languages == {"ur", "en"}
