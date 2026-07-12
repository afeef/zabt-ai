# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Composite notification provider — fans out to multiple channels."""

from __future__ import annotations

import logging
from typing import Sequence

from app.services.notifications.provider import NotificationEvent, NotificationProvider

logger = logging.getLogger(__name__)


class CompositeProvider(NotificationProvider):
    """Dispatches to all configured providers. Each failure is isolated."""

    def __init__(self, providers: Sequence[NotificationProvider]) -> None:
        self._providers = list(providers)

    def send(self, event: NotificationEvent) -> None:
        for provider in self._providers:
            try:
                provider.send(event)
            except Exception:
                logger.warning(
                    "Provider %s failed for event %s",
                    type(provider).__name__,
                    event.event_type,
                    exc_info=True,
                )
