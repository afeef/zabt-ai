# Feature Specification: YouTube URL Ingestion

**Feature Branch**: `001-youtube-ingestion`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Allow users to ingest meetings from YouTube videos by pasting a URL"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paste YouTube URL to Create Meeting (Priority: P1)

A user has a recorded meeting or presentation on YouTube that they want transcribed and summarized. They click the "Paste URL" button next to the Import button on the home page. A dialog opens with a text input. They paste a YouTube video URL and click "Process". The system validates the URL, closes the dialog, and a new meeting card appears in the feed with "Processing" status. The backend extracts audio from the video, transcribes it, and summarizes it — producing the same result as a file upload. The meeting title defaults to the YouTube video title.

**Why this priority**: Core feature — without this, the entire feature has no value. This is the primary user journey that delivers the end-to-end capability.

**Independent Test**: Can be fully tested by pasting a valid YouTube URL and verifying a meeting is created, transcribed, and summarized. Delivers immediate value as a standalone feature.

**Acceptance Scenarios**:

1. **Given** a logged-in user on the home page, **When** they click "Paste URL", **Then** a dialog opens with a text input field and a "Process" button.
2. **Given** the URL dialog is open, **When** the user pastes a valid YouTube URL (e.g., `youtube.com/watch?v=...`) and clicks "Process", **Then** the dialog closes and a new meeting card appears in the feed with "Processing" status.
3. **Given** a YouTube URL has been submitted, **When** processing completes, **Then** the meeting has a transcript and summary, and the title matches the YouTube video title.
4. **Given** a YouTube URL has been submitted, **When** the user views the meeting card, **Then** a visual indicator (icon or badge) shows the meeting originated from YouTube.

---

### User Story 2 - URL Validation and Error Handling (Priority: P2)

A user pastes an invalid or unsupported URL. The system validates URL format client-side and at the API level, providing instant feedback in the dialog. Server-side checks (video existence, duration, accessibility) happen asynchronously in the worker — failures surface as error status on the meeting card, not in the dialog.

**Why this priority**: Essential for a polished user experience — users will inevitably paste wrong URLs, and clear error messages prevent confusion and support tickets.

**Independent Test**: Can be tested by submitting various invalid URLs and verifying appropriate error messages appear inline.

**Acceptance Scenarios**:

1. **Given** the URL dialog is open, **When** the user pastes a non-YouTube URL (e.g., `vimeo.com/...`), **Then** an inline error appears: "Please enter a valid YouTube video URL".
2. **Given** the URL dialog is open, **When** the user pastes a malformed URL (e.g., random text), **Then** an inline error appears: "Please enter a valid YouTube video URL".
3. **Given** the URL dialog is open, **When** the user pastes a YouTube playlist URL, **Then** an inline error appears: "Playlist URLs are not supported. Please paste a single video URL."
4. **Given** a valid YouTube URL is submitted, **When** the video is unavailable (deleted, private, or geo-blocked), **Then** the meeting card shows a failed status with the reason: "Video unavailable — it may be private, deleted, or restricted."
5. **Given** a valid YouTube URL is submitted, **When** the video exceeds the maximum duration (4 hours), **Then** the meeting card shows a failed status with the reason: "Video exceeds the maximum duration of 4 hours."

---

### User Story 3 - Processing Progress and Status (Priority: P3)

A user wants to know the status of their YouTube ingestion. The meeting card in the feed reflects the current processing stage, consistent with how file uploads display progress. If processing fails at any stage, the user sees a clear error message.

**Why this priority**: Completes the user experience by providing transparency into what can be a longer processing time (YouTube download + transcription + summarization). Less critical than the core flow but important for user confidence.

**Independent Test**: Can be tested by submitting a YouTube URL and observing status transitions on the meeting card from "Processing" through to "Completed" or "Failed".

**Acceptance Scenarios**:

1. **Given** a YouTube URL has been submitted, **When** the meeting card is displayed in the feed, **Then** it shows "Processing" status with appropriate visual treatment (same as file uploads).
2. **Given** processing is in progress, **When** audio extraction fails, **Then** the meeting card shows "Failed" status with the reason displayed.
3. **Given** processing completes successfully, **When** the user views the meeting card, **Then** it shows "Completed" status and the user can view the transcript and summary.

---

### Edge Cases

