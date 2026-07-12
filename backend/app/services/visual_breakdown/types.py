"""Pydantic types for the vision worker's HTTP/RunPod response."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VisualSegmentResponse(BaseModel):
    id: str               # worker-assigned uuid hex (becomes part of the S3 key)
    sequence: int
    start_time: float
    end_time: float
    screenshot_s3_key: str
    caption: str
    confidence: float


class VisionWorkerResult(BaseModel):
    status: str  # "completed" | "failed"
    segments: List[VisualSegmentResponse] = Field(default_factory=list)
    raw_output_s3_key: Optional[str] = None
    model: str
    params: Dict[str, Any] = Field(default_factory=dict)
    stage_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    error: Optional[str] = None
    failed_stage: Optional[str] = None
