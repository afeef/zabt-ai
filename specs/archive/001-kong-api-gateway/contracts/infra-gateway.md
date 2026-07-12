# Infrastructure Contract: API Gateway Routing

**Feature**: 001-kong-api-gateway
**Date**: 2026-03-05
**Type**: Infrastructure / Docker Compose + Kong declarative config

---

## Overview

This contract defines the Kong gateway routing table, plugin configuration, and environment variables that compose the gateway layer. All public traffic must pass through Kong before reaching backend services.

---

## Kong Declarative Config (`kong/kong.yml`)

Format version: `3.0` (Kong 3.x compatible)

### Services & Routes

| Service Name     | Upstream URL        | Route Path  | Strip Path | Preserve Host | Notes                              |
|-----------------|---------------------|-------------|------------|---------------|------------------------------------|
| `api-service`   | `http://api:8000`   | `/`         | `false`    | `false`       | All API traffic; catch-all prefix  |
| `minio-service` | `http://minio:9000` | `/storage`  | `true`     | `true`        | Presigned URL proxy; HMAC requires preserve_host |

### Plugins

| Plugin           | Scope        | Config                                              |
|-----------------|--------------|-----------------------------------------------------|
| `rate-limiting` | `api-service` route | `minute: 100`, `policy: local`, `error_code: 429` |

---

## Port Assignments

| Service   | Internal Port | Host-Bound Port | Purpose                         |
|-----------|--------------|----------------|---------------------------------|
| Kong proxy | 8000         | `8100`          | Public entry point (Cloudflare tunnel target) |
| Kong admin | 8001         | —              | Admin API (internal only, not host-exposed) |
| API        | 8000         | —              | Backend; no longer host-exposed  |
| MinIO      | 9000         | —              | Object storage; no longer host-exposed |

---

## Required Environment Variables

### docker-compose.yml additions

```yaml
kong:
  environment:
    KONG_DATABASE: "off"
    KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
    KONG_PROXY_LISTEN: "0.0.0.0:8000"
    KONG_ADMIN_LISTEN: "127.0.0.1:8001"
    KONG_LOG_LEVEL: notice
```

### Changed variables (existing services)

| Variable               | Old Value                    | New Value                              | Service |
|------------------------|------------------------------|----------------------------------------|---------|
| `MINIO_PUBLIC_ENDPOINT` | `http://localhost:9000`      | `https://api.zabt.ai`     | `api`, `worker`, `worker-gpu` |

### Cloudflare tunnel (`config.yml`)

```yaml
# Changed route
- hostname: api.zabt.ai
  service: http://localhost:8100   # was: http://localhost:8000
```

---

## Network Isolation Contract

- The `api` service MUST NOT bind port `8000` to the host after Kong is introduced (remove `ports: ["8000:8000"]` from `api` service in docker-compose.yml).
- MinIO MUST NOT bind port `9000` or `9001` to the host (remove `ports` from `minio` service).
- Kong is the ONLY service with a host-bound port on the public interface.

---

## Kong Service File Layout

```text
kong/
└── kong.yml    # Declarative config — version-controlled, no UI editing
```

Volume mount in docker-compose.yml:
```yaml
kong:
  volumes:
    - ./kong/kong.yml:/etc/kong/kong.yml:ro
```
