"""Local HTTP server — mirrors RunPod's /run + /status/{job_id} API pattern."""

import os
import tempfile
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import sentry_sdk
import torch
import whisperx
from fastapi import FastAPI

from src.config import settings
from src.logging import get_logger
from src.models import TranscriptionJobInput, TranscriptionJobStatus, TranscriptionResult
from src.pipeline import PipelineConfig, format_result, run_pipeline

logger = get_logger(__name__)

app = FastAPI(title="Zabt GPU Worker", version="0.1.0")

if settings.LOGFIRE_TOKEN:
    import logfire
    logfire.instrument_fastapi(app)
    logfire.instrument_httpx()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# Pre-load Whisper model at startup
import time as _time
from pathlib import Path

_hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
_whisper_cache_dir = _hf_cache / f"models--Systran--faster-whisper-{settings.WHISPER_MODEL}"

if _whisper_cache_dir.exists():
    logger.info("WhisperX model=%s found in cache, loading... (device=%s)", settings.WHISPER_MODEL, DEVICE)
else:
    logger.info("WhisperX model=%s not in cache, downloading... (device=%s)", settings.WHISPER_MODEL, DEVICE)

_t0 = _time.time()
whisper_model = whisperx.load_model(settings.WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
logger.info("WhisperX model ready in %.1fs", _time.time() - _t0)

# In-memory job tracking
_jobs: dict[str, dict] = {}
_jobs_lock = Lock()
_executor = ThreadPoolExecutor(max_workers=1)  # GPU can only handle 1 job at a time


def _process_job(job_id: str, input_data: TranscriptionJobInput):
    """Run transcription in background thread."""
    tmp_path = None
    try:
        with _jobs_lock:
            _jobs[job_id]["status"] = "IN_PROGRESS"

        # Download audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as tmp:
            tmp_path = tmp.name
        urllib.request.urlretrieve(input_data.audio_url, tmp_path)

        from src.audio_validation import validate_audio_stream
        validate_audio_stream(tmp_path)

        transcription_type = getattr(input_data, "transcription_type", "general") or "general"

        pipeline_config = PipelineConfig(
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            whisper_model_name=settings.WHISPER_MODEL,
            diarization_model_name=settings.DIARIZATION_MODEL,
            hf_token=settings.HF_TOKEN,
            language=input_data.language,
            allowed_languages=set(input_data.allowed_languages) if input_data.allowed_languages else None,
            min_speakers=input_data.min_speakers or settings.DIARIZATION_MIN_SPEAKERS,
            max_speakers=input_data.max_speakers or settings.DIARIZATION_MAX_SPEAKERS,
            transcription_type=transcription_type,
            medasr_model_name=settings.MEDASR_MODEL,
        )

        raw = run_pipeline(
            tmp_path,
            config=pipeline_config,
            whisper_model=whisper_model if transcription_type == "general" else None,
        )

        method = "local_medasr" if transcription_type == "medical" else "local_whisperx"
        result = format_result(
            raw,
            language=raw["language"],
            provider_name="local_whisper",
            recognition_method=method,
            cost_per_minute=settings.COST_PER_MINUTE,
        )

        with _jobs_lock:
            _jobs[job_id]["status"] = "COMPLETED"
            _jobs[job_id]["output"] = result

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        sentry_sdk.capture_exception(e)
        with _jobs_lock:
            _jobs[job_id]["status"] = "FAILED"
            _jobs[job_id]["error"] = str(e)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/run")
def submit_job(body: dict):
    """Submit a transcription job. Mirrors RunPod's /run endpoint."""
    input_data = TranscriptionJobInput(**body.get("input", body))
    job_id = str(uuid.uuid4())

    with _jobs_lock:
        _jobs[job_id] = {"status": "QUEUED", "output": None, "error": None}

    _executor.submit(_process_job, job_id, input_data)

    return {"id": job_id, "status": "QUEUED"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Poll job status. Mirrors RunPod's /status endpoint."""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        return {"id": job_id, "status": "NOT_FOUND", "error": f"Job {job_id} not found"}

    response = {"id": job_id, "status": job["status"]}
    if job["status"] == "COMPLETED" and job["output"]:
        response["output"] = job["output"]
    if job["status"] == "FAILED" and job["error"]:
        response["error"] = job["error"]

    return response


@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE, "model": settings.WHISPER_MODEL}
