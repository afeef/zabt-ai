# Research: Download Transcript as PDF

## Decision 1: Reuse existing pdf-export.ts vs. new file

**Decision**: Add `exportTranscriptAsPDF()` to the existing `frontend-2/app/lib/pdf-export.ts` file.

**Rationale**: The existing file already handles pdfmake initialization (dynamic import, vfs fonts setup), filename sanitization, duration formatting, metadata header construction, and document styles. All of these are directly reusable. Creating a separate file would duplicate 80% of the code.

**Alternatives considered**:
- Separate `pdf-export-transcript.ts` file — rejected because it would duplicate pdfmake init, sanitization, styles, and metadata header logic.

## Decision 2: Transcript segment formatting in PDF

**Decision**: Each segment rendered as a two-part block: speaker name (bold, indigo color) + timestamp on one line, followed by the spoken text as a paragraph. Segments separated by a small margin.

**Rationale**: This mirrors the on-screen transcript viewer layout and provides clear visual separation between speakers. Using the same stone/indigo color scheme as the summary PDF maintains brand consistency.

**Alternatives considered**:
- Table layout (speaker | timestamp | text) — rejected because long text wrapping in table cells looks cramped and is harder to read.
- Continuous paragraph with inline speaker labels — rejected because it's harder to scan for specific speakers.

## Decision 3: Timestamp formatting

**Decision**: Format timestamps as `MM:SS` or `H:MM:SS` (for meetings over 1 hour). Omit timestamp display if the segment's start time is 0 and it's the first segment.

**Rationale**: Consistent with the transcript viewer's on-screen display. Users expect timestamps in human-readable format, not raw seconds.

## Decision 4: Button placement

**Decision**: Add "Download PDF" button in the Transcript tab header area, next to the existing transcript viewer. Use a download icon (lucide-react `Download`) with text label.

**Rationale**: Consistent with summary tab which already has PDF download in the SummaryMenu. The transcript tab currently has no export controls.

## Decision 5: Data model — no changes needed

**Decision**: No data model changes. The `Meeting` interface already includes `segments?: TranscriptSegment[]` with `speaker`, `start`, `end`, `text`, and `words` fields. The `speakers` map provides display names.

**Rationale**: All required data is already available on the frontend Meeting object.
