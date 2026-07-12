from __future__ import annotations
import hashlib
from typing import Protocol, runtime_checkable

import resend

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
from app.models import Meeting


def _body_hash(html: str) -> str:
    """Short, stable hash of the email body.

    Scopes Resend idempotency to the exact body so a re-summarized or
    re-transcribed meeting can be re-sent without colliding with the
    previous send's 24h idempotency window (ZABT-API-3).
    """
    return hashlib.sha1(html.encode("utf-8")).hexdigest()[:12]


# ── Abstract interface (satisfies Constitution Principle IX) ──────────────────

@runtime_checkable
class EmailProvider(Protocol):
    def send_summary_email(self, to: str, meeting: Meeting) -> None: ...
    def send_failure_email(self, to: str, meeting: Meeting, error: str) -> None: ...


# ── Concrete implementation ───────────────────────────────────────────────────

class ResendEmailProvider:
    """Sends transactional emails via Resend. Fails silently if API key is absent."""

    def __init__(self, api_key: str, from_email: str, app_url: str) -> None:
        self._from_email = from_email
        self._app_url = app_url
        if api_key:
            resend.api_key = api_key
        self._enabled = bool(api_key)

    def send_summary_email(self, to: str, meeting: Meeting) -> None:
        if not self._enabled:
            logger.info("email_skipped: no RESEND_API_KEY meeting_id=%s", meeting.id)
            return
        meeting_url = f"{self._app_url}/meetings/{meeting.id}"
        summary = meeting.summary_text or "No summary was generated."
        html = f"""
        <h2>Your meeting summary is ready</h2>
        <p><strong>{meeting.title}</strong></p>
        <hr/>
        <div style="white-space:pre-wrap">{summary}</div>
        <hr/>
        <p><a href="{meeting_url}">View in Zabt &rarr;</a></p>
        """
        try:
            resp = resend.Emails.send(
                {"from": self._from_email, "to": [to],
                 "subject": f"Summary: {meeting.title}", "html": html},
                options={"idempotency_key": f"meeting-{meeting.id}-summary-{_body_hash(html)}"},
            )
            logger.info("summary_email_sent meeting_id=%s resend_id=%s", meeting.id, resp["id"])
        except Exception:
            logger.exception("summary_email_failed meeting_id=%s to=%s", meeting.id, to)

    def send_failure_email(self, to: str, meeting: Meeting, error: str) -> None:
        if not self._enabled:
            logger.info("email_skipped: no RESEND_API_KEY meeting_id=%s", meeting.id)
            return
        meeting_url = f"{self._app_url}/meetings/{meeting.id}"
        html = f"""
        <h2>Processing failed for your meeting</h2>
        <p><strong>{meeting.title}</strong> could not be processed.</p>
        <p>You can retry from the meeting page or contact support.</p>
        <p><a href="{meeting_url}">View in Zabt &rarr;</a></p>
        """
        try:
            resp = resend.Emails.send(
                {"from": self._from_email, "to": [to],
                 "subject": f"Processing failed: {meeting.title}", "html": html},
                options={"idempotency_key": f"meeting-{meeting.id}-failure-{_body_hash(html)}"},
            )
            logger.info("failure_email_sent meeting_id=%s resend_id=%s", meeting.id, resp["id"])
        except Exception:
            logger.exception("failure_email_failed meeting_id=%s to=%s", meeting.id, to)


# ── Singleton ─────────────────────────────────────────────────────────────────

email_service: EmailProvider = ResendEmailProvider(
    api_key=settings.RESEND_API_KEY,
    from_email=settings.RESEND_FROM_EMAIL,
    app_url=settings.APP_URL,
)
