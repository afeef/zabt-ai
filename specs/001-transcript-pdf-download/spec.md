# Feature Specification: Download Transcript as PDF

**Feature Branch**: `001-transcript-pdf-download`
**Created**: 2026-03-09
**Status**: Draft
**Input**: User description: "Download transcript as a styled PDF from the meeting detail page"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download Transcript as PDF (Priority: P1)

A user has a completed meeting with a full transcript. They want to download the transcript as a professionally formatted PDF to share with a colleague who does not have access to Zabt, or to archive for offline reference. The user navigates to the meeting detail page, switches to the Transcript tab, and clicks a "Download PDF" button. The system generates a PDF in the browser containing the meeting metadata header (title, date, duration, speakers) followed by the full transcript with speaker labels and timestamps. The PDF downloads automatically.

**Why this priority**: This is the core value — users currently have no way to export transcripts as formatted documents. Summaries already have PDF export; transcripts do not.

**Independent Test**: Navigate to a completed meeting with transcript data, click "Download PDF" on the Transcript tab, verify a PDF file downloads with the correct meeting title in the filename, containing a metadata header and the full transcript with speaker labels and timestamps.

**Acceptance Scenarios**:

1. **Given** a completed meeting with transcript segments, **When** the user clicks "Download PDF" on the Transcript tab, **Then** a PDF file downloads with filename `{meeting-title}-transcript.pdf` containing the meeting metadata header and all transcript segments with speaker names and timestamps
2. **Given** a completed meeting with multiple speakers, **When** the PDF is generated, **Then** each transcript segment shows the speaker name (bold) and timestamp, followed by the spoken text
3. **Given** a meeting that is still processing, **When** the user views the Transcript tab, **Then** the "Download PDF" button is disabled or hidden
4. **Given** a completed meeting with no transcript segments, **When** the user views the Transcript tab, **Then** the "Download PDF" button is not shown

---

### Edge Cases

- What happens when the meeting title contains special characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`)? The filename MUST sanitize these characters by replacing them with hyphens.
- What happens when the transcript is very long (e.g., a 3-hour meeting with hundreds of segments)? The PDF MUST handle pagination automatically without truncating content.
- What happens when a speaker name is missing for some segments? The system MUST display "Unknown Speaker" as a fallback label.
- What happens when timestamps are missing or zero? The system MUST omit the timestamp display for that segment rather than showing "00:00".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a transcript PDF entirely in the browser — no server-side processing required
- **FR-002**: The transcript PDF MUST include a metadata header with: meeting title, date, duration, and speaker names
- **FR-003**: Each transcript segment in the PDF MUST display the speaker name (bold) and timestamp, followed by the spoken text on the next line
- **FR-004**: The PDF filename MUST follow the pattern `{sanitized-meeting-title}-transcript.pdf` where special characters are replaced with hyphens
- **FR-005**: The "Download PDF" button MUST be disabled or hidden when the meeting status is not "completed"
- **FR-006**: The "Download PDF" button MUST not appear when there are no transcript segments
- **FR-007**: The PDF MUST use Zabt brand styling: clean layout, professional typography, consistent with existing summary PDF styling (stone/indigo color palette for headers)
- **FR-008**: The PDF MUST handle transcripts of any length with proper pagination
- **FR-009**: Speaker names that are empty or missing MUST display as "Unknown Speaker"
- **FR-010**: The "Download PDF" button MUST be placed in the Transcript tab area, accessible alongside the transcript viewer

### Key Entities

- **Transcript Segment**: A single spoken passage with speaker identity, timestamp (start time in seconds), and text content
- **Meeting**: The parent entity containing metadata (title, date, duration, speakers map) and an array of transcript segments

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can download a transcript PDF in under 3 seconds for meetings up to 2 hours long
- **SC-002**: 100% of transcript segments appear in the downloaded PDF with correct speaker attribution
- **SC-003**: Downloaded PDF opens correctly in all major PDF readers (browser built-in, Adobe, Preview)
- **SC-004**: PDF filename is always valid across Windows, macOS, and Linux file systems (no illegal characters)

## Assumptions

- The existing summary PDF export utility provides reusable patterns for metadata headers, filename sanitization, and document initialization — the transcript export will follow the same conventions
- The PDF generation library is already installed in the frontend project
- Transcript segments are available on the Meeting object as an array of objects with speaker, start time, and text fields
- The speakers map on the Meeting object maps speaker IDs to display names
- No new environment variables are needed
- No backend changes are needed
