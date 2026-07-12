# Advanced: cloud / RunPod split deployment

The single-machine setup is great for self-hosting on one GPU box. The **split topology** is
how zabt.ai runs in production and suits teams that want elastic GPU without keeping a GPU
server running 24/7:

- A small, cheap **API VPS** runs `api`, `worker`, `beat` (no GPU).
- **Transcription** runs on **RunPod Serverless** GPUs, invoked per job.
- **Postgres** and **object storage** are managed services (e.g. Supabase Postgres + S3/R2).
- **Kong** fronts the API for TLS + rate limiting (optional if you terminate TLS elsewhere).

```mermaid
flowchart LR
    subgraph VPS [Small API VPS]
      K[Kong :80/:443] --> API[FastAPI]
      API --> WK[Celery worker]
      RD[(Redis)]
    end
    WK -->|presigned audio URL| RP[RunPod Serverless GPU]
    RP -->|transcript| WK
    API --> PG[(Managed Postgres)]
    API --> S3[(S3 / R2)]
    WEB[Web UI on Vercel] --> K
```

## 1. Provision external services

- **Postgres:** a managed Postgres (Supabase, Neon, RDS…). Get its asyncpg URL.
- **Object storage:** an S3-compatible bucket (AWS S3, Cloudflare R2, MinIO elsewhere).
- **RunPod:** deploy the GPU worker as a Serverless endpoint (see `zabt-gpu-worker/` and its
  handler). Note the endpoint ID and an API key.
- **Supabase:** auth project (as in the single-machine guide).

## 2. Configure `.env`

```dotenv
COMPOSE_PROFILES=                         # empty — do NOT run local db/minio/gpu/web
DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/DB
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=zabt-media
S3_PUBLIC_URL=https://media.your-domain
S3_REGION=auto
TRANSCRIPTION_BACKEND=runpod
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...
APP_URL=https://app.your-domain
NEXT_PUBLIC_API_URL=https://api.your-domain/api/v1
MINIO_PUBLIC_ENDPOINT=https://api.your-domain
```

With `STORAGE_PROVIDER=s3` there is no MinIO webhook; the frontend calls
`POST /api/v1/meetings/{id}/confirm-upload` after uploading to trigger the pipeline.

## 3. Kong (TLS gateway)

`docker-compose.cloud.yml` includes a `kong` service that reads `kong/kong.yml` and TLS certs
from `kong/ssl/`:

```bash
mkdir -p kong/ssl
# place origin.pem and origin.key (e.g. a Cloudflare Origin Certificate) in kong/ssl/
```

If you terminate TLS elsewhere (Cloudflare Tunnel, an external load balancer, another reverse
proxy), delete the `kong` service from `docker-compose.cloud.yml` and expose `api` directly.

## 4. Launch

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d
```

This runs `redis`, `api`, `worker`, `beat`, and `kong` — no local GPU, DB, or storage.

## 5. Frontend

In this topology the Next.js UI is usually hosted separately (e.g. Vercel) pointing
`NEXT_PUBLIC_API_URL` at your API domain. To run it in a container instead, add `local` to
`COMPOSE_PROFILES` (it will start the `web` service).

## Notes

- Keep the API VPS firewalled to 80/443 only; Postgres/Redis should not be publicly reachable.
- RunPod cold starts add latency to the first job after idle; tune endpoint min-workers to
  trade cost for latency.
- Rotate `RUNPOD_API_KEY`, storage keys, and `SUPABASE_JWT_SECRET` on any suspected exposure.
