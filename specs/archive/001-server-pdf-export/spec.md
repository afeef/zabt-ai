# Feature Specification: Server-Side PDF Export

**Feature Branch**: `001-server-pdf-export`
**Created**: 2026-03-09
**Status**: Draft
**Input**: Replace client-side pdfmake PDF generation with server-side PDF generation for meeting summary and transcript exports, with full multilingual support (Arabic/Urdu RTL, Devanagari/Hindi, Latin).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download Summary as PDF (Priority: P1)

A user navigates to a completed meeting's detail page and wants to download the meeting summary as a professionally formatted PDF for offline reading, sharing, or archiving. They click the "Download PDF" option in the Summary tab. The system generates a PDF on the server with the meeting metadata header (title, date, duration, speakers), the full summary with markdown formatting preserved (headings, lists, bold, italic), and any action items. The PDF downloads to their device with a descriptive filename.

**Why this priority**: Summary PDF is the most-requested export format. Users share summaries with stakeholders who don't have app access. This is the core value proposition of the feature.

**Independent Test**: Navigate to a completed meeting → Summary tab → click "Download PDF" → verify PDF downloads with correct metadata header, formatted summary content, and action items.

**Acceptance Scenarios**:

1. **Given** a completed meeting with a summary, **When** the user clicks "Download PDF" on the Summary tab, **Then** a PDF file downloads with the filename `{meeting-title}-summary.pdf` containing the meeting metadata header and formatted summary content.
2. **Given** a completed meeting with summary text containing markdown (headings, bold, lists), **When** the PDF is generated, **Then** the markdown formatting is visually preserved in the PDF output.
3. **Given** a completed meeting with action items, **When** the PDF is generated, **Then** the action items section appears below the summary in the PDF.
4. **Given** a meeting that is still processing, **When** the user views the Summary tab, **Then** the "Download PDF" option is not available.

---

### User Story 2 - Download Transcript as PDF (Priority: P1)

A user navigates to a completed meeting's Transcript tab and wants to download the full transcript as a PDF. They click the "Download PDF" button. The system generates a PDF with the meeting metadata header, followed by the full transcript with speaker labels (bold, colored) and timestamps for each segment. The PDF downloads with a descriptive filename.

**Why this priority**: Transcript PDF is equally important — users need formatted transcripts for legal records, meeting minutes, and sharing with absent participants. Same priority as summary since both are core export use cases.

**Independent Test**: Navigate to a completed meeting → Transcript tab → click "Download PDF" → verify PDF downloads with metadata header, speaker labels, timestamps, and transcript text.

**Acceptance Scenarios**:

1. **Given** a completed meeting with transcript segments, **When** the user clicks "Download PDF" on the Transcript tab, **Then** a PDF file downloads with the filename `{meeting-title}-transcript.pdf` containing the metadata header and full transcript.
2. **Given** a transcript with multiple speakers, **When** the PDF is generated, **Then** each segment shows the speaker name prominently and the timestamp, followed by the spoken text.
3. **Given** a transcript segment with an unknown speaker, **When** the PDF is generated, **Then** the speaker is displayed as "Unknown Speaker".
4. **Given** a meeting with no transcript segments, **When** the user views the Transcript tab, **Then** the "Download PDF" button is not visible.

---

### User Story 3 - Multilingual PDF Export (Priority: P1)

A user has a meeting recorded in Urdu, Hindi, Arabic, or any other non-Latin language. When they download the summary or transcript as PDF, the text renders correctly with proper script shaping, ligatures, and right-to-left layout where applicable — not as empty boxes or garbled characters.

**Why this priority**: The current client-side solution fails entirely for non-Latin scripts. Multilingual support is a critical requirement since the user base includes Urdu and Hindi speakers. This is the primary reason for migrating to server-side generation.

**Independent Test**: Upload/create a meeting with Urdu or Hindi content → download summary or transcript PDF → verify text renders correctly with proper script rendering and layout direction.

**Acceptance Scenarios**:

1. **Given** a meeting with Urdu/Arabic summary text, **When** the PDF is generated, **Then** the Arabic script renders correctly with proper ligatures and right-to-left text direction.
2. **Given** a meeting with Hindi/Devanagari transcript, **When** the PDF is generated, **Then** the Devanagari script renders correctly with proper conjunct characters.
3. **Given** a meeting with mixed Latin and Arabic text, **When** the PDF is generated, **Then** both scripts render correctly in the same document with appropriate bidirectional layout.

---

### User Story 4 - Remove Client-Side PDF Dependencies (Priority: P2)

After server-side PDF generation is in place, the client-side pdfmake library, font files, and related code are removed from the frontend. This reduces the frontend bundle size and eliminates the maintenance burden of client-side font management.

**Why this priority**: Cleanup task — depends on US1-US3 being complete. Reduces bundle size and removes dead code, but doesn't deliver new user value on its own.

**Independent Test**: After removal, verify the frontend builds without errors, both PDF download buttons still work via the server endpoint, and the frontend bundle no longer includes pdfmake.

