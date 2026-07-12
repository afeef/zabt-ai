# Feature Specification: Fix S3/MinIO Connection in Docker

**Feature Branch**: `010-fix-minio-connection`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "Fix S3/MinIO connection error in Docker by correctly setting MINIO_ENDPOINT to minio:9000 in docker-compose.yml"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Celery Worker Connection (Priority: P1)

As a developer, I want the Celery worker to successfully connect to MinIO when running in Docker, so that media files can be processed without "Connection Refused" errors.

**Why this priority**: Blocking issue for transcription and media processing.

**Independent Test**: Can be verified by checking worker logs for "botocore.exceptions.EndpointConnectionError".

**Acceptance Scenarios**:

1. **Given** a Docker Compose environment, **When** the worker service starts, **Then** it correctly resolves the `minio` service endpoint and initializes the storage service without errors.

---

### User Story 2 - API Presigned URL Support (Priority: P1)

As a developer, I want the API service to connect to MinIO correctly to generate presigned URLs and create buckets if they don't exist.

**Why this priority**: Required for file uploads from the frontend.

**Acceptance Scenarios**:

1. **Given** a Docker Compose environment, **When** a user requests a presigned upload URL, **Then** the API service correctly communicates with MinIO to generate the URL.

---

### User Story 3 - PydanticAI Worker Stability (Priority: P1)

As a developer, I want the Celery worker to start without `TypeError` regressions, so that it can process meetings and use the configured AI models.

**Why this priority**: Regression found during MinIO fix; prevents worker from running.

**Acceptance Scenarios**:

1. **Given** the current backend code, **When** the worker service starts, **Then** `OpenAIModel` is initialized correctly without `TypeError`.

---

### User Story 4 - Direct Meeting Upload (Priority: P1)

As a developer, I want a direct multipart upload endpoint for meetings, so that the frontend can upload files in a single POST request without negotiating presigned URLs.

**Why this priority**: Required to fix the "405 Method Not Allowed" error on the `/upload` path.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they POST a multipart file to `/api/v1/meetings/upload`, **Then** the file is stored in MinIO, a database record is created, and the Celery worker is triggered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow configuring the MinIO endpoint via the `MINIO_ENDPOINT` environment variable.
- **FR-002**: `docker-compose.yml` MUST pass `MINIO_ENDPOINT=minio:9000` to all backend services (`api`, `worker`, `worker-gpu`).
- **FR-003**: The system MUST fallback to `localhost:9000` only for local development outside of Docker.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero `EndpointConnectionError` or `ConnectionRefusedError` in backend logs related to MinIO after starting with Docker Compose.
- **SC-002**: Successful initialization of `S3StorageService` (bucket existence check) during startup.
- **SC-003**: Successful file upload via `POST /api/v1/meetings/upload` resulting in a `200 OK` or `201 Created` status code.
