# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Unified GPU Transcription Client — talks to GPU service via RunPod SDK or HTTP.

Implements the TranscriptionProvider protocol. The backend (RunPod or local HTTP)
is selected via TRANSCRIPTION_BACKEND config.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import httpx

from app.core.config import settings
from app.models import TranscriptionBackend
from app.services.transcription.types import (
    ResultSegment,
    TranscriptionConfig,
    TranscriptionResult,
    WordTimestamp,
)

logger = logging.getLogger(__name__)


class GpuTranscriptionClient:
    """TranscriptionProvider that delegates to the GPU service."""

    def __init__(self, backend: TranscriptionBackend = TranscriptionBackend.RUNPOD) -> None:
        self._backend = backend
        self._poll_interval = settings.RUNPOD_POLL_INTERVAL
        self._timeout = settings.RUNPOD_TIMEOUT

        if backend == TranscriptionBackend.RUNPOD:
            import runpod
            runpod.api_key = settings.RUNPOD_API_KEY
            self._endpoint = runpod.Endpoint(settings.RUNPOD_ENDPOINT_ID)
            logger.info(
                "GpuTranscriptionClient (runpod) endpoint=%s timeout=%ds",
                settings.RUNPOD_ENDPOINT_ID, self._timeout,
            )
        else:
            self._base_url = settings.GPU_SERVICE_URL.rstrip("/")
            self._http = httpx.Client(timeout=30)
            logger.info(
                "GpuTranscriptionClient (gpu-local) url=%s timeout=%ds",
                self._base_url, self._timeout,
            )

    def get_provider_name(self) -> str:
        return f"gpu_{self._backend}"

    def process_audio(
        self,
        audio_path: str,
        config: TranscriptionConfig | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> TranscriptionResult:
        """Submit transcription job and poll until complete."""
        from app.services.storage import storage

        config = config or TranscriptionConfig()

        if not config.storage_key:
            raise ValueError(
                "GpuTranscriptionClient requires config.storage_key to generate a presigned URL."
            )

        download_url = storage.get_public_presigned_download_url(
            config.storage_key, expiration=3600
        )

        job_input: dict[str, Any] = {
            "audio_url": download_url,
            "min_speakers": config.min_speakers,
            "max_speakers": config.max_speakers,
        }
        if config.language:
            job_input["language"] = config.language
        if config.allowed_languages:
            job_input["allowed_languages"] = sorted(config.allowed_languages)
        if config.transcription_type:
            job_input["transcription_type"] = config.transcription_type.value

        if on_status_change:
            on_status_change("transcribing")

        # Submit job
        job_id = self._submit(job_input)
        logger.info("Job submitted (id=%s, backend=%s)", job_id, self._backend)

        # Poll for completion
        deadline = time.time() + self._timeout
        last_status = None

        while time.time() < deadline:
            status, output, error = self._poll(job_id)

            if status != last_status:
                logger.info("Job %s status: %s", job_id, status)
                last_status = status
                if status == "IN_PROGRESS" and on_status_change:
                    on_status_change("diarizing")

            if status == "COMPLETED":
                logger.info("Job %s completed", job_id)
                return self._parse_response(output)

            if status in ("FAILED", "TIMED_OUT", "CANCELLED"):
                error_msg = f"GPU job {job_id} {status}"
                if error:
                    error_msg += f": {error}"
                raise RuntimeError(error_msg)

            time.sleep(self._poll_interval)

        # Timeout
        self._cancel(job_id)
        raise TimeoutError(
            f"GPU job {job_id} timed out after {self._timeout}s. "
            "Increase RUNPOD_TIMEOUT for long audio files."
        )

    async def transcribe_chunk(self, data: bytes) -> str:
        raise NotImplementedError("GPU service does not support real-time chunk transcription.")

    # ── Backend-specific methods ──────────────────────────────────────────

    def _submit(self, job_input: dict) -> str:
        if self._backend == TranscriptionBackend.RUNPOD:
            run_request = self._endpoint.run(job_input)
            self._current_request = run_request
            return run_request.job_id
        else:
            resp = self._http.post(f"{self._base_url}/run", json={"input": job_input})
            resp.raise_for_status()
            return resp.json()["id"]

    def _poll(self, job_id: str) -> tuple[str, Any, str | None]:
        """Returns (status, output_dict_or_None, error_str_or_None)."""
        if self._backend == TranscriptionBackend.RUNPOD:
            status = self._current_request.status()
            if status == "COMPLETED":
                output = self._current_request.output()
                return status, output, None
            if status in ("FAILED", "TIMED_OUT", "CANCELLED"):
                try:
                    output = self._current_request.output()
                    if isinstance(output, dict) and "error" in output:
                        return status, None, output["error"]
                except Exception:
                    pass
                return status, None, None
            return status, None, None
        else:
            resp = self._http.get(f"{self._base_url}/status/{job_id}")
            resp.raise_for_status()
            data = resp.json()
            return data["status"], data.get("output"), data.get("error")

    def _cancel(self, job_id: str) -> None:
        if self._backend == TranscriptionBackend.RUNPOD:
            try:
                self._current_request.cancel()
            except Exception:
                pass
        # Local server doesn't support cancellation

    @staticmethod
    def _parse_response(output: Any) -> TranscriptionResult:
        if not isinstance(output, dict):
            raise ValueError(f"Unexpected GPU output type: {type(output)}")

        segments = []
        for seg_data in output.get("segments", []):
            words = [
                WordTimestamp(
                    word=w.get("word", ""),
                    start=w.get("start", 0.0),
                    end=w.get("end", 0.0),
                    speaker_label=w.get("speaker_label"),
                    confidence=w.get("confidence"),
                )
                for w in seg_data.get("words", [])
            ]
            segments.append(
                ResultSegment(
                    start=seg_data.get("start", 0.0),
                    end=seg_data.get("end", 0.0),
                    text=seg_data.get("text", ""),
                    speaker=seg_data.get("speaker", "SPEAKER_UNKNOWN"),
                    words=words,
                )
            )

        return TranscriptionResult(
            text=output.get("text", ""),
            language=output.get("language", "en"),
            segments=segments,
            provider_name=output.get("provider_name", "gpu_whisper"),
            recognition_method=output.get("recognition_method", "gpu_whisperx"),
            audio_duration_seconds=output.get("audio_duration_seconds", 0.0),
            estimated_cost=output.get("estimated_cost", 0.0),
        )
