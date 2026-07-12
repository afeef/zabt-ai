# API Contract Changes: Transcription Type Selection

## Modified Endpoints

### POST /api/v1/meetings/ (Create Meeting)

**Request body** — new optional field:

```json
{
  "title": "Clinical Dictation - March 15",
  "file_key": "uploads/abc123.wav",
  "transcription_type": "medical"
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `transcription_type` | string | No | `"normal"` | Must be `"normal"` or `"medical"` |

**Response** — new field in MeetingRead:

```json
{
  "id": 42,
  "title": "Clinical Dictation - March 15",
  "transcription_type": "medical",
  ...
}
```

### POST /api/v1/meetings/youtube (YouTube Ingestion)

**Request body** — new optional field:

```json
{
  "url": "https://youtube.com/watch?v=...",
  "transcription_type": "normal"
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `transcription_type` | string | No | `"normal"` | Must be `"normal"` or `"medical"` |

### GET /api/v1/meetings/{id} (Get Meeting)

**Response** — new field in MeetingRead:

```json
{
  "id": 42,
  "transcription_type": "medical",
  ...
}
```

### GET /api/v1/meetings/ (List Meetings)

**Response** — each meeting object includes new field:

```json
[
  {
    "id": 42,
    "transcription_type": "medical",
    ...
  }
]
```

## Error Responses

No new error responses. Invalid `transcription_type` values return standard 422 Validation Error.
