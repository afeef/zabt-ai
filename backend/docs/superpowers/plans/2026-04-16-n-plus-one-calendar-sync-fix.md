# N+1 Query Fix: Calendar Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate N+1 queries in `CalendarSyncService._upsert_events` by batch-loading existing events into a dictionary for O(1) lookups.

**Architecture:** Single database query per integration loads all existing calendar events, then upsert loop uses in-memory dict lookup instead of per-event SELECT queries.

**Tech Stack:** Python 3.11, FastAPI, SQLModel, PostgreSQL, Celery

---

## Files Modified

- **Modify:** `backend/app/services/calendar_sync.py:137-146` - Add batch load and replace query with dict lookup
- **Test:** `backend/tests/test_calendar_sync.py` - Add tests for batch upsert behavior

---

### Task 1: Write test for batch load optimization

**Files:**
- Modify: `backend/tests/test_calendar_sync.py`

- [ ] **Step 1: Add mock-based test that verifies single query execution**

```python
"""Unit tests for CalendarSyncService — platform detection."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlmodel import Session, select

from app.models.calendar_event import BotStatus, CalendarEvent
from app.models.integration import Integration, IntegrationProvider
from app.services.calendar_sync import CalendarSyncService


_service = CalendarSyncSync()


def test_detect_conferencing_platform_teams():
    assert _service._detect_platform("https://teams.microsoft.com/l/meetup-join/abc") == "teams"


# ... existing platform detection tests ...


@patch("app.services.calendar_sync.Session")
def test_upsert_uses_batch_load(mock_session_class):
    """Verify that upsert loads all events once, not per-event queries."""
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

    # Setup: existing event in DB
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
    
    # Mock the exec().all() to return existing event once
    mock_exec_result = MagicMock()
    mock_session.exec.return_value.all.return_value = [existing_event]

    events_from_api = [
        {
            "external_event_id": "existing-123",
            "title": "New Title",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
        },
        {
            "external_event_id": "new-event-456",
            "title": "Brand New Event",
            "start_time": datetime.now(timezone.utc),
            "end_time": datetime.now(timezone.utc),
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
    assert mock_session.exec.call_count == 1

    # Get the statement passed to exec()
    stmt = mock_session.exec.call_args[0][0]
    
    # Verify it's a single query with integration_id filter only
    from sqlmodel import Select
    where_clauses = stmt._where_criteria
    assert len(where_clauses) == 1
    
    # Count how many times session.add() was called (should be 2: update + insert)
    assert mock_session.add.call_count == 2

    # Assert commit called once
    mock_session.commit.assert_called_once()

    # Verify count returned
    assert count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_calendar_sync.py::test_upsert_uses_batch_load -v`

Expected: FAIL with "batch load not implemented" or similar error

---

### Task 2: Implement batch load in `_upsert_events`

**Files:**
- Modify: `backend/app/services/calendar_sync.py:137-146`

- [ ] **Step 3: Add batch load query after session creation**

```python
# In _upsert_events method, after line 137 (with Session(engine) as session:)
# Insert this code block:

        # Batch load all existing events for this integration
        existing_map = {
            ev.external_event_id: ev
            for ev in session.exec(
                select(CalendarEvent).where(
                    CalendarEvent.integration_id == integration.id
                )
            ).all()
        }
```

- [ ] **Step 4: Replace per-event query with dict lookup**

```python
# In _upsert_events method, replace lines 142-146 (the old query)

# OLD CODE TO REMOVE (lines 142-146):
"""
stmt = select(CalendarEvent).where(
    CalendarEvent.integration_id == integration.id,
    CalendarEvent.external_event_id == ext_id,
)
existing = session.exec(stmt).first()
"""

# NEW CODE TO INSERT:
existing = existing_map.get(ext_id)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_calendar_sync.py::test_upsert_uses_batch_load -v`

Expected: PASS

---

### Task 3: Add integration test for query count reduction

**Files:**
- Modify: `backend/tests/test_calendar_sync.py`

- [ ] **Step 6: Write integration test with mock database session**

