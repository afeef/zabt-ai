# N+1 Query Fix: Calendar Sync Service

**Date:** 2026-04-16  
**Status:** Approved  
**Component:** `backend/app/services/calendar_sync.py`

---

## Problem Statement

The `_upsert_events` method in `CalendarSyncService` executes one database query per calendar event during sync:

```python
# Current implementation (line 142-146)
for ev in events:
    ext_id = ev["external_event_id"]
    stmt = select(CalendarEvent).where(
        CalendarEvent.integration_id == integration.id,
        CalendarEvent.external_event_id == ext_id,
    )
    existing = session.exec(stmt).first()  # N queries!
```

For an integration with 100 calendar events, this generates **100+ database queries** per sync run (every 5 minutes), causing:
- Slow sync performance
- Unnecessary database load
- Potential connection pool exhaustion under heavy usage

---

## Solution Overview

Load all existing events for the integration in a single query, then use an in-memory dictionary for O(1) lookups during upsert.

### Architecture Change

**Before:**
```
API Events → For each event: Query DB → Upsert (N queries total)
```

**After:**
```
API Events ← Batch Load (1 query) → Dict lookup → Bulk Upsert (3 queries total)
```

---

## Implementation Details

### File: `backend/app/services/calendar_sync.py`

#### Change 1: Batch Load Existing Events (after line 137)

```python
def _upsert_events(self, integration: Integration, events: list[dict]) -> int:
    now = datetime.now(timezone.utc)
    incoming_ids: set[str] = set()

    with Session(engine) as session:
        # NEW: Load all existing events for this integration once
        existing_map = {
            ev.external_event_id: ev
            for ev in session.exec(
                select(CalendarEvent).where(
                    CalendarEvent.integration_id == integration.id
                )
            ).all()
        }

        for ev in events:
            ext_id = ev["external_event_id"]
            incoming_ids.add(ext_id)

            # NEW: O(1) dict lookup instead of query
            existing = existing_map.get(ext_id)
            
            # ... rest of upsert logic unchanged
```

#### Change 2: Replace Per-Event Query (line 142-146)

**Remove:**
```python
stmt = select(CalendarEvent).where(
    CalendarEvent.integration_id == integration.id,
    CalendarEvent.external_event_id == ext_id,
)
existing = session.exec(stmt).first()
```

**Replace with:**
```python
existing = existing_map.get(ext_id)
```

---

## Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Queries per integration | N+2 (N upserts + future check + commit) | 3 (batch load + future check + commit) | ~95% reduction |
| Memory overhead | ~0 bytes | ~2MB for 10k events | Acceptable |
| Sync time (100 events) | ~500ms | ~50ms | ~10x faster |
| Code complexity | Low | Low | Same |

### Memory Calculation

- Each `CalendarEvent` object: ~200 bytes
- 1,000 events: ~200KB
- 10,000 events: ~2MB
- Sync runs every 5 minutes, memory is short-lived (GC collects after session closes)

---

## Safety & Correctness

### Transactional Guarantees
✅ All operations occur within a single database session  
✅ Commit happens only after all upserts and deletions complete  
✅ Rollback on exception preserves data consistency

### Data Integrity
✅ Matching logic unchanged: `(integration_id, external_event_id)` composite key  
✅ Update vs. create decision based on same lookup criteria  
✅ Deletion logic for cancelled events remains identical (line 183-212)

### Edge Cases Handled
✅ Past events loaded but not deleted (only future events checked for cancellation)  
✅ New events created when `external_event_id` not in `existing_map`  
✅ Existing events updated with new data from API  
✅ Events with linked bot jobs or meetings protected from deletion

---

## Testing Strategy

### Unit Tests
1. **Verify batch load executes once**: Mock `session.exec()` and assert single call for existing events
2. **Verify dict lookup works**: Test upsert with known existing event ID
3. **Verify new event creation**: Test with unknown external_event_id
4. **Verify update logic**: Modify event data, confirm fields updated correctly

### Integration Tests
1. Run `sync_calendars` with 100+ mock events
2. Measure query count (should be ~3, not N+2)
3. Verify all events upserted correctly
4. Confirm cancelled future events deleted

---

## Rollback Plan

If issues arise:
1. Revert commit to `calendar_sync.py`
2. No schema changes required (safe rollback)
3. Monitor sync performance for 1 hour post-revert

---

## Future Optimizations (Out of Scope)

- **Pagination**: If users have >50k calendar events, consider loading only recent N months
- **Index optimization**: Ensure `(integration_id, external_event_id)` composite index exists
- **Bulk upsert**: Use SQLAlchemy's `bulk_insert_mappings` for further performance gains

---

## References

- Original query: `SELECT calendarevent.id, ... WHERE integration_id = ? AND end_time >= ?`
- Related files:
  - `backend/app/worker.py:435-450` (sync_calendars task)
  - `backend/app/models/calendar_event.py` (model definition)
