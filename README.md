# Zabt — AI Note Taker

Zabt is an AI-powered meeting note taker. It transcribes and summarizes your meetings automatically using a local AI backend secured by Supabase authentication.

## Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS 4 (deployed on Vercel)
- **Backend**: Python 3.11, FastAPI, Celery, SQLModel
- **Auth**: Supabase Cloud (JWT)
- **AI**: OpenAI-compatible API (local LM Studio or remote)
- **Database**: PostgreSQL 16
- **Queue**: Redis 7
- **Storage**: MinIO (local dev) or AWS S3 (production)
- **Gateway**: Kong 3.6 (API gateway + rate limiting)
- **Vector DB**: Qdrant (for future RAG/AI Chat)

## Architecture

```
Internet → Cloudflare (DNS proxy + SSL) → Kong (:80/:443) → FastAPI API (:8000)
                                                           → MinIO (:9000)
Frontend (Vercel) → Kong → FastAPI
```

### Services

| Service | Image | Purpose |
|---------|-------|---------|
| `db` | `postgres:16-alpine` | Primary database |
| `redis` | `redis:7-alpine` | Celery task broker |
| `minio` | `minio/minio` | Object storage — local only (`compose/storage.local.yml`) |
| `kong` | `kong:3.6` | API gateway, SSL termination, rate limiting (prod only — `compose/prod.yml`) |
| `api` | `zabt-api:latest` | FastAPI backend |
| `worker` | `zabt-worker:latest` | Celery worker |
| `worker-gpu` | `afeef/zabt-gpu-worker` | GPU transcription worker — local only (`compose/gpu.local.yml`) |
| `web` | `zabt-web` | Next.js frontend — local only (`compose/local.yml`) |

## Quick Start (Local Development)

The Compose stack is split into a base file plus opt-in overlays in
`compose/`. See [`compose/README.md`](compose/README.md) for the full guide.

Quick start (full standalone — local Postgres, MinIO, GPU worker):

```bash
cp compose/local.env.example .env
# Fill in Supabase credentials at minimum. Other secrets can stay empty.
docker compose up
```

Frontend at `http://localhost:3000`, API at `http://localhost:8000`,
MinIO console at `http://localhost:9001`.

To dev against cloud services (no GPU box, testing only api/worker), edit
`COMPOSE_FILE` in `.env`:

```
COMPOSE_FILE=docker-compose.yml:compose/local.yml
```

## Storage Providers

Zabt supports two storage backends, controlled by the `STORAGE_PROVIDER` environment variable.

### MinIO (Local Development — default)

Set `STORAGE_PROVIDER=minio` (or leave unset). MinIO runs as a Docker service and triggers the transcription pipeline via webhook.

```bash
# Start with MinIO + GPU worker + web (local dev)
# .env should have COMPOSE_FILE including compose/storage.local.yml + compose/gpu.local.yml
docker compose up -d
```

### AWS S3 (Production VPS)

Set `STORAGE_PROVIDER=s3` and configure the `S3_*` variables in `.env`:

```env
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY_ID=<your-aws-access-key>
S3_SECRET_ACCESS_KEY=<your-aws-secret-key>
S3_BUCKET_NAME=zabt-media
S3_PUBLIC_URL=https://s3.amazonaws.com
S3_REGION=us-east-1
```

When using S3, MinIO is not required. The frontend calls `POST /api/v1/meetings/{id}/confirm-upload` after uploading to trigger the transcription pipeline (replacing the MinIO webhook).

```bash
# Start without MinIO/web (VPS with S3 + RunPod transcription)
# .env should have COMPOSE_FILE=docker-compose.yml:compose/prod.yml (see compose/prod.env.example)
docker compose up -d
```

## Transcription Providers

Zabt supports two transcription backends, controlled by the `TRANSCRIPTION_PROVIDER` environment variable.

### Local (Development — default)

Set `TRANSCRIPTION_PROVIDER=local` (or leave unset). The worker runs Whisper + pyannote locally using the GPU.

### RunPod Serverless (Production VPS)

Set `TRANSCRIPTION_PROVIDER=runpod` for VPS deployments without a GPU. The worker delegates transcription to a RunPod Serverless endpoint running Whisper large-v3 + pyannote.

```env
TRANSCRIPTION_PROVIDER=runpod
RUNPOD_API_KEY=rp_xxxxxxxxxxxxxxxx
RUNPOD_ENDPOINT_ID=<your-endpoint-id>
```

See [`runpod/README.md`](runpod/README.md) for handler deployment instructions.

## VPS Deployment (Contabo)

The production backend runs on a Contabo VPS (6 vCPU, 12GB RAM) with Cloudflare DNS (proxied) for SSL and DDoS protection.

### Initial Setup

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 3. Clone and configure
git clone <repo-url> /opt/zabt
cd /opt/zabt
# Create .env with production values

# 4. Place Cloudflare Origin Certificate for SSL
mkdir -p kong/ssl
# Copy origin.pem and origin.key to kong/ssl/

# 5. Set up .env (first time): COMPOSE_FILE=docker-compose.yml:compose/prod.yml + secrets
cp compose/prod.env.example .env  # then fill secrets
docker build -f backend/Dockerfile.worker-base -t zabt-worker-base:latest ./backend
docker compose up -d --build

# 6. Migrate database (from local machine)
# Local: docker compose exec db pg_dump -U app -d zabt > zabt_dump.sql
# Local: scp zabt_dump.sql root@<VPS_IP>:/opt/zabt/
# VPS:   docker compose exec -T db psql -U <user> -d <db> < zabt_dump.sql
```

### Cloudflare DNS

- **A record**: `zabt-api` → VPS public IP (Proxied)
- **SSL/TLS mode**: Flexible (or Full with origin cert)

### Updating

```bash
cd /opt/zabt
git pull
docker compose up -d --build
```

`.env` already contains `COMPOSE_FILE=docker-compose.yml:compose/prod.yml`
from initial setup, so no `--profile` flags or `-f` arguments are needed.

## Docker Images

| File | Tag | Size | Purpose |
|------|-----|------|---------|
| `Dockerfile` (target `api`) | `zabt-api:latest` | ~850 MB | Lightweight FastAPI server (no ML) |
| `Dockerfile.worker-base` | `zabt-worker-base:latest` | ~10 GB | ML base layer — CUDA + PyTorch + Whisper + pyannote |
| `Dockerfile` (target `worker`) | `zabt-worker:latest` | ~10 GB | Celery worker — builds on `worker-base` in seconds |

### Build workflow

The ML base image is large and slow to build (~15-20 min). Build it once and cache it locally. Only rebuild when ML dependencies change (`[dependency-groups] ml` in `pyproject.toml`).

```bash
# One-time (or when ML deps change): ~15-20 minutes
docker build -f backend/Dockerfile.worker-base -t zabt-worker-base:latest ./backend

# Every other time (code changes, new packages like resend/logfire): ~30 seconds
docker build --target worker -t zabt-worker:latest ./backend
docker build --target api -t zabt-api:latest ./backend
```

### When to rebuild `worker-base`

Only when `pyproject.toml` changes under `[dependency-groups] ml`:

```toml
ml = [
    "openai-whisper>=...",
    "whisperx>=...",
    "pyannote-audio>=...",
]
```

All other dependency changes (core deps, new features) only require rebuilding `worker`.
