# Research: Kong API Gateway

**Feature**: 001-kong-api-gateway
**Date**: 2026-03-05

---

## Decision 1: Kong DB-less Mode

**Decision**: Use Kong DB-less (declarative) mode — `KONG_DATABASE=off` with `KONG_DECLARATIVE_CONFIG=/etc/kong/kong.yml`.

**Rationale**: The project stack is Docker Compose on a single host. DB-less mode requires zero extra services (no Cassandra or PostgreSQL for Kong), supports full declarative YAML config that can be version-controlled, and reloads cleanly with `docker compose restart kong`. The routing complexity is low (two upstreams: backend API and MinIO), making the Admin API's dynamic config unnecessary.

**Alternatives considered**:
- Kong with PostgreSQL: Adds a second DB service and Admin API management overhead. Rejected — over-engineered for a two-upstream setup.
- Traefik: Label-based config requires Docker socket access and is more opinionated about service discovery. Rejected — Kong was explicitly requested.
- Nginx reverse proxy: Simpler, but no built-in rate limiting or plugin ecosystem. Rejected — user explicitly requested API gateway features.

---

## Decision 2: MinIO Presigned URL Proxying Strategy

**Decision**: Route MinIO presigned upload and download requests through Kong using the path prefix `/storage/`. Set `preserve_host: true` on the MinIO Kong service/route.

**Rationale**: S3 V4 signatures include the `Host` header value. If Kong rewrites the `Host` header (default behavior), the signature verification on MinIO's side fails with a 403. Setting `preserve_host: true` tells Kong to forward the original `Host` header from the client request (`api.zabt.ai`) instead of substituting `minio:9000`. This makes the HMAC check pass.

**Critical configuration**:
```yaml
# kong.yml
services:
  - name: minio-service
    url: http://minio:9000
    routes:
      - name: minio-storage-route
        paths:
          - /storage
        preserve_host: true   # ← CRITICAL for S3 signature verification
```

**Alternatives considered**:
- Exposing MinIO port directly on host: Violates the core requirement (MinIO must not be internet-reachable). Rejected.
- Rewriting presigned URLs server-side on every request: Adds backend complexity for each download/upload trigger. Rejected — changing `MINIO_PUBLIC_ENDPOINT` to the gateway hostname is sufficient.

---

## Decision 3: Presigned URL Hostname Configuration

**Decision**: Change `MINIO_PUBLIC_ENDPOINT` env var in docker-compose.yml from `http://localhost:9000` to `https://api.zabt.ai`.

**Rationale**: `backend/app/services/storage.py` already implements a dual-client pattern — internal boto3 client uses `MINIO_ENDPOINT` (internal Docker hostname) while the presigned-URL-signing client uses `MINIO_PUBLIC_ENDPOINT`. Changing `MINIO_PUBLIC_ENDPOINT` to the public gateway hostname is the only backend change needed. No code changes required — only a Docker Compose environment variable update.

**Implementation detail**: Boto3 embeds the hostname from `MINIO_PUBLIC_ENDPOINT` into the presigned URL's query parameters (`X-Amz-Credential`, etc.). The path prefix on Kong (`/storage/...`) must match the path that boto3 generates.

**Finding**: Boto3 with path-style addressing generates URLs like `http://public-host/bucket-name/object-key`. Kong strips the `/storage` prefix (via `strip_path: true`) before forwarding to `minio:9000`, resulting in the correct internal path `/bucket-name/object-key`.

---

## Decision 4: Kong Port Assignment

**Decision**: Kong listens on port `8100` (host-bound), replacing the direct backend exposure on port `8000` in the Cloudflare tunnel config.

**Rationale**: The current `config.yml` points `api.zabt.ai → localhost:8000` (the FastAPI backend directly). After Kong is introduced, the tunnel must point to Kong's port instead. Port `8100` avoids conflicts with existing services (`8000` = api, `3000` = frontend, `9000/9001` = MinIO, `5433` = PostgreSQL, `6379` = Redis).

**config.yml change required**:
```yaml
# Before
- hostname: api.zabt.ai
  service: http://localhost:8000

# After
- hostname: api.zabt.ai
  service: http://localhost:8100
```

---

## Decision 5: Rate Limiting Plugin

**Decision**: Use Kong's built-in `rate-limiting` plugin (community edition) on the API route. Configure per IP, window: 1 minute, threshold: configurable via environment variable or declarative YAML.

**Rationale**: Kong's `rate-limiting` plugin is included in Kong Gateway (free) with no additional installation. For DB-less mode it uses the `local` policy (per-instance counters), which is sufficient for a single-host deployment. Returns HTTP 429 with `Retry-After` header natively.

**Alternatives considered**:
- `rate-limiting-advanced` plugin: Requires Kong Enterprise license. Rejected.
- External rate limiting at Cloudflare: Requires paid Cloudflare plan. Rejected.
