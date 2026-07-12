# Feature Specification: GPU Worker Extraction

**Feature Branch**: `025-gpu-worker-extraction`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Extract GPU transcription/diarization into standalone service with dual-mode (RunPod + local) support"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lightweight Main Worker (Priority: P1)

As the platform owner, I want the main backend worker to have zero GPU/ML dependencies so that it builds and deploys in under 60 seconds instead of the current multi-minute builds. The worker should orchestrate transcription by delegating to an external GPU service rather than running ML models locally.

**Why this priority**: Build speed directly impacts development velocity and deployment frequency. Every code change currently triggers a slow rebuild due to heavy ML dependencies that aren't even used (transcription is already offloaded to RunPod).

**Independent Test**: Deploy the main worker without any GPU libraries installed. Upload a file and verify it successfully delegates transcription to the GPU service, receives the transcript, saves it, and completes the pipeline (summarization, notifications).

**Acceptance Scenarios**:

1. **Given** the main worker is deployed without GPU/ML packages, **When** a user uploads an audio file, **Then** the worker generates a presigned URL, submits a transcription job to the GPU service, polls for completion, and saves the transcript to the database.
2. **Given** the GPU service returns a completed transcript, **When** the main worker receives the result, **Then** it proceeds with summarization, status updates, and notifications exactly as before.
3. **Given** the GPU service is unavailable, **When** the main worker attempts to submit a job, **Then** it retries with backoff and eventually marks the meeting as failed with an appropriate error.

---

### User Story 2 - Standalone GPU Service (Priority: P1)

As the platform owner, I want the GPU transcription and diarization code packaged as a standalone service in its own repository with a single Docker image that works in two modes: production (RunPod serverless) and development (local HTTP server with GPU).

**Why this priority**: Decoupling the GPU service enables independent versioning, deployment, and testing of the ML pipeline. A single image for both modes eliminates "works on my machine" issues between local development and production.

**Independent Test**: Build the GPU service image. Run it in local HTTP mode, send an audio file URL, and receive a transcript with speaker labels. Then deploy the same image to RunPod and verify identical output.

**Acceptance Scenarios**:

1. **Given** the GPU service is running in local HTTP mode, **When** a transcription request is submitted with an audio URL, **Then** it downloads the audio, runs transcription and diarization, and returns a transcript with speaker labels and timestamps.
2. **Given** the GPU service is deployed on RunPod, **When** a transcription job is submitted via the RunPod API, **Then** it processes identically to local mode and returns the same transcript format.
3. **Given** the GPU service receives an invalid or inaccessible audio URL, **When** it attempts to download the file, **Then** it returns a clear error with the failure reason.

---

### User Story 3 - Unified Communication Protocol (Priority: P1)

As a developer, I want the main worker to communicate with the GPU service using the same protocol regardless of whether it's RunPod or a local GPU server, so that switching between environments requires only a configuration change.

**Why this priority**: A unified protocol eliminates environment-specific code paths, reducing bugs and making local development mirror production exactly.

**Independent Test**: Configure the main worker to point to a local GPU service, run a transcription job, then reconfigure to point to RunPod and run the same job. Both should produce equivalent results with no code changes.

**Acceptance Scenarios**:

1. **Given** the worker is configured to use a local GPU service, **When** a transcription job is submitted, **Then** it uses the same submit/poll pattern as RunPod (submit job, poll status, retrieve result).
2. **Given** the worker is configured to use RunPod, **When** a transcription job is submitted, **Then** the same client code handles submission, polling, and result retrieval.
3. **Given** the environment configuration changes from local to RunPod (or vice versa), **When** the worker is restarted, **Then** it seamlessly uses the new target with no code changes.

---

### User Story 4 - Error Monitoring in GPU Service (Priority: P2)

As the platform owner, I want errors and performance data from the GPU service reported to Sentry so that I have visibility into transcription failures, processing times, and resource usage across both RunPod and local environments.

**Why this priority**: GPU processing is the most failure-prone and resource-intensive part of the pipeline. Without observability, diagnosing transcription failures requires manual log inspection.

**Independent Test**: Trigger a transcription error (e.g., corrupt audio file) and verify it appears in Sentry with relevant context (job ID, audio URL, error type, environment tag).

