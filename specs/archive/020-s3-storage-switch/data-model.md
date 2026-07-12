# Data Model: S3/MinIO Storage Provider Switch

## No Schema Changes

This feature does not modify the database schema. The `Meeting.file_path` field already stores S3 object keys (`users/{id}/meetings/{uuid}_{filename}`) which are provider-agnostic.

## Configuration Model (Environment Variables)

### New Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `STORAGE_PROVIDER` | str | `"minio"` | Storage backend: `"minio"` or `"s3"` |
| `S3_ENDPOINT_URL` | str | `""` | S3-compatible endpoint (e.g., `https://<account>.r2.cloudflarestorage.com`) |
| `S3_ACCESS_KEY_ID` | str | `""` | S3/R2 access key |
| `S3_SECRET_ACCESS_KEY` | str | `""` | S3/R2 secret key |
| `S3_BUCKET_NAME` | str | `"zabt-media"` | Bucket name |
| `S3_PUBLIC_URL` | str | `""` | Public URL for browser presigned URLs (optional, defaults to endpoint) |
| `S3_REGION` | str | `"auto"` | AWS region or `"auto"` for R2 |

### Existing Settings (Unchanged)

| Variable | Used When |
|----------|-----------|
| `MINIO_ENDPOINT` | `STORAGE_PROVIDER=minio` |
| `MINIO_PUBLIC_ENDPOINT` | `STORAGE_PROVIDER=minio` |
| `MINIO_ACCESS_KEY` | `STORAGE_PROVIDER=minio` |
| `MINIO_SECRET_KEY` | `STORAGE_PROVIDER=minio` |
| `MINIO_BUCKET_NAME` | `STORAGE_PROVIDER=minio` |
| `MINIO_SECURE` | `STORAGE_PROVIDER=minio` |
| `MINIO_WEBHOOK_SECRET` | `STORAGE_PROVIDER=minio` |

## Storage Protocol Interface

```
StorageProvider (Protocol):
  - generate_presigned_upload_url(user_id, filename, content_type, expiration) → (url, key)
  - get_presigned_download_url(object_key, expiration) → url
  - upload_file(file_data, object_key, content_type) → None
  - delete_file(object_key) → None
  - provider_name → str  (read-only property: "minio" or "s3")
```
