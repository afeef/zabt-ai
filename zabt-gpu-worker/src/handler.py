"""RunPod Serverless Handler — Whisper large-v3 + pyannote diarization.

Models are loaded globally so they persist across jobs (warm workers).
"""

import os
import tempfile
import urllib.request

import runpod
import sentry_sdk
import torch
import whisperx

from src.config import settings
from src.logging import get_logger
from src.pipeline import PipelineConfig, format_result, run_pipeline

logger = get_logger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# Pre-load Whisper model at startup (warm between jobs)
logger.info("Loading WhisperX model=%s device=%s compute_type=%s", settings.WHISPER_MODEL, DEVICE, COMPUTE_TYPE)
whisper_model = whisperx.load_model(settings.WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
logger.info("WhisperX model loaded")


def handler(job):
    """Process a transcription job."""
    job_input = job["input"]
    audio_url = job_input.get("audio_url")
    if not audio_url:
        return {"error": "Missing required input: audio_url"}

    language = job_input.get("language")
    allowed_languages_raw = job_input.get("allowed_languages")
    allowed_languages = set(allowed_languages_raw) if allowed_languages_raw else None
    min_speakers = job_input.get("min_speakers", settings.DIARIZATION_MIN_SPEAKERS)
    max_speakers = job_input.get("max_speakers", settings.DIARIZATION_MAX_SPEAKERS)
    transcription_type = job_input.get("transcription_type", "general")

    tmp_path = None
    try:
        runpod.serverless.progress_update(job, "downloading")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as tmp:
            tmp_path = tmp.name
        urllib.request.urlretrieve(audio_url, tmp_path)
        logger.info("Audio downloaded to %s", tmp_path)

        from src.audio_validation import validate_audio_stream
        validate_audio_stream(tmp_path)

        pipeline_config = PipelineConfig(
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            whisper_model_name=settings.WHISPER_MODEL,
            diarization_model_name=settings.DIARIZATION_MODEL,
            hf_token=settings.HF_TOKEN,
            language=language,
            allowed_languages=allowed_languages,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            transcription_type=transcription_type,
            medasr_model_name=settings.MEDASR_MODEL,
        )

        def on_progress(stage: str):
            runpod.serverless.progress_update(job, stage)

        raw = run_pipeline(
            tmp_path,
            config=pipeline_config,
            whisper_model=whisper_model if transcription_type == "general" else None,
            on_status_change=on_progress,
        )

        method = "runpod_medasr" if transcription_type == "medical" else "runpod_whisperx"
        return format_result(
            raw,
            language=raw["language"],
            provider_name="runpod_whisper",
            recognition_method=method,
            cost_per_minute=settings.COST_PER_MINUTE,
        )

    except Exception as e:
        logger.exception("Handler failed")
        sentry_sdk.capture_exception(e)
        return {"error": str(e)}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        sentry_sdk.flush(timeout=5)


def start_handler():
    """Start the RunPod serverless handler."""
    runpod.serverless.start({"handler": handler})
