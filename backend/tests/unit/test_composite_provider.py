# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""CompositeProvider fan-out tests."""

from unittest.mock import MagicMock

from app.services.notifications.composite import CompositeProvider
from app.services.notifications.provider import NotificationEvent


def _event() -> NotificationEvent:
    return NotificationEvent(
        event_type="summary_ready",
        emoji="\U0001f4dd",
        label="Summary Ready",
        user_email="test@example.com",
    )


def test_fans_out_to_all_providers():
    p1 = MagicMock()
    p2 = MagicMock()
    composite = CompositeProvider([p1, p2])
    event = _event()
    composite.send(event)
    p1.send.assert_called_once_with(event)
    p2.send.assert_called_once_with(event)


def test_one_provider_failure_does_not_block_others():
    p1 = MagicMock()
    p1.send.side_effect = RuntimeError("boom")
    p2 = MagicMock()
    composite = CompositeProvider([p1, p2])
    # Must not raise
    composite.send(_event())
    p2.send.assert_called_once()


def test_empty_provider_list_is_noop():
    composite = CompositeProvider([])
    # Must not raise
    composite.send(_event())
