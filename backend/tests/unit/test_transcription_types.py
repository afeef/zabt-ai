# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
def test_transcription_config_has_allowed_languages():
    from app.services.transcription.types import TranscriptionConfig
    cfg = TranscriptionConfig(language="ur", allowed_languages={"ur", "en"})
    assert cfg.language == "ur"
    assert cfg.allowed_languages == {"ur", "en"}
