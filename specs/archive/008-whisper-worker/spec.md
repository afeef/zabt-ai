# Feature Specification: Audio Transcription & Diarization Backend (WhisperX)

**Feature Branch**: `008-whisper-worker`  
**Created**: 2026-02-22  
**Status**: Draft  

## Overview
This specification outlines the architecture and requirements for replacing the synchronous OpenAI Whisper API placeholder with a robust, asynchronous, local machine-learning pipeline. The system leverages **WhisperX** for high-precision transcription, word-level alignment, and speaker diarization, orchestrated by **Celery** and **Redis**.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - High-Quality Audio Transcription & Diarization (Priority: P1)
As a user, I want the system to automatically transcribe my uploaded audio and accurately identify different speakers, giving me a professional meeting transcript with granular word-level timestamps.

**Why this priority**: Transcription and speaker identification form the bedrock of the Zabt intelligence platform. Without it, summaries and downstream features cannot function.

**Independent Test**: Upload a 5-minute English audio file with at least two distinct speakers. Verify the Celery worker outputs a JSON payload containing accurate text segments mapped to `SPEAKER_00` and `SPEAKER_01`.

**Acceptance Scenarios**:
1. **Given** a valid audio file is uploaded to the backend, **When** the WhisperX worker processes the job, **Then** a transcript is successfully generated with word-level start and end times.
2. **Given** a multi-speaker audio file, **When** the diarization phase completes, **Then** transcript segments are logically clustered and assigned to distinct speaker IDs (`SPEAKER_XX`).
3. **Given** conversational English audio, **When** processed, **Then** the transcription word error rate (WER) is visibly minimal and alignment bounds are precise.

---

### User Story 2 - Real-Time Granular Progress Tracking (Priority: P2)
As a user waiting for a long meeting to process, I want to see the real-time status of the transcription job (e.g., "Queued", "Transcribing", "Aligning", "Diarizing"), so I have visibility into the background progress.

**Why this priority**: AI processing takes time. Transparent, multi-stage status updates prevent user frustration and perceived application hangs.

**Independent Test**: Trigger a transcription job and monitor the `Meeting` record's status field in the database. Verify it transitions smoothly across the defined processing phases.

**Acceptance Scenarios**:
1. **Given** a job is submitted to the Celery queue, **When** picked up by a worker, **Then** the database status immediately reflects `processing`.
2. **Given** the worker advances from raw transcription to Wav2Vec2 alignment, **When** queried, **Then** the database `sub_status` or progress log reflects the "Aligning" phase.

---

### User Story 3 - Resilient Hardware Degradation (Priority: P3)
As a system administrator, I want the worker to leverage GPU acceleration natively if available, but gracefully fall back to CPU allocation if a CUDA device is missing, ensuring the service never crashes due to hardware constraints.

**Why this priority**: Operational reliability. Guarantees the backend remains functional even in bare-metal CI environments or limited staging servers.

**Independent Test**: Force the application to launch in a strictly CPU-bound Docker container. Verify the application logs warn about CPU-mode, but successfully complete a transcription job.

**Acceptance Scenarios**:
1. **Given** a valid CUDA-enabled GPU is detected by PyTorch, **When** the Celery task boots, **Then** WhisperX models (`compute_type="float16"`) are loaded into VRAM.
2. **Given** no GPU is detected (`torch.cuda.is_available() == False`), **When** the task boots, **Then** the worker defaults to CPU (`compute_type="int8"`) with reduced batch sizes and succeeds without throwing a `RuntimeError`.

---

## Edge Cases & Error Handling

- **Extremely Large Files (OOM Risk)**: Audio files exceeding 2+ hours could exhaust GPU VRAM during the diarization phase. The system must utilize WhisperX's memory-efficient chunking and set appropriate Celery timeouts.
- **Corrupted Media / Unknown Formats**: If `ffmpeg` fails to decode an uploaded file, the worker must catch the exception, log the codec error, and transition the Meeting status to `failed` to prevent zombie tasks.
- **HuggingFace Rate Limits / Auth**: Pyannote diarization models require a valid HuggingFace Token (`HF_AUTH_TOKEN`). If the token is missing or invalid, the task must fail fast rather than hanging indefinitely.

---

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST strictly orchestrate background tasks using **Celery** with **Redis** configured as the message broker.
- **FR-002**: System MUST integrate **WhisperX** (using standard `openai-whisper` + `pyannote-audio`) for transcription and diarization.
- **FR-003**: System MUST implement an automatic **GPU (CUDA) to CPU fallback** boot sequence, and the services MUST be developed and deployed via Docker with NVIDIA Container Toolkit for GPU passthrough.
- **FR-004**: Celery worker MUST commit transactional updates directly to the PostgreSQL `Meeting` record at each pipeline lifecycle stage.
- **FR-005**: The final payload MUST conform to the `TranscriptSegment` and `TranscriptWord` database schemas, inserting distinct records per transcribed segment.
- **FR-006**: The pipeline MUST support a configuration parameter for language. For Phase 1, it will default to `"en"`.
- **FR-007**: System MUST use absolute or controlled relative paths for audio file retrieval between the FastAPI upload context and the Celery worker context.

### Key Entities

- **Celery Worker Node**: The asynchronous process consuming tasks off the internal Redis queue.
- **Meeting Entity**: The central relational database record Tracking file metadata, lifecycle status (`queued`, `processing`, `completed`, `failed`), and relationships to nested `TranscriptSegment`s.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: A 30-minute English audio file processes in < 5 minutes on a standard NVIDIA T4/A10G GPU.
- **SC-002**: Diarization successfully segments over 90% of speech turns in clean, two-person dialogue.
- **SC-003**: Hardware fallback correctly parses the PyTorch hardware tree, enabling local developer testing seamlessly without Docker GPU passthrough configurations.
