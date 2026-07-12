# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Unit tests for TranscriptionProviderFactory."""

import pytest
from unittest.mock import patch

from app.services.transcription.types import TranscriptionConfig
from app.models import UserTier


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset the lazy-initialised provider singleton between tests."""
    import app.services.transcription.factory as factory_mod

    factory_mod._gpu_client = None
    yield
    factory_mod._gpu_client = None


class TestBuildConfig:
    """Verify build_config() creates TranscriptionConfig from settings."""

    @patch("app.services.transcription.factory.settings")
    def test_diarization_config_from_settings(self, mock_settings):
        mock_settings.DIARIZATION_MIN_SPEAKERS = 2
        mock_settings.DIARIZATION_MAX_SPEAKERS = 6

        from app.services.transcription.factory import build_config

        config = build_config()

        assert config.min_speakers == 2
        assert config.max_speakers == 6

    @patch("app.services.transcription.factory.settings")
    def test_returns_transcription_config(self, mock_settings):
        mock_settings.DIARIZATION_MIN_SPEAKERS = 1
        mock_settings.DIARIZATION_MAX_SPEAKERS = 10

        from app.services.transcription.factory import build_config

        config = build_config(user_tier=UserTier.PRO)

        assert isinstance(config, TranscriptionConfig)
