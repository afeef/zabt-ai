# Self-hosting zabt.ai (single machine)

This is the default and simplest deployment: everything runs on one machine via Docker
Compose — API, workers, GPU transcription, Postgres, Redis, MinIO object storage, and the web
UI. The only external dependency is a Supabase project for authentication (a free one works)
and an LLM API key.

## 1. Prerequisites

- **Docker** and **Docker Compose v2** (`docker compose version`).
- For GPU transcription: an **NVIDIA GPU** + the
  [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
  No GPU is fine — see [CPU-only](#cpu-only).
- ~10-15 GB free disk for model weights and media.
- A **Supabase** project (free): https://supabase.com
- An **OpenAI-compatible LLM** key (OpenRouter, OpenAI, or a local Ollama/vLLM/LM Studio).
- A **Hugging Face** token with the pyannote gate accepted (see below).

## 2. Configure

```bash
git clone https://github.com/afeef/zabt-ai.git
cd zabt-ai
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Where to get it |
|----------|-----------------|
| `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_JWT_SECRET` | Supabase → Project Settings → API → JWT Settings |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Project Settings → API (anon/publishable key) |
| `OPENAI_API_KEY` | Your LLM provider (e.g. https://openrouter.ai/keys) |
| `HF_TOKEN` | https://huggingface.co/settings/tokens (accept pyannote gate first) |

Leave `COMPOSE_PROFILES=local` and the bundled `DATABASE_URL` / MinIO defaults as-is.

### pyannote Hugging Face gate

Diarization models are gated and **not** bundled with this repo. Accept the terms on:
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

Then create a token and set `HF_TOKEN`.

## 3. Start

```bash
docker compose up -d
docker compose logs -f api        # watch startup / migrations
```

- Web UI → http://localhost:3000
- API → http://localhost:8000/docs
- MinIO console → http://localhost:9001 (`minioadmin` / `minioadmin`)

First transcription downloads Whisper + pyannote weights into the `worker_model_cache`
volume (several GB, one-time).

## CPU-only

```bash
docker compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

Set a smaller model for usable speed, e.g. `WHISPER_MODEL=base` in `.env`. CPU transcription
runs `int8` compute automatically and is roughly 1-5× real-time.

## Optional add-ons

Enable by editing `COMPOSE_PROFILES` in `.env` (comma-separated):

- `COMPOSE_PROFILES=local,bot` — Microsoft Teams meeting bot (headless browser).
- `COMPOSE_PROFILES=local,vision` — visual breakdown worker (needs an Ollama host serving
  the vision model; set `OLLAMA_HOST`).

## Operations

```bash
docker compose ps                     # status
docker compose logs -f worker         # transcription/summary pipeline logs
docker compose down                   # stop (keeps volumes/data)
docker compose down -v                # stop and DELETE all data (Postgres, MinIO, models)
docker compose pull && docker compose up -d --build   # update after git pull
```

### Backups
- **Database:** `docker compose exec db pg_dump -U app -d zabt > backup.sql`
- **Object storage:** back up the `minio_data` volume (or your S3 bucket).

## Putting it on the internet

The default binds services to localhost. For remote access, front the `web` (3000) and `api`
(8000) with a TLS-terminating reverse proxy (Caddy, nginx, Traefik) or a tunnel (Cloudflare
Tunnel). Update `APP_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_FRONTEND_URL`,
`BACKEND_CORS_ORIGINS`, and `MINIO_PUBLIC_ENDPOINT` to your public URLs. For a managed-services
/ serverless-GPU topology, see [advanced-runpod-split.md](advanced-runpod-split.md).

## Troubleshooting

- **`could not select device driver "nvidia"`** → NVIDIA Container Toolkit not installed, or
  no GPU. Use the CPU compose file.
- **Diarization fails / 401 from Hugging Face** → `HF_TOKEN` missing or pyannote gate not
  accepted.
- **Uploads don't trigger transcription** → check the `minio-init` container configured the
  bucket webhook, and that `MINIO_WEBHOOK_SECRET` matches between MinIO and the API.
- **Auth errors** → verify the four `SUPABASE_*` values and that `SUPABASE_JWT_SECRET` matches
  your project.
