# Quickstart: YouTube URL Ingestion

## Prerequisites

- Docker and Docker Compose running
- Backend API and worker containers running
- Frontend dev server running (`npm run dev`)
- Valid Supabase account (logged in)

## Environment Variables

No new environment variables required. yt-dlp is installed as a binary in the worker Docker image and requires no API keys or configuration.

**Existing variables used** (already configured):
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Celery broker
- `STORAGE_PROVIDER` / `S3_*` / `MINIO_*` — Object storage for extracted audio
- `SUPABASE_JWT_SECRET` — JWT validation
- `NEXT_PUBLIC_API_URL` — Frontend API base URL

## Setup Steps

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This adds `source_type`, `source_url`, and `youtube_*` columns to the `meeting` table.

### 2. Rebuild Worker Image

```bash
docker compose build worker
```

The worker Dockerfile now includes `yt-dlp` and verifies `ffmpeg` is available.

### 3. Restart Services

```bash
docker compose up -d api worker
```

## Testing the Feature

### Happy Path

1. Open the app home page
2. Click "Paste URL" button (next to Import)
3. Paste a YouTube URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
4. Click "Process"
5. Dialog closes; new meeting card appears with "Processing" status and YouTube badge
6. Wait for processing to complete (download → transcribe → summarize)
7. Meeting card shows "Completed"; click to view transcript and summary

### Error Cases

1. **Invalid URL**: Paste `https://vimeo.com/123` → inline error in dialog
2. **Playlist URL**: Paste `https://youtube.com/playlist?list=PLxxx` → specific playlist error in dialog
3. **Unavailable video**: Submit a deleted/private video URL → meeting card shows "Failed" with reason
4. **Long video**: Submit a video > 4 hours → meeting card shows "Failed: Video exceeds maximum duration"
5. **Concurrency limit**: Submit 4+ YouTube URLs rapidly → 4th returns 429 error

### Verification Checklist

- [ ] "Paste URL" button visible on home page next to Import
- [ ] Dialog opens with input field and Process button
- [ ] Invalid URLs show inline error without closing dialog
- [ ] Valid URL creates meeting with "Processing" status
- [ ] Meeting card shows YouTube icon/badge
- [ ] Processing completes with transcript and summary
- [ ] Meeting title matches YouTube video title
- [ ] Failed videos show appropriate error message on card
- [ ] Existing file upload flow still works unchanged
