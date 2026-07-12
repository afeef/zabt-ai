# Feature Specification: Unified Processing Queue

**Feature Branch**: `001-unified-processing-queue`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Unified Processing Queue — persistent dashboard panel for worker stage progress, replacing in-modal post-upload tracking"

## Clarifications

### Session 2026-03-10

- Q: Should file upload byte progress and YouTube URL verification move to the queue panel? → A: No. File upload stays in the import dialog. YouTube URL verification stays in the YouTube dialog. Only the worker/processing stages (transcribing, aligning, diarizing, summarizing) move out of the dialogs into the queue panel.
- Q: Should the queue pick up pre-existing processing meetings on page load? → A: No. Queue is session-only — it only shows items submitted during the current browser session. Pre-existing processing meetings are visible via status badges in the meeting feed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - File Upload Worker Progress in Queue (Priority: P1)

A user uploads a meeting audio file using the import dialog. The dialog handles file selection, presigned URL upload, and byte progress as it does today. Once the upload completes successfully, the import dialog removes the completed item from its list (or the user closes the dialog). A new item appears in the processing queue panel at the bottom-right of the dashboard showing the file name and worker pipeline stages: transcribing → aligning → diarizing → summarizing → done. The user can close the import dialog and still see processing progress in the queue.

**Why this priority**: This is the core use case — file uploads are the primary ingestion method and currently require the user to keep the modal open to see post-upload processing stages. Moving worker stages out of the modal lets users track processing without being locked into the dialog.

**Independent Test**: Can be fully tested by uploading a file, closing the import dialog after upload completes, and verifying the queue panel shows worker stage progress.

**Acceptance Scenarios**:

1. **Given** a logged-in user who has just completed a file upload in the import dialog, **When** the upload finishes and the worker begins processing, **Then** a processing queue panel appears at the bottom-right showing the file name and current worker stage.
2. **Given** a file being processed by the worker, **When** the worker progresses through stages, **Then** the queue item updates to reflect the current stage (transcribing → aligning → diarizing → summarizing → done).
3. **Given** a file in the processing queue, **When** the worker fails, **Then** the queue item shows an error state with the failure reason.
4. **Given** an active processing queue, **When** the user closes the import dialog, **Then** the queue panel remains visible and continues updating worker stage progress.

---

### User Story 2 - YouTube URL Worker Progress in Queue (Priority: P1)

A user pastes a YouTube URL in the Paste URL dialog. The dialog handles URL input, client-side validation, and API submission as it does today. Once the backend accepts the URL and the worker begins processing, the dialog closes and a new item appears in the processing queue panel. The item shows the video title (or URL as fallback) and worker pipeline stages: downloading → transcribing → aligning → diarizing → summarizing → done.

**Why this priority**: YouTube ingestion currently has zero progress visibility after the dialog closes. This is a critical gap in user experience that makes the feature feel broken.

**Independent Test**: Can be fully tested by submitting a YouTube URL and verifying the queue panel appears with worker stage progress updates after the dialog closes.

**Acceptance Scenarios**:

1. **Given** a logged-in user who has just submitted a valid YouTube URL, **When** the backend accepts the URL and the dialog closes, **Then** a processing queue item appears showing the URL or video title and the current worker stage.
2. **Given** a YouTube ingestion being processed by the worker, **When** the worker progresses through stages, **Then** the queue item updates to reflect the current stage (downloading → transcribing → summarizing → done).
3. **Given** a YouTube ingestion that fails (e.g., video unavailable), **When** the failure is detected, **Then** the queue item shows an error state with the failure reason.

---

### User Story 3 - Queue Management (Priority: P2)

A user has multiple items processing simultaneously (a mix of file uploads and YouTube ingestions). The queue panel shows all active worker items in a scrollable list. Each item independently tracks its own worker stage progress. When all items complete, the queue auto-hides after a brief delay. The user can manually collapse the queue panel to minimize it while items are still processing.

**Why this priority**: Multi-item management builds on the single-item experience. Users frequently upload multiple files or mix upload methods in a single session.

**Independent Test**: Can be tested by triggering multiple uploads/YouTube ingestions and verifying the queue tracks each independently.

**Acceptance Scenarios**:

1. **Given** multiple active items in the queue, **When** the user views the queue panel, **Then** each item shows its own independent worker stage progress.
2. **Given** all items in the queue have completed (success or failure), **When** 10 seconds elapse after the last completion, **Then** the queue panel auto-hides.
3. **Given** an active processing queue, **When** the user clicks the collapse/minimize control, **Then** the panel collapses to a compact indicator showing the count of active items.
4. **Given** a completed item in the queue, **When** the user clicks on it, **Then** they are navigated to the meeting detail page for that item.

---

### User Story 4 - Import Dialog Refactoring (Priority: P2)

The import dialog retains its current file selection, upload byte progress, and cancellation functionality. However, once a file upload completes, the dialog no longer tracks worker processing stages (transcribing, aligning, etc.) — that responsibility is handed off to the processing queue. The dialog's post-upload polling and stage visualization are removed.

**Why this priority**: Removing worker stage tracking from the import dialog eliminates duplicated progress logic and creates a clean separation: dialog handles upload, queue handles processing.

