# Research: Docker Build Optimization

**Feature**: 014-docker-build-optimization
**Date**: 2026-03-01

## R1: Dependency Splitting Strategy

**Decision**: Use PEP 735 `[dependency-groups]` to create an `ml` group for heavy ML packages.

**Rationale**: Dependency groups are designed for deployment-environment concerns (not published to PyPI). The project already uses `[dependency-groups]` for `dev`. The `ml` group follows the same pattern. `uv sync --group ml` installs the group; `uv sync` (without `--group ml`) excludes it. All groups share a single `uv.lock` lockfile, so compatibility is guaranteed across profiles.

**Alternatives considered**:
- `[project.optional-dependencies]` (extras): Designed for published packages where downstream consumers choose features. Not appropriate here — ML deps are a deployment concern, not a user-facing feature toggle. Would work technically but semantically incorrect.
- Separate `pyproject.toml` files: Would require restructuring into a monorepo with separate packages. Overkill for this use case and breaks the single-codebase constraint.
- Requirements files (`requirements-api.txt`, `requirements-worker.txt`): Legacy approach that loses uv lockfile guarantees. Not recommended.

**Packages moved to `ml` group**:
- `openai-whisper>=20250625` — Whisper speech-to-text (pulls in torch ~2 GB)
- `whisperx>=3.8.1` — Enhanced whisper with alignment (pulls in additional torch deps)
- `pyannote-audio>=4.0.4` — Speaker diarization (pulls in torch, torchaudio)

All three packages transitively pull in `torch`, `torchaudio`, and CUDA bindings, which account for ~6-8 GB of the final image size.

## R2: Docker Multi-Target vs Separate Dockerfiles

**Decision**: Single Dockerfile with named build targets (`FROM ... AS api` and `FROM ... AS worker`).

**Rationale**: Single source of truth for all build logic. Docker BuildKit only processes stages required by the target — building `--target api` never touches the `worker` stage. The `api` and `worker` targets use different base images (`python:3.11-slim` vs `nvidia/cuda`), so they cannot share final layers anyway, but a single file keeps the build definition canonical and avoids duplicating uv/COPY patterns.

**Alternatives considered**:
- Separate Dockerfiles (`Dockerfile.api`, `Dockerfile.worker`): Simpler per file but duplicates boilerplate (uv setup, COPY patterns, ENV vars). Two files to maintain when common patterns change. No meaningful advantage for this project size.
- Docker Compose `extends` with overrides: Only works for runtime config, not build-time differences.

## R3: Base Image Selection

**Decision**: `python:3.11-slim` for API, `nvidia/cuda:12.1.1-runtime-ubuntu22.04` for worker.

**Rationale**: The API service has zero CUDA/GPU requirements. `python:3.11-slim` is ~45 MB compressed / ~130 MB uncompressed — orders of magnitude smaller than the CUDA image. The worker needs CUDA for GPU-accelerated torch/whisperx. The `-runtime` variant (not `-devel`) is sufficient since we don't compile CUDA code — we only run pre-built wheels.

**Size comparison**:
| Image | Compressed | Uncompressed |
|-------|-----------|-------------|
| python:3.11-slim | ~45 MB | ~130 MB |
| nvidia/cuda:12.1.1-runtime-ubuntu22.04 | ~350 MB | ~870 MB |

**Final estimated image sizes**:
| Target | Base + deps | Total |
|--------|-----------|-------|
| API (python:3.11-slim + core deps) | ~130 MB + ~200 MB | ~300-500 MB |
| Worker (nvidia/cuda + core + ML deps) | ~870 MB + ~7-9 GB | ~8-10 GB |

## R4: uv Sync Commands per Target

**Decision**: Use `--no-dev` for both production targets. Add `--group ml` for the worker target.

| Target | Install Command | What Gets Installed |
|--------|----------------|---------------------|
| API | `uv sync --frozen --no-dev` | Core 30 packages only |
| Worker | `uv sync --frozen --no-dev --group ml` | Core 30 + 3 ML packages |
| Local dev | `uv sync` | Core 30 + dev packages |
| Local dev + whisper | `uv sync --group ml` | Core 30 + dev + ML packages |

The `--frozen` flag ensures the lockfile is used as-is without re-resolving (fast, deterministic).

## R5: Docker Compose Build Targets

**Decision**: Use `build.target` property in docker-compose.yml to select the build stage.

```yaml
api:
  build:
    context: ./backend
    target: api
  image: zabt-api:latest

worker:
  build:
    context: ./backend
    target: worker
  image: zabt-worker:latest
```

`docker compose build api` builds only the API target. `docker compose build worker` builds only the worker target. `docker compose up` builds both as needed.

## R6: Application Code Impact

**Decision**: Zero application code changes required.

**Rationale**: The transcription provider factory (`factory.py`) already uses lazy imports — `WhisperProvider` and `ChirpProvider` are only imported when `get_provider()` is called. The API service never calls `get_provider()` directly (it only queues Celery tasks). Therefore, the API service never imports torch/whisper at runtime, and the absence of these packages in the API image causes no import errors.

Verified by tracing imports:
- `app/main.py` → imports FastAPI, routers, middleware, config — no ML imports
- `app/api/v1/endpoints/meetings.py` → imports models, services — no ML imports
- `app/worker.py` → imports `get_provider` from factory → lazy-loads WhisperProvider/ChirpProvider
- `app/services/transcription/factory.py` → imports inside `get_provider()` function body, not at module level

The health endpoint (`/api/v1/health/transcription`) imports `circuit_breaker` but not the providers themselves, so it works without ML packages.
