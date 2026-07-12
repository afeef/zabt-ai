# Implementation Plan: Medical Transcription Type Selection

**Branch**: `026-medical-transcription` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-medical-transcription/spec.md`

## Summary

Add transcription type selection (General / Medical) to the upload flow. The GPU worker routes to WhisperX or MedASR based on the `transcription_type` field. Multi-stage Docker build with a base image on Docker Hub for fast rebuilds. The project is managed with uv/pyproject.toml for reproducible builds.

## Technical Context

**Language/Version**: Python 3.11 (backend + GPU worker), TypeScript 5 / Node.js 20 (frontend-2)
**Primary Dependencies**: FastAPI, SQLModel, Celery (backend); Next.js 16, React 19, Tailwind CSS 4, shadcn/ui (frontend); WhisperX, google/medasr, pyannote-audio (GPU worker)
**Storage**: PostgreSQL (via SQLModel + Supabase), S3/MinIO (audio files)
**Testing**: Playwright/Python (E2E), manual verification
**Target Platform**: Linux server (VPS + RunPod serverless)
**Project Type**: Web application (full-stack) + GPU microservice
**Performance Goals**: Medical transcription within 2x processing time of general; no cold-start penalty
**Constraints**: MedASR model (105M params) baked into Docker image; English-only for medical
**Scale/Scope**: Same user base; medical transcription is an additional model option

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | PASS | Upload modal already uses shadcn/ui components; medical/general toggle follows existing button patterns |
| API Contract | Yes | PASS | Existing `/meetings/` endpoint extended with `transcription_type` field; contract documented |
| Auth/Security | Yes | PASS | No new auth flows; existing JWT validation applies to all meeting operations |
| Env Config | Yes | PASS | `MEDASR_MODEL` env var added to docker-compose and documented in quickstart.md |
| Scope Boundary | Yes | PASS | Limited to transcription type selection; LLM model selection and user preferences explicitly deferred |
| E2E Testing | Yes | PASS | E2E test planned for upload with medical type selection |
| Repository Pattern | Yes | PASS | `MeetingService.update_transcription_type()` uses BaseService pattern |
| Provider Abstraction | Yes | PASS | `GpuTranscriptionClient` implements `TranscriptionProvider` protocol; routing happens inside GPU worker |
| Cost Awareness | Yes | PASS | Both models run on same self-hosted GPU; no additional per-minute API costs |
| Migration Safety | Yes | PASS | WhisperX remains the default; MedASR is additive, not a replacement |
| DB Migration | Yes | PASS | Alembic migration adds `transcription_type` column with default "general" |
| shadcn/ui Components | Yes | PASS | Upload modal toggle uses shadcn/ui Button components |

## Project Structure

### Documentation (this feature)

```text
specs/026-medical-transcription/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py                          # TranscriptionType enum, Meeting model
│   ├── worker.py                          # Celery task passes transcription_type to GPU client
│   └── services/
│       ├── meeting.py                     # update_transcription_type(TranscriptionType)
│       └── transcription/
│           ├── types.py                   # TranscriptionConfig with TranscriptionType
│           ├── gpu_client.py              # Sends transcription_type.value in job payload
│           └── factory.py                 # TranscriptionBackend enum, get_provider()
├── alembic/versions/
│   └── f7a8b9c0d1e2_add_transcription_type.py  # Migration (already exists)

frontend-2/
├── app/
│   ├── components/
│   │   └── upload-modal.tsx               # General/Medical toggle buttons
│   └── lib/
│       └── api.ts                         # Meeting type with transcription_type field

zabt-gpu-worker/
├── pyproject.toml                         # uv-managed dependencies
├── uv.lock                               # Locked dependencies
├── Dockerfile.base                        # CUDA + Python + PyTorch base image
├── Dockerfile                             # FROM base, uv sync, copy source
├── scripts/
│   └── download_models.py                # Pre-downloads WhisperX + MedASR + pyannote
└── src/
    ├── config.py                          # MEDASR_MODEL setting
    ├── pipeline.py                        # Routes to _transcribe_whisperx or _transcribe_medasr
    ├── handler.py                         # RunPod handler
    ├── server.py                          # Local FastAPI server
    └── models.py                          # TranscriptionJobInput with transcription_type field
```

**Structure Decision**: Existing three-component layout (backend, frontend-2, zabt-gpu-worker). Changes span all three components plus Docker build restructuring.

## Complexity Tracking

No constitution violations to justify.
