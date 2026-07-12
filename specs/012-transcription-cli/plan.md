# Implementation Plan: Transcription CLI

**Branch**: `012-transcription-cli` | **Date**: 2026-02-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-transcription-cli/spec.md`

## Summary

Provide a Typer-based CLI that lets developers run the full transcription pipeline
(Whisper → alignment → diarization) against a local audio file, with optional AI
summarization, without requiring a running database, MinIO, or web server. The CLI
reuses the same `TranscriptionService` and `meeting_agent` already used by the
Celery worker, ensuring identical output.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: Typer (CLI framework), rich (terminal formatting — bundled with Typer), existing transcription stack (openai-whisper, whisperx, pyannote-audio, pydantic-ai)
**Storage**: N/A — CLI reads local files; no database or object storage required
**Testing**: pytest (unit) — no E2E tests (CLI-only, no browser UI)
**Target Platform**: Linux/macOS developer workstation (same machine running the backend locally)
**Project Type**: Backend extension — new `app/cli/` module within existing `backend/` project
**Performance Goals**: Process a 5-minute audio file through all phases without memory issues
**Constraints**: Must not import DB engine or establish database connections; must not require MinIO or Redis
**Scale/Scope**: Single developer tool; no concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | no | n-a | No UI changes |
| API Contract — contracts/ populated | no | n-a | No new API endpoints |
| Auth/Security — no hardcoded secrets | no | n-a | CLI is local dev tool, no auth required |
| Env Config — vars in quickstart.md | yes | pass | HF_AUTH_TOKEN, OPENAI_*, WHISPER_MODEL already in config.py with defaults; documented in quickstart.md |
| Scope Boundary — within spec | yes | pass | Implementation covers spec FR-001 through FR-010 only |
| E2E Testing — Playwright/Python in tests/e2e/ | no | n-a | CLI-only feature, no browser UI |
| Repository Pattern — services/ follow base | no | n-a | CLI does not perform any database access |
| CLI/Typer — CLI built with Typer in app/cli/ | yes | pass | CLI built with Typer; code in dedicated `backend/app/cli/` module |

## Project Structure

### Documentation (this feature)

```text
specs/012-transcription-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (entities reference)
├── quickstart.md        # Phase 1 output (setup & usage guide)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── cli/
│   │   ├── __init__.py          # Typer app definition + entry point
│   │   └── transcribe.py        # `transcribe` command implementation
│   │
│   ├── services/
│   │   ├── transcription.py     # TranscriptionService (EXISTING — no changes)
│   │   ├── ai_agent.py          # meeting_agent (EXISTING — no changes)
│   │   ├── style_reader.py      # NEW — standalone PDF reader utility
│   │   └── styles.py            # MODIFIED — delegates to style_reader
│   │
│   └── core/
│       └── config.py            # Settings (EXISTING — no changes)
│
└── pyproject.toml               # MODIFIED — add typer dependency + [project.scripts] entry
```

**Structure Decision**: Backend-only extension. New `app/cli/` module follows the
constitution-mandated dedicated CLI module pattern. No frontend changes. The CLI is a
thin orchestration layer over existing reusable services.

### Reusable Architecture (Cross-Consumer Service Design)

The core services are consumed by three independent entry points:

```text
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│  Typer CLI          │    │  Celery Worker      │    │  FastAPI Endpoint   │
│  (app/cli/)         │    │  (app/worker.py)    │    │  (app/api/)         │
└────────┬───────────┘    └────────┬───────────┘    └────────┬───────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     Shared Service Layer                             │
│                                                                      │
│  TranscriptionService.process_audio(path, callback)                  │
│  meeting_agent.run_sync(transcript, deps=styles)                     │
│  read_style_examples(styles_dir) → str                               │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design rule**: The service layer MUST NOT import database, storage, or task-queue
modules. Each consumer (CLI, worker, API) is responsible for its own I/O orchestration
(file download, DB persistence, HTTP response formatting) and delegates only the
compute-heavy work to the shared services.

### Import Chain Isolation

| Module | DB Import? | CLI-Safe? | Notes |
|--------|-----------|-----------|-------|
| `app.services.transcription` | No | Yes | Imports only `app.core.config` |
| `app.services.ai_agent` | No | Yes | Imports only `app.core.config` + `pydantic_ai` |
| `app.services.style_reader` (NEW) | No | Yes | Standalone pypdf utility |
| `app.services.styles` | Yes (via BaseService) | No | Inherits from BaseService → imports engine |
| `app.core.config` | No | Yes | All fields have defaults; works without DB env vars |

## Complexity Tracking

> No Constitution Check violations. No entries needed.
