# Quickstart: 017 — Transcription Progress Tracking

**Date**: 2026-03-03
**Feature**: [spec.md](spec.md)

## Prerequisites

No new dependencies or environment variables are introduced by this feature.

### Existing Environment Variables (unchanged)

| Variable | Service | Purpose |
| --- | --- | --- |
| `REDIS_URL` | Backend | Celery broker + result backend (also used for future Redis Pub/Sub) |
| `BACKEND_CORS_ORIGINS` | Backend | Allowed CORS origins for frontend |

### Existing Dependencies (unchanged)

- **Backend**: `celery`, `redis`, `sqlmodel`, `fastapi` — all already installed
- **Frontend**: `axios` — already installed

## Development Setup

No additional setup needed beyond the standard `docker compose up`. The feature modifies existing code paths only.

### Verification Steps

1. **Backend**: After implementation, verify the meetings API returns `sub_status`:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/meetings/ | jq '.[0].sub_status'
   ```

2. **Frontend**: Upload a meeting file and observe:
   - Upload modal shows stage progression after file upload completes
   - Meetings list updates with specific stage labels (not generic "Processing…")

3. **Celery tasks**: Verify the pipeline is split into chained tasks:
   ```bash
   docker compose exec worker celery -A app.worker inspect registered
   ```
   Should show: `stage_download`, `stage_transcribe`, `stage_summarize`

## Architecture Notes

- **Celery task chain**: `stage_download → stage_transcribe → stage_summarize`
- **Error handling**: Each task has its own `link_error` callback that sets `meeting.status = "failed"`
- **Polling**: Frontend polls every 5s on list pages, 3s in upload modal
- **Future**: Redis Pub/Sub channel `meeting:{id}:status` is published to but not subscribed — ready for future SSE endpoint