**Acceptance Scenarios**:

1. **Given** the GPU service encounters an error during transcription, **When** the error occurs, **Then** it is reported to Sentry with job context before the handler returns.
2. **Given** the GPU service completes a transcription successfully, **When** performance data is captured, **Then** processing duration per stage (download, transcription, diarization) is visible in Sentry.

---

### Edge Cases

- What happens when the audio file is too large for the GPU service's available memory?
- How does the system handle RunPod cold starts? (Mitigated: models are baked into the image, so cold start only involves container startup and model loading into GPU memory, not downloading.)
- What happens when a transcription job is submitted but the GPU service crashes mid-processing?
- How does the system handle concurrent transcription requests exceeding GPU capacity?
- What happens when the presigned URL expires before the GPU service downloads the audio?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The main worker MUST operate without any GPU/ML dependencies (no torch, whisperx, pyannote in its dependency tree).
- **FR-002**: The GPU service MUST accept a single input: an audio file URL (presigned S3/MinIO URL) and return a structured transcript with speaker labels, timestamps, and text segments.
- **FR-003**: The GPU service MUST support two operational modes from the same codebase and Docker image: RunPod serverless handler and local HTTP server, switchable via configuration.
- **FR-004**: The main worker MUST communicate with the GPU service using a poll-based pattern: submit job, poll for status, retrieve result — identical for both RunPod and local modes.
- **FR-005**: The main worker MUST handle GPU service failures gracefully with retries and appropriate error states on the meeting record.
- **FR-006**: The GPU service MUST have no knowledge of users, meetings, or the application database — it is a stateless function (audio in, transcript out).
- **FR-007**: The GPU service MUST report errors and performance data to an external monitoring service.
- **FR-008**: The GPU service MUST flush monitoring data before the handler returns to account for ephemeral container lifecycles.
- **FR-009**: The GPU service MUST live in a separate repository with its own dependency management, build configuration, and CI pipeline.
- **FR-010**: The main worker MUST continue to handle all orchestration: presigned URL generation, transcript persistence, meeting status updates, summarization triggering, and notification dispatch.
- **FR-011**: The GPU service Docker image MUST include all ML model weights baked in at build time — no runtime model downloads. Model updates are handled by rebuilding the image with pinned model versions.

### Key Entities

- **Transcription Job**: Represents a request to the GPU service — contains audio URL, job ID, status (queued/in_progress/completed/failed), and result payload.
- **Transcript Result**: The GPU service's output — a list of segments, each with speaker label, start time, end time, and text content.
- **Transcription Client**: The main worker's abstraction for communicating with the GPU service — handles job submission, status polling, and result retrieval regardless of backend (RunPod or local).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Main worker Docker image builds in under 60 seconds (compared to current multi-minute builds with ML dependencies).
- **SC-002**: Transcription results from the GPU service are identical regardless of mode (local vs RunPod) for the same audio input.
- **SC-003**: Switching between local GPU and RunPod requires only changing environment variables — zero code changes.
- **SC-004**: GPU service errors appear in monitoring within 30 seconds of occurrence.
- **SC-005**: End-to-end transcription pipeline (upload → transcript saved) completes within the same time bounds as the current system.
- **SC-006**: The GPU service repository has no imports or dependencies from the main application codebase.

## Clarifications

### Session 2026-03-15

- Q: Should models be pre-built into the Docker image to avoid cold-start downloads? → A: Yes. Models MUST be baked into the Docker image at build time. No runtime downloads.
- Q: How should model updates be handled? → A: Rebuild and redeploy the Docker image with new model weights baked in. Models are pinned to specific versions.

## Assumptions

- The existing RunPod integration's API pattern (submit/poll/retrieve) is the reference protocol for the unified client.
- Presigned URLs have sufficient TTL (at least 1 hour) to account for RunPod cold starts and queue wait times.
- The GPU service will initially support the same models currently in use (WhisperX + pyannote) with no model changes in this feature scope.
- The new repository will be hosted on the same GitHub organization as the main repo.
- Local GPU development uses the same NVIDIA/CUDA stack currently in use.
