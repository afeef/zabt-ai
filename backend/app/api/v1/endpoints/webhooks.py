# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import urllib.parse
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.meeting import meeting_service

logger = get_logger(__name__)

router = APIRouter()

# ── S3 Event Pydantic DTOs ───────────────────────────────────────────────────

class S3Object(BaseModel):
    key: str
    size: int = 0
    contentType: str = ""

class S3Bucket(BaseModel):
    name: str

class S3Info(BaseModel):
    bucket: S3Bucket
    object: S3Object

class S3EventRecord(BaseModel):
    eventName: str
    s3: S3Info

class S3EventNotification(BaseModel):
    EventName: str = ""
    Key: str = ""
    Records: list[S3EventRecord] = []

class WebhookResponse(BaseModel):
    status: str  # "ok" | "skipped" | "error"
    meeting_id: int | None = None
    message: str = ""

# ── Endpoints ────────────────────────────────────────────────────────────────

@router.head("/minio")
def minio_health_check() -> Response:
    """MinIO sends periodic HEAD requests to verify the webhook endpoint is reachable.
    These requests may not include the Authorization header (known MinIO issue #14507).
    """
    return Response(status_code=200)


@router.post("/minio", response_model=WebhookResponse)
def receive_minio_event(
    event: S3EventNotification,
    authorization: str | None = Header(default=None),
) -> Any:
    """Receive MinIO S3 bucket event notification.
    Validates the shared Bearer token, parses the object key,
    and triggers processing via MeetingService.
    """
    # Validate webhook secret
    expected = f"Bearer {settings.MINIO_WEBHOOK_SECRET}"
    if not authorization or authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Parse object key from event
    if not event.Records:
        return WebhookResponse(status="skipped", message="No records in event")

    record = event.Records[0]
    raw_key = record.s3.object.key
    file_key = urllib.parse.unquote_plus(raw_key)

    # Trigger processing via service layer
    meeting = meeting_service.initiate_processing(file_key)

    if meeting:
        return WebhookResponse(
            status="ok",
            meeting_id=meeting.id,
            message="Processing triggered",
        )

    return WebhookResponse(
        status="skipped",
        meeting_id=None,
        message="No pending meeting for this file",
    )
