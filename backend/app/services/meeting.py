import logging
from typing import List, Optional
from sqlalchemy import func
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.models import Meeting, MeetingCreate, MeetingRead, TranscriptSegment, TranscriptionType
from app.core.config import settings
from app.db.engine import engine
from app.services.base import BaseService

logger = logging.getLogger(__name__)

class MeetingService(BaseService):
    def on_before_action(self, action: str, **kwargs):
        """
        Specialized audit hook for MeetingService.
        """
        print(f"AUDIT [MEETING] [BEFORE]: User is performing '{action}' on Meeting.")

    def on_after_action(self, action: str, result: any, **kwargs):
        """
        Specialized audit hook for MeetingService.
        """
        print(f"AUDIT [MEETING] [AFTER]: Finished '{action}' on Meeting with result type: {type(result)}")

    def create_meeting(self, meeting_in: MeetingCreate, owner_id: int) -> Meeting:
        meeting = Meeting.from_orm(meeting_in)
        meeting.owner_id = owner_id
        return self.save(meeting)

    def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        with Session(engine) as session:
            statement = select(Meeting).where(Meeting.id == meeting_id).options(selectinload(Meeting.segments))
            return session.exec(statement).first()

    def get_meetings(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Meeting]:
        """List meetings without heavy text columns. summary_text is truncated to 300 chars."""
        with Session(engine) as session:
            # Select lightweight columns + truncated summary
            light_cols = [
                Meeting.id,
                Meeting.title,
                Meeting.description,
                Meeting.file_path,
                Meeting.duration_seconds,
                Meeting.owner_id,
                Meeting.created_at,
                Meeting.status,
                Meeting.sub_status,
                Meeting.template_id,
                Meeting.template_name,
                Meeting.transcription_type,
                Meeting.source_type,
                Meeting.source_url,
                Meeting.youtube_title,
                Meeting.youtube_duration_seconds,
                Meeting.youtube_thumbnail_url,
                Meeting.youtube_channel,
                Meeting.summary_edited,
                func.left(Meeting.summary_text, 300).label("summary_text"),
            ]
            statement = (
                select(*light_cols)
                .where(Meeting.owner_id == owner_id)
                .order_by(Meeting.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return session.exec(statement).all()

    def update_status(self, meeting_id: int, status: str) -> Optional[Meeting]:
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.status = status
        return self.save(meeting)

    def update_transcription_type(self, meeting_id: int, transcription_type: TranscriptionType) -> Optional[Meeting]:
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.transcription_type = transcription_type
        return self.save(meeting)

    def update_meeting_type(self, meeting_id: int, meeting_type: str) -> Optional[Meeting]:
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.meeting_type = meeting_type
        return self.save(meeting)

    def update_sub_status(
        self,
        meeting_id: int,
        sub_status: str,
        status: str = "processing",
    ) -> Optional[Meeting]:
        """Update the granular processing sub-stage and optionally the top-level status.

        Also publishes a fire-and-forget event to Redis Pub/Sub for future SSE support.
        """
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.status = status
        meeting.sub_status = sub_status
        meeting = self.save(meeting)

        # Fire-and-forget Redis Pub/Sub (non-blocking, best-effort)
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.publish(f"meeting:{meeting_id}:status", sub_status)
            r.close()
        except Exception as e:
            logger.warning("Failed to publish to Redis for meeting %s: %s", meeting_id, e)

        return meeting

    def mark_completed(
        self,
        meeting_id: int,
        summary_text: str | None = None,
        action_items_text: str | None = None,
        template_id: int | None = None,
        template_name: str | None = None,
    ) -> Optional[Meeting]:
        """Mark a meeting as completed, clearing sub_status and setting final outputs."""
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.status = "completed"
        meeting.sub_status = None
        if summary_text is not None:
            meeting.summary_text = summary_text
        if action_items_text is not None:
            meeting.action_items_text = action_items_text
        if template_id is not None:
            meeting.template_id = template_id
        if template_name is not None:
            meeting.template_name = template_name
        return self.save(meeting)

    def mark_failed(self, meeting_id: int, error_message: str) -> Optional[Meeting]:
        """Mark a meeting as failed with an error message in summary_text."""
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        meeting.status = "failed"
        meeting.sub_status = None
        meeting.summary_text = f"[Error: {error_message}]"
        return self.save(meeting)

    def add_segment(self, meeting_id: int, start: float, end: float, text: str) -> TranscriptSegment:
        segment = TranscriptSegment(
            meeting_id=meeting_id,
            start_time=start,
            end_time=end,
            text=text
        )
        return self.save(segment)

    def initiate_processing(self, file_key: str) -> Optional[Meeting]:
        """
        Called by webhook handler. Looks up meeting by file_path,
        validates status is pending_upload, transitions to 'queued',
        and dispatches the event-driven Celery pipeline chain.
        Returns None if no match or already processed.
        """
        with Session(engine) as session:
            statement = select(Meeting).where(
                Meeting.file_path == file_key,
                Meeting.status == "pending_upload"
            )
            meeting = session.exec(statement).first()

        if not meeting:
            return None

        meeting.status = "queued"
        meeting = self.save(meeting)

        from app.worker import dispatch_pipeline
        dispatch_pipeline(meeting.id)

        return meeting

    def update_summary(self, meeting_id: int, summary_text: str) -> Optional[Meeting]:
        """Update the summary text. On first edit, preserve the original AI summary."""
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        if meeting.original_summary_text is None and meeting.summary_text is not None:
            meeting.original_summary_text = meeting.summary_text
        meeting.summary_text = summary_text
        meeting.summary_edited = True
        return self.save(meeting)

    def restore_summary(self, meeting_id: int) -> Optional[Meeting]:
        """Restore the original AI-generated summary."""
        meeting = self.get(Meeting, meeting_id)
        if not meeting:
            return None
        if meeting.original_summary_text is None:
            return None
        meeting.summary_text = meeting.original_summary_text
        meeting.summary_edited = False
        return self.save(meeting)

    def create_from_youtube(self, url: str, owner_id: int) -> Meeting:
        """Create a meeting record for YouTube ingestion.

        Starts at 'queued' status (skips 'pending_upload' since there's no file upload step).
        """
        meeting = Meeting(
            title="YouTube Video",
            source_type="youtube",
            source_url=url,
            status="queued",
            owner_id=owner_id,
        )
        return self.save(meeting)

    def count_active_youtube(self, owner_id: int) -> int:
        """Count active YouTube ingestions for a user (queued or processing)."""
        with Session(engine) as session:
            statement = select(Meeting).where(
                Meeting.owner_id == owner_id,
                Meeting.source_type == "youtube",
                Meeting.status.in_(["queued", "processing"]),
            )
            return len(session.exec(statement).all())

    def update_field(self, meeting_id: int, field: str, value) -> Optional[Meeting]:
        """Update a single field on a meeting."""
        with Session(engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                return None
            setattr(meeting, field, value)
            session.add(meeting)
            session.commit()
            session.refresh(meeting)
            return meeting

    def delete_meeting(self, meeting_id: int) -> bool:
        return self.delete(Meeting, meeting_id)

meeting_service = MeetingService()
