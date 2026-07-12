"""Telegram notification provider using the Bot API."""

from __future__ import annotations

import logging

import httpx

from app.services.notifications.provider import NotificationEvent, NotificationProvider

logger = logging.getLogger(__name__)


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


class TelegramProvider(NotificationProvider):
    """Sends notifications via the Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._chat_id = chat_id
        self._client = httpx.Client(timeout=5.0)

    def send(self, event: NotificationEvent) -> None:
        """Send a Telegram message. Never raises exceptions."""
        try:
            lines = [
                f"{event.emoji} *{_escape_md(event.label)}*",
                f"\U0001f4e7 {_escape_md(event.user_email)}",
            ]
            if event.meeting_title:
                lines.append(f"\U0001f4dd {_escape_md(event.meeting_title)}")
            for key, value in event.extra.items():
                lines.append(f"{_escape_md(key)}: {_escape_md(value)}")
            lines.append(
                f"\U0001f550 {_escape_md(event.timestamp.strftime('%Y-%m-%d %H:%M UTC'))}"
            )

            self._client.post(
                self._url,
                json={
                    "chat_id": self._chat_id,
                    "text": "\n".join(lines),
                    "parse_mode": "MarkdownV2",
                },
            )
        except Exception:
            logger.warning("Telegram notification failed", exc_info=True)
