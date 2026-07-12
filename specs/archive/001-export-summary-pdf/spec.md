# Feature Specification: Export Summary as PDF

**Feature Branch**: `001-export-summary-pdf`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "As a user, I want to export the generated transcript summary in a pdf format, so that I can download it and share it with others later"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download Summary as PDF (Priority: P1)

A user views a completed meeting's summary and wants to save it offline or share it with colleagues who don't have access to the platform. They click an "Export PDF" button and the browser immediately downloads a well-formatted PDF containing the meeting title, date, and full summary content.

**Why this priority**: This is the core deliverable of the feature — without it, no value is delivered.

**Independent Test**: Open any completed meeting, click "Export PDF", and verify a PDF file downloads containing the meeting title, date, and full summary text.

**Acceptance Scenarios**:

1. **Given** a completed meeting with a summary, **When** the user clicks "Export PDF", **Then** a PDF file downloads automatically named after the meeting title.
2. **Given** a meeting with a long summary containing multiple sections, **When** the PDF is downloaded, **Then** all sections, headings, and content are present and readable.
3. **Given** a meeting with a markdown-formatted summary, **When** the PDF is generated, **Then** headings, bold text, and bullet points are rendered correctly — not shown as raw symbols.

---

### User Story 2 - PDF Includes Meeting Metadata (Priority: P2)

The downloaded PDF should be useful as a standalone document. Beyond the summary text, it includes context like the meeting title, recording date, duration, and speakers so the recipient understands what they are reading without platform access.

**Why this priority**: A PDF with no metadata is hard to identify or file. Metadata makes the exported document immediately shareable and professional.

**Independent Test**: Download a PDF and verify it displays the meeting title, date, and available metadata in a header section.

**Acceptance Scenarios**:

1. **Given** a meeting with a title and creation date, **When** the PDF is generated, **Then** the PDF header displays the meeting title and formatted date.
2. **Given** a meeting where speaker information is available, **When** the PDF is downloaded, **Then** participant names are listed in the document.
3. **Given** a meeting with a duration recorded, **When** the PDF is exported, **Then** the duration is shown in the document header.

---

### Edge Cases

- What happens when the meeting has no summary or is not yet completed? The export button must be hidden or disabled.
- What happens if the summary contains special characters or non-Latin scripts? The PDF must render them correctly without corruption.
- What if the meeting title contains characters invalid in filenames (e.g., `/`, `:`)? The filename must be sanitized before download.
- What if the user's browser blocks automatic file downloads? A fallback visible link must appear.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to export the summary of any completed meeting as a PDF file from the meeting detail page.
- **FR-002**: The exported PDF MUST include the meeting title, date, and full summary content.
- **FR-003**: Markdown formatting in the summary (headings, bold, italics, bullet lists) MUST be rendered as formatted content in the PDF, not as raw symbols.
- **FR-004**: The PDF filename MUST be derived from the meeting title and sanitized to remove characters invalid in filenames.
- **FR-005**: The export action MUST trigger an automatic browser download without navigating away from the page.
- **FR-006**: The "Export PDF" option MUST only be visible and active for meetings with a completed status and a non-empty summary.
- **FR-007**: The exported PDF MUST include available metadata: date, duration (if known), and speaker names (if available).

### Key Entities

- **Meeting Summary Export**: A generated PDF document representing a completed meeting's summary. Attributes: meeting title, meeting date, duration, participant list, summary body (rendered from markdown).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can trigger a PDF download in under 3 seconds from clicking the export button.
- **SC-002**: 100% of markdown formatting elements (headings, bold, lists) present in the summary are correctly rendered in the exported PDF.
- **SC-003**: The exported PDF filename always reflects the meeting title with no invalid filename characters.
- **SC-004**: The export button is shown only on completed meetings with a non-empty summary — zero export attempts succeed on incomplete meetings.
- **SC-005**: The exported PDF opens and displays correctly in any standard PDF viewer without errors.

## Assumptions

- PDF generation is client-side (browser-based) — no server round-trip is required for generating the PDF.
- The feature exports the summary tab content only; raw transcript text export is out of scope for this feature.
- Action items text, if present alongside the summary, is included in the PDF export.
- No custom branding or logo is required in the initial version; a clean, readable layout is sufficient.
- Users must be authenticated to export; no public/anonymous export links are in scope.
