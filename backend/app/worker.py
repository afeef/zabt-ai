# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import os
import urllib.request
from math import ceil

from celery import Celery, chain
from celery.signals import worker_shutdown

from app.core.config import settings
from app.core.logging import init_sentry, init_logfire, get_logger

init_sentry()
init_logfire(service_name="zabt-worker")
logger = get_logger(__name__)

if settings.LOGFIRE_TOKEN:
    import logfire
    logfire.instrument_celery()
from app.db.engine import engine
from app.models import Meeting, TranscriptSegment, TranscriptionBackend, TranscriptionType, User
from app.services.meeting import meeting_service
from app.services.storage import storage
from app.services.transcription import get_provider, build_config
from app.services.styles import style_service
from app.services.ai_agent import summarize_transcript
from app.services.template import template_service
from app.services import analytics
from app.services.notifications import notify

from sqlmodel import Session, select


@worker_shutdown.connect
def flush_analytics(**kwargs):
    analytics.shutdown()

celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)


# ── Notification task ────────────────────────────────────────────────────────

@celery_app.task(name="send_notification", ignore_result=True)
def send_notification(
    emoji: str, label: str, user_email: str,
    meeting_title: str | None, meeting_id: int | None, extra: dict[str, str],
) -> None:
    """Deliver a notification via the configured provider. Best-effort."""
    from app.services.notifications import get_provider
    from app.services.notifications.provider import NotificationEvent

    provider = get_provider()
    if provider is None:
        return
    event = NotificationEvent(
        event_type=label,
        emoji=emoji,
        label=label,
        user_email=user_email,
        meeting_title=meeting_title,
        meeting_id=meeting_id,
        extra=extra,
    )
    provider.send(event)

# ── Shared temp directory for passing file paths between stages ──────────────
# Must be a volume shared across all worker replicas — /tmp is per-container.
TEMP_DIR = os.environ.get("TEMP_DIR", "/media/tmp")  # noqa: env override for non-docker dev
os.makedirs(TEMP_DIR, exist_ok=True)


def _temp_path_for(meeting_id: int) -> str:
    """Return the conventional temp file path for a meeting's downloaded audio."""
    return os.path.join(TEMP_DIR, f"zabt_meeting_{meeting_id}.audio")


# ── Error callback (linked to each stage via link_error) ─────────────────────

@celery_app.task(name="on_stage_failure")
def on_stage_failure(request, exc, traceback):
    """Error callback for any pipeline stage. Marks meeting as failed."""
    # The first argument of the original task is always meeting_id
    meeting_id = request.args[0] if request.args else None
    if meeting_id is None:
        logger.warning("on_stage_failure: could not determine meeting_id request_args=%s", str(request.args))
        return

    logger.info("on_stage_failure triggered meeting_id=%s exc=%s", meeting_id, str(exc))
    meeting_service.mark_failed(meeting_id, str(exc))

    # Track failure in PostHog
    try:
        failed_meeting = meeting_service.get(Meeting, meeting_id)
        if failed_meeting and failed_meeting.owner_id:
            error_reason = str(exc)[:200]
            analytics.capture(
                failed_meeting.owner_id,
                "transcription_failed",
                {
                    "meeting_id": meeting_id,
                    "error_reason": error_reason,
                    "source_type": failed_meeting.source_type,
                    "transcription_type": failed_meeting.transcription_type,
                },
            )
    except Exception:
        logger.exception("on_stage_failure analytics failed meeting_id=%s", meeting_id)

    # Send failure email (fire-and-forget — never raises)
    try:
        from app.services.email import email_service
        failed_meeting = failed_meeting or meeting_service.get(Meeting, meeting_id)
        if failed_meeting and failed_meeting.owner_id:
            with Session(engine) as session:
                user = session.get(User, failed_meeting.owner_id)
            if user and user.email:
                email_service.send_failure_email(user.email, failed_meeting, str(exc))
    except Exception:
        logger.exception("on_stage_failure email lookup failed meeting_id=%s", meeting_id)

    # Clean up temp file if it exists
    temp_path = _temp_path_for(meeting_id)
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ── Stage 1: Download ────────────────────────────────────────────────────────

