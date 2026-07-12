# Feature Specification: Transcription Progress Tracking

**Feature Branch**: `017-transcription-progress`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "As a user, when I upload a meeting file to the application, it shows the file uploaded status on the modal dialog but does not show if the transcription or later processes have started. When I close the modal dialog I see the list of meetings but they also don't show the current state of the transcription progress. I want to update the frontend on each stage of processing both on the modal dialog box and the meetings page — i.e. file uploaded stage, transcription stage, alignment stage, diarization stage and done stage."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Upload Modal Shows Processing Stages (Priority: P1)

As a user who has just uploaded a meeting file, after the upload completes I want to see the current processing stage update live inside the upload modal — so I know the system is actively working on my file and can gauge how far along it is without closing the modal.

**Why this priority**: The upload modal is the first place a user looks after uploading. Without live stage feedback, the green checkmark ("success") is misleading — it only means the file was received, not that transcription has started or is progressing.

**Independent Test**: Upload a file, keep the modal open, and verify stage labels cycle through each processing phase in real time.

**Acceptance Scenarios**:

1. **Given** a file upload has completed (green checkmark shown), **When** the backend begins processing the meeting, **Then** the upload item in the modal updates to show the current processing stage label (e.g., "Transcribing…", "Aligning…", "Diarizing…").
2. **Given** the modal is open and the meeting is processing, **When** the processing stage changes on the backend, **Then** the stage label in the modal updates within a few seconds without requiring the user to close and reopen the modal.
3. **Given** the modal is open and processing completes, **When** the status reaches "done", **Then** the upload item clearly indicates completion (e.g., label changes to "Done", visual indicator updates).
4. **Given** the modal is open and processing fails, **When** the backend sets the meeting to failed, **Then** the upload item shows an error state with a brief message.

---

### User Story 2 — Meetings List Shows Processing Stages (Priority: P1)

As a user viewing my meetings list, I want each in-progress meeting to display its current processing stage — so I can monitor progress without clicking into individual meeting detail pages.

**Why this priority**: The meetings list is the primary dashboard view. Currently it only shows a generic "Processing…" label, which gives no insight into how far along the pipeline a meeting is.

**Independent Test**: Navigate to the meetings page while a meeting is processing, and verify the meeting card shows a specific stage label that updates live.

**Acceptance Scenarios**:

1. **Given** I am on the meetings list and a meeting is in the "processing" state, **When** the page loads, **Then** the meeting card shows the specific processing stage (e.g., "Transcribing…") instead of just "Processing…".
2. **Given** I am on the meetings list, **When** the backend processing stage changes, **Then** the meeting card's stage label updates within a few seconds without a full page reload.
3. **Given** a meeting transitions from "processing" to "completed", **When** the update reaches the frontend, **Then** the status badge changes to "Completed" and the meeting becomes clickable/viewable.
4. **Given** a meeting transitions from "processing" to "failed", **When** the update reaches the frontend, **Then** the status badge changes to "Failed" with a brief error indicator.

---

### User Story 3 — Stage Progress Indicator (Priority: P2)

As a user, I want a visual progress indicator that shows which stages have been completed and which remain — so I can estimate how much longer the processing will take.

**Why this priority**: A stepped progress indicator adds significant value by letting users anticipate wait times, but the core requirement (showing the current stage name) can function without it.

**Independent Test**: Observe a processing meeting and verify a multi-step indicator highlights completed stages and the active stage.

**Acceptance Scenarios**:

1. **Given** a meeting is processing, **When** I view it in the upload modal or meetings list, **Then** I see a stepped progress indicator showing all major stages (Uploaded → Transcribing → Aligning → Diarizing → Done).
2. **Given** the meeting has completed the transcription stage, **When** I view the progress indicator, **Then** the "Transcribing" step is marked as complete and the "Aligning" step is marked as active.
3. **Given** processing completes, **When** I view the progress indicator, **Then** all steps are marked as complete.

---

### Edge Cases

