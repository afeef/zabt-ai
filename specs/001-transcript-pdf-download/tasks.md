# Tasks: Download Transcript as PDF

**Input**: Design documents from `/specs/001-transcript-pdf-download/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/ui-transcript-pdf.md, quickstart.md

**Tests**: E2E test included (constitution requirement for user-facing features).

**Organization**: Single user story (US1) — Download Transcript as PDF.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify existing dependencies are in place

- [x] T001 Verify `pdfmake` and `@types/pdfmake` are installed in frontend-2/ — run `npm ls pdfmake` in `frontend-2/`

---

## Phase 2: User Story 1 — Download Transcript as PDF (Priority: P1) 🎯 MVP

**Goal**: Users can download a professionally formatted PDF of the meeting transcript from the Transcript tab.

**Independent Test**: Navigate to a completed meeting → switch to Transcript tab → click "Download PDF" → verify a PDF downloads with metadata header, speaker labels, timestamps, and full transcript text.

### Implementation

- [x] T002 [US1] Add `formatTimestamp(seconds: number): string` helper to frontend-2/app/lib/pdf-export.ts — format as `MM:SS` for values under 3600, `H:MM:SS` for values 3600+; return empty string for 0 or negative values
- [x] T003 [US1] Add `exportTranscriptAsPDF(meeting: Meeting): Promise<void>` function to frontend-2/app/lib/pdf-export.ts — reuse existing pdfmake initialization, sanitizeFilename, formatDuration, metadata header, separator line, and styles from `exportSummaryAsPDF`; build transcript body by iterating `meeting.segments`: for each segment render speaker name (bold, color `#4f46e5`) + timestamp on one line, then spoken text as a paragraph below; use "Unknown Speaker" fallback for missing speaker names; download as `{sanitized-title}-transcript.pdf`
- [x] T004 [US1] Add "Download PDF" button to the Transcript tab in frontend-2/app/(dashboard)/meetings/[id]/page.tsx — show only when `meeting.status === "completed"` and `meeting.segments` is non-empty; place above the transcript viewer aligned right; use `Download` icon from lucide-react; style with `text-sm font-medium text-stone-600 hover:text-stone-800 border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors`; on click call `exportTranscriptAsPDF(meeting)` and fire PostHog event `transcript_exported` with `{ meeting_id: meeting.id }`
- [x] T005 [US1] Run `npx tsc --noEmit` in frontend-2/ and fix any TypeScript errors

**Checkpoint**: User Story 1 complete — users can download transcript as PDF

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing and final validation

- [x] T006 Write E2E test for transcript PDF download in tests/e2e/test_transcript_pdf.py — Playwright/Python: navigate to completed meeting, switch to Transcript tab, verify "Download PDF" button visible, click it, verify download triggers with correct filename pattern
- [x] T007 Verify design system compliance — audit Download PDF button for: no shadows, border-stone-200, rounded-lg, stone text hierarchy, consistent with existing button patterns on the page

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **User Story 1 (Phase 2)**: Depends on Phase 1 (pdfmake verified)
- **Polish (Phase 3)**: Depends on Phase 2 (download flow must work)

### Within User Story 1

- T002 (timestamp helper) before T003 (export function uses it)
- T003 (export function) before T004 (button calls the function)
- T004 (button integration) before T005 (type check)

### Parallel Opportunities

None within this feature — tasks are sequential due to file dependencies (all modify the same two files).

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Verify pdfmake installed
2. Complete Phase 2: Build export function + integrate button
3. **STOP and VALIDATE**: Test download flow on a real meeting
4. Deploy — users can now download transcript PDFs

### Incremental Delivery

1. Setup → Dependencies verified
2. User Story 1 → Download works → Deploy (MVP!)
3. Polish → E2E test + design audit → Confidence for production

---

## Notes

- Reuses existing `pdf-export.ts` patterns — pdfmake init, filename sanitization, metadata header, styles
- No backend changes, no database changes, no new environment variables
- The `sanitizeFilename()` and `formatDuration()` helpers already exist in `pdf-export.ts`
- Speaker names resolved via `meeting.speakers` map (speaker ID → display name)
- E2E tests are in Playwright/Python per constitution (Principle VI)
