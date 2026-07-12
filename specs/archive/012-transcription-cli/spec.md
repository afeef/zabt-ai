# Feature Specification: Transcription CLI

**Feature Branch**: `012-transcription-cli`
**Created**: 2026-02-26
**Status**: Draft
**Input**: User description: "I want to test out the transcription service independently and directly. For this purpose I'm looking for a command line interface where I provide the file for transcription and it goes through all transcription phases and gives the response. The same transcription service needs to be used as the one used in the worker and should have a reusable architecture."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Direct File Transcription (Priority: P1)

As a developer, I want to provide a local audio or video file path to a CLI command and receive the full transcription pipeline output (transcription, alignment, and speaker diarization) printed to the terminal, so that I can test and iterate on the transcription service without deploying the full web stack or going through the upload flow.

**Why this priority**: This is the core ask — running the transcription pipeline directly against a local file. It delivers immediate value for development and debugging, and validates that the transcription service works correctly in isolation.

**Independent Test**: Can be fully tested by running the CLI command with a sample audio file (e.g., a 30-second WAV or MP3) and verifying that speaker-labeled, timestamped transcript segments are printed to the terminal.

**Acceptance Scenarios**:

1. **Given** a valid audio file exists on disk, **When** the developer runs the transcription CLI command with the file path, **Then** the system processes the file through all transcription phases (transcription, alignment, diarization) and prints the resulting segments with speaker labels and timestamps.
2. **Given** the CLI is running, **When** each processing phase begins (transcription, alignment, diarization), **Then** the terminal displays a progress indicator showing which phase is currently active.
3. **Given** the transcription completes successfully, **When** the output is compared to the output the worker would produce for the same file, **Then** the transcript content (segments, speaker labels, timestamps) is identical.

---

### User Story 2 - Optional AI Summarization (Priority: P2)

As a developer, I want to optionally include AI summarization when running the transcription CLI, so that I can validate the full end-to-end pipeline (transcription through summarization) from a single command.

**Why this priority**: Extends the CLI to cover the complete processing pipeline. Less critical than basic transcription since summarization depends on an external LLM service, but important for full pipeline validation.

**Independent Test**: Can be fully tested by running the CLI with the summarization flag on a transcribed file and verifying that a summary, key decisions, action items, and sentiment analysis are produced.

**Acceptance Scenarios**:

1. **Given** a valid audio file and the summarization option is enabled, **When** the developer runs the CLI, **Then** the system completes transcription and then produces a summary with key decisions, action items (with owners), and sentiment analysis.
2. **Given** the summarization option is not enabled (default), **When** the developer runs the CLI, **Then** only the transcription output is produced and no summarization request is made.
3. **Given** the summarization service is unavailable or returns an error, **When** the developer runs the CLI with summarization enabled, **Then** the transcription output is still displayed and a clear error message about the summarization failure is shown.

---

### User Story 3 - Output Format Options (Priority: P3)

As a developer, I want to choose the output format for transcription results (human-readable or structured data), so that I can pipe results into other tools or review them visually.

**Why this priority**: Quality-of-life enhancement that makes the CLI more versatile. Not essential for core testing but significantly improves developer experience.

**Independent Test**: Can be tested by running the CLI with different output format flags on the same file and verifying each produces correctly formatted output.

**Acceptance Scenarios**:

1. **Given** the default output mode, **When** the developer runs the CLI, **Then** the output is displayed in a human-readable format with speaker labels, timestamps, and text.
2. **Given** a structured output option is selected, **When** the developer runs the CLI, **Then** the output is printed as valid JSON containing all segment data (speaker, start time, end time, text, words).

---

### Edge Cases

- What happens when the file path does not exist or is inaccessible? The CLI MUST display a clear error message and exit with a non-zero status code.
- What happens when the file format is unsupported or corrupted? The CLI MUST catch the error during processing and display a meaningful message rather than an unhandled stack trace.
- What happens when the audio file contains no speech? The system MUST complete successfully and produce an empty or minimal transcript rather than crashing.
- What happens when the Hugging Face auth token is missing (required for diarization)? The CLI MUST skip diarization gracefully and produce a transcript without speaker labels, with a warning message.
- What happens when the file is very large (e.g., 3+ hours of audio)? The CLI MUST process it without memory issues, showing phase progress to indicate the system is still working.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command-line interface that accepts a local file path as input and runs the transcription pipeline against it.
- **FR-002**: System MUST execute the same transcription phases as the background worker: speech-to-text transcription, word-level alignment, and speaker diarization.
- **FR-003**: System MUST reuse the existing transcription service — the same code path that processes audio in the worker MUST be invoked by the CLI.
- **FR-004**: System MUST display real-time progress in the terminal as each processing phase starts (e.g., "Transcribing...", "Aligning...", "Diarizing...").
- **FR-005**: System MUST output the transcript as speaker-labeled segments with timestamps upon completion.
- **FR-006**: System MUST support an optional flag to additionally run AI summarization on the transcript, producing a summary, key decisions, action items, and sentiment.
- **FR-007**: System MUST support outputting results in both human-readable (default) and structured JSON formats.
- **FR-008**: System MUST not require a running database, MinIO, or web server for basic transcription (US1). Summarization (US2) requires only the LLM service.
- **FR-009**: System MUST exit with a non-zero status code and display a clear error message when the input file does not exist, is inaccessible, or processing fails.
- **FR-010**: System MUST gracefully skip diarization if the required authentication token is not configured, displaying a warning and producing a transcript without speaker labels.

### Key Entities

- **Transcript Segment**: A contiguous spoken passage with a start time, end time, text content, optional speaker label, and optional word-level timestamps.
- **Meeting Summary**: The AI-generated output containing a summary, key decisions, action items (with owner and due date), and overall sentiment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can transcribe a local audio file with a single command and receive speaker-labeled, timestamped output within the terminal.
- **SC-002**: The transcription output from the CLI is identical to the output the background worker produces for the same file (given the same model configuration).
- **SC-003**: Each processing phase displays its status in the terminal within 1 second of starting.
- **SC-004**: The CLI completes a 5-minute audio file through all transcription phases without requiring any service beyond the local machine (no database, no object storage, no web server).
- **SC-005**: With the summarization flag enabled, the CLI produces a structured summary, action items, and sentiment from the transcript.
