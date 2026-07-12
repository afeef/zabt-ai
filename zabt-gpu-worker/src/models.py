# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from pydantic import BaseModel


class TranscriptionJobInput(BaseModel):
    audio_url: str
    language: str | None = None
    allowed_languages: list[str] | None = None  # whisper codes; if set, force `language` when detection misses
    min_speakers: int | None = None
    max_speakers: int | None = None
    transcription_type: str = "general"  # "general" or "medical"


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    speaker_label: str | None = None
    confidence: float | None = None


class ResultSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str = "SPEAKER_UNKNOWN"
    words: list[WordTimestamp] = []


class TranscriptionResult(BaseModel):
    text: str
    language: str
    segments: list[ResultSegment]
    provider_name: str
    recognition_method: str
    audio_duration_seconds: float
    estimated_cost: float


class TranscriptionJobStatus(BaseModel):
    id: str
    status: str  # QUEUED, IN_PROGRESS, COMPLETED, FAILED
    output: TranscriptionResult | None = None
    error: str | None = None