**Acceptance Scenarios**:

1. **Given** the server-side PDF export is working, **When** the client-side PDF code and dependencies are removed, **Then** the frontend builds successfully without errors.
2. **Given** the cleanup is complete, **When** a user clicks either "Download PDF" button, **Then** the PDF is generated and downloaded via the server endpoint.

---

### Edge Cases

- What happens when the user downloads a PDF for a meeting with an extremely long title? The filename is sanitized to remove invalid characters and truncated if necessary.
- What happens if the server-side PDF generation fails (e.g., out of memory for very large transcripts)? The user receives a clear error message indicating the download failed.
- What happens when a user tries to download a PDF for a meeting they don't own? The request is rejected with an appropriate authorization error.
- What happens when the meeting summary or transcript contains special characters (HTML entities, code blocks, URLs)? These are rendered correctly or safely escaped in the PDF.
- What happens when a transcript has hundreds of segments (2+ hour meeting)? The PDF generates within a reasonable time and includes all segments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a server-side endpoint that generates a PDF for a given meeting, accepting a type parameter to distinguish between summary and transcript exports.
- **FR-002**: System MUST convert meeting summary markdown to formatted PDF output preserving headings, lists, bold, italic, and paragraph structure.
- **FR-003**: System MUST generate transcript PDFs with speaker name labels, timestamps (MM:SS or H:MM:SS format), and spoken text for each segment.
- **FR-004**: System MUST include a metadata header in every PDF containing: meeting title, date, duration, and speaker names.
- **FR-005**: System MUST render Arabic/Urdu script (RTL), Devanagari/Hindi script, and Latin script correctly in generated PDFs, including mixed-script documents.
- **FR-006**: System MUST set the `Content-Disposition` header to trigger a browser download with the filename pattern `{sanitized-title}-summary.pdf` or `{sanitized-title}-transcript.pdf`.
- **FR-007**: System MUST authenticate the requesting user and verify they own the meeting before generating the PDF.
- **FR-008**: System MUST return an appropriate error when the meeting is not in "completed" status.
- **FR-009**: System MUST return an appropriate error when requesting a transcript PDF for a meeting with no transcript segments.
- **FR-010**: The frontend "Download PDF" buttons MUST trigger the server-side endpoint instead of client-side generation.
- **FR-011**: The frontend MUST remove the pdfmake library, associated font files, and client-side PDF generation code after migration.
- **FR-012**: PDFs MUST follow the Zabt brand styling — clean, professional appearance with the stone/indigo color palette.
- **FR-013**: System MUST include action items section in the summary PDF when action items exist for the meeting.

### Key Entities

- **Meeting**: The source data entity — contains title, created_at, duration_seconds, summary_text (markdown), action_items_text (markdown), segments (array of transcript entries), speakers (map of speaker ID to name), and status.
- **Transcript Segment**: A portion of the transcript — contains speaker identifier, start timestamp (seconds), and spoken text.
- **Speaker**: A participant in the meeting — identified by ID, with a display name resolved from the meeting's speakers map.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can download a summary PDF within 5 seconds of clicking the button for meetings up to 60 minutes long.
- **SC-002**: Users can download a transcript PDF within 10 seconds of clicking the button for meetings up to 120 minutes long.
- **SC-003**: 100% of Arabic/Urdu and Hindi/Devanagari text renders correctly in generated PDFs — no missing glyphs, empty boxes, or broken ligatures.
- **SC-004**: PDF downloads work on all major browsers (Chrome, Firefox, Safari, Edge) without additional plugins or configuration.
- **SC-005**: Frontend bundle size decreases after removing the pdfmake dependency and font files.
- **SC-006**: Both summary and transcript PDF downloads maintain existing button placement and user interaction patterns — no change to the user's click workflow.

## Assumptions

- The backend server has sufficient memory to generate PDFs for meetings up to 2+ hours (potentially hundreds of transcript segments).
- System fonts for Arabic, Devanagari, and Latin scripts can be installed in the server's container environment.
- The existing authentication mechanism (Supabase JWT) can be used to authenticate the PDF export endpoint.
- Meeting data (summary, transcript, speakers) is already fully populated by the time a meeting reaches "completed" status.
- The current "Download PDF" button placements (Summary tab via SummaryMenu, Transcript tab above viewer) remain unchanged — only the underlying mechanism changes from client-side to server-side.

## Scope Boundaries

**In scope**:
- Server-side PDF generation for summary and transcript
- Multilingual rendering (Arabic/Urdu, Hindi/Devanagari, Latin)
- Authenticated API endpoint with ownership verification
- Frontend integration to call the new endpoint
- Removal of client-side pdfmake code, dependencies, and font files

**Out of scope**:
- Batch export (downloading multiple meeting PDFs at once)
- Custom PDF templates or user-configurable styling
- PDF generation for meetings in non-completed states
- Email delivery of PDFs
- PDF preview before download
