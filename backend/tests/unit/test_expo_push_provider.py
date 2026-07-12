# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""ExpoPushProvider tests — verify HTTP payload and silent failure."""

from unittest.mock import MagicMock, patch

from app.services.notifications.expo_push import ExpoPushProvider
from app.services.notifications.provider import NotificationEvent


def _event(meeting_id: int | None = None) -> NotificationEvent:
    return NotificationEvent(
        event_type="summary_ready",
        emoji="\U0001f4dd",
        label="Summary Ready",
        user_email="user@example.com",
        meeting_title="Team standup",
        meeting_id=meeting_id,
    )


def test_sends_post_to_expo_endpoint_per_token():
    token_getter = MagicMock(return_value=["ExpoPushToken[a]", "ExpoPushToken[b]"])
    with patch("app.services.notifications.expo_push.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        provider = ExpoPushProvider(user_tokens_provider=token_getter)
        provider.send(_event(meeting_id=42))

    assert mock_client.post.call_count == 2
    first_call = mock_client.post.call_args_list[0]
    assert first_call.args[0] == "https://exp.host/--/api/v2/push/send"
    body = first_call.kwargs["json"]
    assert body["to"] == "ExpoPushToken[a]"
    assert body["title"] == "Summary Ready"
    assert "Team standup" in body["body"]
    assert body["data"] == {"meeting_id": 42}


def test_no_tokens_no_requests():
    token_getter = MagicMock(return_value=[])
    with patch("app.services.notifications.expo_push.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        provider = ExpoPushProvider(user_tokens_provider=token_getter)
        provider.send(_event())
    mock_client.post.assert_not_called()


def test_http_failure_is_silent():
    """Provider must never raise — notification failures should never break callers."""
    token_getter = MagicMock(return_value=["ExpoPushToken[a]"])
    with patch("app.services.notifications.expo_push.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.side_effect = RuntimeError("network down")
        mock_client_cls.return_value = mock_client
        provider = ExpoPushProvider(user_tokens_provider=token_getter)
        # Should not raise
        provider.send(_event())