@celery_app.task(name="stage_download")
def stage_download(meeting_id: int) -> int:
    """Download audio from storage. Skips download for RunPod (it fetches via presigned URL)."""
    logger.info("stage_download started meeting_id=%s", meeting_id)

    try:
        meeting = meeting_service.get(Meeting, meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found.")

        meeting_service.update_sub_status(meeting_id, "downloading")

        if not meeting.file_path:
            raise ValueError("No S3 file path associated with meeting.")

        # RunPod fetches audio directly via presigned URL — skip local download
        if settings.TRANSCRIPTION_BACKEND == TranscriptionBackend.RUNPOD:
            logger.info("stage_download skipped (RunPod mode) meeting_id=%s", meeting_id)
        else:
            download_url = storage.get_presigned_download_url(meeting.file_path)
            temp_audio_path = _temp_path_for(meeting_id)
            urllib.request.urlretrieve(download_url, temp_audio_path)

        logger.info("stage_download complete meeting_id=%s owner_id=%s", meeting_id, meeting.owner_id)
    except Exception:
        logger.exception("stage_download failed meeting_id=%s", meeting_id)
        raise

    return meeting_id


# ── Stage 2: Transcribe (includes provider's align + diarize) ────────────────


def _resolve_meeting_language_for_transcription(
    session: "Session", meeting_id: int,
) -> tuple[str | None, set[str]]:
    """Return (forced_whisper_lang, allowed_whisper_langs) for a meeting.

    forced is the whisper code of the meeting's requested language (the source
    side of a transliteration pair, if applicable). allowed is the set derived
    from the user's full preference list, with `forced` added if set.
    """
    from app.models.base import Meeting
    from app.services.languages import catalog as lang_catalog
    from app.services.languages import preferences as lang_prefs

    meeting = session.get(Meeting, meeting_id)
    if meeting is None:
        return None, set()

    forced: str | None = None
    if meeting.requested_language:
        entry = lang_catalog.get_entry(session, meeting.requested_language)
        if entry:
            if entry.transliterate_from:
                source_entry = lang_catalog.get_entry(session, entry.transliterate_from)
                forced = source_entry.whisper_lang if source_entry else None
            else:
                forced = entry.whisper_lang

    allowed: set[str] = set()
    if meeting.owner_id:
        allowed = lang_prefs.get_allowed_whisper_langs(session, meeting.owner_id)
        if forced:
            allowed.add(forced)

    return forced, allowed


@celery_app.task(name="stage_transcribe")
def stage_transcribe(meeting_id: int) -> int:
    """Run the transcription provider pipeline (transcribe + align + diarize)."""
    logger.info("stage_transcribe started meeting_id=%s", meeting_id)

    is_runpod = settings.TRANSCRIPTION_BACKEND == TranscriptionBackend.RUNPOD
    temp_audio_path = _temp_path_for(meeting_id)
    if not is_runpod and not os.path.exists(temp_audio_path):
        raise FileNotFoundError(f"Temp audio file not found: {temp_audio_path}")

    def on_transcribe_progress(stage: str):
        """Callback from provider — updates sub_status for each internal stage."""
        # Use the base stage key for sub_status (strip progress details like percentages)
        sub = stage.split(" (")[0]
        meeting_service.update_sub_status(meeting_id, sub)

    try:
        with Session(engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found.")

            # Look up user tier for provider routing
            user: User | None = session.get(User, meeting.owner_id) if meeting.owner_id else None
            user_tier = user.tier if user else None

        # Resolve language preferences for this meeting
        with Session(engine) as session:
            forced_lang, allowed_langs = _resolve_meeting_language_for_transcription(
                session, meeting_id
            )

        # Get the active provider and tier-aware config
        provider = get_provider(user_tier=user_tier)
        config = build_config(
            user_tier=user_tier,
            language=forced_lang,
            allowed_languages=allowed_langs or None,
        )
        config.storage_key = meeting.file_path  # Used by RunPodProvider for presigned URL
        config.transcription_type = meeting.transcription_type or TranscriptionType.GENERAL

        meeting_service.update_sub_status(meeting_id, "transcribing")

        # Run the transcription pipeline
        result = provider.process_audio(
            temp_audio_path,
            config=config,
            on_status_change=on_transcribe_progress,
        )

        # Write segments to DB
        with Session(engine) as session:
            # Delete old segments if this is a retried job
            old_segments = session.exec(
                select(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
            ).all()
            for old in old_segments:
                session.delete(old)

            # Write new segments from TranscriptionResult
            for seg in result.segments:
                words_dicts = [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "speaker": w.speaker_label,
                    }
                    for w in seg.words
                ]
                db_segment = TranscriptSegment(
                    meeting_id=meeting_id,
                    start_time=seg.start,
                    end_time=seg.end,
                    text=seg.text,
                    speaker=seg.speaker,
                    words=words_dicts,
                )
                session.add(db_segment)

            meeting_obj = session.get(Meeting, meeting_id)
            if meeting_obj:
                meeting_obj.transcript_text = result.text
                if result.audio_duration_seconds:
                    meeting_obj.duration_seconds = int(result.audio_duration_seconds)
            session.commit()

            # Update minutes used this month
            if user_tier is not None:
                user_obj = session.get(User, meeting.owner_id) if meeting.owner_id else None
                if user_obj:
                    user_obj.minutes_used_this_month += ceil(result.audio_duration_seconds / 60)
                    session.add(user_obj)
                    session.commit()

    except Exception as provider_exc:
        logger.exception("stage_transcribe failed meeting_id=%s", meeting_id)
        raise provider_exc

    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

    def _duration_tier(seconds: float) -> str:
        if seconds < 600:
            return "short"
        if seconds <= 3600:
            return "medium"
        return "long"

    with Session(engine) as session:
        meeting_for_analytics = session.get(Meeting, meeting_id)
        if meeting_for_analytics and meeting_for_analytics.owner_id:
            analytics.capture(
                meeting_for_analytics.owner_id,
                "transcription_completed",
                {
                    "meeting_id": meeting_id,
                    "duration_tier": _duration_tier(result.audio_duration_seconds),
                },
            )
            user_obj = session.get(User, meeting_for_analytics.owner_id)
            notify(
                "transcription_completed",
                (user_obj.email if user_obj else None) or str(meeting_for_analytics.owner_id),
                meeting_for_analytics.title,
                meeting_id=meeting_id,
                extra={"Duration": f"{ceil(result.audio_duration_seconds / 60)} min"},
            )

            # Capture language-resolution telemetry (best-effort)
            try:
                analytics.capture(
                    meeting_for_analytics.owner_id,
                    "transcription_language_resolved",
                    {
                        "meeting_id": meeting_id,
                        "requested_language": meeting_for_analytics.requested_language,
                        "forced_whisper_lang": forced_lang,
                        "detected_language": result.language,
                        "detection_inside_allowed_set": (
                            result.language in allowed_langs if allowed_langs else None
                        ),
                    },
                )
            except Exception:
                logger.warning(
                    "Failed to capture transcription_language_resolved", exc_info=True
                )

    logger.info("stage_transcribe complete meeting_id=%s", meeting_id)
    return meeting_id


# ── Stage 2b: Transliterate ──────────────────────────────────────────────────

@celery_app.task(name="stage_transliterate")
def stage_transliterate(meeting_id: int) -> int:
    """If meeting.requested_language has a transliteration target, populate
    meeting.transliterated_text with the alternate-script version."""
    from app.models.base import Meeting
    from app.services.languages import catalog as lang_catalog
    from app.services.languages.transliteration import transliterate

    logger.info("stage_transliterate started meeting_id=%s", meeting_id)

    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if meeting is None or meeting.requested_language is None:
            return meeting_id

        requested = lang_catalog.get_entry(session, meeting.requested_language)
        if requested is None:
            return meeting_id

        # Decide source / target pair
        if requested.transliterate_from:
            source_code = requested.transliterate_from
            target_code = requested.code
        else:
            target_entry = lang_catalog.transliteration_target_for(session, requested.code)
            if target_entry is None:
                return meeting_id  # nothing to do
            # Only transliterate if the user has the alternate-script entry in their preferences
            if meeting.owner_id:
                from app.services.languages import preferences as lang_prefs
                user_prefs = lang_prefs.get_preferences(session, meeting.owner_id)
                if target_entry.code not in user_prefs:
                    return meeting_id
            source_code = requested.code
            target_code = target_entry.code

        if not meeting.transcript_text:
            logger.info("stage_transliterate: no transcript_text yet for %s", meeting_id)
            return meeting_id

        try:
            roman = transliterate(
                text=meeting.transcript_text,
                source_code=source_code,
                target_code=target_code,
            )
        except Exception as exc:
            logger.exception("Transliteration failed for meeting %s", meeting_id)
            try:
                if meeting.owner_id:
                    analytics.capture(
                        meeting.owner_id,
                        "transliteration_failed",
                        {
                            "meeting_id": meeting_id,
                            "source_code": source_code,
                            "target_code": target_code,
                            "error": str(exc)[:200],
                        },
                    )
            except Exception:
                logger.warning(
                    "Failed to capture transliteration_failed meeting_id=%s", meeting_id
                )
            return meeting_id

        meeting.transliterated_text = roman
        session.add(meeting)
        session.commit()

        try:
            if meeting.owner_id:
                analytics.capture(
                    meeting.owner_id,
                    "transliteration_completed",
                    {
                        "meeting_id": meeting_id,
                        "source_code": source_code,
                        "target_code": target_code,
                        "text_length": len(roman),
                    },
                )
        except Exception:
            logger.warning(
                "Failed to capture transliteration_completed meeting_id=%s", meeting_id
            )

    return meeting_id


# ── Stage 3: Summarize ───────────────────────────────────────────────────────

@celery_app.task(name="stage_summarize")
def stage_summarize(meeting_id: int, template_id: int | None = None) -> int:
    """Run AI agent for summary + action items, then mark meeting as completed."""
    logger.info("stage_summarize started meeting_id=%s template_id=%s", meeting_id, template_id)

    meeting_service.update_sub_status(meeting_id, "summarizing")

    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found.")

    summary_text = None
    active_template = None

    if meeting.transcript_text:
        style_examples = style_service.get_style_examples()

        # Resolve template: explicit override → user default → system default
        try:
            if template_id is not None:
                active_template = template_service.get_accessible(template_id, meeting.owner_id)
            elif meeting.owner_id:
                active_template = template_service.get_active_default(meeting.owner_id)
        except Exception as e:
            print(f"[{meeting_id}] Warning: could not resolve template ({e}), falling back to system default")
            try:
                active_template = template_service.get_active_default(meeting.owner_id) if meeting.owner_id else None
            except Exception:
                active_template = None

        template_body = active_template.body if active_template else None
        summary_text = summarize_transcript(
            meeting.transcript_text,
            style_examples=style_examples,
            template_body=template_body,
            template_id=str(active_template.id) if active_template else None,
            upload_date=meeting.created_at.strftime("%B %d, %Y") if meeting.created_at else None,
        )

    # Infer a meaningful title from the summary via LLM
    inferred_title = None
    if summary_text:
        from app.services.ai_agent import infer_title
        inferred_title = infer_title(summary_text)

    meeting_service.mark_completed(
        meeting_id,
        summary_text,
        None,
        template_id=active_template.id if active_template else None,
        template_name=active_template.name if active_template else None,
    )

    if inferred_title and meeting.title:
        file_extensions = ('.m4a', '.mp3', '.wav', '.mp4', '.mov', '.webm', '.ogg', '.flac')
        if any(meeting.title.lower().endswith(ext) for ext in file_extensions):
            meeting_service.update_field(meeting_id, "title", inferred_title)
    if meeting.owner_id:
        def _word_count_tier(n: int) -> str:
            if n < 200:
                return "short"
            if n <= 500:
                return "medium"
            return "long"

        analytics.capture(
            meeting.owner_id,
            "summary_generated",
            {
                "meeting_id": meeting_id,
                "template_id": active_template.id if active_template else None,
                "word_count_tier": _word_count_tier(len(summary_text.split()) if summary_text else 0),
            },
        )

    # Send summary email and notification (fire-and-forget — never raises)
    if meeting.owner_id:
        try:
            from app.services.email import email_service
            with Session(engine) as session:
                user = session.get(User, meeting.owner_id)
            if user and user.email:
                email_service.send_summary_email(user.email, meeting)
                notify("summary_generated", user.email, meeting.title, meeting_id=meeting_id)
        except Exception:
            logger.exception("stage_summarize email lookup failed meeting_id=%s", meeting_id)

    logger.info("stage_summarize complete meeting_id=%s owner_id=%s", meeting_id, meeting.owner_id)
    return meeting_id


# ── Stage 4: Extract Meeting Intelligence ───────────────────────────────────

@celery_app.task(name="stage_extract_intelligence")
def stage_extract_intelligence(meeting_id: int) -> int:
    """Extract highlights and structured output from the meeting transcript."""
    logger.info("stage_extract_intelligence started meeting_id=%s", meeting_id)

    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting or not meeting.transcript_text:
        logger.warning("stage_extract_intelligence: no transcript for meeting_id=%s", meeting_id)
        return meeting_id

    from app.services.meeting_intelligence import intelligence_service

    meeting_type = meeting.meeting_type or "generic"

    # Update status to processing
    with Session(engine) as session:
        db_meeting = session.get(Meeting, meeting_id)
        if db_meeting:
            db_meeting.structured_output_status = "processing"
            session.add(db_meeting)
            session.commit()

    try:
        # Call 1: Extract highlights (action items, key questions, chapters)
        highlights_data = intelligence_service.extract_highlights(meeting.transcript_text)
        intelligence_service.save_highlights(meeting_id, highlights_data)

        # Call 2: Extract structured output (meeting-type-specific)
        structured_output = intelligence_service.extract_structured_output(
            meeting.transcript_text, meeting_type
        )

        # Save structured output and mark as completed
        with Session(engine) as session:
            db_meeting = session.get(Meeting, meeting_id)
            if db_meeting:
                db_meeting.structured_output = structured_output
                db_meeting.structured_output_status = "completed"
                session.add(db_meeting)
                session.commit()

        logger.info("stage_extract_intelligence complete meeting_id=%s type=%s", meeting_id, meeting_type)

    except Exception:
        logger.exception("stage_extract_intelligence failed meeting_id=%s", meeting_id)
        with Session(engine) as session:
            db_meeting = session.get(Meeting, meeting_id)
            if db_meeting:
                db_meeting.structured_output_status = "failed"
                session.add(db_meeting)
                session.commit()

    return meeting_id


# ── Email share task ────────────────────────────────────────────────────────

@celery_app.task(name="send_meeting_summary_emails", ignore_result=True)
def send_meeting_summary_emails(
    meeting_id: int, user_id: int, recipient_emails: list[str]
) -> None:
    """Send meeting summary emails via Microsoft Graph (async bridge)."""
    import asyncio
    from app.services.email_share import email_share_service

    logger.info(
        "send_meeting_summary_emails meeting_id=%s user_id=%s recipients=%d",
        meeting_id, user_id, len(recipient_emails),
    )
    asyncio.run(
        email_share_service.send_to_recipients(meeting_id, user_id, recipient_emails)
    )


@celery_app.task(name="cleanup_abandoned_uploads", ignore_result=True)
def cleanup_abandoned_uploads() -> None:
    """Abort S3 multipart uploads that were never completed (older than 24h)."""
    from app.services.storage import storage

    try:
        pending = storage.list_pending_multipart_uploads(older_than_hours=24)
        for entry in pending:
            storage.abort_multipart_upload(
                object_key=entry["Key"],
                upload_id=entry["UploadId"],
            )
            logger.info(
                "Aborted abandoned upload: key=%s upload_id=%s initiated=%s",
                entry["Key"], entry["UploadId"], entry["Initiated"],
            )
    except Exception:
        logger.warning("cleanup_abandoned_uploads failed", exc_info=True)


# ── Stage 5: Visual Breakdown ────────────────────────────────────────────────

@celery_app.task(name="stage_visual_breakdown")
def stage_visual_breakdown(meeting_id: int) -> dict:
    """Run the visual-breakdown pipeline via zabt-vision-worker. User-triggered
    per-meeting. Overwrites any prior breakdown."""
    from datetime import datetime

    from app.models import TranscriptSegment, VisualSegment
    from app.services.visual_breakdown.vision_client import VisionClient
    from app.services.visual_segments import VisualSegmentService

    logger.info("stage_visual_breakdown started meeting_id=%s", meeting_id)

    # Step 1: mark processing and capture the data we need for the worker call
    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if meeting is None:
            logger.warning("stage_visual_breakdown: meeting %s not found", meeting_id)
            return {"status": "skipped", "reason": "meeting_not_found"}
        if not meeting.file_path:
            meeting.visual_breakdown_status = "failed"
            meeting.visual_breakdown_error = "no_video_file"
            session.add(meeting)
            session.commit()
            logger.warning("stage_visual_breakdown: meeting %s has no file_path", meeting_id)
            return {"status": "failed", "reason": "no_video_file"}

        meeting.visual_breakdown_status = "processing"
        meeting.visual_breakdown_error = None
        session.add(meeting)
        session.commit()
        owner_id = meeting.owner_id
        file_path = meeting.file_path
        meeting_title = meeting.title

        transcript = session.exec(
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.start_time)
        ).all()
        transcript_payload = [
            {"speaker": t.speaker or "SPEAKER_00", "text": t.text,
             "start": t.start_time, "end": t.end_time}
            for t in transcript
        ]

    # Step 2: call the worker
    try:
        video_url = storage.get_presigned_download_url(file_path, expiration=3600)
        client = VisionClient()
        result = client.submit_and_wait({
            "video_url": video_url,
            "owner_id": str(owner_id) if owner_id is not None else "unknown",
            "meeting_id": str(meeting_id),
            "transcript": transcript_payload,
            "params": {},
        })
    except Exception as e:
        logger.exception("stage_visual_breakdown: worker call failed")
        _finalize_visual_breakdown_failure(meeting_id, f"{type(e).__name__}: {e}", None, owner_id)
        raise

    # Step 3: worker reported failure in the result body
    if result.status == "failed":
        _finalize_visual_breakdown_failure(
            meeting_id, result.error or "unknown_worker_error", result.failed_stage, owner_id,
        )
        return {"status": "failed", "failed_stage": result.failed_stage}

    # Step 4: persist segments
    worker_segments = [
        VisualSegment(
            meeting_id=meeting_id,
            sequence=s.sequence,
            start_time=s.start_time,
            end_time=s.end_time,
            screenshot_s3_key=s.screenshot_s3_key,
            caption=s.caption,
            confidence=s.confidence,
        )
        for s in result.segments
    ]
    VisualSegmentService().replace_for_meeting(meeting_id, worker_segments)

    # Step 5: finalize meeting fields
    total_duration_ms = sum(m.get("duration_ms", 0) for m in result.stage_metrics.values())
    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if meeting is None:
            logger.warning("stage_visual_breakdown: meeting %s deleted mid-run", meeting_id)
            return {"status": "skipped", "reason": "meeting_deleted_mid_run"}
        meeting.visual_breakdown_status = "completed"
        meeting.visual_breakdown_completed_at = datetime.utcnow()
        meeting.visual_raw_output_s3_key = result.raw_output_s3_key
        meeting.visual_breakdown_model = result.model
        meeting.visual_breakdown_params = result.params
        meeting.visual_breakdown_run_count = (meeting.visual_breakdown_run_count or 0) + 1
        session.add(meeting)
        session.commit()

    # Step 6: PostHog — high-level event + per-stage events
    if owner_id is not None:
        analytics.capture(
            owner_id,
            "visual_breakdown_completed",
            {
                "meeting_id": meeting_id,
                "segment_count": len(result.segments),
                "model": result.model,
                "total_duration_ms": total_duration_ms,
            },
        )
        for stage_name, metrics in result.stage_metrics.items():
            analytics.capture(
                owner_id,
                "visual_breakdown_stage_completed",
                {"meeting_id": meeting_id, "stage": stage_name, **metrics},
            )

    # Step 7: Telegram (via existing notify dispatcher — event kind registered in Task 10)
    try:
        user_obj = None
        with Session(engine) as session:
            if owner_id is not None:
                user_obj = session.get(User, owner_id)
        notify(
            "visual_breakdown_completed",
            (user_obj.email if user_obj else None) or str(owner_id or ""),
            meeting_title,
            meeting_id=meeting_id,
            extra={"segment_count": str(len(result.segments))},
        )
    except Exception:
        logger.warning("stage_visual_breakdown: notify failed", exc_info=True)

    logger.info(
        "stage_visual_breakdown done meeting_id=%s segments=%s",
        meeting_id, len(result.segments),
    )
    return {"status": "completed", "segment_count": len(result.segments)}


def _finalize_visual_breakdown_failure(
    meeting_id: int,
    error: str,
    failed_stage: str | None,
    owner_id: int | None,
) -> None:
    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if meeting is not None:
            meeting.visual_breakdown_status = "failed"
            meeting.visual_breakdown_error = (error or "")[:500]
            session.add(meeting)
            session.commit()

    if owner_id is not None:
        analytics.capture(
            owner_id,
            "visual_breakdown_failed",
            {
                "meeting_id": meeting_id,
                "error_reason": (error or "")[:100],
                "failed_stage": failed_stage,
            },
        )


celery_app.conf.beat_schedule = {
    "cleanup-abandoned-uploads-daily": {
        "task": "cleanup_abandoned_uploads",
        "schedule": 86400.0,
    },
}
celery_app.conf.timezone = "UTC"


# ── Pipeline dispatch helper ─────────────────────────────────────────────────

def dispatch_pipeline(meeting_id: int):
    """Build and dispatch the Celery chain for processing a meeting."""
    pipeline = chain(
        stage_download.s(meeting_id).set(link_error=[on_stage_failure.s()]),
        stage_transcribe.s().set(link_error=[on_stage_failure.s()]),
        stage_transliterate.s().set(link_error=[on_stage_failure.s()]),
        stage_summarize.s().set(link_error=[on_stage_failure.s()]),
        stage_extract_intelligence.s().set(link_error=[on_stage_failure.s()]),
    )
    pipeline.apply_async()


# ── Stage 0 (YouTube): Download from YouTube ────────────────────────────────

@celery_app.task(name="stage_youtube_download")
def stage_youtube_download(meeting_id: int) -> int:
    """Download audio from YouTube, extract metadata, store in object storage.

    This replaces stage_download for YouTube-sourced meetings. After completion,
    the existing stage_transcribe → stage_summarize chain runs unchanged.
    """
    from app.services.youtube import (
        extract_metadata,
        download_audio,
        YouTubeError,
        DurationExceededError,
    )

    logger.info("stage_youtube_download started meeting_id=%s", meeting_id)

    meeting = meeting_service.get(Meeting, meeting_id)
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found.")

    if not meeting.source_url:
        raise ValueError("No YouTube URL associated with meeting.")

    meeting_service.update_sub_status(meeting_id, "downloading_youtube")

    try:
        # Step 1: Extract metadata (title, duration, thumbnail, channel)
        metadata = extract_metadata(meeting.source_url)

        # Step 2: Validate duration (max 4 hours = 14400 seconds)
        if metadata["duration"] > 14400:
            raise DurationExceededError(
                "Video exceeds the maximum duration of 4 hours."
            )

        # Step 3: Update meeting with YouTube metadata
        with Session(engine) as session:
            m = session.get(Meeting, meeting_id)
            if m:
                m.title = metadata["title"]
                m.youtube_title = metadata["title"]
                m.youtube_duration_seconds = metadata["duration"]
                m.youtube_thumbnail_url = metadata["thumbnail"]
                m.youtube_channel = metadata["channel"]
                session.add(m)
                session.commit()

        # Step 4: Download audio to temp directory
        video_id = metadata["id"]
        audio_path = download_audio(meeting.source_url, TEMP_DIR, video_id)

        # Step 5: Upload audio to object storage
        file_key = f"users/{meeting.owner_id}/meetings/yt_{video_id}.mp3"
        with open(audio_path, "rb") as f:
            storage.upload_file(f.read(), file_key, "audio/mpeg")

        # Step 6: Update meeting file_path and set temp path for transcription
        with Session(engine) as session:
            m = session.get(Meeting, meeting_id)
            if m:
                m.file_path = file_key
                session.add(m)
                session.commit()

        # Move/rename to the conventional temp path for stage_transcribe
        conventional_path = _temp_path_for(meeting_id)
        os.rename(audio_path, conventional_path)

        logger.info(
            "stage_youtube_download complete meeting_id=%s video_id=%s duration=%s",
            meeting_id,
            video_id,
            metadata["duration"],
        )

        if meeting.owner_id:
            analytics.capture(
                meeting.owner_id,
                "youtube_download_completed",
                {
                    "meeting_id": meeting_id,
                    "duration_seconds": metadata["duration"],
                    "video_id": video_id,
                },
            )

    except YouTubeError:
        raise  # Let link_error handler catch it with the descriptive message
    except Exception:
        logger.exception("stage_youtube_download failed meeting_id=%s", meeting_id)
        raise

    return meeting_id


def dispatch_youtube_pipeline(meeting_id: int):
    """Build and dispatch the Celery chain for YouTube ingestion.

    Uses stage_youtube_download instead of stage_download, then feeds
    into the existing stage_transcribe → stage_transliterate → stage_summarize → stage_extract_intelligence chain.
    """
    pipeline = chain(
        stage_youtube_download.s(meeting_id).set(link_error=[on_stage_failure.s()]),
        stage_transcribe.s().set(link_error=[on_stage_failure.s()]),
        stage_transliterate.s().set(link_error=[on_stage_failure.s()]),
        stage_summarize.s().set(link_error=[on_stage_failure.s()]),
        stage_extract_intelligence.s().set(link_error=[on_stage_failure.s()]),
    )
    pipeline.apply_async()
