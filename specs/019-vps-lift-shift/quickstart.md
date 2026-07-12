# Quickstart: VPS Deployment

## Prerequisites

- Contabo VPS (6 vCPU, 12 GB RAM) with SSH access
- Domain `api.zabt.ai` managed by Cloudflare
- Existing Cloudflare tunnel credentials (`4b6ccbdf-f3e8-4d62-94ab-03f56a00c91b.json`)

## 1. VPS Initial Setup

```bash
# SSH into VPS
ssh root@<VPS_IP>

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Verify Docker
docker --version
docker compose version

# Install cloudflared
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/cloudflared.list
apt update && apt install cloudflared
```

## 2. Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable
```

## 3. Cloudflare Tunnel

```bash
# Create credentials directory
mkdir -p /root/.cloudflared

# Copy tunnel credentials (from local machine)
# scp ~/.cloudflared/4b6ccbdf-f3e8-4d62-94ab-03f56a00c91b.json root@<VPS_IP>:/root/.cloudflared/

# Copy config.yml (from local machine)
# scp config.yml root@<VPS_IP>:/root/.cloudflared/config.yml

# Install as systemd service
cloudflared service install

# Enable and start
systemctl enable cloudflared
systemctl start cloudflared

# Verify
systemctl status cloudflared
```

## 4. Deploy Application

```bash
# Clone repository
git clone <repo-url> /opt/zabt
cd /opt/zabt

# Copy environment file
# scp .env root@<VPS_IP>:/opt/zabt/.env
# (Or create .env manually with production values)

# Build and start (CPU worker profile)
COMPOSE_PROFILES=cpu docker compose up -d --build

# Verify all services are running
docker compose ps

# Check logs
docker compose logs -f api
docker compose logs -f worker
```

## 5. Database Migration

```bash
# Run Alembic migrations
docker compose exec api alembic upgrade head
```

## 6. Verify Deployment

1. Open `https://zabt.ai` — frontend should connect to VPS backend
2. Log in with test account
3. Upload a short audio file
4. Wait for transcription to complete (CPU — may take 20-60 min for 30 min audio)
5. Verify summary email received
6. Check meeting in dashboard shows "completed"

## Environment Variables

All existing environment variables from `.env` are used as-is on the VPS. No new variables are introduced by this migration.

| Variable | Description | Where Set |
|----------|-------------|-----------|
| `COMPOSE_PROFILES` | Set to `cpu` on VPS, `gpu` for local dev with GPU | Shell environment on VPS |
| All others | Same as local `.env` | `.env` file on VPS |

## Running Database Migrations on VPS

```bash
ssh root@<VPS_IP>
cd /opt/zabt
docker compose exec api alembic upgrade head
```

## Updating the Application on VPS

```bash
ssh root@<VPS_IP>
cd /opt/zabt
git pull
docker compose up -d --build
```

## Monitoring

```bash
# Service status
docker compose ps

# Logs (all services)
docker compose logs -f

# RAM usage
docker stats --no-stream

# Disk usage
df -h
docker system df
```

## Local Development (unchanged)

Local development continues to work exactly as before:

```bash
# Start all services locally (no GPU worker)
docker compose up

# Start with GPU worker
docker compose --profile gpu up

# Start with CPU worker
docker compose --profile cpu up
```
