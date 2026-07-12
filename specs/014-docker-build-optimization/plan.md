# Implementation Plan: Docker Build Optimization

**Branch**: `014-docker-build-optimization` | **Date**: 2026-03-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-docker-build-optimization/spec.md`

## Summary

Split the single monolithic `zabt-backend` Docker image (~8-10 GB) into two purpose-built images: a lightweight API image (~300-500 MB) using `python:3.11-slim` and a heavy worker image retaining the CUDA base for ML transcription. Uses `uv` dependency groups (PEP 735) to separate core dependencies from ML dependencies, and a single multi-target Dockerfile with `--target api` and `--target worker` build targets. Docker Compose updated to build each service with its own target. Enables rapid prototyping with sub-60-second API rebuilds while preserving full transcription capability in the worker.

## Technical Context

**Language/Version**: Python 3.11 (backend)
**Primary Dependencies**: FastAPI, Celery, SQLModel, uv (package manager), Docker BuildKit
**Storage**: PostgreSQL (via SQLModel), MinIO (S3-compatible object storage) — unchanged
**Testing**: Manual verification (docker compose up, image size checks, transcription job test)
**Target Platform**: Linux server (local deployment via Docker Compose + Cloudflare Tunnels)
**Project Type**: Web service (split into API + worker containers)
**Performance Goals**: API image <500 MB, API rebuild <60 seconds, full stack starts successfully
**Constraints**: Worker must retain CUDA 12.1 base for GPU-accelerated WhisperX; API must never import torch/whisper
**Scale/Scope**: Single-server deployment, 2 container images from 1 Dockerfile

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes |
| API Contract | No | N/A | No endpoint changes — API service behavior is unchanged |
| Auth/Security | No | N/A | No auth changes; env vars remain the same |
| Env Config | No | N/A | No new env vars introduced; existing ones are preserved |
| Scope Boundary | Yes | PASS | Changes limited to Dockerfile, docker-compose.yml, and pyproject.toml |
| E2E Testing | No | N/A | No user-facing flow changes; infrastructure-only change |
| Repository Pattern | No | N/A | No data access changes |
| CLI/Typer | No | N/A | No CLI changes |
| Provider Abstraction | No | N/A | Provider architecture unchanged; this feature only affects container packaging |
| Cost Awareness | No | N/A | No external API cost changes |
| Migration Safety | No | N/A | No provider migration; the existing WhisperProvider and ChirpProvider remain intact |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/014-docker-build-optimization/
├── plan.md              # This file
├── research.md          # Phase 0: dependency splitting & Docker strategy research
├── quickstart.md        # Phase 1: build & deployment commands
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── Dockerfile           # Multi-target: FROM ... AS api / FROM ... AS worker
├── .dockerignore        # Already exists, verify patterns
├── pyproject.toml       # Core deps in [project.dependencies], ML in [dependency-groups.ml]
├── uv.lock              # Regenerated after pyproject.toml change
└── app/                 # Application code — NO changes
    ├── main.py           # API entry point (unchanged)
    ├── worker.py         # Celery entry point (unchanged)
    └── services/
        └── transcription/
            ├── factory.py           # Lazy provider import (unchanged)
            ├── whisper_provider.py   # Only loaded by worker (unchanged)
            └── chirp_provider.py    # Only loaded by worker (unchanged)

docker-compose.yml       # Updated: separate build targets per service
```

**Structure Decision**: No new directories or files are created beyond replacing the existing Dockerfile content and updating docker-compose.yml. The pyproject.toml dependency layout changes but the file stays in place.

## Implementation Approach

### Step 1: Refactor pyproject.toml Dependencies

Move the three heavy ML packages from `[project.dependencies]` to `[dependency-groups.ml]`:

**Moved to `ml` group:**
- `openai-whisper>=20250625`
- `whisperx>=3.8.1`
- `pyannote-audio>=4.0.4`

**Remain in core dependencies:**
All other 30 packages stay in `[project.dependencies]` — they are needed by both the API and worker.

**After change:**
- `uv sync --frozen --no-dev` → installs core deps only (API)
- `uv sync --frozen --no-dev --group ml` → installs core + ML deps (worker)
- `uv sync` → installs core + dev deps (local development)
- `uv sync --group ml` → installs core + dev + ML deps (local development with whisper)

### Step 2: Regenerate uv.lock

After modifying pyproject.toml, run `uv lock` to regenerate the lockfile. All dependency groups are resolved together into a single lockfile, so compatibility is guaranteed.

### Step 3: Rewrite Dockerfile with Multi-Target Build

The existing single-stage Dockerfile is replaced with a multi-target build:

**Target `api`:**
- Base: `python:3.11-slim`
- System deps: `libpq-dev` only (for psycopg2)
- Python deps: `uv sync --frozen --no-dev --no-install-project` then `uv sync --frozen --no-dev`
- Entrypoint: `uvicorn app.main:app`
- Expected size: ~300-500 MB

**Target `worker`:**
- Base: `nvidia/cuda:12.1.1-runtime-ubuntu22.04` (unchanged from current)
- System deps: python3.11, ffmpeg, build-essential, libpq-dev, libgl1, libglib2.0
- Python deps: `uv sync --frozen --no-dev --group ml --no-install-project` then `uv sync --frozen --no-dev --group ml`
- Entrypoint: `celery -A app.worker.celery_app worker`
- Expected size: ~8-10 GB (unchanged — same as current single image)

Both targets use BuildKit cache mounts (`--mount=type=cache,target=/root/.cache/uv`) for fast rebuilds.

### Step 4: Update docker-compose.yml

- `api` service: `build.target: api`, `image: zabt-api:latest`
- `worker` service: `build.target: worker`, `image: zabt-worker:latest`
- `worker-gpu` service: `build.target: worker`, `image: zabt-worker:latest` (same image, GPU runtime config)
- All environment variables and volume mounts remain unchanged

### Step 5: Verify .dockerignore

Ensure the existing `.dockerignore` covers:
- `.venv/`, `__pycache__/`, `.git/`, `.env`
- `tests/` (not needed in production images)
- `specs/`, `.specify/`, `.claude/` (development artifacts)

## Complexity Tracking

> No constitution violations. No complexity exceptions needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
