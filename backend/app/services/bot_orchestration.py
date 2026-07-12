# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Bot orchestration — dispatch bots to join meetings, handle callbacks."""

from datetime import datetime
from typing import Optional

import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.engine import engine
from app.models.bot_job import BotJob, BotJobStatus
from app.models.calendar_event import BotStatus, CalendarEvent

logger = get_logger(__name__)


class BotOrchestrationService:
    def __init__(self):
        self.bot_worker_url = settings.BOT_WORKER_URL

    async def dispatch_bot(self, calendar_event: CalendarEvent) -> BotJob:
        """Create a BotJob and dispatch to the bot worker."""
        logger.debug(
            "dispatch_bot: event_id=%s join_url_preview=%.50s auto_join=%s",
            calendar_event.id,
            calendar_event.join_url[:50] if calendar_event.join_url else None,
            calendar_event.auto_join,
        )
        
        if not calendar_event.join_url:
            raise ValueError(f"CalendarEvent {calendar_event.id} has no join_url")

        # 1. Create BotJob record (status=queued)
        bot_job = BotJob(
            calendar_event_id=calendar_event.id,
            join_url=calendar_event.join_url,
            status=BotJobStatus.QUEUED,
        )
        with Session(engine) as session:
            session.add(bot_job)
            session.commit()
            session.refresh(bot_job)

        # 2. POST to bot worker
        # Use internal Docker network URL for callback (bot worker → api service)
        callback_url = "http://api:8000/api/v1/integrations/bot-callback"
        payload = {
            "join_url": calendar_event.join_url,
            "event_id": calendar_event.id,
            "bot_job_id": bot_job.id,
            "callback_url": callback_url,
        }

        try:
            logger.debug(
                "dispatch_bot: POSTing to bot_worker_url=%s payload_event_id=%s",
                self.bot_worker_url,
                calendar_event.id,
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.bot_worker_url}/jobs",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            logger.debug(
                "dispatch_bot: bot worker response worker_instance_id=%s",
                data.get("worker_instance_id"),
            )
            
            # 3. Update BotJob with worker_instance_id
            with Session(engine) as session:
                job = session.get(BotJob, bot_job.id)
                if job:
                    job.worker_instance_id = data.get("worker_instance_id")
                    job.status = BotJobStatus.JOINING
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                    session.commit()
                    session.refresh(job)
                    bot_job = job

            # 4. Update CalendarEvent bot_status to "scheduled"
            with Session(engine) as session:
                event = session.get(CalendarEvent, calendar_event.id)
                if event:
                    event.bot_status = BotStatus.SCHEDULED
                    event.updated_at = datetime.utcnow()
                    session.add(event)
                    session.commit()

        except Exception:
            logger.exception(
                "dispatch_bot: failed to dispatch bot for event %s", calendar_event.id
            )
            # Mark job as failed AND reset event bot_status to idle for retry
            with Session(engine) as session:
                job = session.get(BotJob, bot_job.id)
                if job:
                    job.status = BotJobStatus.FAILED
                    job.error_message = "Failed to dispatch to bot worker"
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                event = session.get(CalendarEvent, calendar_event.id)
                if event:
                    event.bot_status = BotStatus.IDLE
                    event.updated_at = datetime.utcnow()
                    session.add(event)
                session.commit()
            raise

        logger.info(
            "dispatch_bot: dispatched bot_job=%s for event=%s",
            bot_job.id,
            calendar_event.id,
        )
        return bot_job

    def handle_callback(self, result: dict) -> None:
        """Handle callback from bot worker when meeting ends."""
        bot_job_id = result.get("bot_job_id")
        event_id = result.get("event_id")
        callback_status = result.get("status", "failed")

        # 1. Find BotJob
        with Session(engine) as session:
            if bot_job_id:
                job = session.get(BotJob, bot_job_id)
            elif event_id:
                job = session.exec(
                    select(BotJob)
                    .where(BotJob.calendar_event_id == event_id)
                    .order_by(BotJob.created_at.desc())
                ).first()
            else:
                logger.warning("handle_callback: no bot_job_id or event_id in payload")
                return

            if not job:
                logger.warning(
                    "handle_callback: BotJob not found bot_job_id=%s event_id=%s",
                    bot_job_id,
                    event_id,
                )
                return

            # 2. Update BotJob with results
            job.audio_url = result.get("audio_url")
            job.duration_seconds = result.get("duration_seconds")
            job.speakers_count = result.get("speakers_count")
            job.attendees = result.get("attendees", [])
            job.ended_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()

            if callback_status == "completed":
                job.status = BotJobStatus.COMPLETED
            else:
                job.status = BotJobStatus.FAILED
                job.error_message = result.get("error_message", "Unknown error")

            session.add(job)
            session.commit()

            calendar_event_id = job.calendar_event_id

        # 3. Update CalendarEvent status
        with Session(engine) as session:
            event = session.get(CalendarEvent, calendar_event_id)
            if event:
                if callback_status == "completed":
                    event.bot_status = BotStatus.COMPLETED
                else:
                    # Reset to idle so the event can be retried on next dispatch
                    event.bot_status = BotStatus.IDLE
                event.updated_at = datetime.utcnow()
                session.add(event)
                session.commit()

        # 4. If completed and audio_url present, create Meeting and dispatch transcription
        if callback_status == "completed" and result.get("audio_url"):
            self._create_meeting_and_transcribe(calendar_event_id, result)

        logger.info(
            "handle_callback: processed bot_job_id=%s status=%s",
            bot_job_id,
            callback_status,
        )

    def _create_meeting_and_transcribe(
        self, calendar_event_id: int, result: dict
    ) -> None:
        """Create a Meeting record from bot recording and dispatch the transcription pipeline."""
        from app.models import Meeting
        from app.services.meeting import meeting_service

        with Session(engine) as session:
            event = session.get(CalendarEvent, calendar_event_id)
            if not event:
                logger.warning(
                    "_create_meeting_and_transcribe: event %s not found",
                    calendar_event_id,
                )
                return

            # Create Meeting record
            meeting = Meeting(
                title=event.title,
                owner_id=event.user_id,
                file_path=result.get("audio_url", ""),
                source_type="bot",
                status="processing",
            )
            session.add(meeting)
            session.commit()
            session.refresh(meeting)

            # Link meeting to calendar event
            event.meeting_id = meeting.id
            event.updated_at = datetime.utcnow()
            session.add(event)
            session.commit()

            meeting_id = meeting.id

        # Dispatch transcription pipeline
        from app.worker import dispatch_pipeline

        dispatch_pipeline(meeting_id)
        logger.info(
            "_create_meeting_and_transcribe: dispatched pipeline meeting_id=%s event_id=%s",
            meeting_id,
            calendar_event_id,
        )

    def get_jobs_for_event(self, event_id: int) -> list[BotJob]:
        """List bot jobs for a calendar event."""
        with Session(engine) as session:
            jobs = session.exec(
                select(BotJob)
                .where(BotJob.calendar_event_id == event_id)
                .order_by(BotJob.created_at.desc())
            ).all()
            return list(jobs)

    def get_job(self, job_id: int) -> Optional[BotJob]:
        """Get a single bot job by ID."""
        with Session(engine) as session:
            return session.get(BotJob, job_id)


bot_orchestration_service = BotOrchestrationService()
