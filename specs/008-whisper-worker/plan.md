# Implementation Plan: WhisperX Transcription Backend

**Branch**: `008-whisper-worker` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-whisper-worker/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a robust, local transcription worker for Zabt using the **WhisperX** library and Celery + Redis. This implementation will replace the synchronous OpenAI API placeholder with a high-performance machine-learning pipeline, ensuring precise word-level alignment and speaker diarization, while retaining resilience through automatic CPU fallback. To support seamless frontend UI updates, the worker will mutate `status` and `sub_status` directly in the database. Media storage will transition from local FS to S3-compatible object storage (MinIO for dev, AWS S3 for production) to allow distributed worker nodes.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, Celery, Redis, WhisperX, Pyannote-Audio, Whisper, Boto3 (for S3/MinIO)
**Storage**: PostgreSQL (SQLModel), S3 Protocol (MinIO locally)
**Testing**: pytest (unit/integration), Playwright/Python (E2E)
**Target Platform**: Linux server, Docker Engine (with NVIDIA Container Toolkit for GPU passthrough)
**Project Type**: web application (backend + worker)
**Performance Goals**: <5 min transcription for 30m audio on GPU
**Constraints**: Requires `HF_AUTH_TOKEN` for Pyannote DIARIZATION; Requires `ffmpeg` binary.
**Scale/Scope**: Horizontally scalable Celery worker nodes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Backend payload matches existing frontend mapping logic |
| API Contract — contracts/ populated | yes | pass | Will update to support S3 upload signatures |
| Auth/Security — no hardcoded secrets | yes | pass | MinIO and HF keys bound strictly to `.env` |
| Env Config — vars in quickstart.md | yes | pass | Required `MINIO_*` and `HF_*` keys will be documented |
| Scope Boundary — within spec | yes | pass | Sticks strictly to spec boundaries |
| E2E Testing — Playwright/Python in tests/e2e/ | yes | pass | Playwright pipeline validation |

## Project Structure

### Documentation (this feature)

```text
specs/008-whisper-worker/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── core/
│   │   └── config.py        # Add S3/MinIO & HF environment variables
│   ├── services/
│   │   ├── storage.py       # Refactor to support Boto3 for MinIO/S3
│   │   └── transcription.py # New WhisperX 3-stage service layer
│   └── worker.py            # Revamped Celery pipeline and status dispatcher
└── tests/
    └── e2e/                 # Playwright integration tests

frontend-2/
└── src/                     # Existing API clients updated for S3 uploads logic
```

**Structure Decision**: Web application spanning the `backend/` FastApi + Celery architecture and `frontend-2/` UI components. Storage abstractions will map neatly to standard Object Storage primitives.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A       | N/A        | N/A |
