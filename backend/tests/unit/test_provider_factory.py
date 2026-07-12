"""Unit tests for TranscriptionProviderFactory."""

import pytest
from unittest.mock import patch

from app.services.transcription.types import TranscriptionConfig
from app.models import UserTier


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset lazy-initialised provider singleton between tests."""
    import app.services.transcription.factory as factory_mod

    factory_mod._whisper_provider = None
    yield
    factory_mod._whisper_provider = None


class TestGetProvider:
    """Verify get_provider() always returns WhisperProvider."""

    @patch("app.services.transcription.factory.settings")
    def test_returns_whisper(self, mock_settings):
        mock_settings.TRANSCRIPTION_DEVICE = "cpu"
        mock_settings.WHISPER_MODEL = "base.en"
        mock_settings.HF_AUTH_TOKEN = ""

        with patch("app.services.transcription.whisper_provider.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            with patch(
                "app.services.transcription.whisper_provider.settings", mock_settings
            ):
                from app.services.transcription.factory import get_provider

                provider = get_provider()

        assert provider.get_provider_name() == "whisper"

    @patch("app.services.transcription.factory.settings")
    def test_user_tier_does_not_change_provider(self, mock_settings):
        mock_settings.TRANSCRIPTION_DEVICE = "cpu"
        mock_settings.WHISPER_MODEL = "base.en"
        mock_settings.HF_AUTH_TOKEN = ""

        with patch("app.services.transcription.whisper_provider.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            with patch(
                "app.services.transcription.whisper_provider.settings", mock_settings
            ):
                from app.services.transcription.factory import get_provider

                for tier in [UserTier.FREE, UserTier.PRO, UserTier.ENTERPRISE, None]:
                    provider = get_provider(user_tier=tier)
                    assert provider.get_provider_name() == "whisper"


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
