from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.base import Meeting, User
from app.models.meeting_intelligence import MeetingHighlightRead
from app.services.meeting import meeting_service
from app.services.meeting_intelligence import intelligence_service
from app.worker import stage_extract_intelligence

router = APIRouter(prefix="/meetings", tags=["highlights"])


@router.get("/{meeting_id}/highlights", response_model=list[MeetingHighlightRead])
def get_meeting_highlights(
    meeting_id: int,
    highlight_type: str | None = None,
    user: User = Depends(get_current_user),
):
    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting or meeting.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return intelligence_service.get_highlights(meeting_id, highlight_type)


@router.patch("/{meeting_id}/meeting-type", status_code=202)
def update_meeting_type(
    meeting_id: int,
    body: dict,
    user: User = Depends(get_current_user),
):
    """Update meeting type and trigger re-extraction."""
    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting or meeting.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    new_type = body.get("meeting_type", "generic")
    valid_types = ["generic", "grooming", "standup", "retro", "one_on_one"]
    if new_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid meeting type. Must be one of: {valid_types}")

    meeting_service.update_field(meeting_id, "meeting_type", new_type)
    stage_extract_intelligence.delay(meeting_id)
    return {"status": "processing", "meeting_type": new_type}


@router.post("/{meeting_id}/re-extract", status_code=202)
def re_extract_intelligence(
    meeting_id: int,
    user: User = Depends(get_current_user),
):
    """Re-run intelligence extraction for a meeting."""
    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting or meeting.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.transcript_text:
        raise HTTPException(status_code=400, detail="Meeting has no transcript")

    meeting_service.update_field(meeting_id, "structured_output_status", "processing")
    stage_extract_intelligence.delay(meeting_id)
    return {"status": "processing"}
