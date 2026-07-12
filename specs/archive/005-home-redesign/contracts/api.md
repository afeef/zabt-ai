# API Contracts: Home Page Redesign

**Feature**: 005-home-redesign  
**Date**: 2026-02-22

---

> **Note**: This feature introduces **no new API endpoints**. The contracts below document the existing endpoints consumed by the new UI components. They are referenced here as required by constitution Principle III.

---

## GET /api/v1/meetings/

**Purpose**: Fetch the authenticated user's meetings for the home page activity feed.

**Method**: `GET`  
**Path**: `/api/v1/meetings/?skip={skip}&limit={limit}`  
**Auth**: Bearer token (Supabase JWT) via `Authorization` header

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | `integer` | `0` | Pagination offset |
| `limit` | `integer` | `20` | Maximum items to return |

### Success Response — `200 OK`

```json
{
  "items": [
    {
      "id": 42,
      "title": "Q1 Planning",
      "description": null,
      "file_path": "uploads/q1-planning.mp3",
      "duration_seconds": 3600,
      "created_at": "2026-02-22T06:00:00Z",
      "status": "completed",
      "transcript_text": "...",
      "summary_text": "The team discussed Q1 objectives...",
      "action_items_text": "1. Draft roadmap by Friday"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

### Error Responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | Missing or expired JWT — interceptor redirects to `/login` |
| `500 Internal Server Error` | Unexpected server failure — UI shows error banner |

---

## Supabase Auth — getUser()

**Purpose**: Retrieve the signed-in user's profile for the greeting and sidebar avatar.

**Method**: Supabase client call (not a raw HTTP endpoint)  
**Client**: `createClient()` from `@/app/lib/supabase/client`  
**Call**: `supabase.auth.getUser()`

### Success Shape

```typescript
{
  data: {
    user: {
      id: string,
      email: string,
      user_metadata: {
        full_name?: string
      }
    }
  }
}
```

**Consumed fields**: `full_name` (greeting + avatar initials), `email` (sidebar secondary label)
