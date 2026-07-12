# Feature Specification: Transcription Worker Provider Switch (RunPod / Local)

**Feature Branch**: `021-runpod-worker`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "The system should support switching between local Celery workers (CPU or GPU) and RunPod Serverless for transcription, using environment variables only — similar to how we handle MinIO vs S3 storage."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - RunPod Transcription on VPS (Priority: P1)

As a VPS operator deploying Zabt on a machine without a GPU, I want transcription to be offloaded to RunPod Serverless so that meetings are transcribed quickly using cloud GPUs instead of slow CPU-only processing.

**Why this priority**: The VPS has no GPU, and CPU transcription is too slow for production. This is the core reason for the feature — without it, the VPS deployment is not viable for real users.

**Independent Test**: Deploy with `TRANSCRIPTION_PROVIDER=runpod` and upload a meeting. The worker sends audio to RunPod, polls for completion, retrieves transcript+diarization results, stores segments in the database, and proceeds to summarization — all without any local Whisper/pyannote installation.

**Acceptance Scenarios**:

1. **Given** the system is configured with `TRANSCRIPTION_PROVIDER=runpod` and valid RunPod credentials, **When** a meeting audio file is uploaded and the transcription pipeline is triggered, **Then** the worker sends the audio to RunPod Serverless, polls until completion, and stores the transcript segments and speaker labels in the database in the same format as local transcription.
2. **Given** the system is configured with `TRANSCRIPTION_PROVIDER=runpod`, **When** the transcription completes on RunPod, **Then** the summarization step runs locally on the worker as usual (LLM call is never offloaded).
3. **Given** the system is configured with `TRANSCRIPTION_PROVIDER=runpod`, **When** the RunPod job fails or times out, **Then** the meeting is marked as failed and the user receives a failure notification email.

---

### User Story 2 - Local GPU Transcription for Development (Priority: P2)

As a developer running Zabt locally with a GPU, I want transcription to continue using the local Whisper+pyannote pipeline with zero configuration changes so that my development workflow is unaffected.

**Why this priority**: Local development must remain seamless. Developers should not need RunPod credentials or internet access for transcription during development.

**Independent Test**: Start with `COMPOSE_PROFILES=local` (no `TRANSCRIPTION_PROVIDER` set or set to `local`). Upload a meeting. The GPU worker transcribes locally using Whisper+pyannote exactly as before.

**Acceptance Scenarios**:

1. **Given** the system is running with the `local` Docker Compose profile and `TRANSCRIPTION_PROVIDER` is unset or set to `local`, **When** a meeting is uploaded, **Then** the GPU worker transcribes using the local WhisperX+pyannote pipeline with CUDA acceleration.
2. **Given** no RunPod-related environment variables are configured, **When** the worker starts, **Then** no RunPod connectivity is attempted and the worker operates in fully offline local mode.

---

### User Story 3 - RunPod Serverless Endpoint (Priority: P3)

As a DevOps engineer, I need a RunPod Serverless endpoint definition (handler code) that runs Whisper large-v3 + pyannote speaker-diarization-3.1 and returns results in Zabt's expected format, so that the VPS worker can call it.

**Why this priority**: The RunPod endpoint is infrastructure that must exist for US1 to work, but it's a one-time setup artifact rather than ongoing application logic.

**Independent Test**: Deploy the handler to RunPod Serverless and call it directly with an audio file URL. It returns a JSON response with transcript text, segments (start, end, text, speaker), and word-level timestamps.

**Acceptance Scenarios**:

1. **Given** the RunPod handler is deployed, **When** it receives a request with an audio file URL, **Then** it downloads the audio, runs Whisper large-v3 transcription and pyannote diarization, and returns a JSON response matching Zabt's `TranscriptionResult` format.
2. **Given** the RunPod handler receives an audio file, **When** processing completes, **Then** the response includes: full transcript text, detected language, segments with start/end times and speaker labels, and word-level timestamps.

---

### Edge Cases

