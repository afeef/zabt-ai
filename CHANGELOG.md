# Changelog

All notable changes to Zabt AI are documented here.

## [Unreleased] - 2026-04-19

### Added
- **Visual Breakdown — Plan 1: Vision Worker** (PR [#128](https://github.com/afeef/zabt-ai/pull/128), branch `feat/visual-breakdown`)
  - Standalone `zabt-vision-worker/` service. Stateless, mirrors `zabt-gpu-worker` pattern: video URL + transcript in, structured `JobResult` out (visual segments + per-stage metrics + raw-output S3 key).
  - Five-stage precision-first pipeline: ffmpeg frame extraction (2 fps) → multi-signal candidate generation (pHash + OCR diff + PySceneDetect + transcript-hint regex) → video-native detection via Qwen3-VL → cross-validation (single structured-output judge call per candidate with previous-keyframe and transcript context) → boundary refinement (high-fps rescan + pHash snap to exact transition frame).
  - Pluggable `VisionInference` Protocol with `OllamaInference` backend for local RTX 3090 testing. Transformers backend for RunPod is deferred to a follow-up plan.
  - FastAPI server (`/health`, `/run`) and Typer CLI (`zabt-vision run`, `zabt-vision serve`) share `JobInput`/`Settings`/`run_pipeline` end-to-end — no parallel implementation.
  - Per-stage exception isolation via `PipelineStageError` so the backend can populate `JobResult.failed_stage` for telemetry.
  - Heavy ML deps split into `[scene]` and `[ocr]` optional extras so unit-test iteration stays fast (no torch/easyocr install needed for the mocked tests).
  - 48 unit tests + 1 opt-in integration test, ruff clean.
- **Visual Breakdown — Plan 2: Backend Wiring** (PR [#130](https://github.com/afeef/zabt-ai/pull/130), branch `feat/visual-breakdown-backend`)
  - Alembic migration: new `visualsegment` table (autoincrement int PK, FK cascade to `meeting`) + 7 new `visual_breakdown_*` columns on `meeting`.
  - `VisualSegmentService` with two-pointer transcript alignment computed on read (no persisted join table — see Plan 2 spec for "Future work / versioning" rationale).
  - `VisionClient` mirroring `GpuTranscriptionClient`: HTTP single-call for local mode, RunPod submit/poll for production.
  - `stage_visual_breakdown` Celery task: status transitions, segment persistence, per-stage PostHog events, Telegram dispatch on completion, `failed_stage` propagation.
  - `POST /meetings/{id}/visual-breakdown` (202 with 400/403/404/409 guards) and `GET /meetings/{id}/visual-segments` (presigned screenshot URLs + transcript-aligned response).
  - `MeetingRead.visual_breakdown_status` exposed for the frontend tab state machine.
  - Telegram event kind `visual_breakdown_completed` (📸).
  - `storage.delete_prefix()` helper on both Minio and S3 backends; meeting-delete handler now wipes `users/{owner_id}/meetings/{meeting_id}/visual/` so screenshots and raw output JSON don't outlive the meeting.
  - Lean docker-compose service + CPU-only Dockerfile for the vision worker (scene-extra only — no torch).
  - 19 unit + integration tests.
- **Local-dev infra:** Backend's `Settings` now reads the single root `.env` via an absolute path (was CWD-relative). Added `python-dotenv` bootstrap so legacy modules reading `os.environ.get()` directly (e.g., `worker.py` for `TEMP_DIR`) see root `.env` values when running from the host. Added a `zabt_test` database to `docker/postgres/init.sql` so the pytest suite stays isolated from dev data.

### Planned
- **Visual Breakdown — Plan 3: Frontend Tab + Viewer** (branch `feat/visual-breakdown-frontend`, plan written, execution pending)
  - "Visual breakdown" tab on the meeting detail page in `frontend-2`.
  - Two-pane viewer (transcript cards on the left, sticky screenshot panel on the right tracked via `IntersectionObserver`), mobile single-column variant, fullscreen lightbox, audio-player seek on timestamp click, re-run confirm dialog.
  - Three frontend PostHog events.

## [0.1.0.0] - 2026-04-08

### Added
- **Meeting Intelligence (Phase 1):** Meeting-type-aware structured output. Users select a meeting type (Grooming, Standup, Retro, 1:1, Generic) and get domain-specific outputs. Grooming sessions produce user story cards, standups produce speaker update tables, retros produce three-column layouts.
- **AI Extraction Pipeline:** New Celery stage (`stage_extract_intelligence`) chains after summarization. Two LLM calls: one for highlights (action items, key questions, chapters) and one for meeting-type-specific structured output with JSON schema validation.
- **Enriched Meeting Detail Page:** Three tabs (Notes, Transcript, Structured Output). Notes tab shows inline action items, key questions, and chapters with clickable timestamps that seek the audio player. Structured Output tab renders a schema-driven generic view.
- **5 Preset Meeting Type Templates:** Generic, Grooming, Standup, Retro, 1:1. Each with tailored prompts, JSON schemas, and layout hints.
- **Highlights API:** `GET /highlights`, `PATCH /meeting-type`, `POST /re-extract` endpoints.
- **Headless Browser Bot Worker:** Rewrote Teams bot worker with Playwright + Xvfb + PulseAudio + ffmpeg for reliable meeting audio capture.
- **Microsoft Integration (Phase 1-4):** OAuth, calendar sync, OneDrive recording pickup, email summaries, Teams bot worker.

### Fixed
- Bot status enum standardization (uppercase values match names)
- Bot dispatch for any non-completed event
- Teams lobby handling and page load timing
- Calendar event deletion with linked bot jobs (FK constraint)
- Null meeting titles from Graph API
