# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""WhisperX Pipeline — shared transcription logic used by both local and RunPod providers.

This module contains the pure transcription pipeline (transcribe → align → diarize)
with no dependency on app settings, RunPod SDK, or provider abstractions. Both
WhisperProvider and the RunPod handler import from here.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict

import sentry_sdk

from src.logging import get_logger

logger = get_logger(__name__)


@dataclass
class _ResolvedLanguage:
    code: str
    was_forced: bool


def _resolve_language_after_detect(
    detected: str,
    forced: str | None,
    allowed: set[str] | None,
) -> _ResolvedLanguage:
    """Pick the language to use after a first-pass detection.

    - If user explicitly forced a language with no allowed set, use it.
    - Else if no allowed set, trust detection.
    - Else if detected is in allowed set, trust detection.
    - Else fall back to forced (caller's primary).
    """
    if forced and not allowed:
        return _ResolvedLanguage(code=forced, was_forced=True)
    if not allowed:
        return _ResolvedLanguage(code=detected, was_forced=False)
    if detected in allowed:
        return _ResolvedLanguage(code=detected, was_forced=False)
    if forced:
        return _ResolvedLanguage(code=forced, was_forced=True)
    return _ResolvedLanguage(code=detected, was_forced=False)


@dataclass
class PipelineConfig:
    """Configuration for a single pipeline run."""
    device: str
    compute_type: str
    whisper_model_name: str
    diarization_model_name: str
    hf_token: str
    language: str | None = None  # None = auto-detect
    allowed_languages: set[str] | None = None  # if set, force `language` when detection misses
    min_speakers: int = 1
    max_speakers: int = 10
    batch_size: int = 16
    transcription_type: str = "general"  # "general" or "medical"
    medasr_model_name: str = "google/medasr"


def _transcribe_whisperx(
    audio_path: str,
    config: PipelineConfig,
    whisper_model: Any,
    on_status_change: Callable[[str], None] | None,
) -> tuple[Dict[str, Any], str]:
    """WhisperX transcription + alignment. Returns (aligned_result, language)."""
    import torch
    import whisperx

    if on_status_change:
        on_status_change("transcribing")

    t0 = time.time()

    if whisper_model is None:
        logger.info(
            "Loading WhisperX model (model=%s, device=%s, compute_type=%s)...",
            config.whisper_model_name, config.device, config.compute_type,
        )
        whisper_model = whisperx.load_model(
            config.whisper_model_name,
            device=config.device,
            compute_type=config.compute_type,
        )
        logger.info("  Model loaded in %.1fs", time.time() - t0)

    t1 = time.time()
    raw_result: Dict[str, Any] = whisper_model.transcribe(
        audio_path, batch_size=config.batch_size, print_progress=True,
    )
    detected = raw_result.get("language", "en")
    resolved = _resolve_language_after_detect(
        detected=detected,
        forced=config.language,
        allowed=config.allowed_languages,
    )
    language = resolved.code

    if resolved.was_forced and language != detected:
        logger.info(
            "  Detected %s outside allowed set %s — re-transcribing forced as %s",
            detected, config.allowed_languages, language,
        )
        raw_result = whisper_model.transcribe(
            audio_path,
            batch_size=config.batch_size,
            print_progress=True,
            language=language,
        )

    logger.info(
        "  Transcription done in %.1fs (%d segments)",
        time.time() - t1, len(raw_result.get("segments", [])),
    )

    del whisper_model
    if config.device == "cuda":
        torch.cuda.empty_cache()

    # Alignment
    if on_status_change:
        on_status_change("aligning")

    logger.info("Aligning word timestamps...")
    t2 = time.time()
    model_a, metadata = whisperx.load_align_model(
        language_code=language, device=config.device,
    )
    raw_result = whisperx.align(
        raw_result["segments"],
        model_a,
        metadata,
        audio_path,
        config.device,
        return_char_alignments=False,
    )
    logger.info("  Alignment done in %.1fs", time.time() - t2)

    del model_a
    if config.device == "cuda":
        torch.cuda.empty_cache()

    return raw_result, language