- What happens when the user closes and reopens the upload modal — does it still show progress for recently uploaded files? **Assumption**: Once the modal is closed, progress tracking for that upload session ends. The meetings list takes over as the progress-monitoring surface.
- What happens if the backend skips a stage (e.g., alignment not needed for a particular provider)? **Assumption**: Skipped stages are marked as complete instantly and the indicator advances to the next applicable stage.
- What happens if the user has multiple files uploading simultaneously? Each file should independently track and display its own processing stage.
- What happens if the user navigates away from the meetings page and returns? The latest processing stage should be fetched and displayed immediately on page load.
- What happens on a slow or intermittent network connection? The stage display should show the last known stage and update when connectivity resumes. Stale data should not mislead the user into thinking processing is stuck.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose the current processing sub-stage of a meeting through the existing meetings data (the backend already tracks sub-stages: downloading, validating, extracting audio, transcribing, aligning, diarizing, parsing, summarizing — these must be surfaced to the frontend).
- **FR-002**: The upload modal MUST continue tracking a meeting's processing progress after the file upload itself completes, showing stage transitions in real time.
- **FR-003**: The meetings list page MUST display the specific processing stage for each in-progress meeting, replacing the generic "Processing…" label.
- **FR-004**: The frontend MUST poll or receive updates for processing stage changes at a frequency that keeps the displayed stage current (within a few seconds of a backend stage transition).
- **FR-005**: The system MUST display a user-friendly stage label for each processing phase. The stages visible to the user are: **Uploaded**, **Transcribing**, **Aligning**, **Diarizing**, and **Done**. Internal stages (downloading, validating, extracting audio, parsing, cleaning up, summarizing) MUST be grouped under the nearest user-visible stage.
- **FR-006**: The system MUST visually distinguish between completed stages, the active stage, and pending stages.
- **FR-007**: When processing fails, the system MUST show the failure state clearly on both the upload modal (if open) and the meetings list, with a brief error description.
- **FR-008**: The meeting detail page MUST also display the current processing stage with the same granularity as the meetings list.

### Stage Mapping

The backend tracks internal sub-stages. These map to user-visible stages as follows:

| User-Visible Stage | Backend Sub-Stages Included                                      |
| ------------------- | ---------------------------------------------------------------- |
| Uploaded            | pending_upload, queued, downloading, validating, extracting_audio |
| Transcribing        | uploading (cloud), transcribing                                  |
| Aligning            | aligning                                                         |
| Diarizing           | diarizing, parsing                                               |
| Done                | cleaning_up, summarizing, completed                              |

### Key Entities

- **Meeting**: Existing entity. Relevant fields: `status` (high-level state), `sub_status` (granular processing stage — already tracked by the backend but not currently exposed to the frontend).
- **Processing Stage**: A user-facing representation of the current point in the transcription pipeline (Uploaded → Transcribing → Aligning → Diarizing → Done).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the exact processing stage of any in-progress meeting within 5 seconds of viewing the meetings list or upload modal.
- **SC-002**: Stage updates appear on the frontend within 10 seconds of the backend transitioning to a new stage.
- **SC-003**: 100% of processing stage transitions are reflected in the UI — no stage is silently skipped without visual feedback.
- **SC-004**: Users no longer need to click into a meeting detail page to determine processing progress — the meetings list provides sufficient stage information.
- **SC-005**: The upload modal provides post-upload processing visibility, reducing user uncertainty about whether transcription has started after file upload completes.

## Assumptions

- The backend already persists `sub_status` for each processing stage. The primary work is exposing this data to the frontend and building the UI to display it.
- Polling is an acceptable mechanism for near-real-time updates. WebSockets or SSE are not required for this iteration.
- The five user-visible stages (Uploaded, Transcribing, Aligning, Diarizing, Done) provide sufficient granularity. Users do not need to see internal stages like "downloading" or "parsing".
- The upload modal only tracks progress for files uploaded in the current session. It does not retroactively show progress for previously uploaded files.
- The meeting detail page's existing polling mechanism will be extended to show stage-level progress, but the detail page is not the primary focus of this feature (it already has a processing banner).
