"""T034 — Unit tests for WhisperProvider."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.transcription.types import TranscriptionResult


@pytest.fixture
def whisper_provider():
    """Create a WhisperProvider with mocked torch + settings."""
    with (
        patch("app.services.transcription.whisper_provider.torch") as mock_torch,
        patch("app.services.transcription.whisper_provider.settings") as mock_settings,
    ):
        mock_torch.cuda.is_available.return_value = False
        mock_settings.TRANSCRIPTION_DEVICE = "cpu"
        mock_settings.WHISPER_MODEL = "base.en"
        mock_settings.HF_AUTH_TOKEN = ""

        from app.services.transcription.whisper_provider import WhisperProvider

        provider = WhisperProvider()
        yield provider


class TestWhisperProviderProtocol:
    """Verify WhisperProvider implements TranscriptionProvider Protocol."""

    def test_has_process_audio(self, whisper_provider):
        assert hasattr(whisper_provider, "process_audio")
        assert callable(whisper_provider.process_audio)

    def test_has_transcribe_chunk(self, whisper_provider):
        assert hasattr(whisper_provider, "transcribe_chunk")
        assert callable(whisper_provider.transcribe_chunk)

    def test_has_get_provider_name(self, whisper_provider):
        assert whisper_provider.get_provider_name() == "whisper"


class TestWhisperProviderProcessAudio:
    """Verify process_audio returns a valid TranscriptionResult."""

    @patch("app.services.transcription.whisper_provider.whisperx")
    @patch("app.services.transcription.whisper_provider.whisper")
    def test_returns_transcription_result(
        self, mock_whisper, mock_whisperx, whisper_provider
    ):
        # Setup mocks for the 3-stage pipeline
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 2.5,
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 1.0},
                        {"word": "world", "start": 1.2, "end": 2.5},
                    ],
                }
            ],
            "language": "en",
        }

        mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
        mock_whisperx.align.return_value = mock_model.transcribe.return_value

        with patch.object(whisper_provider, "_validate_duration"):
            with patch("os.path.exists", return_value=True):
                result = whisper_provider.process_audio("/tmp/test.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.provider_name == "whisper"
        assert result.recognition_method == "local_whisperx"
        assert result.language == "en"
        assert len(result.segments) > 0

    @patch("app.services.transcription.whisper_provider.whisperx")
    @patch("app.services.transcription.whisper_provider.whisper")
    def test_cost_estimation(
        self, mock_whisper, mock_whisperx, whisper_provider
    ):
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        # 60 seconds of audio = 1 minute → $0.006
        mock_model.transcribe.return_value = {
            "segments": [
                {
                    "text": "test",
                    "start": 0.0,
                    "end": 60.0,
                    "speaker": "SPEAKER_00",
                    "words": [],
                }
            ],
            "language": "en",
        }
        mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
        mock_whisperx.align.return_value = mock_model.transcribe.return_value

        with patch.object(whisper_provider, "_validate_duration"):
            with patch("os.path.exists", return_value=True):
                result = whisper_provider.process_audio("/tmp/test.mp3")

        # 1 minute * $0.006/min = $0.006
        assert result.estimated_cost == 0.006
        assert result.audio_duration_seconds == 60.0

    def test_file_not_found_raises(self, whisper_provider):
        with pytest.raises(FileNotFoundError):
            whisper_provider.process_audio("/nonexistent/path.mp3")
