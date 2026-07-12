# API Contract: Meeting Summary Edit

**Feature**: 001-edit-summary | **Date**: 2026-03-09

## PATCH /api/v1/meetings/{meeting_id}/summary

Update the summary text of a completed meeting.

### Request

**Method**: `PATCH`
**Path**: `/api/v1/meetings/{meeting_id}/summary`
**Auth**: Bearer token (Supabase JWT)
**Content-Type**: `application/json`

**Path Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `meeting_id` | `int` | Meeting ID |

**Body**:

```json
{
  "summary_text": "# Updated Summary\n\nNew markdown content here."
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `summary_text` | `string` | Yes | Non-empty, max 50,000 characters |

### Success Response

**Status**: `200 OK`

```json
{
  "id": 42,
  "summary_text": "# Updated Summary\n\nNew markdown content here.",
  "original_summary_text": "# AI Summary\n\nOriginal content.",
  "summary_edited": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Meeting ID |
| `summary_text` | `string` | Updated summary (markdown) |
| `original_summary_text` | `string \| null` | Original AI summary |
| `summary_edited` | `bool` | Always `true` after edit |

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| `400` | Meeting is processing | `{"detail": "Cannot edit summary while meeting is processing."}` |
| `400` | Empty summary_text | `{"detail": "Summary text cannot be empty."}` |
| `403` | Not owner | `{"detail": "Not enough permissions"}` |
| `404` | Meeting not found | `{"detail": "Meeting not found"}` |
| `422` | Invalid body | Standard FastAPI validation error |

### Behavior

1. If `original_summary_text` is `NULL` (first edit), copy current `summary_text` → `original_summary_text`
2. Set `summary_text` = request body value
3. Set `summary_edited` = `True`
4. If the new `summary_text` equals `original_summary_text`, still save (don't auto-detect "no change")

---

## POST /api/v1/meetings/{meeting_id}/summary/restore

Restore the original AI-generated summary.

### Request

**Method**: `POST`
**Path**: `/api/v1/meetings/{meeting_id}/summary/restore`
**Auth**: Bearer token (Supabase JWT)
**Body**: None

### Success Response

**Status**: `200 OK`

```json
{
  "id": 42,
  "summary_text": "# AI Summary\n\nOriginal content.",
  "original_summary_text": "# AI Summary\n\nOriginal content.",
  "summary_edited": false
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| `400` | No original to restore (`original_summary_text` is NULL) | `{"detail": "No original summary available to restore."}` |
| `403` | Not owner | `{"detail": "Not enough permissions"}` |
| `404` | Meeting not found | `{"detail": "Meeting not found"}` |

### Behavior

1. Copy `original_summary_text` → `summary_text`
2. Set `summary_edited` = `False`
3. Keep `original_summary_text` intact (available for future edits)
