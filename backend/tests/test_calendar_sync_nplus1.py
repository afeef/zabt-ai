# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
"""Regression tests for ZABT-API-1Z / ZABT-API-1V.

- ZABT-API-1V: future-events re-query per integration (redundant).
- ZABT-API-1Z: per-integration batch load repeated across integrations.

The fix collapses both into a single ``WHERE integration_id IN (...)``
query at the Celery task level, with _upsert_events consuming the
pre-loaded slice and filtering future events in memory.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.models.calendar_event import BotStatus, CalendarEvent
from app.models.integration import Integration, IntegrationProvider
from app.services.calendar_sync import CalendarSyncService


def _make_integration(integration_id: int) -> Integration:
    integration = MagicMock(spec=Integration)
    integration.id = integration_id
    integration.user_id = 1
    return integration


def _make_stored_event(**overrides) -> CalendarEvent:
    now = datetime.utcnow()
    defaults = {
        "id": 1,
        "user_id": 1,
        "integration_id": 1,
        "provider": "microsoft",
        "external_event_id": "ext-1",
        "title": "Original Title",
        "start_time": now + timedelta(hours=1),
        "end_time": now + timedelta(hours=2),
        "attendees": [],
        "bot_status": BotStatus.IDLE,
        "meeting_id": None,
    }
    defaults.update(overrides)
    return CalendarEvent(**defaults)


def test_upsert_issues_no_select_queries_with_cached_existing() -> None:
    """_upsert_events must not call session.exec(select(...)) for loading
    events when existing_events is supplied by the caller."""
    service = CalendarSyncService()
    integration = _make_integration(1)
    existing = _make_stored_event(external_event_id="ext-1", title="Old")

    session = MagicMock()
    # Record every .exec call so we can assert none of them were SELECTs
    session.exec.return_value.all.return_value = []  # for any BotJob check

    events_from_graph = [
        {
            "external_event_id": "ext-1",
            "title": "Updated",
            "start_time": existing.start_time,
            "end_time": existing.end_time,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        },
    ]
    service._upsert_events(
        integration, events_from_graph, session=session, existing_events=[existing],
    )

    # No SELECT on CalendarEvent should happen — existing_events is the source of truth.
    # The only .exec allowed is the BotJob-per-cancelled-event lookup, which
    # shouldn't fire here (no cancellations).
    assert session.exec.call_count == 0, (
        "No DB SELECT should be issued when existing_events is provided "
        "(ZABT-API-1V / 1Z regression)"
    )

    session.add.assert_called()  # the UPDATE path ran
    session.commit.assert_called_once()


def test_upsert_derives_future_cancellations_from_cache() -> None:
    """If a future event is in DB but no longer in the API response,
    _upsert_events must mark it for deletion without issuing the
    legacy ``WHERE end_time >= now`` query."""
    service = CalendarSyncService()
    integration = _make_integration(1)
    future = _make_stored_event(
        external_event_id="ext-future",
        end_time=datetime.utcnow() + timedelta(days=1),
    )

    session = MagicMock()
    session.exec.return_value.all.return_value = []  # no BotJobs

    # Empty events list → the future event has no match → should be deleted
    service._upsert_events(
        integration, [], session=session, existing_events=[future],
    )

    session.delete.assert_called_once_with(future)


def test_upsert_ignores_past_events_when_computing_cancellations() -> None:
    """A past event missing from the API response must NOT be deleted."""
    service = CalendarSyncService()
    integration = _make_integration(1)
    past = _make_stored_event(
        external_event_id="ext-past",
        end_time=datetime.utcnow() - timedelta(days=1),
    )

    session = MagicMock()
    session.exec.return_value.all.return_value = []

    service._upsert_events(
        integration, [], session=session, existing_events=[past],
    )

    session.delete.assert_not_called()


def test_upsert_handles_aware_datetimes_from_graph() -> None:
    """Regression for ZABT-API-29.

    Graph returns tz-aware datetimes but ``calendarevent.end_time`` is
    stored naive. After an UPDATE in the upsert loop, the in-memory
    attribute retained tzinfo until the DB roundtrip, which made the
    subsequent future-event comparison raise
    ``can't compare offset-naive and offset-aware datetimes``.
    """
    service = CalendarSyncService()
    integration = _make_integration(1)
    existing = _make_stored_event(
        external_event_id="ext-1",
        end_time=datetime.utcnow() + timedelta(hours=2),
    )

    session = MagicMock()
    session.exec.return_value.all.return_value = []

    # Graph-style tz-aware datetimes
    aware_start = datetime.now(timezone.utc) + timedelta(hours=1)
    aware_end = datetime.now(timezone.utc) + timedelta(hours=2)

    events_from_graph = [
        {
            "external_event_id": "ext-1",
            "title": "Updated",
            "start_time": aware_start,
            "end_time": aware_end,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        },
    ]

    # Must not raise TypeError comparing aware vs naive.
    service._upsert_events(
        integration, events_from_graph, session=session, existing_events=[existing],
    )

    # After normalization, the in-memory attribute is naive.
    assert existing.end_time.tzinfo is None
    assert existing.start_time.tzinfo is None


def test_to_naive_utc_converts_aware_to_naive() -> None:
    aware = datetime(2026, 4, 19, 12, 0, 0, tzinfo=timezone.utc)
    result = CalendarSyncService._to_naive_utc(aware)
    assert result.tzinfo is None
    assert result == datetime(2026, 4, 19, 12, 0, 0)


def test_to_naive_utc_passes_through_naive() -> None:
    naive = datetime(2026, 4, 19, 12, 0, 0)
    assert CalendarSyncService._to_naive_utc(naive) == naive


def test_upsert_preserves_events_with_linked_meeting() -> None:
    """Future events linked to a meeting must be kept even if not in API."""
    service = CalendarSyncService()
    integration = _make_integration(1)
    linked = _make_stored_event(
        external_event_id="ext-linked",
        end_time=datetime.utcnow() + timedelta(days=1),
        meeting_id=42,
    )

    session = MagicMock()
    session.exec.return_value.all.return_value = []

    service._upsert_events(
        integration, [], session=session, existing_events=[linked],
    )

    session.delete.assert_not_called()
