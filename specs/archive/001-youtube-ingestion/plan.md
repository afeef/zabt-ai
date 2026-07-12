# Implementation Plan: YouTube URL Ingestion

**Branch**: `001-youtube-ingestion` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-ingestion/spec.md`

## Summary

Allow users to ingest YouTube videos as meetings by pasting a URL. The API endpoint validates URL format and creates a meeting record with `source_type: "youtube"`. A dedicated Celery task chain handles YouTube audio download (via yt-dlp), then feeds into the existing transcription → summarization pipeline. The frontend adds a "Paste URL" button and dialog to the home page, with a YouTube badge on meeting cards.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend-2)
**Primary Dependencies**: FastAPI, SQLModel, Celery (Redis broker), yt-dlp (new — YouTube audio extraction); Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react, shadcn/ui
**Storage**: PostgreSQL (via SQLModel) — extended `meeting` table with source fields; MinIO/S3 (audio files)
**Testing**: Playwright/Python E2E tests (constitution requirement); pytest for backend unit tests
**Target Platform**: Linux server (Docker), Web browser (frontend)
**Project Type**: Web application (full-stack)
**Performance Goals**: API response < 200ms for URL submission; YouTube download throughput limited by network; existing transcription performance unchanged
**Constraints**: Max 3 concurrent YouTube ingestions per user; max 4-hour video duration; yt-dlp must be installed in worker Docker image only (not API image)
**Scale/Scope**: Single new API endpoint, 1 new Celery task, 3 new frontend components, 1 Alembic migration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes — new UI components | PASS | Paste URL button, dialog, YouTube badge all use shadcn/ui components + design tokens |
| API Contract | Yes — new endpoint | PASS | Contract documented in `contracts/youtube-ingest.md` |
| Auth/Security | Yes — user data | PASS | Endpoint requires Supabase JWT; meeting scoped to authenticated user |
| Env Config | Yes — yt-dlp config | PASS | No new env vars needed (yt-dlp is a binary, not a service) |
| Scope Boundary | Yes | PASS | Implementation matches spec; no undocumented additions |
| E2E Testing | Yes — user-facing flow | PASS | E2E test planned: paste URL → meeting created → processing |
| Repository Pattern | Yes — data access | PASS | MeetingService handles all DB operations |
| CLI/Typer | No — no CLI | N/A | |
| Provider Abstraction | No — yt-dlp is a local binary, not an external API service | N/A | yt-dlp is a local tool installed in the worker image; it doesn't require a provider abstraction |
| Cost Awareness | No — yt-dlp is free/open-source | N/A | No external paid APIs added |
| Migration Safety | No — no provider replacement | N/A | |
| DB Migration | Yes — new columns on meeting table | PASS | Alembic migration adds source_type, source_url, youtube_* fields |
| shadcn/ui Components | Yes — new UI elements | PASS | Dialog, Button, Input, Badge all from shadcn/ui |

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-ingestion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── youtube-ingest.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py                          # Meeting model — add source_type, source_url, youtube_* fields
│   ├── worker.py                          # Add stage_youtube_download task + youtube pipeline chain
│   ├── services/
│   │   ├── meeting.py                     # MeetingService — add create_from_youtube(), count_active_youtube()
│   │   └── youtube.py                     # NEW — YouTube URL validation + metadata extraction utilities
│   └── api/v1/endpoints/
│       └── meetings.py                    # Add POST /meetings/youtube endpoint
├── alembic/versions/
│   └── xxx_add_youtube_source_fields.py   # NEW — Alembic migration
└── Dockerfile                             # Worker target — add yt-dlp installation

frontend-2/
├── app/
│   ├── (dashboard)/page.tsx               # Add Paste URL button to ActionBar
│   ├── components/
│   │   ├── action-bar.tsx                 # Add "Paste URL" button
│   │   ├── youtube-url-dialog.tsx         # NEW — URL input dialog
│   │   ├── meeting-feed.tsx               # Add YouTube badge to MeetingFeedCard
│   │   └── status-badge.tsx               # No changes needed (existing statuses cover YouTube flow)
│   └── lib/
│       ├── api.ts                         # Add submitYoutubeUrl() function
│       └── youtube-utils.ts               # NEW — client-side URL format validation

tests/e2e/
└── test_youtube_ingestion.py              # NEW — E2E test
```

**Structure Decision**: Follows existing web application structure (backend/ + frontend-2/). New files are minimal — 1 new backend service module, 1 new frontend component, 1 new frontend utility, 1 Alembic migration, 1 E2E test. Most changes extend existing files.

## Complexity Tracking

> No constitution violations. All gates pass.
