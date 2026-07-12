# Data Model: MinIO Webhook Trigger & API Refactoring

**Feature**: 011-minio-webhook | **Date**: 2026-02-25

---

## Existing Entities (Modified)

### Meeting

No schema changes to the `Meeting` table. The `status` field gains a new valid value.

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| `status` | `str` | **Extended** | New value: `"pending_upload"` added before `"queued"` |

**Status transitions (updated)**:

```
pending_upload → queued → processing → completed
                                    → failed
```

- `pending_upload`: Meeting record created; file not yet uploaded to MinIO.
- `queued`: Webhook received; Celery task enqueued. (Previously the default on creation.)
- `processing` / `completed` / `failed`: Unchanged.

**Default value change**: `Meeting.status` default changes from `"queued"` to `"pending_upload"` in the model definition. The webhook handler sets it to `"queued"` when the file lands.

---

## New Pydantic Models (Request/Response DTOs)

### S3EventNotification (webhook request body)

Represents the MinIO S3 event notification payload. Only the fields we parse are modeled; extra fields are ignored.

```python
class S3Object(BaseModel):
    key: str           # URL-encoded object key, e.g. "users/42/meetings/abc_file.webm"
    size: int = 0
    contentType: str = ""

class S3Bucket(BaseModel):
    name: str          # "zabt-media"

class S3Info(BaseModel):
    bucket: S3Bucket
    object: S3Object

class S3EventRecord(BaseModel):
    eventName: str     # "s3:ObjectCreated:Put"
    s3: S3Info

class S3EventNotification(BaseModel):
    EventName: str = ""
    Key: str = ""
    Records: list[S3EventRecord] = []
```

### WebhookResponse

```python
class WebhookResponse(BaseModel):
    status: str        # "ok" | "skipped" | "error"
    meeting_id: int | None = None
    message: str = ""
```

---

## New Configuration Fields

### Settings (app/core/config.py)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `MINIO_WEBHOOK_SECRET` | `str` | `"change-me-in-production"` | Shared secret for webhook auth; matched against `Authorization: Bearer <secret>` |

---

## Service Layer Changes

### MeetingService — New Method

```python
def initiate_processing(self, file_key: str) -> Meeting | None:
    """
    Called by webhook handler. Looks up meeting by file_path,
    validates status, transitions to 'queued', triggers Celery.
    Returns the meeting or None if no matching record / already processed.
    """
```

**Logic**:
1. Query `Meeting` where `file_path == file_key` and `status == "pending_upload"`.
2. If not found → return `None` (idempotent: already processed or no record yet).
3. Update `status` to `"queued"`.
4. Save via `BaseService.save()`.
5. Trigger `process_meeting.delay(meeting.id)`.
6. Return the meeting.

---

## Entity Relationship (unchanged)

```
User 1──* Meeting 1──* TranscriptSegment
```

No new tables or relationships. The webhook feature operates on existing entities with a new status value and a new service method.
