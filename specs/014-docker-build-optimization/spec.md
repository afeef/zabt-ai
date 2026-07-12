# Feature Specification: Docker Build Optimization

**Feature Branch**: `014-docker-build-optimization`
**Created**: 2026-03-01
**Status**: Draft
**Input**: User description: "The CLI commands work well directly but running everything via Docker Compose produces very large container images because heavy ML models are downloaded during build. The build process is slow and container sizes are excessive. The application needs to run on a local server using Docker Compose with Cloudflare Tunnels for internet exposure, while also enabling rapid prototyping with quick build-and-test cycles."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast API Service Rebuild (Priority: P1)

As a developer, I want to rebuild and restart the API service quickly after making code changes so that I can rapidly prototype and test features without waiting for heavy ML dependencies to re-install.

**Why this priority**: This directly addresses the core pain point — the developer cannot iterate quickly because every rebuild of the API service pulls in multi-gigabyte ML dependencies that it does not need at runtime. The API service only needs lightweight web framework dependencies.

**Independent Test**: Can be tested by making a code change in the API layer, rebuilding the API container, and verifying that the build completes in under 2 minutes and the container starts serving requests within seconds.

**Acceptance Scenarios**:

1. **Given** a code change in the API layer, **When** the developer runs the build command for the API service, **Then** the build completes without downloading or installing any ML/transcription dependencies.
2. **Given** the API service container is built, **When** the developer checks the container image size, **Then** it is significantly smaller than the current combined image (target: under 500 MB).
3. **Given** both API and worker services are running, **When** the developer makes a change only to API code, **Then** only the API container needs to be rebuilt — the worker container remains untouched.

---

### User Story 2 - Worker Service with ML Dependencies (Priority: P2)

As a system operator, I want the worker service to contain all ML/transcription dependencies (Whisper, WhisperX, pyannote, torch) so that it can process transcription jobs independently from the API service.

**Why this priority**: The worker is the service that actually runs transcription pipelines. It must retain all heavy dependencies but should be isolated so its large image size does not affect the API service build time.

**Independent Test**: Can be tested by submitting a transcription job and verifying that the worker picks it up and completes the transcription using the local Whisper pipeline.

**Acceptance Scenarios**:

1. **Given** the worker service container is built with ML dependencies, **When** a transcription job is submitted via Celery, **Then** the worker processes the job using WhisperX and produces a valid transcript.
2. **Given** the worker container image is built, **When** the developer inspects the image, **Then** it contains all required ML libraries (torch, whisperx, pyannote-audio, openai-whisper).
3. **Given** the worker image has been built once, **When** a code-only change is made (no dependency changes), **Then** the rebuild leverages cached layers and completes quickly.

---

### User Story 3 - Local Server Deployment with Internet Exposure (Priority: P3)

As a system operator, I want to deploy the full application stack on my local server using Docker Compose and expose it to the internet via Cloudflare Tunnels so that external users can access the application.

**Why this priority**: This is the deployment goal — once build optimization is in place, the operator needs confidence that the split-service architecture works correctly in a production-like Docker Compose environment with external access.

**Independent Test**: Can be tested by running `docker compose up`, then accessing the application from an external device through the configured Cloudflare Tunnel URL.

**Acceptance Scenarios**:

1. **Given** the Docker Compose configuration is set up with all services, **When** the operator runs `docker compose up`, **Then** all services (API, worker, database, Redis, MinIO) start and communicate correctly.
2. **Given** the application is running behind a Cloudflare Tunnel, **When** an external user accesses the application URL, **Then** they can use all features including uploading files and receiving transcriptions.
3. **Given** the API service is restarted independently, **When** the worker is mid-transcription, **Then** the worker completes its current job and the API resumes serving requests without data loss.

---

### Edge Cases

- What happens when the worker container is not running but a user uploads a file for transcription? The API should accept the upload and queue the job; the job will be processed once the worker starts.
- What happens when the developer changes a shared dependency (e.g., pydantic) used by both API and worker? Both containers need to be rebuilt, but the build should still be fast due to layer caching.
- What happens during the transition from single-image to split-image architecture? Existing volumes and database state must be preserved.
- How does the system behave if the Cloudflare Tunnel drops? The local network access should continue working; external access resumes when the tunnel reconnects.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The build system MUST produce separate container images for the API service and the worker service.
- **FR-002**: The API service image MUST NOT include ML/transcription dependencies (torch, whisperx, openai-whisper, pyannote-audio, CUDA runtime).
- **FR-003**: The worker service image MUST include all ML/transcription dependencies required for local Whisper-based transcription.
- **FR-004**: Both services MUST share the same application codebase and be installable from the same repository.
- **FR-005**: The Docker Compose configuration MUST define separate build contexts or targets for the API and worker services.
- **FR-006**: The API service MUST continue to handle all existing endpoints (REST API, webhooks, health checks) without modification to the application code.
- **FR-007**: The worker service MUST continue to process Celery tasks (transcription, summarization) without modification to the task code.
- **FR-008**: Dependency management MUST allow installing only the subset of dependencies required by each service profile (lightweight for API, full for worker).
- **FR-009**: The Docker Compose configuration MUST support exposing the API service for external access (compatible with Cloudflare Tunnel or similar reverse proxy).
- **FR-010**: Layer caching MUST be optimized so that code-only changes result in fast rebuilds for both services.

### Key Entities

- **API Service Image**: A lightweight container image containing only the web framework, database drivers, and task queue client. Does not run any ML workloads.
- **Worker Service Image**: A full-featured container image containing all ML dependencies plus the shared application code. Runs Celery tasks for heavy processing.
- **Dependency Profile**: A logical grouping of packages — "core" dependencies shared by both services, and "ml" dependencies required only by the worker.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The API service container image size is under 500 MB (down from the current ~8-10 GB combined image).
- **SC-002**: A code-only rebuild of the API service completes in under 60 seconds.
- **SC-003**: The worker service container retains full transcription capability — all existing transcription tests pass.
- **SC-004**: The full stack (`docker compose up`) starts successfully with both services communicating correctly (API queues jobs, worker processes them).
- **SC-005**: The developer can make a code change, rebuild, and test the API within 2 minutes end-to-end.
- **SC-006**: Existing deployment workflows and environment variable configuration require no changes beyond the Docker/Compose files.

## Assumptions

- The API service never needs to run transcription or ML inference directly — all heavy processing is delegated to the Celery worker.
- The existing provider abstraction (TranscriptionProvider Protocol) already separates concerns, so no application code changes are needed for the split.
- The developer has Docker BuildKit enabled (required for cache mounts and multi-stage builds).
- Cloudflare Tunnel configuration is handled externally and only requires the API service to be accessible on a known port.
- The CUDA/GPU runtime is only needed by the worker service for GPU-accelerated transcription.
