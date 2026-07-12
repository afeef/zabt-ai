# API Contract: Transcript Viewer

## `GET /api/v1/meetings/{meeting_id}`

This existing endpoint must be updated to return the rich diarization payload required by the new frontend viewer.

### Authentication

- **Type**: Bearer Token (Supabase JWT)
- **Scope**: User must be the `owner_id` of the referenced `meeting_id`.

### Response Payload extensions

The `MeetingResponse` model will be expanded to include the parsed WhisperX JSON payload.

**Condition**: Success (200 OK)

```json
{
  "id": 123,
  "title": "Afeef with Irfan Lodhi",
  "status": "completed",
  "file_path": "/meetings/123.mp4",
  "media_url": "https://supabase.../123.mp4",
  "duration_seconds": 3660,
  "summary_text": "...",
  "speakers": {
    "SPEAKER_00": {"percentage": 61, "name": "Speaker 1"},
    "SPEAKER_01": {"percentage": 35, "name": "Speaker 2"}
  },
  "segments": [
    {
      "start": 0.5,
      "end": 4.2,
      "speaker": "SPEAKER_00",
      "text": "Hello everyone, let's get started.",
      "words": [
        {"word": "Hello", "start": 0.5, "end": 0.8},
        {"word": "everyone,", "start": 0.9, "end": 1.4},
        {"word": "let's", "start": 1.5, "end": 1.9},
        {"word": "get", "start": 2.0, "end": 2.3},
        {"word": "started.", "start": 2.4, "end": 4.2}
      ]
    }
  ]
}
```

### Business Rules (Validation)

1. The `words` array is strictly required for the frontend syncing logic. If disabled during testing, the frontend must degrade gracefully (fallback to segment-level highlighting).
2. The `media_url` must be a presigned, valid URL with an expiration matching the user session.
