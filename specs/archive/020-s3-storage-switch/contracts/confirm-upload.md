# API Contract: Confirm Upload

## POST /api/v1/meetings/{meeting_id}/confirm-upload

Confirms that the frontend has completed uploading a file to S3/R2 and triggers the transcription pipeline. Only used when `STORAGE_PROVIDER=s3` — when using MinIO, the MinIO webhook triggers the pipeline automatically.

### Request

**Method**: POST
**Path**: `/api/v1/meetings/{meeting_id}/confirm-upload`
**Auth**: Bearer token (Supabase JWT)
**Body**: None (empty)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | int | ID of the meeting whose file upload is complete |

### Success Response

**Status**: `200 OK`

```json
{
  "status": "ok",
  "meeting_id": 42,
  "message": "Processing triggered"
}
```

### Error Responses

**404 Not Found** — Meeting does not exist:
```json
{
  "detail": "Meeting not found"
}
```

**403 Forbidden** — User does not own this meeting:
```json
{
  "detail": "Not enough permissions"
}
```

**400 Bad Request** — Meeting is not in `pending_upload` status:
```json
{
  "detail": "Meeting is not awaiting upload"
}
```

### Behavior

1. Validates authenticated user owns the meeting
2. Checks meeting status is `pending_upload`
3. Calls `meeting_service.initiate_processing(meeting.file_path)` — same function used by MinIO webhook
4. Returns success with meeting ID

### Notes

- This endpoint is idempotent — calling it on an already-processing meeting returns 400
- The frontend should call this immediately after the presigned PUT upload succeeds
- When `STORAGE_PROVIDER=minio`, this endpoint still works but is redundant (MinIO webhook handles it)
