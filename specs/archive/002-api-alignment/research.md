# Research: Backend API Alignment for Frontend-2

**Branch**: `002-api-alignment` | **Date**: 2026-02-19
**Status**: Complete — all unknowns resolved

---

## Decision 1: Pagination Style for `GET /meetings/`

**Decision**: Offset-based pagination using `skip` and `limit` query parameters.

**Rationale**: This is a personal productivity app with fewer than 10,000 meetings per user in any realistic scenario. Offset-based pagination maps directly to SQLModel's `.offset(skip).limit(limit)` query pattern, is simple to implement, and is simple for the frontend to consume. The SQL performance cost of large offsets is irrelevant at this scale.

**Defaults**: `skip=0`, `limit=20`. Maximum `limit` capped at 100 to prevent abuse.

**Alternatives considered**:
- Cursor-based (keyset) pagination — better for massive datasets (>100K rows) where offset queries slow down, but adds significant implementation complexity. Unnecessary here.

---

## Decision 2: File Collision Prevention

**Decision**: Prepend a UUID to each uploaded file's disk filename: `{uuid}_{original_filename}`. Store the UUID-prefixed path in `Meeting.file_path` and the original filename in `Meeting.title`.

**Rationale**: Two users uploading a file named `standup.mp3` would otherwise overwrite each other's files. The UUID prefix guarantees uniqueness. The original name is preserved in `title` so users see a meaningful name in the UI — not a UUID.

**Implementation note**: Use `uuid.uuid4()` from Python's standard library; no new dependency.

**Alternatives considered**:
- User-scoped subdirectory (`/media/uploads/{user_id}/filename`) — equally collision-safe but requires directory creation per user and more complex cleanup. UUID prefix is simpler.
- UUID-only filename — collision-safe but loses the original name entirely, complicating display and download scenarios.

---

## Decision 3: Celery Task Trigger Timing

**Decision**: Call `process_meeting.delay(meeting.id)` **after** the database commit, within the same upload request handler.

**Rationale**: The Celery worker immediately queries the database for the meeting record using `meeting_id`. If the task is dispatched before the DB commit, the worker finds no record and fails or retries unnecessarily. The correct order is:
1. Save file to disk
2. Create meeting record in DB
3. `db.commit()`
4. `db.refresh(meeting)` to get the generated ID
5. Call `process_meeting.delay(meeting.id)`
6. Return the meeting response to the client

**Risk**: If the Celery broker (Redis) is temporarily unavailable at step 5, the task is not enqueued and the meeting stays in "queued" status indefinitely. Acceptable for MVP — the user can re-trigger manually if needed, or an admin can requeue. A retry mechanism can be added in a later phase.

**Alternatives considered**:
- Background thread in FastAPI — simpler but doesn't survive server restarts or scale across containers. Celery is already in the stack.
- Dispatch before commit — causes race condition; rejected.

---

## Decision 4: Delete Behavior

**Decision**: Hard delete — remove the DB record and the file from disk in a single operation.

**Rationale**: This is a personal tool with no compliance or audit trail requirements. Hard delete is the simplest implementation. If the file deletion fails after the DB record is removed, the orphaned file is harmless (it just takes up disk space). If the DB delete fails, the file remains and the operation can be retried safely.

**Cleanup order**: Delete the file first, then the DB record. If file deletion fails (e.g., file already missing), log a warning and proceed with DB deletion — a missing file is not a reason to block the user from removing their meeting record.

**Alternatives considered**:
- Soft delete (`deleted_at` timestamp) — adds query complexity (must filter `WHERE deleted_at IS NULL` everywhere) and doesn't free storage. Only useful for audit trails or recovery, neither of which is required.

---

## Decision 5: Processing Status Updates (Polling vs. WebSockets)

**Decision**: Frontend polls `GET /meetings/{id}` every 3–5 seconds while a meeting is in "queued" or "processing" status.

**Rationale**: For a personal app with a single user (or a small number of concurrent users), polling is perfectly adequate. Polling is stateless on the server, easy to implement on the frontend, and trivial to debug. WebSockets would require a connection manager, a Redis pub/sub channel, and more complex frontend state management — significant added complexity for zero functional benefit at this scale.

**Recommended polling strategy (frontend)**: Start at 3-second intervals; if still processing after 30 seconds, switch to 10-second intervals. Stop polling once status is `completed` or `failed`.

**Alternatives considered**:
- Server-Sent Events (SSE) — simpler than WebSockets but still stateful on the server. Unnecessary for this scale.
- WebSockets — appropriate for real-time collaborative apps; overkill here.

---

## Summary of All Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Pagination | Offset-based, `skip` + `limit`, default 20, max 100 |
| 2 | File collision | UUID prefix on disk; original name in `Meeting.title` |
| 3 | Task timing | `process_meeting.delay()` called after DB commit |
| 4 | Delete behavior | Hard delete (file + DB record) |
| 5 | Status updates | Frontend polls `GET /meetings/{id}` every 3–5 seconds |
