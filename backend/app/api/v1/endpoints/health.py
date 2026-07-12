# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Health check endpoint for transcription provider status."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/transcription")
def transcription_health():
    """Return transcription provider status."""
    return {"provider": "whisper"}
