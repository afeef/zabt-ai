# Data Model: YouTube URL Ingestion

## Entity Changes

### Meeting (extended)

Existing table `meeting` — add the following nullable fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source_type` | `str` | `"upload"` | Meeting source: `"upload"` or `"youtube"` |
| `source_url` | `str?` | `None` | Original YouTube URL (null for file uploads) |
| `youtube_title` | `str?` | `None` | Video title from YouTube metadata |
| `youtube_duration_seconds` | `int?` | `None` | Video duration in seconds |
| `youtube_thumbnail_url` | `str?` | `None` | Video thumbnail URL |
| `youtube_channel` | `str?` | `None` | YouTube channel name |

**Validation rules**:
- `source_type` MUST be one of `"upload"`, `"youtube"`
- `source_url` MUST be non-null when `source_type == "youtube"`
- `source_url` MUST be null when `source_type == "upload"`
- `youtube_duration_seconds` MUST be <= 14400 (4 hours) when set by worker

**Backward compatibility**:
- All new fields have defaults (no existing data affected)
- `source_type` defaults to `"upload"` so all existing meetings remain "upload" type
- No existing columns modified or removed

### State Transitions (YouTube flow)

```
[API creates meeting]
     │
     ▼
  queued ──────────────► failed (concurrency limit, invalid URL format)
     │
     ▼
  processing
  sub_status: "downloading_youtube"
     │
     ├──► failed (video unavailable, age-restricted, geo-blocked, duration exceeded, no audio)
     │
     ▼
  processing
  sub_status: "downloading" → "transcribing" → "aligning" → "diarizing" → "summarizing"
     │                        (existing pipeline, unchanged)
     │
     ▼
  completed ◄──────────── OR ──────────────► failed
```

**Key difference from file upload flow**:
- File uploads start at `pending_upload` (waiting for file to arrive in storage)
- YouTube meetings skip `pending_upload` and start at `queued` (URL is the input, no file upload step)
- YouTube adds a `downloading_youtube` sub_status before entering the existing pipeline

## Alembic Migration

**Migration file**: `backend/alembic/versions/xxx_add_youtube_source_fields.py`

**Upgrade**:
```sql
ALTER TABLE meeting ADD COLUMN source_type VARCHAR NOT NULL DEFAULT 'upload';
ALTER TABLE meeting ADD COLUMN source_url VARCHAR;
ALTER TABLE meeting ADD COLUMN youtube_title VARCHAR;
ALTER TABLE meeting ADD COLUMN youtube_duration_seconds INTEGER;
ALTER TABLE meeting ADD COLUMN youtube_thumbnail_url VARCHAR;
ALTER TABLE meeting ADD COLUMN youtube_channel VARCHAR;
```

**Downgrade**:
```sql
ALTER TABLE meeting DROP COLUMN source_type;
ALTER TABLE meeting DROP COLUMN source_url;
ALTER TABLE meeting DROP COLUMN youtube_title;
ALTER TABLE meeting DROP COLUMN youtube_duration_seconds;
ALTER TABLE meeting DROP COLUMN youtube_thumbnail_url;
ALTER TABLE meeting DROP COLUMN youtube_channel;
```
