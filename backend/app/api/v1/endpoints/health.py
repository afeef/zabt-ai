"""Health check endpoint for transcription provider status."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/transcription")
def transcription_health():
    """Return transcription provider status."""
    return {"provider": "whisper"}
