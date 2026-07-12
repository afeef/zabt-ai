# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Domain types for the transcription provider abstraction layer.

These are in-memory transport types — NOT database models.
They bridge the gap between provider-specific API responses and the
existing DB models (Meeting, TranscriptSegment).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models import TranscriptionType


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    speaker_label: str | None = None
    confidence: float | None = None


@dataclass
class ResultSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None
    words: list[WordTimestamp] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    text: str
    language: str
    segments: list[ResultSegment]
    provider_name: str
    recognition_method: str  # "local_whisperx"
    audio_duration_seconds: float
    estimated_cost: float


@dataclass
class TranscriptionConfig:
    language: str | None = None  # None = auto-detect
    allowed_languages: set[str] | None = None  # whisper_lang codes; None = no validation
    min_speakers: int = 1
    max_speakers: int = 10
    storage_key: str | None = None  # S3/MinIO object key — used by RunPod provider to generate presigned URL
    transcription_type: TranscriptionType = TranscriptionType.GENERAL
