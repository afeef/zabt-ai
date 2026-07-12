# Feature Specification: Lift-and-Shift Backend to Contabo VPS

**Feature Branch**: `019-vps-lift-shift`
**Created**: 2026-03-07
**Status**: Draft
**Input**: Migrate the Zabt backend as-is from the developer's local Docker setup to a Contabo VPS (6 vCPU, 12GB RAM). No application code changes. GPU worker stays local temporarily.

## Clarifications

### Session 2026-03-07

- Q: How should local vs production Docker Compose configurations coexist? → A: Single `docker-compose.yml` with environment-variable toggles for local vs production.
- Q: How should the GPU worker connect to VPS services (Redis, PostgreSQL, MinIO)? → A: The worker runs on the VPS on CPU during lift-and-shift. No remote GPU bridge needed. GPU worker stays local for development only. Later, a provider model will switch to RunPod for GPU tasks in production.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Accessible from the Internet (Priority: P1)

An end user opens the Zabt web application (hosted on Vercel) and the frontend connects to the backend API running on the Contabo VPS. The user can log in, view their dashboard, and interact with the application exactly as before. The migration is invisible to the user.

**Why this priority**: Without the backend being reachable, no other functionality works. This is the foundational requirement.

**Independent Test**: Navigate to the Vercel-hosted frontend, log in with existing credentials, and confirm the dashboard loads with existing meeting data.

**Acceptance Scenarios**:

1. **Given** the backend is deployed on the VPS, **When** a user visits the Zabt frontend and logs in, **Then** the dashboard loads with their meetings and data within 5 seconds.
2. **Given** the backend is deployed on the VPS, **When** an unauthenticated user tries to access a protected page, **Then** they are redirected to the login page.
3. **Given** the VPS is running, **When** the Cloudflare tunnel is active, **Then** the backend API is accessible via the existing domain without exposing any ports directly to the internet.

---

### User Story 2 - File Upload and Storage on VPS (Priority: P1)

A user uploads an audio file through the web application. The file is stored in MinIO running on the VPS. The upload completes successfully and the meeting record is created in the PostgreSQL database on the VPS.

**Why this priority**: File upload is the entry point for the core product workflow. If files cannot be stored on the VPS, the transcription pipeline cannot proceed.

**Independent Test**: Upload a 50 MB audio file through the frontend and verify it appears in the MinIO console on the VPS and the meeting record exists in the database.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they upload an audio file (up to 500 MB), **Then** the file is stored in MinIO on the VPS and a meeting record is created.
2. **Given** a file is being uploaded, **When** the upload completes, **Then** the user sees the meeting appear in their dashboard with "processing" status.
3. **Given** MinIO is running on the VPS, **When** a file is uploaded, **Then** the upload speed is comparable to or faster than the previous local deployment.

---

### User Story 3 - End-to-End Transcription Pipeline on VPS (Priority: P1)

After a file is uploaded to the VPS, the entire transcription pipeline executes on the VPS: the Celery worker (running on CPU) picks up the transcription job, processes the audio, performs diarization, generates the summary, and sends the notification email. Transcription on CPU is slower than GPU but functionally identical. The user receives a summary email and can view the completed summary in the app.

**Why this priority**: This validates that the full pipeline works on the VPS without any GPU dependency. Without this, the product is non-functional in production.

**Independent Test**: Upload an audio file, wait for the full pipeline to complete, then verify the transcript, summary, and email notification are all generated correctly.

**Acceptance Scenarios**:

1. **Given** a file has been uploaded to MinIO on the VPS, **When** the Celery worker picks up the task, **Then** it transcribes the audio using Whisper on CPU.
2. **Given** transcription is complete, **When** diarization finishes, **Then** the worker proceeds with summarization.
3. **Given** summarization is complete, **When** the pipeline finishes, **Then** the user receives a summary email and the meeting status shows "completed" in the dashboard.
4. **Given** a 30-minute audio file, **When** transcription runs on CPU (6 vCPU), **Then** the pipeline completes (transcription may take 20-60 minutes on CPU, which is acceptable for this phase).

---

### User Story 4 - Qdrant Vector Database Available (Priority: P2)

The Qdrant vector database is running on the VPS as part of the docker-compose stack. It is empty but healthy and ready for future use by the AI Chat feature. No application code connects to it yet.

**Why this priority**: Adding Qdrant now avoids a separate deployment task later. It is low effort and has no impact on existing functionality.

**Independent Test**: Verify Qdrant is running and healthy by checking its health endpoint from within the VPS Docker network.

**Acceptance Scenarios**:

1. **Given** the docker-compose stack is running, **When** the Qdrant container starts, **Then** it is healthy and accessible on its default port within the Docker network.
2. **Given** Qdrant is running, **When** its data directory is inspected, **Then** it uses a persistent Docker volume that survives container restarts.

---

### User Story 5 - VPS Security and Stability (Priority: P2)

The VPS is configured with a firewall that only allows traffic through the Cloudflare tunnel. No database ports, Redis ports, or MinIO ports are exposed to the public internet. The system recovers automatically from Docker container crashes.

**Why this priority**: Security is essential before serving real users from the VPS. Exposing internal services would create serious vulnerabilities.

