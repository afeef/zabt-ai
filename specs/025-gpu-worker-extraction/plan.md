# Implementation Plan: GPU Worker Extraction

**Branch**: `025-gpu-worker-extraction` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-gpu-worker-extraction/spec.md`

## Summary

Extract GPU transcription/diarization code (WhisperX + pyannote) from the main backend into a standalone `zabt-gpu-worker` repository. The main worker becomes lightweight (no torch/CUDA deps) and communicates with the GPU service via a unified HTTP poll-based protocol. The GPU service supports dual-mode operation: RunPod serverless (production) and local HTTP server (development) from a single Docker image with models baked in at build time.

## Technical Context

**Language/Version**: Python 3.11 (both main worker and GPU service)
**Primary Dependencies**:
- Main worker: FastAPI, Celery (Redis broker), SQLModel, httpx (for GPU service communication), boto3
- GPU service: WhisperX, pyannote-audio, torch (CUDA 12.8), runpod SDK, FastAPI (local mode), sentry-sdk
**Storage**: PostgreSQL via SQLModel (main worker only), S3/MinIO (presigned URLs for audio)
**Testing**: Manual E2E testing (upload → transcript → summary pipeline)
**Target Platform**: Linux server (VPS for main worker, RunPod/local GPU for GPU service)
**Project Type**: Microservice extraction (splitting monolith worker into two services)
**Performance Goals**: Main worker Docker build < 60 seconds; transcription latency unchanged
**Constraints**: GPU service image must include all model weights (~8-10 GB); no runtime downloads
**Scale/Scope**: Single-tenant, ~10 concurrent transcription jobs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes |
| API Contract | Yes | PASS | GPU service HTTP contract documented in `contracts/` |
| Auth/Security | No | N/A | GPU service is internal, no user auth; presigned URLs for audio access |
| Env Config | Yes | PASS | New env vars documented in `quickstart.md` |
| Scope Boundary | Yes | PASS | Extraction only — no new features, same pipeline behavior |
| E2E Testing | No | N/A | No user-facing flow changes; backend-only refactor |
| Repository Pattern | No | N/A | No new data access patterns; existing services unchanged |
| CLI/Typer | No | N/A | No CLI involved |
| Provider Abstraction | Yes | PASS | Existing `TranscriptionProvider` protocol retained; `RunPodProvider` updated to use unified client |
| Cost Awareness | Yes | PASS | No change to processing costs; same models and providers |
| Migration Safety | Yes | PASS | Old local `WhisperProvider` code remains until GPU service validated; can fall back |
| DB Migration | No | N/A | No schema changes |
| shadcn/ui Components | No | N/A | No frontend changes |

## Project Structure

### Documentation (this feature)

```text
specs/025-gpu-worker-extraction/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── gpu-service-api.md
└── tasks.md
```

### Source Code

**Main repo (zabt-ai) changes:**

```text
backend/
├── app/
│   ├── services/
│   │   └── transcription/
│   │       ├── provider.py          # TranscriptionProvider protocol (unchanged)
│   │       ├── types.py             # Domain types (unchanged)
│   │       ├── factory.py           # Updated: remove local, add gpu-service client
│   │       ├── gpu_client.py        # NEW: unified HTTP client (RunPod + local GPU)
│   │       ├── runpod_provider.py   # REMOVE: replaced by gpu_client.py
│   │       ├── whisper_provider.py  # REMOVE: moved to gpu-worker repo
│   │       └── pipeline.py          # REMOVE: moved to gpu-worker repo
│   └── worker.py                    # Updated: remove local download stage logic
├── pyproject.toml                   # Updated: remove ml dependency group
├── Dockerfile                       # Updated: remove worker-base target, single lightweight image
└── Dockerfile.worker-base           # REMOVE: no longer needed
```

**New repo (zabt-gpu-worker):**

```text
zabt-gpu-worker/
├── pyproject.toml                   # torch, whisperx, pyannote-audio, runpod, fastapi, sentry-sdk
├── Dockerfile                       # CUDA 12.8 + models baked in at build time
├── src/
│   ├── handler.py                   # RunPod serverless handler (entry point)
│   ├── server.py                    # FastAPI local HTTP server (entry point)
│   ├── pipeline.py                  # Shared transcription pipeline (from backend)
│   ├── config.py                    # Settings (model names, device, Sentry DSN)
│   └── models.py                    # Request/response schemas
├── scripts/
│   └── download_models.py           # Pre-download models during Docker build
└── README.md
```

**Structure Decision**: Two-repo split. Main repo loses all GPU/ML code and dependencies. New repo is self-contained with its own Docker image, CI, and deployment.

## Complexity Tracking

No constitution violations.
