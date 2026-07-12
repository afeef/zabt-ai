# Feature Specification: Meeting Upload Progress

**Feature Branch**: `001-meeting-upload`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "As a logged in user i want to upload an existing meeting so that i can get it transcribed and summarized later. First, I upload the meeting file and I get feedback that the meeting file was uploaded successfully. As the meeting file is being uploaded I should get a real time upload status and feedback as shown in the attached images"

## Clarifications

### Session 2026-02-22
- Q: Where is the upload view located? → A: The upload meeting view is a modal dialog triggered from the right panel or feed zero-state, not a full page view.
- Q: Import Quota Calculation (FR-008) → A: Hardcode a static value (e.g., "3 of 3 imports left") for the MVP layout.
- Q: File Restrictions (FR-009) → A: Assume standard Audio/Video (mp4, mov, mp3, wav, m4a) with a 2GB limit.
- Q: Modal Closure Behavior (FR-010) → A: Show warning: "Upload in progress. Cancel anyway?" to prevent accidental data loss.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Meeting File Upload Modal (Priority: P1)

As a logged-in user, I want to click an upload button to open a modal where I can select a meeting recording file, so that the system can begin uploading it.

**Why this priority**: It is the core entry point for getting meetings into the system to be processed.

**Independent Test**: Can be fully tested by clicking the "Upload" CTA, observing the modal open, clicking "Browse files" to select a file, and seeing the file appear in the upload list.

**Acceptance Scenarios**:

1. **Given** I am on the dashboard, **When** I click "Upload a meeting" in the right panel or feed zero-state, **Then** the "Transcribe audio and video" modal opens.
2. **Given** the upload modal is open, **When** I click "Browse files", **Then** my system file picker opens to select an audio/video file.

---

### User Story 2 - Real-time Upload Progress (Priority: P1)

As a logged-in user, I want to see the real-time upload progress (percentage and progress bar) of my selected file, so that I know the system is actively processing my request and how long it might take.

**Why this priority**: Essential feedback for large files (like 1GB+ meeting videos) so the user doesn't think the system is frozen during long network transfers.

**Independent Test**: Upload a large test file and verify the progress bar smoothly updates from 0% to 100% and displays the correct file size formatted in MB.

**Acceptance Scenarios**:

1. **Given** I have selected a file for upload, **When** the upload starts, **Then** I see the file name, file size (in MB), and a progress bar showing the upload percentage.
2. **Given** a file is uploading, **When** the upload completes, **Then** I receive feedback that the file was uploaded successfully and it transitions out of the active upload state.

---

### User Story 3 - Cancel Uploads (Priority: P2)

As a logged-in user, I want to be able to cancel an ongoing upload, or cancel all uploads at once, so that I can correct a mistake if I selected the wrong file.

**Why this priority**: Large files take a long time to upload; cancelling prevents wasting bandwidth and processing time.

**Independent Test**: Start a large upload and click "Cancel", verifying the network request is aborted and the file is removed from the active list.

**Acceptance Scenarios**:

1. **Given** a file is actively uploading, **When** I click "Cancel", **Then** the upload stops immediately and the file is removed from the active list.
2. **Given** multiple files are uploading, **When** I click "Cancel all", **Then** all active uploads are aborted simultaneously.

---

### User Story 4 - Import Quota and Upgrade CTA (Priority: P3)

As a logged-in free user, I want to see how many imports I have left and a button to upgrade, so that I understand my account limits.

**Why this priority**: Important for user awareness and monetization, establishing the constraints of the system.

**Independent Test**: Verify the footer of the modal displays "X of Y imports left" and the "Upgrade to Business" button.

**Acceptance Scenarios**:

1. **Given** I am on a limited plan, **When** I view the upload modal, **Then** I see my remaining import quota and a prominent upgrade button.

---

### Edge Cases

- What happens if the file selected is completely unsupported or too large (e.g., > 2GB)?
- What happens if the network connection drops during an active upload?
- What happens if the user closes the modal (clicks X) while an upload is actively in progress?
- What happens if the user tries to upload more files than their remaining quota allows?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a modal interface for uploading meeting files, consistent with the reference design image.
- **FR-002**: System MUST allow users to select files via a "Browse files" button.
- **FR-003**: System MUST display an active uploads list inside the modal, showing the filename, formatted file size (e.g., MB/GB), upload percentage, and a visual progress bar.
- **FR-004**: System MUST update the upload progress bar and percentage in real-time as bytes are transferred to the server.
- **FR-005**: System MUST allow users to cancel individual active uploads, halting the network transfer.
- **FR-006**: System MUST allow users to cancel all active uploads via a "Cancel all" button.
- **FR-007**: System MUST provide visual indication when an upload completes successfully or fails.
- **FR-008**: System MUST display the user's remaining import quota and an upgrade CTA at the bottom of the modal. For this MVP, a static value is acceptable.
- **FR-009**: System MUST restrict uploads based on file type (mp4, mov, mp3, wav, m4a) and size (max 2GB).
- **FR-010**: System MUST handle modal closure during active uploads by showing a confirmation warning ("Upload in progress. Cancel anyway?").

### Assumptions

- The backend `uploadMeeting` endpoint natively supports multipart/form-data and we can hook into Axios `onUploadProgress` to drive the client-side progress bar.
- The UI will be built as a React Client Component managing local upload state (progress, abort controllers).
- Quota metrics (e.g., `imports_left`, `total_imports`) will be supplied by the backend. If not currently available, they will be mocked or added as part of this feature.

### Key Entities

- **Meeting** (existing): The core entity created upon a successful file upload.
- **User / Subscription** (existing): Determines the tier and quota limits to drive the "X of Y imports left" UI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully upload meeting files up to the maximum allowed file size.
- **SC-002**: The upload progress bar updates smoothly, accurately reflecting real network transfer progress.
- **SC-003**: Click-to-cancel halts network latency immediately, saving bandwidth for both client and server.
- **SC-004**: The modal UI exactly matches the provided reference design while conforming to existing `.interface-design/system.md` patterns (e.g., typography, colors, no shadows).
