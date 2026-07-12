# ag-workspace Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-22

## Active Technologies
- TypeScript 5 / Node.js 20 + Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react (001-frontend-2-migration)
- No local storage; all state served by backend API (001-frontend-2-migration)
- TypeScript 5 / Node.js 20 + Next.js 16.1.6, React 19, Tailwind CSS 4, Axios, lucide-react, clsx (003-social-sso-login)
- Python 3.11 for backend, TypeScript (React/Next.js) for frontend + FastAPI, python-jose, @supabase/supabase-js, @supabase/ssr (001-migrate-supabase)
- Supabase PostgreSQL (001-migrate-supabase)
- Python 3.11 (backend), TypeScript / Node.js 20 (frontend-2) + FastAPI, SQLModel, Celery (Redis broker), pydantic-ai, pypdf, python-jose (002-api-alignment)
- Python 3.11 (backend), TypeScript / Next.js 16 (frontend) — rebrand: project renamed from "Pareto AI" to "Zabt" (001-rebrand-zabt)
- Python 3.11 (Backend), YAML (Docker Compose) + boto3, docker-compose (010-fix-minio-connection)
- MinIO (S3-compatible) (010-fix-minio-connection)
- Python 3.11 (backend), TypeScript / Node.js 20 (frontend-2) + FastAPI, SQLModel, Celery (Redis broker), boto3, pydantic-settings (011-minio-webhook)
- PostgreSQL (via SQLModel), MinIO (S3-compatible object storage) (011-minio-webhook)
- Python 3.11 + Typer (CLI framework), rich (terminal formatting — bundled with Typer), existing transcription stack (openai-whisper, whisperx, pyannote-audio, pydantic-ai) (012-transcription-cli)
- N/A — CLI reads local files; no database or object storage required (012-transcription-cli)
- Python 3.11 + FastAPI, SQLModel, Celery (Redis broker), google-cloud-speech (V2), google-cloud-storage, provider abstraction pattern (TranscriptionProvider Protocol) (013-whisper-chirp-migration)
- PostgreSQL (via SQLModel, unchanged), MinIO (audio uploads, unchanged), GCS (audio staging for Chirp 3 BatchRecognize) (013-whisper-chirp-migration)
- Python 3.11 (backend) + FastAPI, Celery, SQLModel, uv (package manager), Docker BuildKit (014-docker-build-optimization)
- PostgreSQL (via SQLModel), MinIO (S3-compatible object storage) — unchanged (014-docker-build-optimization)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19 + Tailwind CSS 4, clsx, @supabase/supabase-js, @supabase/ssr, lucide-react (015-logout-button)
- N/A — no data model changes; Supabase manages session cookies (015-logout-button)
- Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend) + FastAPI, Celery (canvas: chain, link_error), SQLModel, Redis; Next.js 16, React 19, Axios (017-transcription-progress)
- PostgreSQL (via SQLModel), Redis (Celery broker + Pub/Sub), MinIO (S3-compatible) (017-transcription-progress)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19, Tailwind CSS 4, lucide-react, clsx, Axios (018-home-ui-redesign)
- N/A — no data model or storage changes (018-home-ui-redesign)
- Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend) + FastAPI, SQLModel, Celery (Redis broker), pydantic-ai / OpenAI client; Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react (001-summary-templates)
- PostgreSQL (via SQLModel) — new `summarytemplate` table; `user` and `meeting` tables extended (001-summary-templates)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19, `pdfmake` (new), `@types/pdfmake` (new dev dep) (001-export-summary-pdf)
- YAML (Docker Compose + Kong declarative config); Python 3.11 env var change only — no code changes required + Kong Gateway 3.6 (Docker image `kong:3.6`), existing Docker Compose stack (001-kong-api-gateway)
- MinIO (S3-compatible) — unchanged; access pattern changes (routed through Kong) (001-kong-api-gateway)
- N/A — all analytics data lives in PostHog Cloud (001-product-analytics)
- Python 3.11 (backend only — no frontend changes) + FastAPI 0.129+, Celery 5.6+, SQLModel 0.0.37, OpenAI SDK 2.21+, Logfire 4.25.0 (already installed) (001-observability)
- PostgreSQL via SQLModel (unchanged) (001-observability)
- Python 3.11 (backend), TypeScript / Node.js 20 (frontend-2), YAML (Docker Compose, Kong, Cloudflare) + Docker Compose, Cloudflare Tunnel (`cloudflared`), Kong 3.6, PostgreSQL 16, Redis 7, MinIO, Qdrant, Celery (019-vps-lift-shift)
- PostgreSQL (via SQLModel), MinIO (S3-compatible), Redis (Celery broker), Qdrant (vector DB, empty for now) (019-vps-lift-shift)
- Python 3.11 (backend) + FastAPI, boto3, Celery (Redis broker), pydantic-settings (020-s3-storage-switch)
- PostgreSQL (via SQLModel), MinIO/S3 (object storage) (020-s3-storage-switch)
- Python 3.11 (backend worker + RunPod handler) + FastAPI, Celery (Redis broker), `runpod` Python SDK (new — client calls), WhisperX, pyannote-audio, boto3 (021-runpod-worker)
- PostgreSQL (via SQLModel), S3/MinIO (audio files — presigned URLs passed to RunPod) (021-runpod-worker)
- Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend) + FastAPI, SQLModel (backend); Next.js 16, React 19, Tailwind CSS 4, Tiptap (new — `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-link`, `tiptap-markdown`) (001-edit-summary)
- PostgreSQL (via SQLModel) — two new columns on `meeting` table (001-edit-summary)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19 + pdfmake (already installed), existing `pdf-export.ts` utility (001-transcript-pdf-download)
- Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend-2) + FastAPI, WeasyPrint (v68+), mistune (v3+), existing SQLModel/Celery stack; Next.js 16, React 19, Axios, lucide-react (001-server-pdf-export)
- PostgreSQL (via SQLModel) — read-only access to existing meeting data. No new tables. (001-server-pdf-export)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19, Tailwind CSS 4 + shadcn/ui (new), @radix-ui/* (new — installed by shadcn/ui), clsx (existing), tailwind-merge (existing), lucide-react (existing), Axios, @tiptap/* (unchanged) (001-shadcn-ui-migration)
- N/A — frontend-only, no data model changes (001-shadcn-ui-migration)
- Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend-2) + FastAPI, SQLModel, Celery (Redis broker), yt-dlp (new — YouTube audio extraction); Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react, shadcn/ui (001-youtube-ingestion)
- PostgreSQL (via SQLModel) — extended `meeting` table with source fields; MinIO/S3 (audio files) (001-youtube-ingestion)
- TypeScript 5 / Node.js 20 + Next.js 16, React 19, Tailwind CSS 4, shadcn/ui, lucide-react, Axios (001-unified-processing-queue)
- N/A — session-only React state (no persistence) (001-unified-processing-queue)
- Python 3.11 (backend), YAML (Docker Compose) + FastAPI, SQLModel, Celery, asyncpg, Alembic (022-supabase-db-migration)
- PostgreSQL (migrating from self-hosted → Supabase managed); MinIO/S3 (unchanged) (022-supabase-db-migration)
- Python 3.11 (backend only — no frontend changes) + FastAPI, Celery, httpx (new — async HTTP client for Telegram Bot API), pydantic-settings (023-telegram-notifications)
- N/A — no new tables or schema changes (023-telegram-notifications)
- Python 3.11 (backend only) + FastAPI, Celery, SQLAlchemy, sentry-sdk (new), langfuse (new) (024-sentry-langfuse)
- N/A — no schema changes (024-sentry-langfuse)
- Python 3.11 (both main worker and GPU service) (025-gpu-worker-extraction)
- PostgreSQL via SQLModel (main worker only), S3/MinIO (presigned URLs for audio) (025-gpu-worker-extraction)
- Python 3.11 (backend + GPU worker), TypeScript 5 / Node.js 20 (frontend-2) + FastAPI, SQLModel, Celery (backend); Next.js 16, React 19, Tailwind CSS 4, shadcn/ui (frontend); WhisperX, google/medasr, pyannote-audio (GPU worker) (026-medical-transcription)
- PostgreSQL (via SQLModel + Supabase), S3/MinIO (audio files) (026-medical-transcription)
- Python 3.11 (backend + new vision-worker service), TypeScript 5 / Node.js 20 (frontend-2) + FastAPI, Celery, SQLModel (backend); FastAPI, Typer, ollama-py, easyocr, scenedetect, imagehash, ffmpeg-python (zabt-vision-worker) (027-visual-breakdown)
- PostgreSQL (via SQLModel + Supabase) — new `visualsegment` table + 7 `visual_breakdown_*` cols on `meeting`; S3/MinIO under `users/{owner_id}/meetings/{meeting_id}/visual/` for keyframes + raw output JSON (027-visual-breakdown)

## Project Structure

```text
backend/
frontend-2/
zabt-vision-worker/   # New (PR #128) — stateless Qwen3-VL pipeline
```

## Commands

```bash
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd frontend-2 && npm run dev

# Monorepo (run from repo root)
npm run build:shared     # compile @zabt/shared
npm run dev:shared       # watch mode
npm run dev:web          # alias for frontend-2 dev
```

## Code Style

Python 3.11 (backend): Use Repository Pattern (BaseService) for all data access.
TypeScript / Node.js 20 (frontend-2): Follow standard conventions and design system.

## Recent Changes
- 027-visual-breakdown (PRs #128, #130): Added new stateless `zabt-vision-worker/` service (Python 3.11, FastAPI + Typer + Ollama for local Qwen3-VL inference, scenedetect/easyocr/imagehash for multi-signal candidate generation). Backend wiring: new `visualsegment` table + 7 columns on `meeting`, `VisualSegmentService`, `VisionClient` mirroring `GpuTranscriptionClient`, `stage_visual_breakdown` Celery task with per-stage PostHog telemetry. Two new endpoints (`POST /meetings/{id}/visual-breakdown`, `GET /meetings/{id}/visual-segments`). Plan 3 (frontend tab + viewer) is written but not executed. Local-dev infra: backend `Settings` switched to absolute root `.env` path + `python-dotenv` bootstrap; new `zabt_test` DB in `docker/postgres/init.sql`.
- 026-medical-transcription: Added Python 3.11 (backend + GPU worker), TypeScript 5 / Node.js 20 (frontend-2) + FastAPI, SQLModel, Celery (backend); Next.js 16, React 19, Tailwind CSS 4, shadcn/ui (frontend); WhisperX, google/medasr, pyannote-audio (GPU worker)
- 025-gpu-worker-extraction: Added Python 3.11 (both main worker and GPU service)

<!-- MANUAL ADDITIONS START -->

## Design System

See `DESIGN.md` for the complete design system reference. Key rules for AI agents:

- **Pink/rose accent** (`oklch(0.586 0.253 17.585)`) is the ONLY saturated color in core UI
- **No box shadows** — use borders and background shifts for depth
- **Warm stone neutrals** only — never blue-gray (use `stone-*`, not `slate-*`, `gray-*`, or `zinc-*`)
- **`text-sm` (14px)** for all body text, `text-2xl` for page titles, `text-lg` for section headings
- **`rounded-lg` (10px)** for all containers, `rounded-4xl` for pill badges
- **Three font weights**: 400 (read), 500 (interact), 600-700 (announce)
- **Inter** for UI text, **JetBrains Mono** for code/technical
- **Icons**: lucide-react only
- **Dark mode**: semi-transparent borders (`oklch(1 0 0 / 10%)`), never solid light borders on dark
- **shadcn/ui** components with `@base-ui/react` primitives, styled via CVA variants

<!-- MANUAL ADDITIONS END -->

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health
