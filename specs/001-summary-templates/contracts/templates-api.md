# API Contract: Templates

**Feature**: `001-summary-templates`
**Base path**: `/api/v1/templates`
**Auth**: All endpoints require `Authorization: Bearer <supabase_jwt>`

---

## GET /templates/

List all templates available to the authenticated user: all built-in templates plus the user's own custom templates.

**Request**
```
GET /api/v1/templates/
Authorization: Bearer <token>
```

**Success Response** `200 OK`
```json
[
  {
    "id": 1,
    "name": "General Summary",
    "body": "## Overview\n...",
    "template_type": "built_in",
    "is_system_default": true,
    "owner_id": null,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  },
  {
    "id": 5,
    "name": "My Custom Template",
    "body": "## Custom Section\n...",
    "template_type": "custom",
    "is_system_default": false,
    "owner_id": 42,
    "created_at": "2026-03-04T10:00:00Z",
    "updated_at": "2026-03-04T10:00:00Z"
  }
]
```

**Error Responses**
- `401 Unauthorized` — missing or invalid JWT

---

## POST /templates/

Create a new custom template owned by the authenticated user.

**Request**
```
POST /api/v1/templates/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Retro Format",
  "body": "## What went well\n...\n## Improvements\n..."
}
```

**Validation**:
- `name`: required, non-empty string, max 100 characters
- `body`: required, non-empty string, max 4,000 characters

**Success Response** `201 Created`
```json
{
  "id": 6,
  "name": "My Retro Format",
  "body": "## What went well\n...\n## Improvements\n...",
  "template_type": "custom",
  "is_system_default": false,
  "owner_id": 42,
  "created_at": "2026-03-04T11:00:00Z",
  "updated_at": "2026-03-04T11:00:00Z"
}
```

**Error Responses**
- `400 Bad Request` — validation failure (e.g., body exceeds 4,000 characters)
  ```json
  { "detail": "Template body must not exceed 4000 characters." }
  ```
- `401 Unauthorized`

---

## GET /templates/{template_id}

Fetch a single template by ID. Returns built-in templates (any user) or the requesting user's own custom template.

**Request**
```
GET /api/v1/templates/1
Authorization: Bearer <token>
```

**Success Response** `200 OK`
```json
{
  "id": 1,
  "name": "General Summary",
  "body": "## Overview\n...",
  "template_type": "built_in",
  "is_system_default": true,
  "owner_id": null,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Error Responses**
- `401 Unauthorized`
- `403 Forbidden` — attempting to fetch another user's custom template
- `404 Not Found`

---

## PUT /templates/{template_id}

Update a custom template. Only the owner can update. Built-in templates cannot be updated.

**Request**
```
PUT /api/v1/templates/6
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Retro Format",
  "body": "## Revised content\n..."
}
```

**Validation**: same as POST

**Success Response** `200 OK`
```json
{
  "id": 6,
  "name": "Updated Retro Format",
  "body": "## Revised content\n...",
  "template_type": "custom",
  "is_system_default": false,
  "owner_id": 42,
  "created_at": "2026-03-04T11:00:00Z",
  "updated_at": "2026-03-04T12:00:00Z"
}
```

**Error Responses**
- `400 Bad Request` — validation failure
- `401 Unauthorized`
- `403 Forbidden` — not the owner, or attempting to update a built-in template
  ```json
  { "detail": "Built-in templates cannot be modified." }
  ```
- `404 Not Found`

---

## DELETE /templates/{template_id}

Delete a custom template. Only the owner can delete. Built-in templates cannot be deleted.

If the deleted template was the user's personal default, the user's `default_template_id` is set to `NULL` (system default takes effect for future uploads).

**Request**
```
DELETE /api/v1/templates/6
Authorization: Bearer <token>
```

**Success Response** `204 No Content`

**Error Responses**
- `401 Unauthorized`
- `403 Forbidden` — not the owner, or attempting to delete a built-in template
  ```json
  { "detail": "Built-in templates cannot be deleted." }
  ```
- `404 Not Found`

---

## POST /templates/{template_id}/set-default

Set a template as the authenticated user's personal default for future uploads. Accepts both built-in and user's own custom templates.

**Request**
```
POST /api/v1/templates/2/set-default
Authorization: Bearer <token>
```

No request body required.

**Success Response** `200 OK`
```json
{
  "default_template_id": 2,
  "default_template_name": "Meeting Minutes"
}
```

**Error Responses**
- `401 Unauthorized`
- `403 Forbidden` — attempting to set another user's custom template as default
- `404 Not Found`

---

## POST /meetings/{meeting_id}/summarize

Trigger a re-summarization of an existing meeting using a specified (or default) template. The meeting must be in `completed` or `failed` status (not currently processing).

**Request**
```
POST /api/v1/meetings/123/summarize
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": 2
}
```

- `template_id`: optional integer. If omitted, uses the user's active default template (personal default or system default).

**Success Response** `202 Accepted`
```json
{
  "meeting_id": 123,
  "status": "processing",
  "sub_status": "summarizing",
  "template_id": 2,
  "template_name": "Meeting Minutes"
}
```

**Error Responses**
- `400 Bad Request` — meeting is not in a re-summarizable state
  ```json
  { "detail": "Meeting is currently being processed. Try again when processing is complete." }
  ```
- `401 Unauthorized`
- `403 Forbidden` — meeting belongs to a different user
- `404 Not Found` — meeting or template not found
