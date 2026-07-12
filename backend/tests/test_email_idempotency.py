# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Regression test for ZABT-API-3: Resend idempotency key must vary with body.

Before this fix, the key was ``meeting-{id}-summary`` — stable forever. A
re-summarized or re-transcribed meeting re-sent within 24h would hit
Resend's 24h idempotency window with a different body and fail.

The fix hashes the rendered HTML into the key so a changed body yields a
new key, while an identical resend still dedupes.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.email import ResendEmailProvider, _body_hash


def _fake_meeting(meeting_id: int, title: str, summary: str) -> SimpleNamespace:
    return SimpleNamespace(id=meeting_id, title=title, summary_text=summary)


def test_body_hash_differs_when_summary_changes() -> None:
    assert _body_hash("<p>first</p>") != _body_hash("<p>second</p>")


def test_body_hash_stable_for_identical_input() -> None:
    assert _body_hash("<p>same</p>") == _body_hash("<p>same</p>")


def test_summary_email_key_changes_with_summary_content() -> None:
    provider = ResendEmailProvider(
        api_key="key", from_email="from@x.com", app_url="https://app"
    )
    meeting_v1 = _fake_meeting(240, "Meeting 240", "summary version one")
    meeting_v2 = _fake_meeting(240, "Meeting 240", "summary version two")

    with patch("app.services.email.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "r1"}
        provider.send_summary_email("to@x.com", meeting_v1)
        provider.send_summary_email("to@x.com", meeting_v2)

    assert mock_send.call_count == 2
    key_v1 = mock_send.call_args_list[0].kwargs["options"]["idempotency_key"]
    key_v2 = mock_send.call_args_list[1].kwargs["options"]["idempotency_key"]
    assert key_v1 != key_v2, (
        "Idempotency key must change when summary body changes — "
        "otherwise Resend rejects the second send within 24h (ZABT-API-3)."
    )
    assert key_v1.startswith("meeting-240-summary-")
    assert key_v2.startswith("meeting-240-summary-")


def test_summary_email_key_stable_for_identical_resend() -> None:
    provider = ResendEmailProvider(
        api_key="key", from_email="from@x.com", app_url="https://app"
    )
    meeting = _fake_meeting(240, "Meeting 240", "unchanged summary")

    with patch("app.services.email.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "r1"}
        provider.send_summary_email("to@x.com", meeting)
        provider.send_summary_email("to@x.com", meeting)

    key_a = mock_send.call_args_list[0].kwargs["options"]["idempotency_key"]
    key_b = mock_send.call_args_list[1].kwargs["options"]["idempotency_key"]
    assert key_a == key_b, (
        "Resending the exact same body must keep the same key so Resend dedupes."
    )


def test_failure_email_key_changes_with_title() -> None:
    provider = ResendEmailProvider(
        api_key="key", from_email="from@x.com", app_url="https://app"
    )
    meeting_a = _fake_meeting(240, "Title A", None)
    meeting_b = _fake_meeting(240, "Title B", None)

    with patch("app.services.email.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "r1"}
        provider.send_failure_email("to@x.com", meeting_a, "err")
        provider.send_failure_email("to@x.com", meeting_b, "err")

    key_a = mock_send.call_args_list[0].kwargs["options"]["idempotency_key"]
    key_b = mock_send.call_args_list[1].kwargs["options"]["idempotency_key"]
    assert key_a != key_b
    assert key_a.startswith("meeting-240-failure-")
