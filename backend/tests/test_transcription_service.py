# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import pytest
from unittest.mock import patch, MagicMock
from app.services.transcription import TranscriptionService
from app.core.config import settings

@pytest.fixture
def mock_settings():
    """Mock the settings to force CPU mode."""
    with patch("app.services.transcription.settings") as mock_set:
        mock_set.TRANSCRIPTION_DEVICE = "cpu"
        mock_set.WHISPER_MODEL = "base.en"
        yield mock_set

@patch("app.services.transcription.torch.cuda.is_available", return_value=False)
@patch("app.services.transcription.whisper.load_model")
def test_transcription_service_initialization_cpu_fallback(mock_load, mock_cuda, mock_settings):
    """
    Test that the TranscriptionService accurately detects a missing CUDA context
    and falls back to CPU cleanly when device setting is 'auto'.
    """
    mock_settings.TRANSCRIPTION_DEVICE = "auto"
    
    service = TranscriptionService()
    assert service.device == "cpu"
    assert mock_cuda.called

@patch("app.services.transcription.torch.cuda.is_available", return_value=True)
@patch("app.services.transcription.whisper.load_model")
def test_transcription_service_initialization_gpu(mock_load, mock_cuda, mock_settings):
    """
    Test that the TranscriptionService binds 'cuda' when available.
    """
    mock_settings.TRANSCRIPTION_DEVICE = "auto"
    
    service = TranscriptionService()
    assert service.device == "cuda"
    assert mock_cuda.called
