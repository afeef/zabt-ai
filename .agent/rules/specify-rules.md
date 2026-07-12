# zabt-ai Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-22

## Active Technologies
- TypeScript 5 / React (Next.js 15 App Router) & Python 3 (FastAPI) + Axios (for upload progress), Radix UI (for modal primitives, optional if we build raw Tailwind modal), Tailwind CSS v4 (001-meeting-upload)
- Server local filesystem or object storage (handled by existing backend endpoint) (001-meeting-upload)
- TypeScript 5 / React (Next.js 16 App Router) & Python 3 (FastAPI) + Axios (for upload progress), shadcn/ui (for the Dialog/modal components), Tailwind CSS v4 (001-meeting-upload)
- TypeScript 5 (Next.js 16 App Router) & Python 3.11 (FastAPI) + React, Tailwind CSS v4, shadcn/ui DropdownMenu (or native styling), Axios, Supabase (Auth/DB), Playwright (E2E) (006-delete-meeting)
- PostgreSQL (Supabase) for records, Object/File Storage for media (006-delete-meeting)
- TypeScript 5, Python 3.11 + Next.js 16 (App Router), React 19, Tailwind CSS v4, `react-virtuoso` (virtualized lists) (007-transcript-viewer)
- N/A (read-only frontend consumption of existing JSON payload/media URL) (007-transcript-viewer)
- Python 3.11 + FastAPI, Celery, Redis, WhisperX, Pyannote-Audio, Faster-Whisper, Boto3 (for S3/MinIO) (008-whisper-worker)
- PostgreSQL (SQLModel), S3 Protocol (MinIO locally) (008-whisper-worker)

- TypeScript 5 / Next.js 15 (App Router) + Tailwind CSS v4, `clsx`, Supabase JS client, Axios (005-home-redesign)

## Project Structure

```text
src/
tests/
```

## Commands

npm test && npm run lint

## Code Style

TypeScript 5 / Next.js 15 (App Router): Follow standard conventions

## Recent Changes
- 008-whisper-worker: Added Python 3.11 + FastAPI, Celery, Redis, WhisperX, Pyannote-Audio, Faster-Whisper, Boto3 (for S3/MinIO)
- 007-transcript-viewer: Added TypeScript 5, Python 3.11 + Next.js 16 (App Router), React 19, Tailwind CSS v4, `react-virtuoso` (virtualized lists)
- 006-delete-meeting: Added TypeScript 5 (Next.js 16 App Router) & Python 3.11 (FastAPI) + React, Tailwind CSS v4, shadcn/ui DropdownMenu (or native styling), Axios, Supabase (Auth/DB), Playwright (E2E)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
