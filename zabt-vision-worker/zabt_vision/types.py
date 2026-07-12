from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TranscriptLine(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class VisualSegment(BaseModel):
    id: str
    sequence: int
    start_time: float = Field(ge=0.0)
    end_time: float
    screenshot_s3_key: str
    caption: str
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def end_after_start(self) -> "VisualSegment":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class JobInput(BaseModel):
    video_url: str
    owner_id: str
    meeting_id: str
    transcript: list[TranscriptLine] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class JobResult(BaseModel):
    status: Literal["completed", "failed"]
    segments: list[VisualSegment] = Field(default_factory=list)
    raw_output_s3_key: str | None = None
    model: str
    params: dict[str, Any] = Field(default_factory=dict)
    stage_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    error: str | None = None
    failed_stage: str | None = None
