# API Contract: Delete Meeting

## `DELETE /api/v1/meetings/{meeting_id}`

Permanently deletes a specific meeting record and its associated physical file storage from the system.

### Authentication

- **Type**: Bearer Token (Supabase JWT)
- **Scope**: User must be the `owner_id` of the referenced `meeting_id`.

### Path Parameters

- `meeting_id` (integer) - *Required*. The unique ID of the meeting to delete.

### Business Rules (Validation)

1. Wait for ownership matching before deletion.
2. If `meeting.status == 'processing'` or `meeting.status == 'queued'`, the deletion MUST be rejected.

### Response Codes

#### 204 No Content

**Condition**: Meeting was successfully deleted, and physical file was garbage collected.
**Response**: Empty body. *(Note: Many FastAPI implementations prefer 200 OK with `{"message": "deleted"}` — either is acceptable as long as it is documented. We will use a `200 OK` for simplicity if standard.)*

#### 400 Bad Request

**Condition**: Meeting is actively transcribing/queued and cannot be deleted safely.
```json
{
  "detail": "Cannot delete a meeting while it is processing."
}
```

#### 403 Forbidden / 400 Bad Request

**Condition**: The user does not own the meeting.
```json
{
  "detail": "Not enough permissions"
}
```

#### 404 Not Found

**Condition**: The meeting does not exist or was already deleted.
```json
{
  "detail": "Meeting not found"
}
```