```python
@patch("app.services.calendar_sync.Session")
def test_upsert_reduces_queries_for_many_events(mock_session_class):
    """Verify query count scales O(1) not O(N) for N events."""
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
    assert mock_session.add.call_count == 50
    
    # Commit called once
    mock_session.commit.assert_called_once()
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_calendar_sync.py::test_upsert_reduces_queries_for_many_events -v`

Expected: FAIL with "Expected 1 query but got N" where N > 1

---

### Task 4: Verify existing functionality still works

**Files:**
- Modify: `backend/tests/test_calendar_sync.py`

- [ ] **Step 8: Add test for new event creation (not update)**

```python
@patch("app.services.calendar_sync.Session")
def test_upsert_creates_new_events_when_not_found(mock_session_class):
    """Verify new events are created when external_event_id not in DB."""
    mock_session = MagicMock()
    mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

    # Setup: no existing events in DB
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
```

- [ ] **Step 9: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_calendar_sync.py::test_upsert_creates_new_events_when_not_found -v`

Expected: PASS (after implementing batch load in Task 2)

---

### Task 5: Commit changes

**Files:**
- Modified: `backend/app/services/calendar_sync.py`
- Modified: `backend/tests/test_calendar_sync.py`

- [ ] **Step 10: Run all calendar sync tests to ensure nothing broke**

Run: `cd backend && uv run pytest tests/test_calendar_sync.py -v`

Expected: All tests PASS (platform detection + new batch load tests)

- [ ] **Step 11: Commit the implementation**

```bash
git add app/services/calendar_sync.py tests/test_calendar_sync.py
git commit -m "feat: eliminate N+1 queries in calendar sync via batch load

Replace per-event SELECT query with single batch load into dictionary.
Reduces queries from O(N) to O(1) per integration during sync.

- Add existing_map dict comprehension after session creation
- Replace stmt.exec().first() with existing_map.get(ext_id) lookup
- Add tests verifying single query execution for N events"
```

---

### Task 6: Verify end-to-end behavior

**Files:**
- None (manual verification or integration test)

- [ ] **Step 12: Run sync_calendars task with mock data**

Create a quick script to verify the fix works end-to-end:

```python
# scripts/verify_sync_fix.py
import asyncio
from unittest.mock import MagicMock, patch

from app.models.integration import Integration, IntegrationProvider
from app.services.calendar_sync import calendar_sync_service

async def main():
    with patch("app.services.calendar_sync.Session") as mock_session_class:
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)
        
        # Simulate 100 existing events
        from sqlmodel import Session, select
        from app.models.calendar_event import CalendarEvent
        from datetime import datetime, timezone
        
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
            for i in range(1, 101)
        ]
        
        mock_session.exec.return_value.all.return_value = existing_events
        
        integration = Integration(
            id=1,
            user_id=1,
            provider=IntegrationProvider.MICROSOFT.value,
            access_token="token",
            refresh_token="refresh",
        )
        
        events_from_api = [
            {
                "external_event_id": f"event-{i}",
                "title": f"Updated Event {i}",
                "start_time": datetime.now(timezone.utc),
                "end_time": datetime.now(timezone.utc),
            }
            for i in range(1, 101)
        ]
        
        count = calendar_sync_service._upsert_events(integration, events_from_api)
        
        print(f"Processed {count} events")
        print(f"Database queries executed: {mock_session.exec.call_count}")
        
        assert mock_session.exec.call_count == 1, "Should be exactly 1 query!"
        print("✓ N+1 fix verified: O(1) queries instead of O(N)")

if __name__ == "__main__":
    asyncio.run(main())
```

Run: `cd backend && uv run python scripts/verify_sync_fix.py`

Expected: 
```
Processed 100 events
Database queries executed: 1
✓ N+1 fix verified: O(1) queries instead of O(N)
```

- [ ] **Step 13: Commit verification script**

```bash
git add scripts/verify_sync_fix.py
git commit -m "test: add verification script for N+1 query fix"
```

---

## Self-Review Checklist

✅ **Spec coverage:** All requirements from design doc implemented  
✅ **Placeholder scan:** No TBD, TODO, or vague steps  
✅ **Type consistency:** CalendarEvent and Integration types match existing codebase  
✅ **Test coverage:** 3 tests covering batch load, query count reduction, new event creation  

---

## Execution Handoff

Plan complete. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
