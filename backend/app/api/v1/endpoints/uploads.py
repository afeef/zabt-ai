# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Chunked multipart upload endpoints for mobile clients."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models import User
from app.services.storage import storage

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_TOTAL_PARTS = 200  # 5MB * 200 = 1GB upper bound per upload


class InitiateRequest(BaseModel):
    filename: str
    content_type: str
    total_parts: int = Field(gt=0, le=MAX_TOTAL_PARTS)


class PartUrlEntry(BaseModel):
    part_number: int
    url: str


class InitiateResponse(BaseModel):
    upload_id: str
    s3_key: str
    part_urls: List[PartUrlEntry]


class PartUrlRequest(BaseModel):
    s3_key: str
    upload_id: str
    part_number: int = Field(gt=0)


class PartUrlResponse(BaseModel):
    url: str


class CompletePartEntry(BaseModel):
    part_number: int = Field(gt=0)
    etag: str


class CompleteRequest(BaseModel):
    s3_key: str
    upload_id: str
    parts: List[CompletePartEntry]


class CompleteResponse(BaseModel):
    s3_key: str


@router.post("/initiate", response_model=InitiateResponse)
def initiate(
    payload: InitiateRequest,
    user: User = Depends(get_current_user),
) -> InitiateResponse:
    """Start a multipart upload. Returns presigned URLs for all expected parts."""
    upload_id, s3_key = storage.create_multipart_upload(
        user_id=user.id,
        filename=payload.filename,
        content_type=payload.content_type,
    )
    part_urls = [
        PartUrlEntry(
            part_number=n,
            url=storage.generate_part_url(s3_key, upload_id, n),
        )
        for n in range(1, payload.total_parts + 1)
    ]
    return InitiateResponse(upload_id=upload_id, s3_key=s3_key, part_urls=part_urls)


@router.post("/part-url", response_model=PartUrlResponse)
def get_part_url(
    payload: PartUrlRequest,
    user: User = Depends(get_current_user),
) -> PartUrlResponse:
    """Re-issue a presigned URL for a specific part (used on retry or if chunk count grew)."""
    url = storage.generate_part_url(
        object_key=payload.s3_key,
        upload_id=payload.upload_id,
        part_number=payload.part_number,
    )
    return PartUrlResponse(url=url)


@router.post("/complete", response_model=CompleteResponse)
def complete(
    payload: CompleteRequest,
    user: User = Depends(get_current_user),
) -> CompleteResponse:
    """Finalize a multipart upload. Parts must be in ascending part_number order."""
    if not payload.parts:
        raise HTTPException(status_code=400, detail="at least one part required")

    s3_parts = [
        {"PartNumber": p.part_number, "ETag": p.etag}
        for p in sorted(payload.parts, key=lambda p: p.part_number)
    ]
    storage.complete_multipart_upload(
        object_key=payload.s3_key,
        upload_id=payload.upload_id,
        parts=s3_parts,
    )
    return CompleteResponse(s3_key=payload.s3_key)
