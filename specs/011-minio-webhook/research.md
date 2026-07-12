# Research: MinIO Webhook Trigger & API Refactoring

**Feature**: 011-minio-webhook | **Date**: 2026-02-25

---

## R-001: How to pass User ID and Meeting Title through S3 upload (FR-003)

**Decision**: Extract `user_id` from the S3 object key path; title is already stored in the Meeting record (created before upload).

**Rationale**: The presigned URL flow already generates keys in the pattern `users/{user_id}/meetings/{uuid}_{filename}`. Since the meeting record is created *before* the file upload (see R-003), the webhook only needs to look up the existing Meeting by `file_path` — user ownership and title are already persisted. Extracting `user_id` from the key serves as a fallback/validation only.

**Alternatives considered**:
- S3 user-defined metadata headers (`x-amz-meta-*`): Adds complexity to presigned URL generation and MinIO doesn't forward metadata in webhook payloads by default. Rejected.
- Encoding metadata in the object key itself: Already partially done (user_id in path). Title in key is fragile (special characters, length limits). Rejected for title.

---

## R-002: Webhook endpoint security (FR-005)

**Decision**: Use MinIO's `auth_token` mechanism with a shared Bearer token stored in environment variables.

**Rationale**: MinIO natively supports `MINIO_NOTIFY_WEBHOOK_AUTH_TOKEN_PRIMARY` which places the value verbatim in the `Authorization` HTTP header. A `Bearer <secret>` scheme is simple, well-understood, and sufficient for internal Docker network communication. The FastAPI endpoint validates this header on POST requests.

**Alternatives considered**:
- Payload signature (HMAC): MinIO does not support payload signing for webhooks. Would require custom MinIO plugin or proxy. Rejected.
- IP allowlisting: Fragile in Docker (IPs change on restart). Rejected.
- Hardcoded secret in URL path (e.g., `/webhooks/minio/<secret>`): Leaks secret in logs and MinIO console. Rejected.

**Implementation detail**: MinIO sends periodic HEAD health-check requests that may not include the `Authorization` header (known issue minio/minio#14507). The endpoint must accept HEAD requests without auth validation.

---

## R-003: Frontend Meeting ID availability after upload (FR-006)

**Decision**: Reorder the frontend API calls — create the meeting record *before* uploading the file to MinIO.

**Rationale**: The current flow is: (1) get presigned URL, (2) upload to MinIO, (3) POST /meetings/ to create record. The webhook fires after step 2, before step 3, creating a race condition where no Meeting record exists yet. By reordering to: (1) get presigned URL, (2) POST /meetings/ with `file_key` and `status=pending_upload`, (3) upload to MinIO — the meeting record exists before the webhook fires. The frontend receives `meeting.id` synchronously from step 2 and can navigate immediately.

**Alternatives considered**:
- Webhook creates meeting record: Frontend has no meeting.id for navigation without polling a new endpoint. Adds complexity. Rejected.
- Webhook retries until meeting exists: Unreliable; adds latency and couples webhook to API timing. Rejected.
- Frontend polls by `file_key`: Requires new endpoint and polling logic. Over-engineered. Rejected.

**New meeting status**: `pending_upload` → `queued` (set by webhook when file lands) → `processing` → `completed`/`failed`.

---

## R-004: MinIO webhook configuration in Docker Compose

**Decision**: Configure webhook target via MinIO environment variables; subscribe bucket via a `minio-init` one-shot container.

**Rationale**: MinIO environment variables (`MINIO_NOTIFY_WEBHOOK_*`) configure the webhook *target* but do not subscribe buckets to events. The `mc event add` command is required to subscribe `zabt-media` to `s3:ObjectCreated:Put` events. A `minio-init` service using the `minio/mc` image runs after MinIO starts and executes the subscription command.

**Configuration**:
```yaml
# In minio service environment:
MINIO_NOTIFY_WEBHOOK_ENABLE_PRIMARY: "on"
MINIO_NOTIFY_WEBHOOK_ENDPOINT_PRIMARY: "http://api:8000/api/v1/webhooks/minio"
MINIO_NOTIFY_WEBHOOK_AUTH_TOKEN_PRIMARY: "Bearer ${MINIO_WEBHOOK_SECRET}"
MINIO_NOTIFY_WEBHOOK_QUEUE_DIR_PRIMARY: "/data/.minio/events"
MINIO_NOTIFY_WEBHOOK_QUEUE_LIMIT_PRIMARY: "100000"
```

**Queue persistence**: `QUEUE_DIR` ensures events are stored on disk if the API is temporarily unavailable. Critical because the API container may start after MinIO.

---

## R-005: MinIO S3 event payload structure

**Decision**: Parse the standard MinIO webhook payload using `Records[0].s3.object.key` for the file path.

**Payload example**:
```json
{
  "EventName": "s3:ObjectCreated:Put",
  "Key": "zabt-media/users/42/meetings/a1b2c3d4_recording.webm",
  "Records": [
    {
      "eventName": "s3:ObjectCreated:Put",
      "s3": {
        "bucket": { "name": "zabt-media" },
        "object": {
          "key": "users/42/meetings/a1b2c3d4_recording.webm",
          "size": 15728640,
          "contentType": "audio/webm"
        }
      }
    }
  ]
}
```

**Key extraction**: `record["s3"]["object"]["key"]` gives the object key (URL-encoded; must decode with `urllib.parse.unquote_plus`).

---

## R-006: Consolidating create_meeting and upload_meeting (FR-007)

**Decision**: Remove `upload_meeting` (multipart POST /meetings/upload) entirely. Consolidate Celery triggering into MeetingService. POST /meetings/ no longer triggers Celery — it only creates the record.

**Rationale**:
- `upload_meeting` is the legacy flow where the backend proxies the file upload. The presigned URL flow replaces it.
- Both endpoints duplicated: `meeting_service.create_meeting()` + `process_meeting.delay()`.
- With webhook-triggered processing, neither endpoint should call `process_meeting.delay()`. The webhook is the sole trigger.
- A new `MeetingService.initiate_processing(file_key)` method encapsulates: look up meeting by file_path → validate status → update status to "queued" → trigger Celery. Called only by the webhook handler.

**Alternatives considered**:
- Keep both endpoints, just remove Celery calls: Still leaves dead code (upload_meeting serves no purpose with presigned URLs). Rejected.
- Merge into one endpoint with optional file field: Confusing API contract. Rejected.

---

## R-007: Webhook retry and idempotency

**Decision**: Make the webhook handler idempotent. If a meeting is already in `queued`/`processing`/`completed` status, skip re-triggering.

**Rationale**: MinIO may retry webhook delivery (configurable via `MAX_RETRY`). The handler must not enqueue duplicate Celery tasks. Checking meeting status before triggering ensures idempotency.

**Implementation**: `MeetingService.initiate_processing()` checks `meeting.status == "pending_upload"` before transitioning to `"queued"` and triggering Celery. Any other status is a no-op (returns success to MinIO to prevent further retries).
