# Quickstart: Backend API Alignment for Frontend-2

**Branch**: `002-api-alignment` | **Date**: 2026-02-19

This guide explains how to run and manually test the backend changes introduced in this feature.

---

## Prerequisites

- Docker and Docker Compose installed
- `backend/` directory with all existing code
- `.env` file at the repo root (see below)

---

## 1. Environment Setup

Create or update `.env` in the repository root:

```
# Required: generate a strong random string (e.g., openssl rand -hex 32)
SECRET_KEY=your-strong-random-secret-key-here

# Database (defaults work with docker-compose)
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=meetily_clone

# AI Model (LM Studio or compatible endpoint)
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
OPENAI_API_KEY=lm-studio
OPENAI_MODEL=llama-3-8b
```

> **Why SECRET_KEY?** The JWT signing secret was previously hardcoded as `"your-secret-key-here"` in source code. This change moves it to the environment so it is not checked into version control.

---

## 2. Start the Stack

```bash
docker-compose up --build
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Celery worker (background task processor)
- Web frontend — **frontend-2** (port 3000) ← updated from `frontend`

---

## 3. Verify the Backend is Running

```
GET http://localhost:8000/
```

Expected response:
```json
{"message": "Welcome to Meetily Clone API", "docs": "/docs"}
```

Interactive API docs available at: `http://localhost:8000/docs`

---

## 4. Testing the New Endpoints

### Step 1: Register a user

```
POST http://localhost:8000/api/v1/users/
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "testpassword123"
}
```

### Step 2: Log in to get a token

```
POST http://localhost:8000/api/v1/login/access-token
Content-Type: application/x-www-form-urlencoded

username=test@example.com&password=testpassword123
```

Save the `access_token` from the response.

### Step 3: Upload a meeting

```
POST http://localhost:8000/api/v1/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: (attach an audio file)
```

Expected: 200 response with `status: "queued"` and a real `id`.

### Step 4: List your meetings

```
GET http://localhost:8000/api/v1/meetings/
Authorization: Bearer {access_token}
```

Expected: A paginated list containing the meeting you just uploaded.

### Step 5: Poll for meeting results

```
GET http://localhost:8000/api/v1/meetings/{id}
Authorization: Bearer {access_token}
```

Poll every 3–5 seconds. Status will transition: `queued` → `processing` → `completed`

When `completed`, the response includes:
- `transcript_text`: full audio transcript
- `summary_text`: AI-generated summary
- `action_items_text`: extracted action items

### Step 6: Delete a meeting

```
DELETE http://localhost:8000/api/v1/meetings/{id}
Authorization: Bearer {access_token}
```

Expected: 204 No Content. Confirm the meeting no longer appears in the list.

---

## 5. Verifying Security Fixes

### JWT secret from environment
Check that the backend starts without errors when `SECRET_KEY` is set in `.env`. The hardcoded string `"your-secret-key-here"` should no longer appear in `security.py` or `deps.py`.

### Upload requires authentication
Try uploading without a token:
```
POST http://localhost:8000/api/v1/upload
Content-Type: multipart/form-data

file: (attach any file)
```
Expected: **401 Unauthorized** (was previously accepted without auth).

### Meeting ownership isolation
Register a second user and confirm they cannot see or delete the first user's meetings.

---

## 6. Checking the Celery Worker

When a meeting is uploaded, the Celery worker should begin processing. Check worker logs:

```bash
docker-compose logs worker --follow
```

Expected output sequence:
```
Processing meeting {id}...
Attempting transcription...
Running summarization agent...
Meeting {id} processing complete.
```

---

## 7. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `SECRET_KEY not set` error | Missing `.env` variable | Add `SECRET_KEY=...` to `.env` |
| Upload returns 401 | Token expired or missing | Re-login and use new token |
| Meeting stays in "queued" | Worker not running | Run `docker-compose up worker` |
| Worker log shows "File not found" | UUID filename mismatch | Check `Meeting.file_path` matches disk path |
| CORS error in browser | `frontend-2` origin not in allowed list | Verify CORS config in `backend/app/main.py` |
