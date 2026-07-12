"""Unit tests for CalendarSyncService — platform detection and batch load optimization."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlmodel import Session, select

from app.models.calendar_event import BotStatus, CalendarEvent
from app.models.integration import Integration, IntegrationProvider
from app.services.calendar_sync import CalendarSyncService


_service = CalendarSyncService()


def test_detect_conferencing_platform_teams():
    assert _service._detect_platform("https://teams.microsoft.com/l/meetup-join/abc") == "teams"


def test_detect_conferencing_platform_zoom():
    assert _service._detect_platform("https://us04web.zoom.us/j/123456") == "zoom"


def test_detect_conferencing_platform_meet():
    assert _service._detect_platform("https://meet.google.com/abc-defg-hij") == "meet"


def test_detect_conferencing_platform_none():
    assert _service._detect_platform(None) is None
    assert _service._detect_platform("https://example.com/meeting") is None


@patch("app.services.calendar_sync.Session")
def test_upsert_uses_batch_load(mock_session_class):
    """Verify that upsert loads all events once, not per-event queries.

    This test ensures the batch load optimization reduces database queries from O(N) to O(1).
    It mocks the Session context manager and verifies exec() is called exactly once for
    batch loading existing events by integration_id, rather than querying per event.
    """
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

    # Setup: existing event in DB that will be updated
    existing_event = CalendarEvent(
        id=1,
        user_id=1,
        integration_id=1,
        provider="microsoft",
        external_event_id="existing-123",
        title="Old Title",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
    )

    # Mock the exec().all() to return existing event once (batch load)
    mock_session.exec.return_value.all.return_value = [existing_event]

    events_from_api = [
        {
            "external_event_id": "existing-123",
            "title": "New Title",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "conferencing_platform": None,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        },
        {
            "external_event_id": "new-event-456",
            "title": "Brand New Event",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "conferencing_platform": None,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        },
    ]

    integration = Integration(
        id=1,
        user_id=1,
        provider=IntegrationProvider.MICROSOFT.value,
        access_token="encrypted-token",
        refresh_token="encrypted-refresh",
    )

    # Call the method
    count = _service._upsert_events(integration, events_from_api)

    # Assert: exec() called exactly once for batch load (not per event)
    assert mock_session.exec.call_count == 1, \
        f"Expected 1 query for batch load but got {mock_session.exec.call_count}"

    # Get the statement passed to exec() and verify it's a single query with integration_id filter only
    stmt = mock_session.exec.call_args[0][0]
    where_clauses = list(stmt._where_criteria)
    assert len(where_clauses) == 1, "Expected exactly one WHERE clause (integration_id)"

    # Count how many times session.add() was called (should be 2: update + insert)
    add_calls = mock_session.add.call_args_list
    added_items = [call[0][0] for call in add_calls]
    assert len(added_items) == 2, f"Expected 2 add calls but got {len(added_items)}"

    # Verify both existing event (updated) and new event are present via their external_event_ids
    added_ext_ids = [item.external_event_id for item in added_items]
    assert "existing-123" in added_ext_ids, "Existing event should be updated"
    assert "new-event-456" in added_ext_ids, "New event should be created"

    # Assert commit called once
    mock_session.commit.assert_called_once()

    # Verify count returned
    assert count == 2


@patch("app.services.calendar_sync.Session")
def test_upsert_reduces_queries_for_many_events(mock_session_class):
    """Verify query count scales O(1) not O(N) for N events.

    This integration test simulates 50 existing events in the database and verifies that
    exec() is called exactly ONCE (batch load), not 50 times (one per event).
    """
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

    # Setup: 50 existing events in DB
    existing_events = [
        CalendarEvent(
            id=i,
            user_id=1,
            integration_id=1,
            provider="microsoft",
            external_event_id=f"event-{i}",
            title=f"Event {i}",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
        )
        for i in range(1, 51)
    ]

    mock_session.exec.return_value.all.return_value = existing_events

    # API returns 50 events (all already exist)
    events_from_api = [
        {
            "external_event_id": f"event-{i}",
            "title": f"Updated Event {i}",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "conferencing_platform": None,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        }
        for i in range(1, 51)
    ]

    integration = Integration(
        id=1,
        user_id=1,
        provider=IntegrationProvider.MICROSOFT.value,
        access_token="encrypted-token",
        refresh_token="encrypted-refresh",
    )

    # Call the method
    count = _service._upsert_events(integration, events_from_api)

    # Assert: exec() called exactly ONCE (batch load), not 50 times
    assert mock_session.exec.call_count == 1, \
        f"Expected 1 query but got {mock_session.exec.call_count}"

    # Verify all 50 events were updated (session.add called 50 times)
    assert mock_session.add.call_count == 50, \
        f"Expected 50 add calls but got {mock_session.add.call_count}"

    # Commit called once
    mock_session.commit.assert_called_once()


@patch("app.services.calendar_sync.Session")
def test_upsert_creates_new_events_when_not_found(mock_session_class):
    """Verify new events are created when external_event_id not in DB."""
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

    # Setup: no existing events in DB (empty batch load result)
    mock_session.exec.return_value.all.return_value = []

    events_from_api = [
        {
            "external_event_id": "brand-new-event",
            "title": "Brand New Event",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
            "conferencing_platform": None,
            "join_url": None,
            "organizer_email": None,
            "attendees": [],
        }
    ]

    integration = Integration(
        id=1,
        user_id=1,
        provider=IntegrationProvider.MICROSOFT.value,
        access_token="encrypted-token",
        refresh_token="encrypted-refresh",
    )

    # Call the method
    count = _service._upsert_events(integration, events_from_api)

    # Assert: exec() called once for batch load (returns empty)
    assert mock_session.exec.call_count == 1

    # Assert: session.add called once for new event creation
    assert mock_session.add.call_count == 1

    # Verify commit called
    mock_session.commit.assert_called_once()

    # Verify count returned
    assert count == 1
