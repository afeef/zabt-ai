# Data Model: Frontend-2 Migration

**Branch**: `001-frontend-2-migration` | **Date**: 2026-02-19

## Overview

`frontend-2` is a client-side application with no local database or persistent storage. All data is fetched from and written to the backend API. This document defines the data structures the frontend works with (matching the backend's API response schemas), the page/component architecture, and client-side state.

---

## Data Types (from API)

These types are defined in `frontend-2/app/lib/api.ts` and mirror the backend's response schemas.

### Meeting

Returned by `GET /meetings/` and `GET /meetings/{id}`.

```
Meeting {
  id: number
  title: string                    // original filename
  description: string | null
  file_path: string                // server-side path; not rendered in UI
  duration_seconds: number | null
  created_at: string               // ISO 8601 datetime
  status: "queued" | "processing" | "completed" | "failed"
  transcript_text: string | null   // null until processing completes
  summary_text: string | null      // null until processing completes
  action_items_text: string | null // null until processing completes
}
```

### MeetingList

Returned by `GET /meetings/` (paginated).

```
MeetingList {
  items: Meeting[]
  total: number
  skip: number
  limit: number
}
```

### User

Returned by `GET /users/me` and `POST /users/`.

```
User {
  email: string
  full_name: string | null
  tier: "free" | "pro" | "enterprise"
  is_active: boolean
  minutes_used_this_month: number
}
```

### AuthToken

Returned by `POST /login/access-token`.

```
AuthToken {
  access_token: string
  token_type: "bearer"
}
```

---

## Client-Side State

`frontend-2` uses React's `useState` and `useEffect` for local component state. No global state manager (Redux, Zustand, etc.) is required for MVP.

| State | Where | Type | Purpose |
|-------|-------|------|---------|
| `token` | `localStorage` key `"access_token"` | `string \| null` | JWT Bearer token; persists across page reloads |
| `uploading` | Home page component | `boolean` | Controls upload button disabled state and loading indicator |
| `files` | Home page component | `File[]` | Holds selected file(s) before upload |
| `meetings` | Meetings list page | `Meeting[]` | Fetched from `GET /meetings/` |
| `meeting` | Meeting detail page | `Meeting \| null` | Fetched from `GET /meetings/{id}` |
| `pollingActive` | Meeting detail page | `boolean` | Whether to poll for status updates (true when status is queued/processing) |

---

## Page & Component Architecture

### Pages

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Home: audio upload form + AI style PDF upload |
| `/meetings` | `app/meetings/page.tsx` | Real meetings list with status badges |
| `/meetings/[id]` | `app/meetings/[id]/page.tsx` | Meeting detail: transcript, summary, action items |
| `/login` | `app/login/page.tsx` | Login form (email + password) |
| `/register` | `app/register/page.tsx` | Registration form (email + password) |

### Components

| Component | File | Used By | Purpose |
|-----------|------|---------|---------|
| `Button` | `components/ui/button.tsx` | All pages | Reusable primary/secondary button |
| `StatusBadge` | `components/ui/status-badge.tsx` | Meetings list, detail | Color-coded status indicator (queued/processing/completed/failed) |
| `MeetingCard` | `components/meeting-card.tsx` | Meetings list | Summary card showing title, date, status |
| `FileUploadZone` | `components/file-upload-zone.tsx` | Home page | Drag-and-drop + click audio upload area |

### Layout

| File | Purpose |
|------|---------|
| `app/layout.tsx` | Root layout: HTML shell, font setup, global CSS, optional nav |
| `app/globals.css` | Tailwind base + custom CSS variables |

---

## API Client (`app/lib/api.ts`)

All backend communication is centralized here. New functions added vs old `frontend`:

| Function | Method | Endpoint | Status |
|----------|--------|----------|--------|
| `register(email, password)` | POST | `/users/` | NEW |
| `login(email, password)` | POST | `/login/access-token` | NEW |
| `uploadMeeting(file)` | POST | `/upload` | EXISTS (add auth header) |
| `getMeetings(skip?, limit?)` | GET | `/meetings/` | NEW (replaces mock) |
| `getMeeting(id)` | GET | `/meetings/{id}` | NEW |
| `deleteMeeting(id)` | DELETE | `/meetings/{id}` | NEW |
| `uploadStyle(file)` | POST | `/styles/upload` | EXISTS |
| `getStyles()` | GET | `/styles/` | EXISTS |

**Auth header**: All authenticated calls include `Authorization: Bearer {token}` where token is read from `localStorage.getItem("access_token")`.
