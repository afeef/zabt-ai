# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Pre-download models during Docker build to bake them into the image."""

import whisperx

from src.config import settings

print(f"Downloading WhisperX model: {settings.WHISPER_MODEL}")
whisperx.load_model(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
print("WhisperX model downloaded")

if settings.HF_TOKEN:
    print("Downloading diarization model...")
    from whisperx.diarize import DiarizationPipeline
    DiarizationPipeline(
        model_name=settings.DIARIZATION_MODEL,
        token=settings.HF_TOKEN,
        device="cpu",
    )
    print("Diarization model downloaded")
else:
    print("HF_TOKEN not set — skipping diarization model download")

print(f"Downloading MedASR model: {settings.MEDASR_MODEL}")
try:
    from transformers import AutoModelForCTC, AutoProcessor
    AutoProcessor.from_pretrained(settings.MEDASR_MODEL)
    AutoModelForCTC.from_pretrained(settings.MEDASR_MODEL)
    print("MedASR model downloaded")
except Exception as e:
    print(f"Warning: Failed to download MedASR model: {e}")
    print("Medical transcription will not be available")

print("All models downloaded successfully")
