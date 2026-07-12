# Quickstart: S3/MinIO Storage Provider Switch

## Local Development (MinIO — default)

No changes needed. Works exactly as before.

```bash
# .env (no new variables needed for local dev)
# STORAGE_PROVIDER defaults to "minio"

set -o allexport; source .env; set +o allexport
COMPOSE_PROFILES=minio,gpu docker compose up -d
```

## Production VPS (Cloudflare R2)

### 1. Create R2 Bucket

In Cloudflare Dashboard → R2 → Create Bucket:
- Name: `zabt-media`
- Location: Auto

### 2. Create R2 API Token

Cloudflare Dashboard → R2 → Manage R2 API Tokens → Create API Token:
- Permissions: Object Read & Write
- Specify bucket: `zabt-media`
- Save the Access Key ID and Secret Access Key

### 3. Configure CORS on R2 Bucket

Cloudflare Dashboard → R2 → `zabt-media` → Settings → CORS Policy:

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

### 4. Update VPS .env

```bash
# Storage — switch to S3/R2
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=<your-r2-access-key>
S3_SECRET_ACCESS_KEY=<your-r2-secret-key>
S3_BUCKET_NAME=zabt-media
S3_PUBLIC_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_REGION=auto
```

### 5. Migrate Existing Files (if any)

```bash
# Install rclone on VPS
apt install rclone

# Configure rclone for MinIO source
rclone config
# Name: minio
# Type: s3
# Provider: Minio
# Endpoint: http://localhost:9000 (or minio:9000 if inside docker network)
# Access key: minioadmin
# Secret key: minioadmin

# Configure rclone for R2 destination
# Name: r2
# Type: s3
# Provider: Cloudflare
# Endpoint: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
# Access key: <R2 access key>
# Secret key: <R2 secret key>

# Sync all files
rclone sync minio:zabt-media r2:zabt-media --progress
```

### 6. Restart Services (without MinIO)

```bash
set -o allexport; source .env; set +o allexport
# No minio profile — MinIO containers won't start
COMPOSE_PROFILES=cpu docker compose up -d
```

### 7. Verify

```bash
# Check API health
curl https://api.zabt.ai/api/v1/health

# Upload a test file through the frontend and verify transcription completes
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_PROVIDER` | No | `minio` | `"minio"` or `"s3"` |
| `S3_ENDPOINT_URL` | When s3 | — | S3-compatible endpoint URL |
| `S3_ACCESS_KEY_ID` | When s3 | — | S3/R2 access key |
| `S3_SECRET_ACCESS_KEY` | When s3 | — | S3/R2 secret key |
| `S3_BUCKET_NAME` | No | `zabt-media` | Bucket name |
| `S3_PUBLIC_URL` | No | S3_ENDPOINT_URL | Public URL for browser presigned URLs |
| `S3_REGION` | No | `auto` | AWS region or `auto` for R2 |

## Rollback

To switch back to MinIO:

```bash
# In .env
STORAGE_PROVIDER=minio

# Restart with minio profile
COMPOSE_PROFILES=minio,cpu docker compose up -d
```
