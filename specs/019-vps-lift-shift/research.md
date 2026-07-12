# Research: Lift-and-Shift Backend to Contabo VPS

## R1: Cloudflare Tunnel on VPS

**Decision**: Install `cloudflared` as a systemd service on the VPS, using the existing tunnel ID and config.

**Rationale**: `cloudflared` runs as a lightweight daemon, establishes an outbound connection to Cloudflare's edge (no inbound ports needed), and automatically reconnects on failure. Running as a systemd service ensures it starts on boot and restarts on crash — independent of Docker.

**Alternatives considered**:
- Running `cloudflared` inside Docker: Adds complexity (Docker-in-Docker networking), harder to debug. The tunnel should outlive container restarts.
- Exposing ports directly + Cloudflare proxy: Requires opening firewall ports, defeats the purpose of zero-trust tunnel.

**Setup steps**:
1. Install `cloudflared` via apt repository on VPS
2. Copy the existing tunnel credentials file (`4b6ccbdf-f3e8-4d62-94ab-03f56a00c91b.json`) to VPS at `/root/.cloudflared/`
3. Copy `config.yml` to VPS at `/root/.cloudflared/config.yml`
4. Update `config.yml` ingress: `api.zabt.ai` → `http://localhost:8100` (Kong port, same as current)
5. Install as systemd service: `cloudflared service install`
6. Enable and start: `systemctl enable cloudflared && systemctl start cloudflared`

## R2: Qdrant Docker Setup

**Decision**: Add `qdrant/qdrant:latest` to docker-compose.yml with a persistent volume and health check.

**Rationale**: Qdrant has an official Docker image, supports ARM and x86, and runs with minimal configuration. Adding it now (empty) costs ~512 MB RAM idle and avoids a separate deployment task when the AI Chat feature is built.

**Alternatives considered**:
- pgvector (Postgres extension): Rejected by user — risk of accidental data loss during Alembic migrations.
- Pinecone (SaaS): Adds external dependency and cost; self-hosted preferred for now.

**Docker config**:
```yaml
qdrant:
  image: qdrant/qdrant:latest
  volumes:
    - qdrant_data:/qdrant/storage
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## R3: Environment Variable Toggles for Local vs Production

**Decision**: Use environment variable defaults in docker-compose.yml so that local dev works without any extra config, while VPS production overrides specific values via the `.env` file on the VPS.

**Rationale**: Docker Compose already supports `${VAR:-default}` syntax. Services that need production behavior (restart policies, resource limits) can be toggled via a single env var pattern. This avoids maintaining two separate compose files.

**Key toggles**:

| Variable | Local Default | VPS Production |
|----------|--------------|----------------|
| `RESTART_POLICY` | `no` | `unless-stopped` |
| `COMPOSE_PROFILES` | (unset, or `gpu`) | `cpu` |

**Implementation**: Docker Compose `restart` field doesn't support variable interpolation directly. Instead, use `deploy.restart_policy` under a profile, or simply set `restart: unless-stopped` on all services (harmless locally — containers just restart if they crash, which is fine for dev too).

**Simpler approach chosen**: Set `restart: unless-stopped` on all services unconditionally. This is safe for both local dev and production. Locally, `docker compose down` still stops everything cleanly. The only behavioral difference is that a crashed container restarts automatically — which is actually desirable in dev too.

## R4: Worker CPU Transcription on VPS

**Decision**: Run the existing `worker` service (CPU profile) on the VPS. Whisper large-v3 on CPU (6 cores) will be slow (~20-60 min for 30 min audio) but functionally identical.

**Rationale**: The worker code already supports CPU execution — `TRANSCRIPTION_DEVICE=auto` in config.py falls back to CPU when no CUDA GPU is detected. No code changes needed.

**Considerations**:
- Celery task soft/hard timeouts must not kill long-running CPU transcriptions. Current config has no explicit timeout, which is correct for this use case.
- The VPS has 12 GB RAM. Whisper large-v3 on CPU uses ~4-6 GB RAM. With other services at ~2-3 GB, total is ~7-9 GB — within the 12 GB limit but tight. Monitor RAM usage and consider `whisper-medium` if OOM occurs.
- Only one transcription at a time (Celery concurrency=1) to prevent RAM exhaustion.

**Alternatives considered**:
- Skip CPU worker, use Deepgram API: Adds external dependency and cost; deferred to separate feature.
- Use `whisper-medium` instead of `large-v3`: Lower quality; keep `large-v3` for now, downgrade if RAM is an issue.

## R5: VPS Firewall Configuration

**Decision**: Use `ufw` (Uncomplicated Firewall) on the VPS to allow only SSH (port 22) and deny everything else.

**Rationale**: Since Cloudflare tunnel makes outbound connections (no inbound ports needed for the tunnel itself), the firewall only needs to allow SSH for remote management. All other traffic arrives through the tunnel.

**Setup**:
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable
```

## R6: Data Migration Strategy

**Decision**: Fresh database on VPS. Manually re-create test accounts if needed. Optional pg_dump/restore for existing data.

**Rationale**: The application is pre-launch with test users only. A fresh database is simpler and avoids potential migration issues. Real user data migration will be needed when moving between environments post-launch.

## R7: Docker & Docker Compose Installation on VPS

**Decision**: Install Docker Engine and Docker Compose plugin via the official Docker apt repository.

**Rationale**: Standard approach, well-documented, ensures latest stable version. Contabo VPS ships with Ubuntu — Docker's primary supported platform.

**Setup**:
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
docker compose version
```
