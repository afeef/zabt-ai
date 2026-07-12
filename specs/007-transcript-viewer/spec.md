# Feature Specification: Media Transcription Viewer

**Feature Branch**: `007-transcript-viewer`  
**Created**: 2026-02-22
**Status**: Draft  
**Input**: Build a speaker-wise media transcription viewer and player interface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transcript Navigation & Playback (Priority: P1)

As a user, I want a persistent media player with a vertical transcript log that highlights my current playback position and allows me to seek by clicking timestamps, so that I can easily review and navigate the meeting's dialog.

**Why this priority**: Core value proposition of the viewer. Without playback and time-synced transcripts, the feature is just a text block.

**Independent Test**: Can be fully tested by launching the viewer for a meeting, pressing play to observe word-level highlighting, and clicking a transcript timestamp to verify the player jumps to that moment.

**Acceptance Scenarios**:
1. **Given** the user is viewing a meeting transcript, **When** they click a specific timestamp next to a speaker's text, **Then** the media player immediately seeks to that exact moment in the media.
2. **Given** the media is playing, **When** the current time reaches a specific word, **Then** that word is visually highlighted in the transcript in real-time.
3. **Given** the user scrolls to the bottom of the transcript, **When** the sticky media player is active, **Then** the player must not obscure or visually overlap the final lines of the text.

---

### User Story 2 - Metadata & Speaker Identification (Priority: P2)

As a user, I want to see a metadata header and a "Speakers" section showing talk time percentages, so that I can quickly understand who was in the meeting and who dominated the conversation.

**Why this priority**: Important for meeting context and analytics, but secondary to the actual act of reading/listening to the transcript.

**Independent Test**: Can be tested by loading the viewer and verifying the header displays the correct participants, duration, keywords, and the proportion of talk time for each speaker.

**Acceptance Scenarios**:
1. **Given** a meeting with multiple speakers, **When** the user views the "Speakers" section, **Then** they see a breakdown of the percentage of total talk time for each speaker (e.g., Speaker 1 (61%), Speaker 2 (35%)).
2. **Given** the backend returns an "Unknown Speaker" or overlapping speech, **When** the system renders the transcript log and speaker section, **Then** it gracefully displays a placeholder label without breaking the UI.

---

### User Story 3 - Paywall for Long Media (Priority: P3)

As a free-tier user, I want to be prompted to upgrade if the media exceeds 30 minutes, so that I understand the limits of my plan and know how to access the full recording.

**Why this priority**: Essential for monetization limits, but applies primarily to a specific tier and media length.

**Independent Test**: Can be tested by loading a meeting longer than 30 minutes as a free user and verifying the bottom text is blurred with an upgrade prompt blocking further scrolling.

**Acceptance Scenarios**:
1. **Given** a free-tier user views a meeting longer than 30 minutes, **When** they scroll down to the 30-minute mark in the transcript, **Then** a "Transcript limit reached" modal overlay appears.
2. **Given** the limit modal is active, **When** the user attempts to scroll or view content past 30 minutes, **Then** the underlying text is blurred, scrolling is prevented, and a clear "Upgrade" primary button is presented.

---

### Edge Cases

- What happens if the backend JSON payload containing text, speaker IDs, and word-level timestamps is malformed or missing timestamps?
- How does the system handle "Unknown Speaker" labels or overlapping speech if the backend diarization model returns ambiguous data? (Covered by gracefully handling UI fallbacks).
- Ensure the sticky bottom player does not overlap or obscure the last lines of the transcript. (Covered by padding/margin constraints).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a tabbed interface allowing the user to switch between a "Summary" and a "Transcript" view.
- **FR-002**: System MUST display a metadata header showing participants, total duration, and a list of generated Keywords.
- **FR-003**: System MUST display a "Speakers" section summarizing the percentage of talk time for each participant.
- **FR-004**: System MUST render the transcript as a vertical log where each entry shows the speaker's avatar, name, timestamp, and spoken text.
- **FR-005**: System MUST highlight the specific word currently being spoken in the transcript in real-time, synced tightly with the media player.
- **FR-006**: System MUST seek the media player to the exact moment represented by a clicked timestamp in the transcript.
- **FR-007**: System MUST display a persistent media player at the bottom of the screen with play/pause, 10-second rewind, playback speed toggle, and a progress bar.
- **FR-008**: System MUST visually segment the media player's progress bar using different colors corresponding to when different speakers are talking.
- **FR-009**: System MUST enforce a 30-minute view limit for free-tier users, implementing a modal overlay that blurs underlying text past 30 minutes, prevents scrolling, and prompts an upgrade.

### Key Entities

- **Transcript View Payload**: The JSON structure containing an array of speaker segments, where each segment contains text, speaker IDs, and word-level timestamps.
- **Meeting Metadata**: The high-level data including title/participants, duration, and keywords.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The transcript viewer successfully ingests and renders the complete JSON payload containing text, speaker IDs, and word-level timestamps.
- **SC-002**: Real-time word highlighting accurately syncs with media playback, updating without noticeable lag (e.g., <100ms drift).
- **SC-003**: Clicking a transcript timestamp triggers a media seek operation that resolves instantly.
- **SC-004**: Users are prevented from reading text or seeking media past the 30-minute mark if governed by the free-tier UI blocker.
- **SC-005**: All speaker blocks in the timeline progress bar are visually distinct and map to the correct timestamps.
