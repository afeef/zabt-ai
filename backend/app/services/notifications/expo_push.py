# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Expo Push Notifications provider — fans out to APNs + FCM via Expo's service."""

from __future__ import annotations

import logging
from typing import Callable

import httpx

from app.services.notifications.provider import NotificationEvent, NotificationProvider

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class ExpoPushProvider(NotificationProvider):
    """Sends push notifications to registered mobile devices via Expo's service.

    The provider does not know about the database directly. It is constructed
    with a `user_tokens_provider` callable so tests can pass a mock, and the
    factory in __init__.py passes the real DB-backed lookup.
    """

    def __init__(
        self,
        user_tokens_provider: Callable[[str], list[str]],
        access_token: str | None = None,
    ) -> None:
        """
        Args:
            user_tokens_provider: callable(user_email) -> list of Expo push tokens.
            access_token: optional EXPO_ACCESS_TOKEN for enhanced delivery receipts.
        """
        self._get_tokens = user_tokens_provider
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        self._client = httpx.Client(timeout=5.0, headers=headers)

    def send(self, event: NotificationEvent) -> None:
        """Send a push notification. Never raises exceptions."""
        try:
            tokens = self._get_tokens(event.user_email)
            if not tokens:
                return
            for token in tokens:
                self._send_single(token, event)
        except Exception:
            logger.warning("Expo push notification failed", exc_info=True)

    def _send_single(self, token: str, event: NotificationEvent) -> None:
        body_lines = []
        if event.meeting_title:
            body_lines.append(event.meeting_title)
        for key, value in event.extra.items():
            body_lines.append(f"{key}: {value}")

        payload = {
            "to": token,
            "title": event.label,
            "body": "\n".join(body_lines) or event.label,
            "sound": "default",
            "priority": "high",
            "data": {"meeting_id": event.meeting_id} if event.meeting_id else {},
        }

        try:
            self._client.post(EXPO_PUSH_URL, json=payload)
        except Exception:
            logger.warning("Expo push delivery failed for one token", exc_info=True)
