"""Email share service — send meeting summaries to attendees via Microsoft Graph."""

import re
from datetime import datetime
from typing import List

from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.engine import engine
from app.models import (
    EmailShare,
    EmailShareStatus,
    Meeting,
    IntegrationProvider,
)
from app.services.integration import integration_service
from app.services.microsoft_graph import MicrosoftGraphClient, MicrosoftGraphError

logger = get_logger(__name__)

MAX_RECIPIENTS = 50


class EmailShareService:
    """Sends meeting summary emails via Microsoft Graph on behalf of the user."""

    # ------------------------------------------------------------------
    # HTML helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _md_to_simple_html(text: str) -> str:
        """Convert minimal markdown to inline-styled HTML for email clients.

        Handles: **bold**, - bullet items, blank-line paragraph breaks.
        """
        if not text:
            return ""

        lines = text.split("\n")
        html_parts: list[str] = []
        in_list = False

        for line in lines:
            stripped = line.strip()

            # Bullet item
            if stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    html_parts.append('<ul style="margin:8px 0;padding-left:20px;">')
                    in_list = True
                item = stripped[2:]
                item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item)
                html_parts.append(f"<li>{item}</li>")
            else:
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False

                if not stripped:
                    html_parts.append("<br>")
                else:
                    converted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
                    html_parts.append(f"<p style='margin:4px 0;'>{converted}</p>")

        if in_list:
            html_parts.append("</ul>")

        return "\n".join(html_parts)

    def build_summary_html(self, meeting: Meeting) -> str:
        """Convert meeting summary to an HTML email body with inline styles."""
        date_str = meeting.created_at.strftime("%B %d, %Y") if meeting.created_at else ""

        duration_str = ""
        if meeting.duration_seconds:
            mins = meeting.duration_seconds // 60
            duration_str = f"{mins} min" if mins else "< 1 min"

        summary_html = self._md_to_simple_html(meeting.summary_text or "")
        action_items_html = self._md_to_simple_html(meeting.action_items_text or "")

        parts: list[str] = [
            '<!DOCTYPE html><html><head><meta charset="utf-8"></head>',
            '<body style="font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;max-width:640px;margin:0 auto;padding:20px;">',
            # Header
            f'<h1 style="font-size:22px;margin-bottom:4px;">{meeting.title}</h1>',
            f'<p style="color:#666;font-size:14px;margin-top:0;">{date_str}',
        ]
        if duration_str:
            parts.append(f" &middot; {duration_str}")
        parts.append("</p>")
        parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:16px 0;">')

        # Summary
        if summary_html:
            parts.append('<h2 style="font-size:18px;margin-bottom:8px;">Summary</h2>')
            parts.append(summary_html)

        # Action items
        if action_items_html:
            parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:16px 0;">')
            parts.append('<h2 style="font-size:18px;margin-bottom:8px;">Action Items</h2>')
            parts.append(action_items_html)

        # Footer
        parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:24px 0 12px;">')
        parts.append(
            '<p style="font-size:12px;color:#999;text-align:center;">'
            'Powered by <a href="https://zabt.ai" style="color:#999;">Zabt</a></p>'
        )
        parts.append("</body></html>")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def send_to_recipients(
        self,
        meeting_id: int,
        user_id: int,
        recipient_emails: list[str],
    ) -> EmailShare:
        """Send meeting summary email to selected recipients via Microsoft Graph."""

        # 1. Load meeting
        with Session(engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                raise ValueError(f"Meeting {meeting_id} not found")

        # 2. Get Microsoft integration
        integration = integration_service.get_by_provider(
            user_id, IntegrationProvider.MICROSOFT
        )
        if not integration:
            raise ValueError("Microsoft integration not connected")

        access_token = integration_service.decrypt_token(integration.access_token)

        # 3. Create pending EmailShare record
        share = EmailShare(
            meeting_id=meeting_id,
            sender_user_id=user_id,
            integration_id=integration.id,
            recipients=[
                {"email": email, "name": "", "status": "pending"}
                for email in recipient_emails
            ],
            status=EmailShareStatus.PENDING,
        )
        with Session(engine) as session:
            session.add(share)
            session.commit()
            session.refresh(share)
            share_id = share.id

        # 4. Build email content
        date_str = meeting.created_at.strftime("%b %d, %Y") if meeting.created_at else ""
        subject = f"Meeting Notes \u2014 {meeting.title} ({date_str})"
        html_body = self.build_summary_html(meeting)

        graph_client = MicrosoftGraphClient(
            client_id=settings.MICROSOFT_CLIENT_ID,
            client_secret=settings.MICROSOFT_CLIENT_SECRET,
            tenant_id=settings.MICROSOFT_TENANT_ID,
            redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        )

        # 5. Send one email per recipient
        updated_recipients: list[dict] = []
        sent_count = 0
        fail_count = 0

        for entry in recipient_emails:
            email = entry.strip()
            try:
                await graph_client.send_email(
                    access_token=access_token,
                    to_email=email,
                    to_name="",
                    subject=subject,
                    html_body=html_body,
                )
                updated_recipients.append({"email": email, "name": "", "status": "sent"})
                sent_count += 1
                logger.info(
                    "email_share sent meeting_id=%s to=%s", meeting_id, email
                )
            except MicrosoftGraphError as exc:
                updated_recipients.append({"email": email, "name": "", "status": "failed"})
                fail_count += 1
                logger.warning(
                    "email_share failed meeting_id=%s to=%s error=%s",
                    meeting_id, email, str(exc),
                )

        # 6. Determine final status
        if fail_count == 0:
            final_status = EmailShareStatus.SENT
        elif sent_count == 0:
            final_status = EmailShareStatus.FAILED
        else:
            final_status = EmailShareStatus.PARTIALLY_FAILED

        error_msg = f"{fail_count}/{len(recipient_emails)} failed" if fail_count else None

        # 7. Update the EmailShare record
        with Session(engine) as session:
            db_share = session.get(EmailShare, share_id)
            if db_share:
                db_share.recipients = updated_recipients
                db_share.status = final_status
                db_share.sent_at = datetime.utcnow()
                db_share.error_message = error_msg
                session.add(db_share)
                session.commit()
                session.refresh(db_share)
                return db_share

        # Fallback: return the share as-is (should not happen)
        return share

    def get_shares_for_meeting(
        self, meeting_id: int, user_id: int
    ) -> List[EmailShare]:
        """List past email shares for a meeting owned by the user."""
        with Session(engine) as session:
            statement = (
                select(EmailShare)
                .where(
                    EmailShare.meeting_id == meeting_id,
                    EmailShare.sender_user_id == user_id,
                )
                .order_by(EmailShare.created_at.desc())
            )
            return list(session.exec(statement).all())


email_share_service = EmailShareService()
