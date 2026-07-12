# Quickstart: Docker Build Optimization

**Feature**: 014-docker-build-optimization

## Prerequisites

- Docker with BuildKit enabled (Docker 23+ has it by default)
- Docker Compose v2
- uv package manager (for local development)

## Build Commands

### Build individual service images

```bash
# API image only (~300-500 MB, fast build)
docker compose build api

# Worker image only (~8-10 GB, slow build — only needed when ML deps change)
docker compose build worker
```

### Start the full stack

```bash
docker compose up
```

### Rebuild API after code changes (fast iteration)

```bash
docker compose build api && docker compose up -d api
```

## Local Development (without Docker)

```bash
cd backend

# API-only development (no ML packages)
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# With local Whisper transcription
uv sync --group ml
uv run python -m app.cli transcribe path/to/audio.wav
```

## Image Verification

```bash
# Check API image size (target: <500 MB)
docker images zabt-api:latest

# Check worker image size
docker images zabt-worker:latest

# Verify API starts correctly
docker compose up api
curl http://localhost:8000/api/v1/health

# Verify worker processes jobs
docker compose up worker
# Submit a transcription job through the API
```

## Environment Variables

No new environment variables are introduced. All existing variables from the current setup continue to work:

- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis for Celery broker
- `MINIO_ENDPOINT` — MinIO S3-compatible storage
- `TRANSCRIPTION_PROVIDER` — `whisper` or `chirp`
- `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` — LLM configuration
- `SUPABASE_URL`, `SUPABASE_JWT_SECRET` — Authentication
- `BACKEND_CORS_ORIGINS` — CORS configuration

## Cloudflare Tunnel Integration

The API service exposes port 8000. Point the Cloudflare Tunnel to `http://localhost:8000` (or `http://api:8000` from within the Docker network). No special configuration is needed — the tunnel proxies HTTP traffic to the API container.

```bash
# Example: cloudflared tunnel route
cloudflared tunnel --url http://localhost:8000
```

## Dependency Groups

| Group | Packages | Used By |
|-------|----------|---------|
| Core (`[project.dependencies]`) | fastapi, celery, sqlmodel, boto3, etc. (30 packages) | API + Worker |
| ML (`[dependency-groups.ml]`) | openai-whisper, whisperx, pyannote-audio | Worker only |
| Dev (`[dependency-groups.dev]`) | pytest, pytest-asyncio, httpx | Local development |
