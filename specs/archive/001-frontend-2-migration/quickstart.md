# Quickstart: Frontend-2 Migration

**Branch**: `001-frontend-2-migration` | **Date**: 2026-02-19

This guide explains how to scaffold, run, and test the `frontend-2` application and its infrastructure changes.

---

## Prerequisites

- Node.js 20+ and npm installed (for local development)
- Docker and Docker Compose installed (for full stack)
- Backend running (`002-api-alignment` changes applied, including `SECRET_KEY` in `.env`)

---

## 1. Scaffold frontend-2

`frontend-2` currently contains only `.agent/` and `.specify/` scaffolding. Before running, you must initialize it as a Next.js application.

**Option A — Copy from old frontend (recommended for migration):**
```bash
# From repo root
cp frontend/package.json frontend-2/
cp frontend/package-lock.json frontend-2/
cp frontend/tsconfig.json frontend-2/
cp frontend/next.config.ts frontend-2/
cp frontend/postcss.config.mjs frontend-2/
cp frontend/eslint.config.mjs frontend-2/
cp frontend/next-env.d.ts frontend-2/
cp frontend/Dockerfile frontend-2/
cp -r frontend/public frontend-2/
# Then add the new app/ directory (new pages + updated api.ts)
```

**Option B — Fresh scaffold with create-next-app:**
```bash
cd frontend-2
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
```
Then copy `frontend/app/components/` and update `app/lib/api.ts`.

---

## 2. Install Dependencies (local dev)

```bash
cd frontend-2
npm install
```

---

## 3. Environment Setup

Create `frontend-2/.env.local` for local development:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

This file is not committed to git (add to `.gitignore` if not already there).

---

## 4. Run Locally (without Docker)

First, ensure the backend is running:
```bash
docker-compose up db redis api worker
```

Then start the frontend:
```bash
cd frontend-2
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 5. Run with Docker Compose (full stack)

After updating `docker-compose.yml` (see step 6):

```bash
docker-compose up --build
```

The `web` service now builds from `./frontend-2`.

---

## 6. Update docker-compose.yml

Change the `web` service `context` from `./frontend` to `./frontend-2`:

```yaml
# Before:
web:
  build:
    context: ./frontend
    dockerfile: Dockerfile

# After:
web:
  build:
    context: ./frontend-2
    dockerfile: Dockerfile
```

Also verify the `environment` section passes `NEXT_PUBLIC_API_URL`:
```yaml
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 7. Update Backend CORS

In `backend/app/main.py`, replace:

```python
# Before:
allow_origins=["*"],

# After:
allow_origins=["http://localhost:3000"],
```

---

## 8. Verify the Migration

### Check 1: Frontend-2 loads
Open `http://localhost:3000` — the app should load. Verify it is serving from `frontend-2` by making a small visual change (e.g., change the title) and confirming it appears.

### Check 2: Home page upload works
1. Register a new account at `/register`
2. Log in at `/login`
3. Upload an audio file on the home page
4. Confirm: success message shown; no CORS errors in browser console

### Check 3: Meetings list is real
Navigate to `/meetings` — the list should show actual meetings from the database, not mocked data.

### Check 4: Meeting detail loads
Click a completed meeting — it should show the transcript, summary, and action items.

### Check 5: No references to old frontend
```bash
grep -r "./frontend" docker-compose.yml
# Should return nothing (or only comments referencing the old directory)
```

### Check 6: Old frontend still works (standalone)
```bash
cd frontend
npm run dev
# Should still start on localhost:3001 or fail gracefully on port conflict
```

---

## 9. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `CORS error` in browser | CORS not updated in backend | Update `allow_origins` in `backend/app/main.py` |
| `401 Unauthorized` on upload | Not logged in or token expired | Log in at `/login`; check localStorage has `access_token` |
| `Cannot find module 'next'` | `npm install` not run | Run `npm install` in `frontend-2/` |
| `Package.json not found` | `frontend-2` not yet scaffolded | Follow step 1 above |
| Docker build fails | `frontend-2` missing Dockerfile | Copy `Dockerfile` from `frontend/` |
| Port 3000 already in use | Old `frontend` still running | Stop old dev server first |