- What happens when the user pastes a YouTube Shorts URL? System accepts it — Shorts are valid single videos.
- What happens when the same YouTube URL is submitted twice? System creates a second, separate meeting (no deduplication — consistent with uploading the same file twice).
- What happens when the YouTube video has no audio track? Processing fails with a clear error: "No audio track found in video."
- What happens if the backend loses connection to YouTube mid-download? Processing fails with error: "Failed to download audio. Please try again."
- What happens when the user submits a URL and immediately navigates away? Processing continues in the background; the meeting card updates when the user returns.
- What happens with age-restricted videos? Processing fails with error: "Video is age-restricted and cannot be processed."
- What happens with live streams that are currently broadcasting? System rejects with error: "Live streams in progress cannot be processed. Please wait until the stream ends."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a "Paste URL" button adjacent to the existing Import/Upload button on the home page.
- **FR-002**: System MUST display a dialog with a text input field and "Process" button when "Paste URL" is clicked.
- **FR-003**: System MUST validate that the submitted URL matches known YouTube URL formats (standard watch URLs, short links, live links, Shorts).
- **FR-004**: System MUST reject playlist URLs with a specific error message distinguishing them from invalid URLs.
- **FR-005**: The API endpoint MUST only validate URL format and create a meeting record; all YouTube interaction (video existence check, duration check, audio download) MUST happen in a background worker.
- **FR-006**: The worker MUST enforce a maximum video duration of 4 hours and fail the meeting with a clear reason if exceeded.
- **FR-007**: The worker MUST extract audio from the YouTube video and store it permanently in the same object storage used for uploaded files (retained indefinitely, consistent with file uploads).
- **FR-008**: The worker MUST feed extracted audio into the existing transcription and summarization pipeline without modifications to that pipeline.
- **FR-014**: All heavy processing (YouTube download, metadata extraction, audio extraction, transcription, summarization) MUST run in background workers, not in the API request handler.
- **FR-009**: System MUST set the meeting title to the YouTube video title by default.
- **FR-010**: System MUST display a visual indicator (icon or badge) on meeting cards for YouTube-sourced meetings.
- **FR-011**: System MUST show appropriate error messages for all failure modes: video unavailable, age-restricted, geo-blocked, duration exceeded, download failure, no audio track, live stream in progress.
- **FR-012**: System MUST track analytics events for: URL dialog opened, URL submitted, processing started, processing completed, processing failed (with failure reason).
- **FR-013**: System MUST display the meeting card with "Processing" status immediately after URL submission, consistent with the existing file upload behavior.
- **FR-015**: System MUST enforce a limit of 3 concurrent YouTube ingestions per user. If the limit is reached, additional submissions are queued and processed as slots free up. The user MUST be informed when their submission is queued.

### Key Entities

- **Meeting**: Extended with source type (file upload vs. YouTube URL), source URL, and video metadata (original title, duration, thumbnail URL).
- **YouTube Video Metadata**: Video title, duration, thumbnail URL, channel name — extracted during ingestion and stored with the meeting record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a YouTube URL and have a transcribed, summarized meeting available within 2x the video duration (accounting for download + transcription + summarization time).
- **SC-002**: 95% of valid public YouTube URLs are successfully processed without errors.
- **SC-003**: Invalid URL submissions receive error feedback within 2 seconds.
- **SC-004**: YouTube-sourced meetings are visually distinguishable from uploaded meetings at a glance.
- **SC-005**: All existing functionality (file upload, meeting feed, transcription, summarization) continues to work without regression.
- **SC-006**: Users can identify the source YouTube video from the meeting detail page.

## Scope

### In Scope

- Single YouTube video URL ingestion
- Public and unlisted YouTube videos
- Standard YouTube URL formats: watch, short links, live links, Shorts
- Meeting title from video title
- Visual indicator that meeting originated from YouTube
- Error handling for all known failure modes

### Out of Scope

- YouTube playlist ingestion (single video only)
- Private videos requiring YouTube authentication
- Other video platforms (Vimeo, Loom, etc.) — future feature
- Video playback within the app
- Downloading or storing the video file (audio extraction only)
- Editing the meeting title before submission (user can edit after creation)

## Clarifications

### Session 2026-03-10

- Q: Should all heavy processing happen in the worker rather than the API? → A: Yes. FastAPI does URL format validation and creates meeting record only. All YouTube interaction (download, metadata, audio extraction, transcription, summarization) runs in background workers.
- Q: Should the API validate video existence/duration, or defer to worker? → A: Defer all YouTube checks to worker. API validates URL format only, creates meeting immediately. Errors surface asynchronously on the meeting card.
- Q: Should YouTube-extracted audio be retained permanently or cleaned up? → A: Retain permanently, same as uploaded files. Consistent behavior, low storage cost, allows re-processing.
- Q: Should there be a per-user limit on concurrent YouTube ingestions? → A: Limit 3 concurrent per user. New submissions queued until a slot frees up.

## Constraints

- The API endpoint MUST do minimal work: validate URL format, create meeting record, dispatch to worker, return immediately.
- A dedicated worker (or worker task) handles YouTube audio download separately from the existing transcription worker, to avoid blocking transcription jobs with potentially slow YouTube downloads.
- Worker failures MUST update the meeting record with a user-facing error reason.

## Assumptions

- Users have a stable internet connection sufficient to submit the URL; the backend handles the actual video download.
- YouTube's public video access patterns remain stable (the audio extraction tool handles format changes via updates).
- The existing transcription pipeline can handle audio extracted from YouTube without format-specific modifications.
- The maximum video duration limit of 4 hours is sufficient for typical meeting recordings; this can be adjusted later.
- YouTube Shorts are treated as regular videos — they go through the same pipeline.
- Per-user concurrency limit of 3 is sufficient for initial launch; can be adjusted or replaced by credits system later.

## Dependencies

- Existing file upload and meeting creation flow (used as the model for YouTube ingestion behavior).
- Existing transcription and summarization pipeline (reused without modification).
- Object storage for storing extracted audio files.
- Analytics integration for tracking new events.
