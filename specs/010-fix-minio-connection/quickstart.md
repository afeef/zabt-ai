# Quickstart: MinIO Connection

## Environment Variables

The following environment variable controls the MinIO connection:

| Variable | Default (Local) | Docker (internal) | Description |
|----------|-----------------|-------------------|-------------|
| `MINIO_ENDPOINT` | `localhost:9000` | `minio:9000` | The hostname and port for the MinIO API. |

## Docker Compose
When running via `docker-compose up`, the endpoint is automatically set to `minio:9000` in the `environment` section of the services.
