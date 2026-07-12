# API Contracts: Meeting Upload Progress

**Feature**: 001-meeting-upload  
**Date**: 2026-02-22

---

> **Note**: This document outlines the contract for the *existing* upload endpoint that the new UI will consume. No new backend endpoints are being built for this feature.

## POST /api/v1/meetings/upload

**Purpose**: Upload a meeting recording file, save it to storage, and create a meeting record to trigger asynchronous AI processing.

**Method**: `POST`  
**Path**: `/api/v1/meetings/upload`  
**Auth**: Bearer token (Supabase JWT) via `Authorization` header

### Request Body (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `Binary` | **Yes** | The actual audio/video file (mp4, mov, mp3, wav, m4a). Max 2GB. |
| `title` | `String` | No | Optional meeting title. Defaults to "Untitled Meeting" if omitted by client. |
| `description` | `String` | No | Optional context for the meeting. |

### Axios Client Implementation Details

To achieve the progress bar, the frontend must consume this endpoint using Axios like so:

```typescript
const controller = new AbortController();

apiClient.post('/meetings/upload', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  },
  signal: controller.signal,
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
    );
    // Update local React state with percentCompleted
  }
});
```

### Success Response — `200 OK`

Returns the newly created Meeting record. The background Celery task handles transcription asynchronously.

```json
{
  "id": 123,
  "title": "Weekly Sync.mp4",
  "description": null,
  "file_path": "uploads/user_123/timestamp_weekly_sync.mp4",
  "duration_seconds": 0,
  "created_at": "2026-02-22T08:00:00Z",
  "status": "queued",
  "transcript_text": null,
  "summary_text": null,
  "action_items_text": null
}
```

### Error Responses

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | File format unsupported or missing file field. |
| `401 Unauthorized` | Missing or expired JWT. |
| `413 Payload Too Large` | File exceeds server limits (if proxy/server limits are hit before application code). |
| `500 Internal Server Error` | Storage failure or database error. |
