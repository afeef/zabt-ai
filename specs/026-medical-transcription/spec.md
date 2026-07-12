# Feature Specification: Transcription Type Selection (Normal + Medical)

**Feature Branch**: `026-medical-transcription`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Add transcription type selection to the upload flow with MedASR for medical transcription"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medical Transcription Upload (Priority: P1)

A healthcare professional uploads a recording of a doctor-patient consultation or clinical dictation. Before uploading, they select "Medical" as the transcription type. The system processes the audio using a medical-optimized speech recognition model that accurately handles clinical terminology, drug names, anatomical terms, and medical abbreviations. The resulting transcript has significantly higher accuracy for medical content compared to the general-purpose model.

**Why this priority**: This is the core value proposition — enabling medical professionals to get accurate transcriptions of clinical audio that general-purpose models struggle with.

**Independent Test**: Upload a medical dictation recording with "Medical" type selected and verify the transcript accurately captures medical terminology (drug names, diagnoses, anatomical terms).

**Acceptance Scenarios**:

1. **Given** a logged-in user on the upload screen, **When** they select "Medical" transcription type and upload a clinical dictation audio file, **Then** the system processes it using the medical speech recognition model and returns a transcript with accurate medical terminology.
2. **Given** a medical transcription job is processing, **When** the user views the meeting detail page, **Then** they see the transcription type displayed as "Medical" and progress updates work identically to normal transcriptions.
3. **Given** a completed medical transcription, **When** the user views the transcript, **Then** the output format (speaker labels, timestamps, segments) is identical to normal transcriptions.

---

### User Story 2 - Normal Transcription (Default Behavior) (Priority: P1)

A user uploads a recording of a business meeting, podcast, or general conversation. The transcription type defaults to "Normal" and the system processes using the existing general-purpose model. No change to the current user experience — this story ensures backward compatibility.

**Why this priority**: Equal priority to US1 — must ensure existing functionality is not disrupted.

**Independent Test**: Upload any audio file without changing the transcription type selector and verify the transcript is produced identically to the current behavior.

**Acceptance Scenarios**:

1. **Given** a logged-in user on the upload screen, **When** they upload an audio file without changing the default transcription type, **Then** the system processes it using the general-purpose model (existing behavior).
2. **Given** an existing meeting that was transcribed before this feature, **When** the user views it, **Then** it displays as "Normal" transcription type with no changes to the transcript.

---

### User Story 3 - Transcription Type Selection UI (Priority: P1)

The upload flow presents a clear, simple selector for choosing the transcription type before uploading. The default is "Normal." The selector is unobtrusive for users who don't need medical transcription — they can ignore it entirely.

**Why this priority**: The UI control is required for both US1 and US2 to function.

**Independent Test**: Open the upload modal and verify the transcription type selector is visible, defaults to "Normal", and allows switching to "Medical".

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they open the upload modal, **Then** they see a transcription type selector defaulting to "Normal" with "Medical" as an alternative option.
2. **Given** a user has selected "Medical" transcription type, **When** they upload a file, **Then** the selected type is sent with the upload request and stored with the meeting record.
3. **Given** a user is pasting a YouTube URL, **When** they see the upload options, **Then** the transcription type selector is also available for URL-based imports.

---

### Edge Cases

- What happens when a user selects "Medical" for a non-medical recording (e.g., business meeting)? The system processes it with the medical model regardless — the user's choice is respected. Medical model may produce slightly different results for non-medical content but should still be functional.
- What happens when the medical model is unavailable or fails on the processing service? The system reports a transcription failure with an appropriate error message. It does NOT silently fall back to the normal model — the user chose medical for a reason.
- What happens to existing meetings created before this feature? They default to "Normal" transcription type via database migration default value.
- What happens when a user uploads via the URL import flow? The transcription type selector is available and works identically to the file upload flow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present a transcription type selector (Normal / Medical) in the upload flow, defaulting to "Normal"
- **FR-002**: System MUST store the selected transcription type with each meeting record
- **FR-003**: System MUST route transcription processing to the appropriate model based on the selected type — "Normal" uses the general-purpose model, "Medical" uses the medical-optimized model
- **FR-004**: System MUST produce identical output format (speaker labels, timestamps, segments) regardless of which transcription model is used
- **FR-005**: System MUST display the transcription type on the meeting detail page so users can see which model was used
- **FR-006**: System MUST apply "Normal" as the default transcription type to all existing meetings via database migration
- **FR-007**: System MUST support transcription type selection for both file uploads and URL-based imports (YouTube)
- **FR-008**: System MUST NOT silently fall back to a different model if the selected model fails — it should report the failure clearly
- **FR-009**: System MUST bake the medical model into the processing service image at build time to avoid cold-start delays from model downloads
- **FR-010**: Both models MUST support speaker diarization (speaker separation and labeling)
- **FR-011**: The GPU worker MUST use a multi-stage Docker build: a base image (CUDA + Python + PyTorch) hosted on Docker Hub that rebuilds rarely, and a worker image that installs ML dependencies via uv/pyproject.toml and copies source code — so source-only changes rebuild in seconds
- **FR-012**: The GPU worker project MUST be managed with uv and a pyproject.toml/uv.lock for reproducible dependency management

### Key Entities

- **Meeting**: Extended with a `transcription_type` field (enum: "normal", "medical", default "normal"). Records which model was used for transcription.
- **Transcription Job**: The job payload sent to the processing service includes the `transcription_type` field to route to the correct model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Medical professionals can upload clinical audio and receive transcripts with medical terminology accuracy of 95%+ (measured by word error rate on medical terms)
- **SC-002**: Normal transcription behavior is unchanged — existing users see no difference in their workflow or transcript quality
- **SC-003**: Transcription type selection adds no more than 1 additional click to the upload flow
- **SC-004**: Medical model transcription completes within the same time envelope as normal transcription (no more than 2x processing time difference)
- **SC-005**: No cold-start penalty from model loading — medical model is pre-loaded in the processing service

## Clarifications

### Session 2026-03-15

- Q: Does the system need HIPAA compliance for medical users? → A: Best-effort medical transcription — no formal HIPAA compliance. Audio processed on self-hosted GPU (RunPod). Users are responsible for their own compliance.
- Q: Where should the GPU worker base image be hosted? → A: Docker Hub (public or private repo).

## Assumptions

- The medical speech recognition model supports English clinical audio (dictation and conversation). Multi-language medical support is out of scope.
- The medical model uses the same diarization system as the normal model for speaker separation.
- User profile preferences for default transcription type are explicitly deferred to a future feature.
- LLM/summarization model selection is a separate backlog item and not included in this feature.
- The medical model (Google MedASR, 105M parameters) is small enough to be loaded alongside the general-purpose model without requiring additional GPU resources.

## Out of Scope

- User profile preferences for default transcription type
- LLM/summarization model selection
- Multi-language medical transcription
- Medical-specific summary templates (e.g., SOAP notes)
- Real-time/streaming medical transcription