**Independent Test**: Run a port scan against the VPS public IP and confirm only the Cloudflare tunnel port (or SSH) is open. Restart a container and confirm it recovers.

**Acceptance Scenarios**:

1. **Given** the VPS is running, **When** an external port scan is performed, **Then** only SSH and Cloudflare tunnel ports are accessible.
2. **Given** a Docker container crashes, **When** Docker Compose detects the failure, **Then** the container is automatically restarted.
3. **Given** the VPS reboots, **When** it comes back online, **Then** all Docker services start automatically.

---

### User Story 6 - Local Development Mode (Priority: P1)

A developer runs `docker compose up` locally and the entire backend stack starts in development mode, exactly as it does today. The same `docker-compose.yml` is used for both local development and VPS production, with environment variables controlling production-specific behavior (restart policies, resource limits, Cloudflare tunnel). Locally, the developer can still use the GPU worker with `--profile gpu` for fast transcription.

**Why this priority**: Ongoing feature development depends on a working local environment. Breaking local dev would block all progress.

**Independent Test**: After all VPS changes are made, run `docker compose up` locally and verify the full stack starts, API responds, and file uploads work.

**Acceptance Scenarios**:

1. **Given** the updated `docker-compose.yml`, **When** a developer runs `docker compose up` locally without any production environment variables, **Then** all services start in development mode as they do today.
2. **Given** the same `docker-compose.yml`, **When** production environment variables are set on the VPS, **Then** services start with production settings (restart policies, Cloudflare tunnel, etc.).
3. **Given** a developer is working locally, **When** they run the GPU worker with `--profile gpu`, **Then** it connects to the local Redis and processes tasks with GPU acceleration.

---

### Edge Cases

- What happens when the VPS runs out of disk space? The system should log warnings and degrade gracefully rather than corrupting data.
- What happens when the Cloudflare tunnel disconnects temporarily? The frontend should show appropriate error messages; queued tasks should not be lost.
- What happens when a database migration needs to run on the VPS? There should be a documented process for running Alembic migrations remotely.
- What happens when the VPS IP changes? The Cloudflare tunnel should handle reconnection automatically.
- What happens when CPU transcription takes too long (e.g., very large files)? The task should not time out; the user should see a "processing" status until it completes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The entire backend stack (API, database, cache, file storage, API gateway, worker) MUST run on the Contabo VPS via Docker Compose.
- **FR-002**: The Qdrant vector database MUST be added to the Docker Compose stack with a persistent volume.
- **FR-003**: The Cloudflare tunnel MUST route traffic from the existing domain to the Kong API gateway on the VPS.
- **FR-004**: The frontend (Vercel) MUST connect to the backend on the VPS without any user-visible changes.
- **FR-005**: The Celery worker on the VPS MUST run the full transcription pipeline (transcribe, diarize, summarize, notify) on CPU.
- **FR-006**: All Docker services MUST have restart policies to recover from crashes and VPS reboots.
- **FR-007**: The VPS firewall MUST block all public access except SSH and Cloudflare tunnel traffic.
- **FR-008**: All environment variables and secrets required for deployment MUST be documented.
- **FR-009**: PostgreSQL, MinIO, and Qdrant data MUST use persistent Docker volumes that survive container restarts.
- **FR-010**: There MUST be a documented process for running database migrations on the VPS.
- **FR-011**: The same `docker-compose.yml` MUST work for both local development and VPS production, controlled by environment variables.
- **FR-012**: Local development mode MUST continue to function identically to the current setup after all VPS changes are applied, including GPU worker support via `--profile gpu`.

### Key Entities

- **VPS Environment**: The Contabo server (6 vCPU, 12GB RAM) running all backend services including the Celery worker (CPU-only) via Docker Compose.
- **Cloudflare Tunnel**: Secure connection between the VPS and Cloudflare's network, routing public traffic to Kong without exposing ports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can log in and use the application via the Vercel frontend with the VPS backend, with page loads completing within 3 seconds.
- **SC-002**: File uploads of up to 500 MB complete successfully and are stored on the VPS.
- **SC-003**: The full transcription pipeline (upload, transcribe, diarize, summarize, notify) completes end-to-end on the VPS using CPU.
- **SC-004**: No internal service ports (database, cache, file storage, vector database) are accessible from the public internet.
- **SC-005**: All Docker services recover automatically within 60 seconds of a container crash.
- **SC-006**: The VPS consumes less than 8 GB of RAM under normal operation, leaving 4 GB headroom.
- **SC-007**: The developer's local machine is fully freed from running any backend services.
- **SC-008**: Running `docker compose up` locally starts the full development stack without errors, identical to the pre-migration behavior.

## Assumptions

- The Contabo VPS is already provisioned and the developer has SSH access.
- The existing Cloudflare account and domain are available for tunnel configuration.
- The Vercel frontend deployment can be updated with a new backend URL environment variable.
- No data migration is needed for initial deployment (fresh database is acceptable, or a pg_dump/restore will be performed manually).
- CPU transcription on the VPS is slower than GPU (20-60 min for a 30-min meeting vs 2-3 min on GPU) but functionally acceptable for this phase.
- GPU acceleration for production transcription will be added in a separate feature (RunPod Serverless migration) using a provider abstraction pattern.
