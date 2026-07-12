from typing import List, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlmodel import Session

from app.api import deps
from app.db.engine import engine
from app.models import (
    Meeting, MeetingCreate, MeetingRead, MeetingSummaryUpdate, User,
    TranscriptSegmentRead, TranscriptWordRead, SpeakerBreakdown,
    TranscriptionType,
    EmailShareCreate, EmailShareRead, IntegrationProvider,
)
from app.services import analytics
from app.services.languages import catalog as lang_catalog
from app.services.languages import preferences as lang_prefs
from app.services.meeting import meeting_service
from app.services.meeting_intelligence import intelligence_service
from app.services.notifications import notify
from app.services.pdf_export import pdf_export_service
from app.services.storage import storage
from app.services.email_share import email_share_service
from app.services.integration import integration_service

router = APIRouter()


def dispatch_transcription_job(meeting_id: int) -> None:
    """Kick off the full transcription pipeline for an existing meeting."""
    from app.worker import dispatch_pipeline
    dispatch_pipeline(meeting_id)


def _build_meeting_response(meeting: Meeting) -> MeetingRead:
    """Map Meeting + DB segments to MeetingRead with frontend-compatible field names."""
    segments = []
    speaker_durations: dict[str, float] = {}
    total_duration = 0.0

    for seg in meeting.segments:
        words = [
            TranscriptWordRead(word=w["word"], start=w["start"], end=w["end"])
            for w in (seg.words or [])
        ]
        segments.append(TranscriptSegmentRead(
            start=seg.start_time,
            end=seg.end_time,
            text=seg.text,
            speaker=seg.speaker,
            words=words,
        ))
        dur = seg.end_time - seg.start_time
        speaker = seg.speaker or "SPEAKER_UNKNOWN"
        speaker_durations[speaker] = speaker_durations.get(speaker, 0.0) + dur
        total_duration += dur

    speakers = None
    if speaker_durations and total_duration > 0:
        speakers = {
            spk: SpeakerBreakdown(
                percentage=round((dur / total_duration) * 100, 1),
                name=spk,
            ).model_dump()
            for spk, dur in speaker_durations.items()
        }

    # Fetch highlights and layout hint for intelligence fields
    highlights_list = intelligence_service.get_highlights(meeting.id)
    meeting_type = meeting.meeting_type or "generic"
    layout_hint = intelligence_service.get_layout_hint(meeting_type)

    audio_url = None
    if meeting.file_path:
        audio_url = storage.get_public_presigned_download_url(meeting.file_path)

    return MeetingRead(
        id=meeting.id,
        owner_id=meeting.owner_id,
        title=meeting.title,
        description=meeting.description,
        file_path=meeting.file_path,
        duration_seconds=meeting.duration_seconds,
        created_at=meeting.created_at,
        status=meeting.status,
        sub_status=meeting.sub_status,
        transcript_text=meeting.transcript_text,
        summary_text=meeting.summary_text,
        original_summary_text=meeting.original_summary_text,
        summary_edited=meeting.summary_edited,
        action_items_text=meeting.action_items_text,
        template_id=meeting.template_id,
        template_name=meeting.template_name,
        transcription_type=meeting.transcription_type,
        source_type=meeting.source_type,
        source_url=meeting.source_url,
        youtube_title=meeting.youtube_title,
        youtube_duration_seconds=meeting.youtube_duration_seconds,
        youtube_thumbnail_url=meeting.youtube_thumbnail_url,
        youtube_channel=meeting.youtube_channel,
        requested_language=meeting.requested_language,
        transliterated_text=meeting.transliterated_text,
        segments=segments,
        speakers=speakers,
        meeting_type=meeting_type,
        structured_output=meeting.structured_output,
        structured_output_status=meeting.structured_output_status,
        highlights=[h.model_dump() for h in highlights_list],
        layout_hint=layout_hint,
        audio_url=audio_url,
    )

class MeetingCreateWithKey(MeetingCreate):
    file_key: str
    transcription_type: TranscriptionType = TranscriptionType.GENERAL
    meeting_type: str = "generic"
    language: str | None = None

