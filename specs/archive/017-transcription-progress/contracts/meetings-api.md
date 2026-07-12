# API Contract: Meetings Endpoints (Updated)

**Feature**: 017-transcription-progress
**Date**: 2026-03-03

## Changes from Current Contract

The only backend API change is adding `sub_status` to the `MeetingRead` response schema. No new endpoints are required.

---

## GET /api/v1/meetings/

**Description**: List all meetings for the authenticated user.

**Request**:
- Method: `GET`
- Query params: `skip` (int, default 0), `limit` (int, default 20)
- Headers: `Authorization: Bearer <supabase_jwt>`

**Success Response** (200):
```json
[
  {
    "id": 1,
    "title": "meeting.mp4",
    "description": null,
    "file_path": "user-uuid/meeting.mp4",
    "duration_seconds": 3600,
    "created_at": "2026-03-03T15:00:00",
    "status": "processing",
    "sub_status": "transcribing",
    "transcript_text": null,
    "summary_text": null,
    "action_items_text": null,
    "segments": [],
    "speakers": null
  }
]
```

**Changed fields**:
- `sub_status` (string | null) — **NEW**. The granular processing stage. Null when `status` is `pending_upload`, `completed`, or `failed`. One of: `downloading`, `validating`, `extracting_audio`, `uploading`, `transcribing`, `aligning`, `diarizing`, `parsing`, `cleaning_up`, `summarizing` when `status` is `processing`.

**Error Responses**:
- 401: Unauthorized (invalid/missing JWT)

---

## GET /api/v1/meetings/{meeting_id}

**Description**: Get a single meeting with full details.

**Request**:
- Method: `GET`
- Path params: `meeting_id` (int)
- Headers: `Authorization: Bearer <supabase_jwt>`

**Success Response** (200):
```json
{
  "id": 1,
  "title": "meeting.mp4",
  "description": null,
  "file_path": "user-uuid/meeting.mp4",
  "duration_seconds": 3600,
  "created_at": "2026-03-03T15:00:00",
  "status": "processing",
  "sub_status": "aligning",
  "transcript_text": null,
  "summary_text": null,
  "action_items_text": null,
  "segments": [],
  "speakers": null
}
```

**Changed fields**:
- `sub_status` (string | null) — **NEW**. Same semantics as list endpoint.

**Error Responses**:
- 401: Unauthorized
- 404: Meeting not found or not owned by user

---

## Frontend Type Update

```typescript
export interface Meeting {
  id: number;
  title: string;
  description: string | null;
  file_path: string;
  duration_seconds: number | null;
  created_at: string;
  status: "pending_upload" | "queued" | "processing" | "completed" | "failed";
  sub_status: string | null;  // NEW
  transcript_text: string | null;
  summary_text: string | null;
  action_items_text: string | null;
  speakers?: Record<string, SpeakerBreakdown>;
  segments?: TranscriptSegment[];
}
```

## Stage Mapping (Frontend Responsibility)

The frontend maps `status` + `sub_status` to user-visible stages:

```typescript
type UserStage = "uploaded" | "transcribing" | "aligning" | "diarizing" | "done" | "failed";

function getUserStage(meeting: Meeting): UserStage {
  if (meeting.status === "failed") return "failed";
  if (meeting.status === "completed") return "done";
  if (meeting.status === "pending_upload" || meeting.status === "queued") return "uploaded";
  // status === "processing"
  switch (meeting.sub_status) {
    case "downloading":
    case "validating":
    case "extracting_audio":
      return "uploaded";
    case "uploading":
    case "transcribing":
      return "transcribing";
    case "aligning":
      return "aligning";
    case "diarizing":
    case "parsing":
      return "diarizing";
    case "cleaning_up":
    case "summarizing":
      return "done";
    default:
      return "uploaded";
  }
}
```
