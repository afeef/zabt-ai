"""Bot worker HTTP server — accepts jobs, manages browser-based meeting sessions."""

import asyncio
import os
import uuid
from threading import Lock

import httpx
from fastapi import FastAPI

from src.config import settings
from src.logging import get_logger, init_sentry, init_logfire
from src.models import BotJobInput, BotJobResult, BotJobStatus
from src.session import MeetingSession
from src.browser import launch_browser, join_teams_meeting, wait_for_meeting_end
from src.storage import upload_audio

init_sentry()
init_logfire()

logger = get_logger(__name__)

# Initialize PostHog for analytics
try:
    from posthog import PostHog
    if settings.POSTHOG_API_KEY:
        posthog_client = PostHog(
            api_key=settings.POSTHOG_API_KEY,
            host=settings.POSTHOG_HOST or "https://app.posthog.com",
        )
        logger.info("PostHog initialized for analytics")
    else:
        posthog_client = None
except ImportError:
    posthog_client = None


def capture_event(event_name: str, properties: dict) -> None:
    """Capture an event to PostHog if configured."""
    if posthog_client:
        try:
            posthog_client.capture(
                distinct_id=settings.WORKER_ID,
                event=event_name,
                properties=properties,
            )
        except Exception:
            # Don't let analytics failures break the app
            pass

app = FastAPI(title="Zabt Bot Worker", version="0.2.0")

# In-memory job tracking
_jobs: dict[str, dict] = {}
_jobs_lock = Lock()


@app.get("/health")
def health():
    with _jobs_lock:
        active = sum(1 for j in _jobs.values() if j["status"] in ("joining", "recording", "waiting_lobby"))
    return {"status": "ok", "worker_id": settings.WORKER_ID, "active_jobs": active}


@app.post("/jobs")
async def create_job(input: BotJobInput):
    job_id = str(uuid.uuid4())
    
    logger.info(
        "create_job: event_id=%s bot_job_id=%s join_url_preview=%.50s callback_url=%s",
        input.event_id,
        input.bot_job_id,
        input.join_url[:50] if input.join_url else None,
        input.callback_url,
    )
    
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "queued",
            "input": input,
            "result": None,
            "error": None,
        }

    task = asyncio.create_task(_run_job(job_id, input))
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    logger.debug("create_job: job_id=%s queued", job_id)
    
    # Capture PostHog event
    capture_event("bot_job_created", {
        "event_id": input.event_id,
        "bot_job_id": input.bot_job_id,
        "job_id": job_id,
        "worker_id": settings.WORKER_ID,
    })
    
    return BotJobStatus(id=job_id, status="queued")


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return BotJobStatus(id=job_id, status="not_found", error="Job not found")
    return BotJobStatus(
        id=job_id,
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )


