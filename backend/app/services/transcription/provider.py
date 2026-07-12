"""TranscriptionProvider Protocol — the abstract contract for all providers."""

from __future__ import annotations

from typing import Protocol

from app.services.transcription.types import TranscriptionConfig, TranscriptionResult


class TranscriptionProvider(Protocol):
    """Abstract interface that every transcription backend must satisfy."""

    def process_audio(
        self,
        audio_path: str,
        config: TranscriptionConfig | None = None,
        on_status_change: callable | None = None,
    ) -> TranscriptionResult:
        """Transcribe a local audio file and return a normalised result."""
        ...

    async def transcribe_chunk(self, data: bytes) -> str:
        """Transcribe a small audio chunk (for real-time WebSocket use)."""
        ...

    def get_provider_name(self) -> str:
        """Return the human-readable provider identifier."""
        ...