@router.post("/", response_model=MeetingRead)
def create_meeting(
    *,
    meeting_in: MeetingCreateWithKey,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new meeting record with status 'pending_upload'.
    Processing is triggered by the MinIO webhook when the file lands in the bucket.
    """
    # Resolve the requested language: validate explicit value or fall back to user's primary preference.
    requested_language: str | None = meeting_in.language
    if requested_language is not None:
        if not lang_catalog.code_exists(db, requested_language):
            raise HTTPException(
                status_code=400, detail=f"Unknown language: {requested_language}"
            )
    else:
        requested_language = lang_prefs.get_primary_code(db, current_user.id)

    meeting_data = MeetingCreate(
        title=meeting_in.title,
        description=meeting_in.description,
        file_path=meeting_in.file_key
    )
    meeting = meeting_service.create_meeting(meeting_data, owner_id=current_user.id)
    if meeting_in.transcription_type != TranscriptionType.GENERAL:
        meeting_service.update_transcription_type(meeting.id, meeting_in.transcription_type)
    if meeting_in.meeting_type != "generic":
        meeting_service.update_meeting_type(meeting.id, meeting_in.meeting_type)
    if requested_language is not None:
        meeting_service.update_field(meeting.id, "requested_language", requested_language)
        meeting.requested_language = requested_language
    # Build response directly — new meetings have no segments yet,
    # and the meeting object is detached from the session.
    return MeetingRead(
        id=meeting.id,
        owner_id=meeting.owner_id,
        title=meeting.title,
        description=meeting.description,
        file_path=meeting.file_path,
        duration_seconds=meeting.duration_seconds,
        created_at=meeting.created_at,
        status=meeting.status,
        sub_status=meeting.sub_status,
        transcript_text=meeting.transcript_text,
        summary_text=meeting.summary_text,
        action_items_text=meeting.action_items_text,
        transcription_type=meeting.transcription_type,
        source_type=meeting.source_type,
        source_url=meeting.source_url,
        youtube_title=meeting.youtube_title,
        youtube_duration_seconds=meeting.youtube_duration_seconds,
        youtube_thumbnail_url=meeting.youtube_thumbnail_url,
        youtube_channel=meeting.youtube_channel,
        requested_language=meeting.requested_language,
        segments=[],
        speakers=None,
    )

@router.get("/", response_model=List[MeetingRead])
def read_meetings(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve meetings (without segments — use GET /{meeting_id} for full detail).
    """
    rows = meeting_service.get_meetings(owner_id=current_user.id, skip=skip, limit=limit)
    return [MeetingRead(**row._asdict()) for row in rows]

@router.get("/{meeting_id}", response_model=MeetingRead)
def read_meeting(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get meeting by ID.
    """
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return _build_meeting_response(meeting)

@router.get("/{meeting_id}/export/pdf")
def export_meeting_pdf(
    meeting_id: int,
    type: Literal["summary", "transcript"] = Query(..., description="Export type"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Response:
    """Generate and download a PDF of the meeting summary or transcript."""
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="PDF export is only available for completed meetings.",
        )

    safe_title = pdf_export_service._sanitize_filename(meeting.title)

    try:
        if type == "summary":
            pdf_bytes = pdf_export_service.generate_summary_pdf(meeting)
            filename = f"{safe_title}-summary.pdf"
        else:
            if not meeting.segments:
                raise HTTPException(
                    status_code=400, detail="Meeting has no transcript segments."
                )
            # Build speakers dict from segments (same logic as _build_meeting_response)
            speaker_durations: dict[str, float] = {}
            total_duration = 0.0
            for seg in meeting.segments:
                dur = seg.end_time - seg.start_time
                speaker = seg.speaker or "SPEAKER_UNKNOWN"
                speaker_durations[speaker] = speaker_durations.get(speaker, 0.0) + dur
                total_duration += dur

            speakers: dict[str, dict] = {}
            if speaker_durations and total_duration > 0:
                speakers = {
                    spk: {"name": spk, "percentage": round((dur / total_duration) * 100, 1)}
                    for spk, dur in speaker_durations.items()
                }

            pdf_bytes = pdf_export_service.generate_transcript_pdf(
                meeting, meeting.segments, speakers
            )
            filename = f"{safe_title}-transcript.pdf"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF. Please try again.",
        ) from e

    notify(
        "pdf_exported",
        current_user.email or str(current_user.id),
        meeting.title,
        meeting_id=meeting.id,
        extra={"Type": type},
    )
    analytics.capture(
        current_user.id,
        "pdf_exported",
        {
            "meeting_id": meeting_id,
            "export_type": type,
            "source_type": meeting.source_type,
        },
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """
    Permanently delete a meeting and its associated file.
    """
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    if meeting.status in ["processing", "queued"]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete a meeting while it is processing."
        )

    # Attempt to delete the physical file first
    if meeting.file_path:
        try:
            storage.delete_file(meeting.file_path)
        except Exception as e:
            # We log it but proceed to delete the record to avoid infinite orphaned records
            print(f"Warning: Failed to delete file at {meeting.file_path}. Error: {e}")

    # Visual breakdown artifacts (keyframes + raw_output.json) live under a per-meeting
    # S3 prefix. Wipe the entire prefix so we don't leave orphaned screenshots.
    if meeting.owner_id is not None:
        visual_prefix = f"users/{meeting.owner_id}/meetings/{meeting_id}/visual/"
        try:
            storage.delete_prefix(visual_prefix)
        except Exception as e:
            print(f"Warning: Failed to delete visual prefix {visual_prefix}. Error: {e}")

    # Then delete the database record
    success = meeting_service.delete_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete meeting record.")

@router.patch("/{meeting_id}/summary")
def update_meeting_summary(
    meeting_id: int,
    body: MeetingSummaryUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update the summary text of a completed meeting."""
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.status in ("processing", "queued"):
        raise HTTPException(
            status_code=400,
            detail="Cannot edit summary while meeting is processing.",
        )
    if not body.summary_text.strip():
        raise HTTPException(status_code=400, detail="Summary text cannot be empty.")

    updated = meeting_service.update_summary(meeting_id, body.summary_text)
    return {
        "id": updated.id,
        "summary_text": updated.summary_text,
        "original_summary_text": updated.original_summary_text,
        "summary_edited": updated.summary_edited,
    }


@router.post("/{meeting_id}/summary/restore")
def restore_meeting_summary(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Restore the original AI-generated summary."""
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.original_summary_text is None:
        raise HTTPException(
            status_code=400,
            detail="No original summary available to restore.",
        )

    restored = meeting_service.restore_summary(meeting_id)
    return {
        "id": restored.id,
        "summary_text": restored.summary_text,
        "original_summary_text": restored.original_summary_text,
        "summary_edited": restored.summary_edited,
    }


from pydantic import BaseModel
from typing import Optional as Opt


class YouTubeIngestRequest(BaseModel):
    url: str
    transcription_type: TranscriptionType = TranscriptionType.GENERAL


@router.post("/youtube", response_model=MeetingRead, status_code=201)
def ingest_youtube_url(
    body: YouTubeIngestRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Submit a YouTube URL to create a meeting and dispatch background processing."""
    from app.services.youtube import validate_youtube_url, is_playlist_url
    from app.worker import dispatch_youtube_pipeline

    url = body.url.strip()

    if is_playlist_url(url):
        raise HTTPException(
            status_code=400,
            detail="Playlist URLs are not supported. Please paste a single video URL.",
        )

    if not validate_youtube_url(url):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid YouTube video URL",
        )

    active_count = meeting_service.count_active_youtube(current_user.id)
    if active_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="You have reached the maximum of 3 concurrent YouTube ingestions. Please wait for an existing one to complete.",
        )

    meeting = meeting_service.create_from_youtube(url, owner_id=current_user.id)
    if body.transcription_type != TranscriptionType.GENERAL:
        meeting_service.update_transcription_type(meeting.id, body.transcription_type)
    dispatch_youtube_pipeline(meeting.id)

    return MeetingRead(
        id=meeting.id,
        owner_id=meeting.owner_id,
        title=meeting.title,
        description=meeting.description,
        file_path=meeting.file_path,
        duration_seconds=meeting.duration_seconds,
        created_at=meeting.created_at,
        status=meeting.status,
        sub_status=meeting.sub_status,
        transcript_text=meeting.transcript_text,
        summary_text=meeting.summary_text,
        action_items_text=meeting.action_items_text,
        transcription_type=body.transcription_type,
        source_type=meeting.source_type,
        source_url=meeting.source_url,
        youtube_title=meeting.youtube_title,
        youtube_duration_seconds=meeting.youtube_duration_seconds,
        youtube_thumbnail_url=meeting.youtube_thumbnail_url,
        youtube_channel=meeting.youtube_channel,
        segments=[],
        speakers=None,
    )


class ResummarizeRequest(BaseModel):
    template_id: Opt[int] = None


@router.post("/{meeting_id}/summarize", status_code=202)
def resummarize_meeting(
    meeting_id: int,
    body: ResummarizeRequest = ResummarizeRequest(),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Trigger re-summarization of a meeting using a specified (or default) template."""
    from app.worker import stage_summarize
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.status in ("processing", "queued"):
        raise HTTPException(
            status_code=400,
            detail="Meeting is currently being processed. Try again when processing is complete.",
        )
    meeting_service.update_sub_status(meeting_id, "summarizing")
    stage_summarize.apply_async(args=[meeting_id], kwargs={"template_id": body.template_id})
    return {
        "meeting_id": meeting_id,
        "status": "processing",
        "sub_status": "summarizing",
        "template_id": body.template_id,
    }


class ReTranscribeRequest(BaseModel):
    language: str


@router.post("/{meeting_id}/re-transcribe", response_model=MeetingRead)
def re_transcribe_meeting(
    meeting_id: int,
    payload: ReTranscribeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update the requested language and re-dispatch the transcription pipeline."""
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not lang_catalog.code_exists(db, payload.language):
        raise HTTPException(
            status_code=400, detail=f"Unknown language: {payload.language}"
        )

    old_language = meeting.requested_language
    meeting.requested_language = payload.language
    meeting.status = "queued"
    meeting.sub_status = None
    meeting.transliterated_text = None

    # Delete old segments so the UI doesn't show stale transcript
    from sqlmodel import select as sqlmodel_select
    from app.models.base import TranscriptSegment
    old_segments = db.exec(
        sqlmodel_select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
    ).all()
    for seg in old_segments:
        db.delete(seg)

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    try:
        analytics.capture(
            current_user.id,
            "meeting_re_transcribed",
            {
                "meeting_id": meeting_id,
                "old_language": old_language,
                "new_language": payload.language,
            },
        )
    except Exception:
        import logging
        logging.getLogger(__name__).warning(
            "Failed to capture meeting_re_transcribed", exc_info=True
        )

    dispatch_transcription_job(meeting.id)
    return _build_meeting_response(meeting)


class PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str

class PresignedUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    storage_provider: str

@router.post("/presigned-upload", response_model=PresignedUploadResponse)
def request_presigned_upload_url(
    req: PresignedUploadRequest,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Request a Presigned S3/MinIO URL for direct media upload.
    Returns the storage_provider so the frontend knows whether to call confirm-upload.
    """
    upload_url, file_key = storage.generate_presigned_upload_url(
        user_id=current_user.id,
        filename=req.filename,
        content_type=req.content_type
    )

    return PresignedUploadResponse(
        upload_url=upload_url,
        file_key=file_key,
        storage_provider=storage.provider_name,
    )


@router.post("/{meeting_id}/confirm-upload")
def confirm_upload(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Confirm that a file upload to S3/R2 is complete and trigger the transcription pipeline.
    Used when STORAGE_PROVIDER=s3 (MinIO uses webhooks instead).
    """
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.status != "pending_upload":
        raise HTTPException(status_code=400, detail="Meeting is not awaiting upload")

    result = meeting_service.initiate_processing(meeting.file_path)
    if result:
        notify("upload_started", current_user.email or str(current_user.id), meeting.title, meeting_id=meeting.id)
        return {"status": "ok", "meeting_id": meeting.id, "message": "Processing triggered"}

    return {"status": "skipped", "meeting_id": meeting.id, "message": "Could not initiate processing"}


# ── Email share endpoints ──────────────────────────────────────────────────


@router.post("/{meeting_id}/share-email", response_model=EmailShareRead, status_code=202)
def share_meeting_via_email(
    meeting_id: int,
    payload: EmailShareCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Send meeting summary to selected recipients via email (async)."""
    from app.worker import send_meeting_summary_emails

    # Ownership check
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if meeting.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Email sharing is only available for completed meetings.",
        )

    # Validate recipient count
    if len(payload.recipient_emails) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 recipients per share action.",
        )
    if not payload.recipient_emails:
        raise HTTPException(status_code=400, detail="At least one recipient is required.")

    # Validate Microsoft integration exists
    integration = integration_service.get_by_provider(
        current_user.id, IntegrationProvider.MICROSOFT
    )
    if not integration:
        raise HTTPException(
            status_code=400,
            detail="Microsoft integration not connected. Connect your account first.",
        )

    # Dispatch async Celery task
    send_meeting_summary_emails.delay(
        meeting_id, current_user.id, payload.recipient_emails
    )

    # Return immediate pending response
    return EmailShareRead(
        id=0,  # Will be assigned by the Celery task
        meeting_id=meeting_id,
        recipients=[
            {"email": e, "name": "", "status": "pending"}
            for e in payload.recipient_emails
        ],
        status="pending",
        sent_at=None,
        created_at=meeting.created_at,
    )


@router.get("/{meeting_id}/shares", response_model=List[EmailShareRead])
def list_meeting_shares(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """List past email shares for a meeting."""
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return email_share_service.get_shares_for_meeting(meeting_id, current_user.id)


@router.post("/{meeting_id}/visual-breakdown", status_code=202)
def request_visual_breakdown(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Trigger the visual-breakdown pipeline for a meeting. Idempotent — re-running
    overwrites prior segments. Requires the meeting's video file to still be in S3."""
    from app.worker import stage_visual_breakdown

    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not meeting.file_path:
        raise HTTPException(status_code=400, detail="Meeting has no video file")
    if meeting.visual_breakdown_status in ("queued", "processing"):
        raise HTTPException(
            status_code=409,
            detail="Visual breakdown is already running for this meeting",
        )

    # Mark queued and enqueue the task. The Celery task transitions to "processing"
    # once it actually picks up the job.
    with Session(engine) as session:
        m = session.get(Meeting, meeting_id)
        m.visual_breakdown_status = "queued"
        m.visual_breakdown_error = None
        session.add(m)
        session.commit()

    stage_visual_breakdown.apply_async(args=[meeting_id])
    return {
        "meeting_id": meeting_id,
        "visual_breakdown_status": "queued",
    }


from datetime import datetime as _datetime  # noqa: E402


class _TranscriptLineOut(BaseModel):
    speaker: str | None
    text: str
    start: float
    end: float


class _VisualSegmentOut(BaseModel):
    id: int
    sequence: int
    start_time: float
    end_time: float
    screenshot_url: str
    caption: str
    confidence: float
    transcript_lines: list[_TranscriptLineOut]


class VisualBreakdownResponse(BaseModel):
    meeting_id: int
    visual_breakdown_status: str | None
    visual_breakdown_completed_at: _datetime | None
    visual_segments: list[_VisualSegmentOut]


@router.get("/{meeting_id}/visual-segments", response_model=VisualBreakdownResponse)
def get_visual_segments(
    meeting_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> VisualBreakdownResponse:
    """Return visual segments for a meeting with transcript lines aligned by timestamp.
    Returns empty `visual_segments` and null status when no breakdown has been run."""
    from app.services.storage import storage
    from app.services.visual_segments import VisualSegmentService

    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    aligned = VisualSegmentService().get_with_transcript_alignment(meeting_id)
    return VisualBreakdownResponse(
        meeting_id=meeting_id,
        visual_breakdown_status=meeting.visual_breakdown_status,
        visual_breakdown_completed_at=meeting.visual_breakdown_completed_at,
        visual_segments=[
            _VisualSegmentOut(
                id=seg.id,
                sequence=seg.sequence,
                start_time=seg.start_time,
                end_time=seg.end_time,
                screenshot_url=storage.get_presigned_download_url(seg.screenshot_s3_key, expiration=3600),
                caption=seg.caption,
                confidence=seg.confidence,
                transcript_lines=[
                    _TranscriptLineOut(
                        speaker=tl.speaker, text=tl.text, start=tl.start, end=tl.end,
                    )
                    for tl in seg.transcript_lines
                ],
            )
            for seg in aligned
        ],
    )
