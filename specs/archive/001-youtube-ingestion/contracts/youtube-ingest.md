# API Contract: YouTube URL Ingestion

## POST /api/v1/meetings/youtube

Submit a YouTube URL to create a meeting. The API validates URL format, checks concurrency limits, creates a meeting record, and dispatches background processing.

### Request

**Authentication**: Required (Supabase JWT Bearer token)

**Content-Type**: `application/json`

**Body**:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `string` | Yes | YouTube video URL |

**URL validation** (performed synchronously by API):
- Must match a known YouTube URL pattern (watch, youtu.be, live, shorts, embed)
- Must NOT be a playlist URL (`/playlist?list=`)
- Must be a well-formed URL

### Success Response

**Status**: `201 Created`

**Body**: Standard `MeetingRead` object

```json
{
  "id": 42,
  "title": "YouTube Video",
  "description": null,
  "file_path": null,
  "duration_seconds": null,
  "created_at": "2026-03-10T14:30:00Z",
  "status": "queued",
  "sub_status": null,
  "transcript_text": null,
  "summary_text": null,
  "original_summary_text": null,
  "summary_edited": false,
  "action_items_text": null,
  "template_id": null,
  "template_name": null,
  "source_type": "youtube",
  "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "youtube_title": null,
  "youtube_duration_seconds": null,
  "youtube_thumbnail_url": null,
  "youtube_channel": null
}
```

**Notes**:
- `title` is set to a placeholder ("YouTube Video") initially; the worker updates it to the actual video title after metadata extraction
- `file_path` is null at creation; the worker sets it after audio download
- `status` starts at `"queued"` (not `"pending_upload"` — no file upload step)
- YouTube metadata fields (`youtube_title`, etc.) are null initially; populated by worker

### Error Responses

**400 Bad Request** — Invalid URL format

```json
{
  "detail": "Please enter a valid YouTube video URL"
}
```

**400 Bad Request** — Playlist URL

```json
{
  "detail": "Playlist URLs are not supported. Please paste a single video URL."
}
```

**429 Too Many Requests** — Concurrency limit reached

```json
{
  "detail": "You have reached the maximum of 3 concurrent YouTube ingestions. Please wait for an existing one to complete."
}
```

**401 Unauthorized** — Missing or invalid JWT

```json
{
  "detail": "Not authenticated"
}
```

## Extended MeetingRead Schema

The following fields are added to the existing `MeetingRead` response model:

| Field | Type | Description |
|-------|------|-------------|
| `source_type` | `string` | `"upload"` or `"youtube"` |
| `source_url` | `string?` | Original YouTube URL (null for uploads) |
| `youtube_title` | `string?` | Video title from YouTube |
| `youtube_duration_seconds` | `int?` | Video duration in seconds |
| `youtube_thumbnail_url` | `string?` | Thumbnail URL |
| `youtube_channel` | `string?` | Channel name |

These fields appear in all meeting responses (GET /meetings, GET /meetings/{id}, etc.) but are only populated for YouTube-sourced meetings.
