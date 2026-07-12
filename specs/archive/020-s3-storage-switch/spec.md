# Feature Specification: S3/MinIO Storage Provider Switch

**Feature Branch**: `020-s3-storage-switch`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Support switching between MinIO (local dev) and S3/R2 (production) via environment variables"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - S3/R2 Storage on Production VPS (Priority: P1) MVP

As a developer deploying to the VPS, I want to configure the system to use Cloudflare R2 (or any S3-compatible provider) for file storage instead of MinIO, so that I can reduce VPS resource usage and get better durability without changing any application code.

**Why this priority**: This is the core value — moving file storage off the VPS to a managed cloud provider reduces memory/disk pressure on the 12GB VPS and improves reliability.

**Independent Test**: Set environment variables to point at an S3/R2 bucket, remove MinIO from docker-compose, upload a file through the frontend, and verify it lands in the cloud bucket.

**Acceptance Scenarios**:

1. **Given** S3/R2 environment variables are configured, **When** a user uploads an audio file through the frontend, **Then** the file is stored in the configured S3/R2 bucket with the same key structure (`users/{id}/meetings/{uuid}_{filename}`).
2. **Given** S3/R2 is configured, **When** the transcription pipeline runs, **Then** the worker downloads the file from S3/R2 successfully and transcription completes normally.
3. **Given** S3/R2 is configured, **When** MinIO containers are not running, **Then** the system functions normally for all file operations.

---

### User Story 2 - MinIO Continues Working for Local Development (Priority: P1)

As a developer working locally, I want MinIO to continue working exactly as before with no workflow changes, so that I can develop and test without needing cloud credentials.

**Why this priority**: Local development must not break — this is equally critical as production S3 support.

**Independent Test**: Run `docker compose up` locally with default `.env` (no S3 variables), upload a file, and verify the full pipeline works via MinIO as before.

**Acceptance Scenarios**:

1. **Given** no S3-specific environment variables are set (defaults), **When** the system starts, **Then** it connects to MinIO and all file operations work as they do today.
2. **Given** MinIO is the configured provider, **When** a file is uploaded, **Then** the MinIO webhook triggers the transcription pipeline automatically.

---

### User Story 3 - Pipeline Trigger Without MinIO Webhook (Priority: P1)

As the system, when using S3/R2 instead of MinIO, I need an alternative mechanism to trigger the transcription pipeline after file upload, since MinIO's internal webhook won't be available.

**Why this priority**: Without this, uploads to S3/R2 would never trigger transcription — the pipeline would be broken.

**Independent Test**: Upload a file with S3/R2 configured and verify the transcription pipeline starts automatically without MinIO webhooks.

**Acceptance Scenarios**:

1. **Given** S3/R2 is the configured provider, **When** a user creates a meeting and the file upload completes, **Then** the transcription pipeline is triggered automatically.
2. **Given** S3/R2 is configured, **When** the pipeline trigger fires, **Then** the meeting status transitions from `pending_upload` to `queued` and the Celery chain dispatches.

---

### User Story 4 - Public File Access via Presigned URLs (Priority: P2)

As the system serving presigned URLs to the browser, when using S3/R2, presigned URLs should point directly to the cloud provider rather than routing through Kong/MinIO proxy.

**Why this priority**: Without correct presigned URLs, browsers cannot download audio files or access uploaded content. However, this is lower priority than basic upload/download because presigned URLs can point directly to S3/R2 without needing Kong proxy.

**Independent Test**: Generate a presigned URL with S3/R2 configured and verify it resolves to the cloud provider and the browser can access the file.

**Acceptance Scenarios**:

1. **Given** S3/R2 is configured, **When** a presigned upload URL is generated, **Then** it points to the S3/R2 endpoint (not Kong/MinIO).
2. **Given** S3/R2 is configured, **When** a presigned download URL is generated, **Then** the browser can access the file directly from S3/R2.

---

### Edge Cases

- What happens if S3/R2 credentials are misconfigured? The system should fail fast at startup with a clear error message.
- What happens if the S3/R2 bucket doesn't exist? The system should attempt to create it (or fail clearly if permissions don't allow).
- What happens during a provider migration (files in MinIO, switching to S3/R2)? Existing file_path references in the database remain valid only if files are migrated manually.
- What happens if the upload to S3/R2 succeeds but the pipeline trigger fails? The meeting should remain in `pending_upload` state and be retryable.
- What happens if presigned URL expires before the worker downloads? The worker should generate a fresh presigned URL at download time (current behavior).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support switching between MinIO and S3-compatible cloud storage (S3, R2, etc.) using only environment variable changes.
- **FR-002**: System MUST use MinIO as the default storage provider when no cloud storage variables are configured.
- **FR-003**: System MUST generate presigned upload URLs that are valid for the configured provider (MinIO internal or S3/R2 public endpoint).
- **FR-004**: System MUST generate presigned download URLs that work for both internal (worker) and external (browser) access patterns.
- **FR-005**: System MUST trigger the transcription pipeline after file upload completes, regardless of storage provider.
- **FR-006**: When using S3/R2, the system MUST NOT require MinIO containers to be running.
- **FR-007**: When using MinIO, the existing webhook-based pipeline trigger MUST continue working unchanged.
- **FR-008**: When using S3/R2, the system MUST use an application-level mechanism to trigger the pipeline after confirming upload completion.
- **FR-009**: System MUST validate storage provider configuration at startup and fail with a clear error if credentials are invalid or incomplete.
- **FR-010**: The file key structure (`users/{user_id}/meetings/{uuid}_{filename}`) MUST remain identical across both providers.
- **FR-011**: Kong gateway MUST NOT need configuration changes when switching providers — S3/R2 presigned URLs bypass Kong entirely.

### Key Entities

- **StorageProvider**: Configuration determining which storage backend is active (MinIO or S3/R2), including endpoint, credentials, bucket name, and public URL.
- **Meeting**: Existing entity — `file_path` field stores the S3 object key, unchanged across providers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: File upload and transcription pipeline works end-to-end with S3/R2 within the same time bounds as MinIO (no measurable degradation for uploads under 200MB).
- **SC-002**: Switching from MinIO to S3/R2 requires changing only environment variables — zero code changes or config file edits.
- **SC-003**: Local development with MinIO works identically to before the change — no additional setup steps or environment variables required.
- **SC-004**: VPS memory usage decreases after removing MinIO container (freeing ~200-500MB RAM).
- **SC-005**: The system starts successfully and reports a clear error within 10 seconds if storage credentials are misconfigured.
- **SC-006**: Presigned URLs generated for S3/R2 are accessible from a browser without CORS errors or signature mismatches.

## Assumptions

- Cloudflare R2 is the primary target S3-compatible provider, but the implementation should work with any S3-compatible service (AWS S3, Backblaze B2, etc.).
- The R2 bucket will be pre-created manually (or via CLI) before deployment — the system only needs to verify it exists.
- CORS on the R2 bucket will be configured to allow uploads from the frontend domain.
- Existing files in MinIO will be migrated to R2 manually (e.g., via `rclone`) — this feature does not handle data migration.
- The frontend upload flow (presigned URL → direct PUT) remains unchanged — only the URL target changes.
