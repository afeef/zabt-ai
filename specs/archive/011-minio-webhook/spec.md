# Feature Specification: MinIO Webhook Trigger & API Refactoring

**Feature Branch**: `011-minio-webhook`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "Now that the file is uploaded to the backend using minio/s3. I want to trigger an event whenever a file is uploaded to s3/minio that takes the file and starts the transcription in the worker. Also create_meeting and upload_meeting are doing the same thing they need to be refactored."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Event-Driven Transcription (Priority: P1)

As a system architect, I want the backend to automatically start processing a meeting the moment its media file lands in the storage bucket, so that the workflow is highly resilient and decoupled from the frontend API requests.

**Why this priority**: It fulfills the core webhook request and ensures jobs are triggered reliably by infrastructure events rather than synchronous API calls, preventing orphaned files in storage.

**Independent Test**: Can be fully tested by creating a meeting record via `POST /meetings/` (status: `pending_upload`), then dropping the corresponding file into the MinIO bucket using the MinIO console or `mc cp`. The system should automatically detect the upload, transition the meeting to `queued`, and enqueue a Celery transcription task.

**Acceptance Scenarios**:

1. **Given** the MinIO bucket is configured to send `s3:ObjectCreated:Put` events to the backend, **When** a new media file is completely uploaded, **Then** the backend webhook endpoint receives the notification payload.
2. **Given** a valid webhook notification, **When** the backend parses the object key and resolves the existing meeting record by `file_path`, **Then** it transitions the meeting status from `pending_upload` to `queued` and enqueues the Celery worker task.

---

### User Story 2 - Unified Meeting API (Priority: P2)

As a developer, I want the `create_meeting` and `upload_meeting` endpoints refactored, so that there is a single, maintainable source of truth for initializing a meeting, reducing code duplication and edge-case bugs.

**Why this priority**: Technical debt reduction explicitly requested by the user.

**Independent Test**: Can be fully tested by verifying the API contract and codebase to ensure no redundant database insertion or Celery triggering logic exists across the meetings router.

**Acceptance Scenarios**:

1. **Given** the meetings API, **When** reviewing the routes, **Then** the logic surrounding meeting object instantiation and database commits is centralized in a shared service method or unified endpoint.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a dedicated API route to accept S3/MinIO bucket event notifications.
- **FR-002**: System MUST parse the S3 event payload to extract the `file_key`.
- **FR-003**: System MUST extract user ownership information from the S3 object key path convention `users/{user_id}/meetings/{uuid}_{filename}` to assign the meeting to the correct user. The frontend creates the meeting record (with user association) before uploading, so the webhook resolves the meeting by `file_path` rather than parsing user identity from the key.
- **FR-004**: System MUST trigger the Celery transcription task automatically upon successful webhook processing.
- **FR-005**: System MUST validate the webhook request using a shared Bearer token (`MINIO_WEBHOOK_SECRET` environment variable). MinIO sends the token via `Authorization: Bearer {secret}` header. The HEAD endpoint (MinIO health check) is exempt from authentication due to a known MinIO limitation (issue #14507).
- **FR-006**: System MUST ensure the frontend can redirect to the meeting page after upload. The frontend creates the meeting record via `POST /meetings/` (receiving the meeting ID) before uploading the file to MinIO. This eliminates the race condition — the frontend already has the meeting ID for navigation. The webhook subsequently transitions the pre-existing record's status from `pending_upload` to `queued`.
- **FR-007**: System MUST consolidate `create_meeting` (which takes a presigned file_key) and `upload_meeting` (which takes raw multipart file) to remove duplicate task triggering and database logic.

### Key Entities

- **S3 Event Notification**: The JSON payload triggered by MinIO/S3 when an object is created.
- **Meeting**: The existing database entity that tracks the audio file and processing status. Status lifecycle: `pending_upload` → `queued` → `processing` → `completed` | `failed`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of files uploaded directly to the `zabt-media` bucket automatically trigger a background transcription job within 5 seconds of upload completion.
- **SC-002**: Code duplication between meeting creation flows is reduced to 0 (logic consolidated into a single service method).
- **SC-003**: Unauthorized requests to the webhook endpoint are rejected with a 401/403 status code 100% of the time.
