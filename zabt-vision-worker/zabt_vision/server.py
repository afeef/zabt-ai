# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import logging
import traceback

from fastapi import FastAPI

from zabt_vision.inference.factory import make_inference
from zabt_vision.pipeline.run import PipelineStageError, run_pipeline
from zabt_vision.pipeline.upload import make_s3_client
from zabt_vision.settings import get_settings
from zabt_vision.types import JobInput, JobResult

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="zabt-vision-worker", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=JobResult)
def run(job: JobInput) -> JobResult:
    settings = get_settings()
    try:
        inference = make_inference(settings)
        s3_client = make_s3_client(settings)
        return run_pipeline(job=job, settings=settings, inference=inference, s3_client=s3_client)
    except PipelineStageError as e:
        logger.exception("pipeline failed in stage %s", e.stage)
        return JobResult(
            status="failed",
            segments=[],
            model=settings.vision_judge_model,
            params=dict(job.params),
            failed_stage=e.stage,
            error=f"{type(e.original).__name__}: {e.original}\n{traceback.format_exc()[:1000]}",
        )
    except Exception as e:
        logger.exception("pipeline failed")
        return JobResult(
            status="failed",
            segments=[],
            model=settings.vision_judge_model,
            params=dict(job.params),
            error=f"{type(e).__name__}: {e}\n{traceback.format_exc()[:1000]}",
        )
