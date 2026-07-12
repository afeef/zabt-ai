# Frontend API Contract: frontend-2

**Branch**: `001-frontend-2-migration` | **Date**: 2026-02-19

This document defines every API call that `frontend-2` makes to the backend, organized by page. It serves as the integration contract between the frontend and backend teams.

All requests go to `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000/api/v1`).

Authenticated requests include the header:
```
Authorization: Bearer {token}
```
where `{token}` is read from `localStorage.getItem("access_token")`.

---

## Authentication Pages

### `/login` page

**Login**
```
POST /login/access-token
Content-Type: application/x-www-form-urlencoded

username={email}&password={password}

→ 200: { access_token: string, token_type: "bearer" }
→ 400: { detail: "Incorrect email or password" }
```
*On success*: Store `access_token` in `localStorage`. Redirect to `/`.

---

### `/register` page

**Register**
```
POST /users/
Content-Type: application/json

{ "email": string, "password": string }

→ 200: { email, full_name, tier, is_active, minutes_used_this_month }
→ 400: { detail: "The user with this email already exists" }
```
*On success*: Redirect to `/login`.

---

## Home Page (`/`)

### Upload a meeting audio file

```
POST /upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: {File}

→ 200: Meeting object (status: "queued")
→ 401: Not authenticated
→ 500: Server error
```
*On success*: Show confirmation; clear selected file; optionally redirect to `/meetings`.

### Upload a style PDF example

```
POST /styles/upload
Content-Type: multipart/form-data

files: {File}  (single PDF)

→ 200: string[] (list of saved filenames)
→ 500: Server error
```

### List existing style examples

```
GET /styles/

→ 200: string[] (list of filenames)
```
*Called on page load to show currently uploaded styles.*

---

## Meetings List Page (`/meetings`)

### Fetch meetings list

```
GET /meetings/?skip={n}&limit={n}
Authorization: Bearer {token}

→ 200: { items: Meeting[], total: number, skip: number, limit: number }
→ 401: Not authenticated
```
*Called on page load. Refresh when navigating back from detail page.*

### Delete a meeting

```
DELETE /meetings/{id}
Authorization: Bearer {token}

→ 204: (no content)
→ 401: Not authenticated
→ 404: Meeting not found
→ 409: Cannot delete while processing
```
*On success*: Remove meeting from local list state without refetching.*

---

## Meeting Detail Page (`/meetings/[id]`)

### Fetch meeting detail

```
GET /meetings/{id}
Authorization: Bearer {token}

→ 200: Meeting object (with transcript_text, summary_text, action_items_text)
→ 401: Not authenticated
→ 404: Meeting not found
```
*Called on page load and polled every 3–5 seconds while `status` is `"queued"` or `"processing"`. Stop polling when status is `"completed"` or `"failed"`.*

**Polling behaviour**:
- Start: immediately on page load
- Interval: 3 seconds while queued/processing; 10 seconds after 30 seconds elapsed
- Stop: when `status === "completed"` or `status === "failed"`
- Show: loading indicator while queued/processing; result sections once completed

---

## Error Handling Contract

| HTTP Status | Frontend Behaviour |
|-------------|-------------------|
| `401` | Clear localStorage token; redirect to `/login` |
| `403` | Show "Access denied" error message |
| `404` | Show "Not found" message; offer navigation back |
| `409` | Show specific message (e.g., "Cannot delete a meeting that is being processed") |
| `422` | Show field validation errors inline |
| `500` | Show generic "Something went wrong" message; log to console |
| Network error | Show "Could not reach server" message; retry available |