- What happens when RunPod is configured but the endpoint is unreachable? The worker should mark the meeting as failed after a configurable timeout and send a failure email.
- What happens when RunPod returns a partial result (e.g., transcription succeeds but diarization fails)? The worker should store the available transcript without speaker labels rather than failing entirely.
- What happens when the audio file is too large for RunPod's input limits? The worker should detect this before sending and mark the meeting as failed with a descriptive error.
- What happens when `TRANSCRIPTION_PROVIDER` is set to an invalid value? The worker should fail fast at startup with a clear error message.
- What happens when RunPod credentials are missing but `TRANSCRIPTION_PROVIDER=runpod`? The worker should fail fast at startup with a clear error listing the missing variables.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a `TRANSCRIPTION_PROVIDER` environment variable with values `local` (default) and `runpod`.
- **FR-002**: When `TRANSCRIPTION_PROVIDER=runpod`, the Celery worker's `stage_transcribe` task MUST send the audio file to a RunPod Serverless endpoint instead of invoking local Whisper/pyannote.
- **FR-003**: When `TRANSCRIPTION_PROVIDER=local` or unset, the transcription pipeline MUST behave identically to the current implementation (local WhisperX + pyannote).
- **FR-004**: The RunPod integration MUST use the existing `TranscriptionProvider` Protocol interface, returning a standard `TranscriptionResult` with segments, speaker labels, and word timestamps.
- **FR-005**: The worker MUST provide the audio file to RunPod via a presigned URL from the storage provider (S3/MinIO), since the worker and RunPod do not share a filesystem.
- **FR-006**: The worker MUST poll the RunPod job status until completion, with configurable timeout (default: 30 minutes) and polling interval (default: 5 seconds).
- **FR-007**: The summarization step (`stage_summarize`) MUST always run locally on the worker regardless of the transcription provider.
- **FR-008**: The RunPod Serverless handler MUST run Whisper large-v3 and pyannote speaker-diarization-3.1 and return results compatible with Zabt's `TranscriptionResult` format.
- **FR-009**: System MUST require `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` environment variables when `TRANSCRIPTION_PROVIDER=runpod`, and fail fast at startup if they are missing.
- **FR-010**: The `stage_transcribe` status callback (`on_status_change`) MUST continue to report progress stages (downloading, transcribing, diarizing) for both providers, enabling the existing progress tracking to work.
- **FR-011**: Docker Compose `vps` profile MUST include the `TRANSCRIPTION_PROVIDER` and RunPod-related environment variables for the worker service.

### Key Entities

- **TranscriptionProvider**: Existing Protocol interface — no schema changes. RunPod implementation added as a new provider alongside WhisperProvider.
- **TranscriptionResult / ResultSegment / WordTimestamp**: Existing data classes — no changes. RunPod handler must produce output that maps to these structures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A meeting uploaded on the VPS (with `TRANSCRIPTION_PROVIDER=runpod`) is fully transcribed with speaker diarization and summarized within 5 minutes for a 30-minute audio file.
- **SC-002**: Local development workflow remains unchanged — developers can transcribe meetings without RunPod credentials or internet connectivity for transcription.
- **SC-003**: Transcription results from RunPod are identical in structure and quality to local Whisper large-v3 + pyannote results (same segment format, speaker labels, word timestamps).
- **SC-004**: Failed RunPod jobs are detected and the user is notified via the existing failure email flow within 1 minute of the failure.
- **SC-005**: Switching between providers requires only changing environment variables — no code changes, no redeployment of containers beyond restart.

## Assumptions

- The VPS worker has network access to both the RunPod API and the S3/MinIO storage where audio files are stored.
- RunPod Serverless cold starts are acceptable (typically 10-30 seconds) since transcription is already an asynchronous background job.
- The RunPod handler will be deployed and managed separately from the main Zabt application (it's a standalone serverless function on RunPod's platform).
- Audio files are already accessible via presigned URLs from the storage provider, so no additional upload mechanism is needed for RunPod to access them.

## Scope Boundaries

**In scope**:
- RunPod provider implementation in the backend worker
- RunPod Serverless handler code (Whisper + pyannote)
- Environment variable configuration and factory pattern integration
- Docker Compose environment variable additions

**Out of scope**:
- Real-time WebSocket transcription via RunPod (the `transcribe_chunk` method will raise NotImplementedError for RunPod)
- Automatic failover from RunPod to local transcription
- RunPod cost tracking or billing integration
- Changes to the frontend — the provider switch is entirely backend/infrastructure
