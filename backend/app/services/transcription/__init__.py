# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Transcription provider abstraction package.

Public API
----------
- ``get_provider()``  — factory function returning the active provider
- ``build_config()``  — build a tier-aware TranscriptionConfig
- ``TranscriptionProvider`` — the Protocol (for type hints)
- ``TranscriptionResult``, ``ResultSegment``, ``WordTimestamp``,
  ``TranscriptionConfig`` — domain types
"""

from app.services.transcription.factory import build_config, get_provider
from app.services.transcription.provider import TranscriptionProvider
from app.services.transcription.types import (
    ResultSegment,
    TranscriptionConfig,
    TranscriptionResult,
    WordTimestamp,
)

__all__ = [
    "get_provider",
    "build_config",
    "TranscriptionProvider",
    "TranscriptionResult",
    "TranscriptionConfig",
    "ResultSegment",
    "WordTimestamp",
]
