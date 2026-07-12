# Quickstart: Kong API Gateway

**Feature**: 001-kong-api-gateway
**Date**: 2026-03-05

---

## What Changes

1. A new `kong/kong.yml` declarative config file is created at the repo root.
2. A new `kong` service is added to `docker-compose.yml`.
3. Port bindings are removed from the `api` and `minio` services (they become internal-only).
4. `MINIO_PUBLIC_ENDPOINT` is updated to the public gateway hostname.
5. `config.yml` (Cloudflare tunnel) is updated to point at Kong's port instead of the backend directly.

---

## New File: `kong/kong.yml`

```yaml
_format_version: "3.0"
_transform: true

services:
  - name: api-service
    url: http://api:8000
    routes:
      - name: api-route
        paths:
          - /
        strip_path: false
        preserve_host: false
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
          error_code: 429
          error_message: "Rate limit exceeded. Please retry after the indicated delay."

  - name: minio-service
    url: http://minio:9000
    routes:
      - name: minio-storage-route
        paths:
          - /storage
        strip_path: true
        preserve_host: true
```

---

## docker-compose.yml Changes

### Add `kong` service

```yaml
kong:
  image: kong:3.6
  container_name: kong
  restart: unless-stopped
  environment:
    KONG_DATABASE: "off"
    KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
    KONG_PROXY_LISTEN: "0.0.0.0:8000"
    KONG_ADMIN_LISTEN: "127.0.0.1:8001"
    KONG_LOG_LEVEL: notice
  volumes:
    - ./kong/kong.yml:/etc/kong/kong.yml:ro
  ports:
    - "8100:8000"
  networks:
    - default
  depends_on:
    - api
    - minio
```

### Remove port bindings from `api` and `minio`

```yaml
# api service — remove or comment out:
# ports:
#   - "8000:8000"

# minio service — remove or comment out:
# ports:
#   - "9000:9000"
#   - "9001:9001"
```

### Update `MINIO_PUBLIC_ENDPOINT` (in `api`, `worker`, `worker-gpu` services)

```yaml
MINIO_PUBLIC_ENDPOINT: https://api.zabt.ai
```

---

## config.yml Change (Cloudflare Tunnel)

```yaml
ingress:
  - hostname: api.zabt.ai
    service: http://localhost:8100   # ← was localhost:8000
```

---

## Validation Scenarios

### Scenario 1 — API traffic flows through Kong

```bash
# From outside the host (or via Cloudflare hostname)
curl https://api.zabt.ai/api/v1/meetings

# Expected: 200 or 401 (auth required) — NOT connection refused
```

### Scenario 2 — MinIO is not reachable directly

```bash
# From outside the host
curl https://your-host:9000

# Expected: Connection refused / timeout
```

### Scenario 3 — File upload via presigned URL works

1. Create a meeting via the API to get a presigned upload URL.
2. Check that the returned URL begins with `https://api.zabt.ai/storage/...`.
3. PUT the file to that URL from a remote machine.
4. Expected: 200 response; file stored in MinIO.

### Scenario 4 — Rate limiting returns 429

```bash
# Send 101+ requests in one minute to trigger rate limit
for i in $(seq 1 105); do curl -s -o /dev/null -w "%{http_code}\n" https://api.zabt.ai/api/v1/health; done

# Expected: After ~100 requests, responses return 429
```

---

## Reload After Config Change

When `kong/kong.yml` is updated:

```bash
docker compose restart kong
```

No other services need to restart. No Cloudflare tunnel reconfiguration needed.