**Independent Test**: Can be tested by completing a file upload in the dialog and verifying no worker stage indicators appear within the dialog after upload finishes.

**Acceptance Scenarios**:

1. **Given** the import dialog is open and a file upload completes, **When** the worker begins processing, **Then** the dialog shows the upload as complete but does NOT display transcribing/aligning/summarizing stages.
2. **Given** the import dialog, **When** viewing its contents during or after upload, **Then** no worker pipeline stage indicators or post-upload polling status are visible within the dialog.
3. **Given** the import dialog, **When** the user selects a file, **Then** the dialog still shows upload byte progress (loaded/total bytes) as it does today.

---

### Edge Cases

- What happens when the user refreshes the page while items are processing? Queue state resets (session-only); actively processing meetings are visible via status badges in the meeting feed.
- What happens when the user navigates to the dashboard and meetings are already processing from a previous session? The queue does not pick them up; the meeting feed shows their status badges as usual.
- What happens when the user opens and closes dialogs repeatedly without submitting? No queue items are created; the queue only appears when items are actually submitted and the worker begins.
- What happens when the queue has more items than can fit in the visible area? The queue panel becomes scrollable.
- What happens when a meeting reaches "done" state very quickly (e.g., small file)? The item briefly shows completion state before the queue auto-hides.
- What happens when an upload fails mid-transfer in the import dialog? The import dialog handles upload errors as it does today; no queue item is created since the worker never started.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a persistent processing queue panel on the dashboard when any item is actively being processed by the worker.
- **FR-002**: System MUST show worker pipeline stage progress (transcribing → aligning → diarizing → summarizing → done) for file upload items after upload completes.
- **FR-003**: System MUST show worker pipeline stage progress (downloading → transcribing → aligning → diarizing → summarizing → done) for YouTube ingestion items after URL submission.
- **FR-004**: System MUST support both file upload items and YouTube ingestion items in the same queue simultaneously.
- **FR-005**: System MUST allow the user to collapse/minimize the queue panel while items are processing.
- **FR-006**: System MUST auto-hide the queue panel 10 seconds after all items reach a terminal state (done or failed).
- **FR-007**: System MUST display error details when a worker task fails, including the failure reason from the backend.
- **FR-008**: System MUST navigate the user to the meeting detail page when they click a completed queue item.
- **FR-009**: System MUST remove worker stage tracking (post-upload polling and stage visualization) from the import dialog while retaining file upload byte progress and cancellation.
- **FR-010**: System MUST keep the YouTube URL dialog unchanged (input and validation only, no worker stage tracking).
- **FR-011**: System MUST poll for worker status updates and reflect them in the queue in near real-time (within 5 seconds).
- **FR-012**: Queue panel MUST remain visible and functional while the user scrolls or interacts with the meeting feed.
- **FR-013**: Queue MUST be session-only — it tracks only items submitted during the current browser session and does not hydrate pre-existing processing meetings on page load.

### Key Entities

- **QueueItem**: Represents a single item being processed by the worker. Attributes: identifier, display name, source type (file upload or YouTube), current worker pipeline stage, status (processing, done, failed), error message, associated meeting identifier.
- **ProcessingQueue**: The collection of all active queue items. Attributes: list of items, expanded/collapsed state, visibility state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see real-time worker processing progress for both file uploads and YouTube ingestions without keeping any dialog open.
- **SC-002**: 100% of items that enter the worker pipeline appear in the processing queue within 5 seconds of the worker starting.
- **SC-003**: Queue stage updates reflect backend worker status changes within 5 seconds of occurrence.
- **SC-004**: Users can continue browsing and interacting with the meeting list while items process in the background.
- **SC-005**: Import dialog retains full upload byte progress and cancellation while containing zero worker-stage progress elements.
- **SC-006**: Queue correctly tracks up to 5 concurrent items without visual or functional degradation.

## Scope

### In Scope

- Persistent processing queue component on dashboard page
- Unified worker stage progress tracking for file uploads and YouTube URL ingestions
- Collapsible/minimizable queue panel
- Queue item click to navigate to completed meeting
- Error states with failure details from worker
- Removing worker stage tracking from the import dialog (upload progress stays)
- YouTube dialog unchanged (input-only as it already is)

### Out of Scope

- Changes to backend APIs or processing pipeline
- Changes to the transcription/summarization stages themselves
- Moving file upload byte progress out of the import dialog (upload stays in dialog)
- Moving YouTube URL validation out of the YouTube dialog (validation stays in dialog)
- Notification sounds or browser notifications
- Progress persistence across page refreshes (queue resets on refresh)
- Drag-and-drop reordering of queue items
- Retry functionality for failed items (future enhancement)
- Upload cancellation from the queue (cancellation remains in the import dialog)

## Assumptions

- The existing backend polling endpoints provide sufficient status and stage information for the queue to display worker progress.
- The existing presigned upload flow and YouTube submission endpoint do not require changes.
- The meeting feed's existing polling mechanism can be consolidated with the queue's polling to avoid redundant calls.
- A maximum of 5 concurrent items in the queue is sufficient for the current user base.
- The 10-second auto-hide delay after all items complete provides enough time for users to notice completion.
- Queue items are created when the worker begins processing (after upload completes or YouTube URL is accepted), not before.