def _transcribe_medasr(
    audio_path: str,
    config: PipelineConfig,
    medasr_model: Any,
    on_status_change: Callable[[str], None] | None,
) -> tuple[Dict[str, Any], str]:
    """MedASR transcription using HuggingFace Transformers (direct model, no pipeline).

    Uses AutoModelForCTC + AutoProcessor directly to avoid the pipeline's
    torchcodec dependency. Processes audio in chunks for long files.

    Returns (result_in_whisperx_format, language).
    """
    import torch
    import librosa
    import numpy as np

    if on_status_change:
        on_status_change("transcribing")

    t0 = time.time()

    if medasr_model is None:
        from transformers import AutoModelForCTC, AutoProcessor

        logger.info("Loading MedASR model=%s...", config.medasr_model_name)
        processor = AutoProcessor.from_pretrained(config.medasr_model_name)
        model = AutoModelForCTC.from_pretrained(config.medasr_model_name).to(config.device)
        medasr_model = (model, processor)
        logger.info("  MedASR model ready in %.1fs", time.time() - t0)

    model, processor = medasr_model

    t1 = time.time()

    # Load audio at 16kHz mono
    speech, sr = librosa.load(audio_path, sr=16000)
    total_duration = len(speech) / sr

    # Process in chunks (20s with 2s stride) to handle long audio
    chunk_len = 20 * sr  # 20 seconds
    stride = 2 * sr      # 2 seconds overlap
    step = chunk_len - stride

    all_text_parts = []
    if len(speech) <= chunk_len:
        # Short audio — single pass
        inputs = processor(speech, sampling_rate=sr, return_tensors="pt", padding=True).to(config.device)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        text = processor.batch_decode(predicted_ids)[0]
        all_text_parts.append(text)
    else:
        # Chunked inference
        offset = 0
        while offset < len(speech):
            chunk = speech[offset:offset + chunk_len]
            inputs = processor(chunk, sampling_rate=sr, return_tensors="pt", padding=True).to(config.device)
            with torch.no_grad():
                logits = model(**inputs).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            chunk_text = processor.batch_decode(predicted_ids)[0]
            all_text_parts.append(chunk_text)
            offset += step

    full_text = " ".join(all_text_parts).strip()

    # Build a single segment (CTC models don't produce word-level timestamps natively)
    segments = []
    if full_text:
        segments.append({
            "start": 0.0,
            "end": total_duration,
            "text": full_text,
            "words": [],
        })

    logger.info(
        "  MedASR transcription done in %.1fs (%d segments, %.0fs audio)",
        time.time() - t1, len(segments), total_duration,
    )

    del model, processor, medasr_model
    if config.device == "cuda":
        torch.cuda.empty_cache()

    # Return in WhisperX-compatible format
    return {"segments": segments}, "en"


def run_pipeline(
    audio_path: str,
    config: PipelineConfig,
    whisper_model: Any = None,
    medasr_model: Any = None,
    on_status_change: Callable[[str], None] | None = None,
) -> Dict[str, Any]:
    """Run the transcription pipeline and return raw result dict.

    Routes to WhisperX (normal) or MedASR (medical) based on config.transcription_type.

    Args:
        audio_path: Path to the local audio file.
        config: Pipeline configuration.
        whisper_model: Pre-loaded WhisperX model (optional — loaded if None).
        medasr_model: Pre-loaded MedASR model (optional — loaded if None).
        on_status_change: Callback for progress updates.

    Returns:
        Dict with keys: "segments", "language".
    """
    import torch

    t0 = time.time()

    # --- Stage 1 & 2: Transcription (+ alignment for WhisperX) ---
    if config.transcription_type == "medical":
        logger.info("Using MedASR pipeline (medical transcription)")
        raw_result, language = _transcribe_medasr(audio_path, config, medasr_model, on_status_change)
    else:
        logger.info("Using WhisperX pipeline (normal transcription)")
        raw_result, language = _transcribe_whisperx(audio_path, config, whisper_model, on_status_change)

    # --- Stage 3: Diarization ---
    if on_status_change:
        on_status_change("diarizing")

    if not config.hf_token:
        logger.warning("HF_TOKEN not set — skipping diarization")
        for segment in raw_result["segments"]:
            segment["speaker"] = "SPEAKER_UNKNOWN"
    else:
        logger.info("Stage 3/3: Diarizing speakers...")
        t3 = time.time()
        import whisperx
        from whisperx.diarize import DiarizationPipeline, assign_word_speakers

        diarize_model = DiarizationPipeline(
            model_name=config.diarization_model_name,
            token=config.hf_token,
            device=config.device,
        )
        audio = whisperx.load_audio(audio_path)
        diarize_segments = diarize_model(
            audio,
            min_speakers=config.min_speakers,
            max_speakers=config.max_speakers,
        )
        raw_result = assign_word_speakers(diarize_segments, raw_result)
        logger.info("  Diarization done in %.1fs", time.time() - t3)

        del diarize_model
        if config.device == "cuda":
            torch.cuda.empty_cache()

    logger.info("Pipeline complete (total %.1fs).", time.time() - t0)

    return {"segments": raw_result, "language": language}


def format_result(
    raw: Dict[str, Any],
    language: str,
    provider_name: str,
    recognition_method: str,
    cost_per_minute: float,
) -> Dict[str, Any]:
    """Convert raw WhisperX output to Zabt's TranscriptionResult-compatible dict.

    Returns a plain dict (not dataclass) so it can be used by both the backend
    provider (which wraps it in TranscriptionResult) and the RunPod handler
    (which returns it as JSON directly).
    """
    segments = []
    full_text_parts = []
    max_end = 0.0

    for seg in raw.get("segments", {}).get("segments", raw.get("segments", [])):
        text = seg.get("text", "").strip()
        speaker = seg.get("speaker", "SPEAKER_UNKNOWN")
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)
        max_end = max(max_end, end)

        words = []
        for w in seg.get("words", []):
            words.append({
                "word": w.get("word", ""),
                "start": w.get("start", 0.0),
                "end": w.get("end", 0.0),
                "speaker_label": w.get("speaker"),
                "confidence": None,
            })

        segments.append({
            "start": start,
            "end": end,
            "text": text,
            "speaker": speaker,
            "words": words,
        })
        full_text_parts.append(f"[{speaker}] {text}")

    duration_minutes = max_end / 60.0
    estimated_cost = round(duration_minutes * cost_per_minute, 6)

    return {
        "text": "\n".join(full_text_parts),
        "language": language,
        "segments": segments,
        "provider_name": provider_name,
        "recognition_method": recognition_method,
        "audio_duration_seconds": max_end,
        "estimated_cost": estimated_cost,
    }
