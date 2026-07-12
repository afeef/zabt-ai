# Data Model: Backend API Alignment for Frontend-2

**Branch**: `002-api-alignment` | **Date**: 2026-02-19

## Overview

No database schema migrations are required for this feature. All data fields needed for meeting transcripts, summaries, and action items already exist in the `Meeting` table. This document describes the full entity model as it will be exposed through the API after this feature is implemented.

---

## Entities

### User

Represents an authenticated account holder.

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer (PK) | Auto-generated |
| `email` | string (unique) | Login identifier; indexed |
| `full_name` | string (optional) | Display name |
| `hashed_password` | string | bcrypt hash; never exposed via API |
| `tier` | enum: `free` / `pro` / `enterprise` | Account tier; defaults to `free` |
| `is_active` | boolean | Inactive accounts cannot log in |
| `minutes_used_this_month` | integer | Usage tracking for tier limits |

**Relationships**: One User → Many Meetings

**API exposure**: `email`, `full_name`, `tier`, `is_active`, `minutes_used_this_month` (via `UserBase`)

---

### Meeting

Represents a recorded meeting submitted for AI transcription and summarization.

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer (PK) | Auto-generated |
| `title` | string | Original filename as uploaded by user |
| `description` | string (optional) | Not currently used; reserved |
| `file_path` | string | Full path to stored audio/video file on disk |
| `duration_seconds` | integer (optional) | Not yet populated; reserved for future |
| `owner_id` | integer (FK → User) | Which user owns this meeting |
| `created_at` | datetime | UTC timestamp of upload |
| `status` | enum: `queued` / `processing` / `completed` / `failed` | Processing state |
| `transcript_text` | string (optional) | Raw transcript from audio transcription step |
| `summary_text` | string (optional) | AI-generated summary paragraph |
| `action_items_text` | string (optional) | Formatted list of action items with owners |

**Status Transitions**:
```
queued → processing → completed
              ↓
           failed
```

**Relationships**: Many Meetings → One User (owner)

**API exposure (MeetingRead)**: `id`, `title`, `description`, `file_path`, `duration_seconds`, `created_at`, `status`, `transcript_text`, `summary_text`, `action_items_text`

> **Note**: `file_path` is included in MeetingRead for internal consistency but should not be rendered in the frontend UI. The path is a server-side filesystem path, not a downloadable URL.

---

### Style Example (file-based, no DB table)

Represents a user-uploaded PDF document used for AI few-shot style learning. Stored only as a file; no database record.

| Attribute | Notes |
|-----------|-------|
| Filename | Original PDF filename |
| Storage location | `/media/styles/` on the shared Docker volume |
| Scope | Global — style examples apply to all users' meetings (MVP behavior) |

---

## File Storage Layout

```
/media/
├── uploads/                  # Audio/video meeting files
│   └── {uuid}_{original_name}  # e.g., a3f7e2b1_standup.mp3
└── styles/                   # PDF style examples
    └── {original_name}.pdf
```

**Collision prevention**: Meeting audio files are stored with a UUID prefix (`{uuid}_{original_name}`). The original filename is preserved in `Meeting.title` for display in the UI. Style files retain their original names (no UUID prefix) since they are not user-scoped.

---

## Configuration (Settings)

Changes to `backend/app/core/config.py`:

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `SECRET_KEY` | string | `SECRET_KEY` env var | **NEW** — JWT signing secret; no default (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `ACCESS_TOKEN_EXPIRE_MINUTES` env var | **NEW** — defaults to 60 |

All other existing settings (`DATABASE_URL`, `REDIS_URL`, `OPENAI_*`) remain unchanged.

---

## No Schema Migration Required

The existing `Meeting` table already contains all needed columns. The only backend data-layer change is:
1. **File naming**: UUID-prefix on disk (no DB column change; `Meeting.title` stores original name, `Meeting.file_path` stores the full disk path including UUID prefix)
2. **Settings**: New environment variables added to `Settings` class — no DB impact
