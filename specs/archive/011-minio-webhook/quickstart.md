# Quickstart: MinIO Webhook Trigger & API Refactoring

**Feature**: 011-minio-webhook | **Date**: 2026-02-25

---

## New Environment Variables

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `MINIO_WEBHOOK_SECRET` | backend (api), minio | `change-me-in-production` | Shared secret for webhook authentication. MinIO sends it as `Authorization: Bearer <secret>` |

## Modified Docker Compose Services

### `minio` — New environment variables

```yaml
environment:
  # ... existing vars ...
  MINIO_NOTIFY_WEBHOOK_ENABLE_PRIMARY: "on"
  MINIO_NOTIFY_WEBHOOK_ENDPOINT_PRIMARY: "http://api:8000/api/v1/webhooks/minio"
  MINIO_NOTIFY_WEBHOOK_AUTH_TOKEN_PRIMARY: "Bearer ${MINIO_WEBHOOK_SECRET:-change-me-in-production}"
  MINIO_NOTIFY_WEBHOOK_QUEUE_DIR_PRIMARY: "/data/.minio/events"
  MINIO_NOTIFY_WEBHOOK_QUEUE_LIMIT_PRIMARY: "100000"
```

### `minio-init` — New one-shot service

```yaml
minio-init:
  image: minio/mc
  depends_on:
    - minio
  restart: "no"
  entrypoint: >
    /bin/sh -c "
    sleep 5;
    mc alias set myminio http://minio:9000 minioadmin minioadmin;
    mc mb --ignore-existing myminio/zabt-media;
    mc event add myminio/zabt-media arn:minio:sqs::PRIMARY:webhook --event s3:ObjectCreated:Put;
    echo 'Bucket event subscription configured';
    "
```

### `api` — New environment variable

```yaml
environment:
  # ... existing vars ...
  MINIO_WEBHOOK_SECRET: ${MINIO_WEBHOOK_SECRET:-change-me-in-production}
```

## .env File Addition

Add to your `.env` (or set in environment):

```bash
MINIO_WEBHOOK_SECRET=change-me-in-production
```

## Setup Steps

1. Add `MINIO_WEBHOOK_SECRET` to your `.env` file
2. Start services: `docker compose up -d`
3. Verify `minio-init` ran successfully: `docker compose logs minio-init`
4. Verify webhook target is active: Open MinIO console at `http://localhost:9001` → Events → check that the webhook target is listed and online
5. Test: Upload a file via the frontend; verify the webhook triggers processing without the frontend needing to call any additional endpoint

## API Changes

- `POST /api/v1/meetings/` — No longer triggers Celery. Creates record with `status=pending_upload`.
- `POST /api/v1/meetings/upload` — **Removed**. Use presigned URL flow.
- `POST /api/v1/webhooks/minio` — **New**. Receives MinIO S3 events. Secured with `MINIO_WEBHOOK_SECRET`.
- `HEAD /api/v1/webhooks/minio` — **New**. MinIO health check (no auth).

## Frontend Changes

The `uploadMeeting()` function in `frontend-2/app/lib/api.ts` reorders calls:

```
Before: presigned-upload → PUT to MinIO → POST /meetings/
After:  presigned-upload → POST /meetings/ → PUT to MinIO
```

The frontend receives `meeting.id` before the upload starts, enabling immediate navigation.
