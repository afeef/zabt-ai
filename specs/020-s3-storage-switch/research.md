# Research: S3/MinIO Storage Provider Switch

## Decision 1: Storage Provider Abstraction Pattern

**Decision**: Use Python `Protocol` (typing) with two concrete classes: `MinioStorage` and `S3Storage`. A factory function `create_storage()` returns the correct implementation based on `STORAGE_PROVIDER` env var.

**Rationale**: Both MinIO and S3/R2 speak the S3 API via boto3, so the implementations are nearly identical. The key differences are:
- **Endpoint URL**: MinIO uses `http://minio:9000` (internal Docker), S3/R2 uses `https://<account>.r2.cloudflarestorage.com` or `https://s3.<region>.amazonaws.com`
- **Public URL**: MinIO uses Kong proxy (`https://api.zabt.ai/zabt-media`), S3/R2 uses the provider's public URL directly
- **Credentials**: MinIO uses `minioadmin/minioadmin`, S3/R2 uses access key/secret from the cloud provider
- **Webhook trigger**: MinIO has built-in webhooks, S3/R2 needs application-level trigger

**Alternatives considered**:
- Single class with if/else branching: Rejected — violates Provider Abstraction principle (Principle IX)
- Separate packages: Over-engineered for two implementations in one file

## Decision 2: Pipeline Trigger Without MinIO Webhook

**Decision**: Add a `POST /api/v1/meetings/{meeting_id}/confirm-upload` endpoint. The frontend calls this after the presigned PUT upload completes. This endpoint calls `meeting_service.initiate_processing(file_key)` — the same function the MinIO webhook calls.

**Rationale**: When using S3/R2, there's no MinIO container to send webhooks. The simplest trigger mechanism is: frontend confirms upload → backend dispatches pipeline. This is actually more reliable than webhooks since there's no async delay or event queue.

**Flow comparison**:
- **MinIO mode**: Frontend PUT → MinIO stores → MinIO webhook POST → `initiate_processing()`
- **S3/R2 mode**: Frontend PUT → S3/R2 stores → Frontend POST confirm-upload → `initiate_processing()`

**Alternatives considered**:
- S3 Event Notifications (SNS/SQS): Over-engineered, requires additional AWS infra
- R2 Event Notifications: Cloudflare R2 supports event notifications but requires Workers setup
- Polling: Unreliable and wasteful
- Dual mode (webhook + confirm): Keep both paths — MinIO uses webhook, S3/R2 uses confirm-upload. Both coexist safely.

## Decision 3: Environment Variable Design

**Decision**: Add these new env vars:

```
STORAGE_PROVIDER=minio          # "minio" (default) or "s3"

# Only needed when STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=                # e.g., https://<account>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=               # R2/S3 access key
S3_SECRET_ACCESS_KEY=           # R2/S3 secret key
S3_BUCKET_NAME=zabt-media       # Bucket name (same default)
S3_PUBLIC_URL=                  # Public URL for presigned URLs (e.g., https://media.zabt.ai)
S3_REGION=auto                  # R2 uses "auto", AWS uses region name
```

**Rationale**: Separate `S3_*` prefix avoids confusion with `MINIO_*` vars. Default to `minio` so existing setups work without changes.

**Existing MINIO_* vars**: Unchanged — still used when `STORAGE_PROVIDER=minio`.

## Decision 4: Docker Compose Conditional Services

**Decision**: Add `profiles: ["minio"]` to the `minio`, `minio-init` services. On VPS with S3/R2, don't include the minio profile. Locally, run with `COMPOSE_PROFILES=minio,cpu` or `COMPOSE_PROFILES=minio,gpu`.

**Rationale**: Docker profiles are the idiomatic way to conditionally include services. MinIO should only run when needed (local dev).

**Impact on Kong**: When using S3/R2, the `minio-service` route in kong.yml becomes a no-op (no minio container to proxy to). This is harmless — Kong will just return 502 for `/zabt-media` paths, which won't be used since presigned URLs point directly to S3/R2. We can conditionally remove it later.

**Impact on `depends_on`**: Kong currently depends on `minio`. This needs to be conditional or removed when using S3/R2 mode.

## Decision 5: Presigned URL Strategy for S3/R2

**Decision**: When `STORAGE_PROVIDER=s3`:
- **Upload presigned URLs**: Generated against `S3_ENDPOINT_URL` (the actual S3/R2 endpoint). Browser PUTs directly to S3/R2.
- **Download presigned URLs (worker)**: Generated against `S3_ENDPOINT_URL` (internal server-to-server). Worker fetches from S3/R2 directly.
- **Download presigned URLs (browser)**: Generated against `S3_PUBLIC_URL` if set, otherwise `S3_ENDPOINT_URL`.

**Rationale**: Unlike MinIO where we need separate internal/public clients (because MinIO is behind Kong), S3/R2 endpoints are publicly accessible. One client may suffice, but we keep the two-client pattern for consistency and to support custom domain CDN in front of R2.

## Decision 6: CORS Configuration for S3/R2

**Decision**: CORS must be configured on the R2/S3 bucket to allow PUT requests from the frontend domain. This is a manual setup step documented in quickstart.md.

**R2 CORS example**:
```json
[
  {
    "AllowedOrigins": ["https://zabt.ai"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

## Decision 7: Data Migration Strategy

**Decision**: Out of scope for this feature. Existing files in MinIO must be migrated manually using `rclone` or `mc mirror` before switching `STORAGE_PROVIDER` to `s3`.

**Rationale**: Data migration is a one-time operational task. The feature focuses on the application code changes to support both providers.
