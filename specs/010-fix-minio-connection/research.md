# Research: MinIO Connection in Docker Compose

## Problem
The backend application fails to connect to MinIO with "Connection Refused" because it defaults to `localhost:9000`. In Docker, `localhost` refers to the container itself.

## Decisions

### 1. Service Hostname Usage
**Decision**: Use the Docker Compose service name `minio` as the hostname.
**Rationale**: Docker Compose provides a DNS resolver that allows services to communicate using their names.
**Alternatives**:
- Using `host.docker.internal`: Works on Docker Desktop but less portable across Linux environments.
- Using hardcoded IPs: Extremely brittle.

### 2. Environment Variable Injection
**Decision**: Inject `MINIO_ENDPOINT` via the `environment` section of `docker-compose.yml`.
**Rationale**: Pydantic `BaseSettings` automatically picks up environment variables that match the field names. This allows us to keep the `localhost` default for local dev while specializing it for Docker.

## Implementation Details
- `api` service: `MINIO_ENDPOINT=minio:9000`
- `worker` service: `MINIO_ENDPOINT=minio:9000`
- `worker-gpu` service: `MINIO_ENDPOINT=minio:9000`
