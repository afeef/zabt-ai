"""Owner notification system.

Exposes a thin notify() function so consuming code never imports a specific
provider directly. All calls fail silently — notifications must never break
application or worker flow. The actual delivery is offloaded to a Celery task.
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Event type registry
_EVENTS: dict[str, tuple[str, str]] = {
    "new_user": ("\U0001f195", "New User"),
    "user_login": ("\U0001f464", "User Login"),
    "upload_started": ("\U0001f4e4", "Upload Started"),
    "transcription_completed": ("\U0001f399\ufe0f", "Transcription Done"),
    "summary_generated": ("\U0001f4dd", "Summary Generated"),
    "pdf_exported": ("\U0001f4c4", "PDF Downloaded"),
    "visual_breakdown_completed": ("\U0001f4f8", "Visual Breakdown Ready"),
}

from app.services.notifications.provider import NotificationProvider

_provider_name = settings.NOTIFICATION_PROVIDER.lower().strip()
_enabled = bool(_provider_name)

if _enabled:
    logger.info("Notifications enabled (provider=%s)", _provider_name)
else:
    logger.info("Notifications disabled (NOTIFICATION_PROVIDER not set)")


def get_provider() -> NotificationProvider | None:
    """Return the configured notification provider, or None if disabled."""
    if not _provider_name:
        return None

    if _provider_name == "telegram":
        from app.services.notifications.telegram import TelegramProvider
        return TelegramProvider(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)

    if _provider_name == "expo_push":
        return _build_expo_push_provider()

    if _provider_name == "multi":
        from app.services.notifications.composite import CompositeProvider
        providers: list[NotificationProvider] = []
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            from app.services.notifications.telegram import TelegramProvider
            providers.append(TelegramProvider(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID))
        providers.append(_build_expo_push_provider())
        return CompositeProvider(providers)

    logger.warning("Unknown NOTIFICATION_PROVIDER: %s", _provider_name)
    return None


def _build_expo_push_provider() -> "NotificationProvider":
    """Builds ExpoPushProvider with a real DB-backed token lookup."""
    from app.services.notifications.expo_push import ExpoPushProvider
    from app.db.engine import engine
    from app.models import Device, User
    from sqlmodel import Session, select

    def lookup_tokens(user_email: str) -> list[str]:
        with Session(engine) as db:
            user = db.exec(select(User).where(User.email == user_email)).first()
            if not user:
                return []
            devices = db.exec(select(Device).where(Device.user_id == user.id)).all()
            return [d.expo_push_token for d in devices]

    return ExpoPushProvider(
        user_tokens_provider=lookup_tokens,
        access_token=settings.EXPO_ACCESS_TOKEN,
    )


def notify(
    event_type: str,
    user_email: str,
    meeting_title: str | None = None,
    meeting_id: int | None = None,
    extra: dict[str, str] | None = None,
) -> None:
    """Fire a notification event via Celery task. Silently no-ops if unconfigured."""
    if not _enabled:
        return
    emoji, label = _EVENTS.get(event_type, ("\u2139\ufe0f", event_type))
    try:
        from app.worker import send_notification
        send_notification.delay(emoji, label, user_email, meeting_title, meeting_id, extra or {})
    except Exception:
        logger.warning("Failed to dispatch notification task", exc_info=True)
