"""Client for zabt-vision-worker. Mirrors GpuTranscriptionClient shape."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.visual_breakdown.types import VisionWorkerResult

logger = logging.getLogger(__name__)


class VisionClient:
    """HTTP/RunPod client for the vision worker.

    Local mode: a single POST to /run with a long timeout (the worker is
    synchronous — it blocks until done and returns the JobResult directly).

    RunPod mode: submit + poll loop matching GpuTranscriptionClient.
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        local_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self._backend = backend or settings.VISION_BACKEND
        self._local_url = local_url or settings.VISION_LOCAL_URL
        self._timeout = timeout or settings.VISION_TIMEOUT
        self._poll_interval = settings.VISION_POLL_INTERVAL

        if self._backend == "runpod":
            import runpod

            runpod.api_key = settings.VISION_RUNPOD_API_KEY
            self._endpoint = runpod.Endpoint(settings.VISION_RUNPOD_ENDPOINT_ID)
            logger.info(
                "VisionClient (runpod) endpoint=%s timeout=%ds",
                settings.VISION_RUNPOD_ENDPOINT_ID, self._timeout,
            )
        elif self._backend == "local":
            logger.info("VisionClient (local) url=%s timeout=%ds", self._local_url, self._timeout)
        else:
            raise ValueError(f"Unknown VISION_BACKEND: {self._backend}")

    def submit_and_wait(self, payload: Dict[str, Any]) -> VisionWorkerResult:
        if self._backend == "local":
            return self._run_local(payload)
        return self._run_runpod(payload)

    def _run_local(self, payload: Dict[str, Any]) -> VisionWorkerResult:
        logger.info("vision-worker /run local meeting_id=%s", payload.get("meeting_id"))
        with httpx.Client() as client:
            resp = client.post(
                f"{self._local_url}/run",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return VisionWorkerResult.model_validate(resp.json())

    def _run_runpod(self, payload: Dict[str, Any]) -> VisionWorkerResult:
        logger.info("vision-worker /run runpod meeting_id=%s", payload.get("meeting_id"))
        job = self._endpoint.run({"input": payload})
        deadline = time.time() + self._timeout
        while time.time() < deadline:
            status = job.status()
            if status == "COMPLETED":
                return VisionWorkerResult.model_validate(job.output())
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"RunPod vision job {status}: {job.output()}")
            time.sleep(self._poll_interval)
        try:
            job.cancel()
        except Exception:
            pass
        raise TimeoutError(f"vision-worker timed out after {self._timeout}s")