async def _run_job(job_id: str, input: BotJobInput) -> None:
    """Background task: launch browser, join meeting, record audio, upload, callback."""
    session: MeetingSession | None = None
    pw = None
    browser = None

    try:
        with logfire.span("run_bot_job job_id={job_id} event_id={event_id}", 
                          job_id=job_id, event_id=input.event_id):
            
            logger.debug("Running job %s for event_id=%s", job_id, input.event_id)
            
            # 1. Create meeting session (Xvfb + PulseAudio)
            _update_status(job_id, "joining")
            session = MeetingSession(job_id)
            session.start()
            logger.debug("Meeting session started: display=%s audio_path=%s", 
                        session.display_env.get("DISPLAY"), session.audio_path)

            # 2. Launch browser on the session's display + audio sink
            pw, browser = await launch_browser(session.display_env)
            logger.info("Browser launched for job %s", job_id)

            # 3. Join the Teams meeting
            page = await join_teams_meeting(
                browser,
                input.join_url,
                settings.BOT_DISPLAY_NAME,
                job_id,
            )
            logger.info("Joined Teams meeting for job %s", job_id)

            # 4. Start recording
            _update_status(job_id, "recording")
            session.start_recording()
            logger.info("Recording started for job %s", job_id)

            # 5. Wait for meeting to end (with lobby timeout)
            end_state = await wait_for_meeting_end(
                page, job_id, settings.MAX_MEETING_DURATION_HOURS, settings.LOBBY_TIMEOUT_SECONDS
            )
            logger.info("Meeting ended for job %s: %s", job_id, end_state)

            # 6. Stop recording
            duration = session.stop_recording()
            logger.info("Recording stopped for job %s: %.1fs", job_id, duration)

            # 7. Upload to S3
            _update_status(job_id, "uploading")
            s3_key = f"bot-recordings/{job_id}.wav"
            if os.path.exists(session.audio_path) and os.path.getsize(session.audio_path) > 100:
                upload_audio(session.audio_path, s3_key)
                logger.info("Audio uploaded to S3: key=%s", s3_key)
            else:
                file_size = os.path.getsize(session.audio_path) if os.path.exists(session.audio_path) else 0
                logger.warning(
                    "No audio captured for job %s (file exists=%d, size=%d bytes)",
                    job_id,
                    os.path.exists(session.audio_path),
                    file_size,
                )
                s3_key = ""

            # 8. Build result
            result = BotJobResult(
                event_id=input.event_id,
                bot_job_id=input.bot_job_id,
                audio_url=s3_key,
                duration_seconds=int(duration),
                status="completed" if s3_key else "failed",
                error_message="" if s3_key else "No audio captured",
            )
            _update_status(job_id, "completed", result=result)

            # 9. Callback to main backend
            logger.info("Sending callback for job %s to %s", job_id, input.callback_url)
            await _send_callback(input.callback_url, result)
            
            # Capture PostHog event on completion
            capture_event("bot_job_completed", {
                "event_id": input.event_id,
                "bot_job_id": input.bot_job_id,
                "job_id": job_id,
                "worker_id": settings.WORKER_ID,
                "status": result.status,
                "duration_seconds": int(duration),
                "audio_url": s3_key or "",
            })

    except Exception as e:
        logger.exception(
            "Bot job failed job_id=%s event_id=%s bot_job_id=%s error=%s",
            job_id,
            input.event_id,
            input.bot_job_id,
            str(e)[:200],
        )
        
        # Capture PostHog event on failure
        capture_event("bot_job_failed", {
            "event_id": input.event_id,
            "bot_job_id": input.bot_job_id,
            "job_id": job_id,
            "worker_id": settings.WORKER_ID,
            "error": str(e)[:500],
        })
        
        _update_status(job_id, "failed", error=str(e))

        result = BotJobResult(
            event_id=input.event_id,
            bot_job_id=input.bot_job_id,
            status="failed",
            error_message=str(e)[:500],
        )
        await _send_callback(input.callback_url, result)

    finally:
        # Cleanup
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if pw:
            try:
                await pw.stop()
            except Exception:
                pass
        if session:
            session.stop()
            # Clean up audio file
            if os.path.exists(session.audio_path):
                try:
                    os.unlink(session.audio_path)
                except Exception:
                    pass


async def _send_callback(callback_url: str, result: BotJobResult) -> None:
    """Send result callback to the main backend with retry."""
    url = callback_url  # Already a full URL from the orchestration service
    
    logger.debug(
        "Sending callback: event_id=%s bot_job_id=%s status=%s audio_url=%s",
        result.event_id,
        result.bot_job_id,
        result.status,
        result.audio_url or "",
    )
    
    for attempt in range(3):
        try:
            with logfire.span("send_callback_attempt attempt={attempt} event_id={event_id}", 
                              attempt=attempt + 1, event_id=result.event_id):
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(url, json=result.model_dump())
                    logger.info(
                        "Callback sent to %s: event_id=%s status=%d",
                        url,
                        result.event_id,
                        resp.status_code,
                    )
                    
                    # Capture PostHog callback success event
                    if resp.status_code == 200:
                        capture_event("callback_sent_successfully", {
                            "event_id": result.event_id,
                            "bot_job_id": result.bot_job_id,
                            "worker_id": settings.WORKER_ID,
                            "attempt": attempt + 1,
                        })
                    
                    return
        except Exception as e:
            if attempt < 2:
                wait = 2 * (2 ** attempt)
                logger.warning(
                    "Callback attempt %d/3 failed for event_id=%s, retrying in %ds: %s",
                    attempt + 1,
                    result.event_id,
                    wait,
                    str(e)[:100],
                )
                await asyncio.sleep(wait)
            else:
                logger.exception(
                    "Callback failed after 3 attempts for event_id=%s url=%s",
                    result.event_id,
                    url,
                )
                
                # Capture PostHog callback failure event
                capture_event("callback_failed", {
                    "event_id": result.event_id,
                    "bot_job_id": result.bot_job_id,
                    "worker_id": settings.WORKER_ID,
                    "url": url[:100],  # Truncate long URLs
                    "error": str(e)[:200],
                })


def _update_status(
    job_id: str,
    status: str,
    result: BotJobResult | None = None,
    error: str | None = None,
) -> None:
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = status
            if result:
                _jobs[job_id]["result"] = result
            if error:
                _jobs[job_id]["error"] = error
