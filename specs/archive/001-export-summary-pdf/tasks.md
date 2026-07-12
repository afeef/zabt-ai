# Tasks: Export Summary as PDF

**Input**: Design documents from `/specs/001-export-summary-pdf/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/ui-export-pdf.md ✓, quickstart.md ✓

---

## Phase 1: Setup

**Purpose**: Install pdfmake dependency in the frontend project

- [X] T001 Install pdfmake and @types/pdfmake in frontend-2/package.json by running `npm install pdfmake && npm install --save-dev @types/pdfmake` in `frontend-2/`

---

## Phase 2: Foundational — PDF Export Utility

**Purpose**: Core `pdf-export.ts` utility that both user stories depend on

**⚠️ CRITICAL**: Must be complete before any UI integration

- [X] T002 Create `frontend-2/app/lib/pdf-export.ts` with `exportSummaryAsPDF(meeting: Meeting): void` function that: initialises pdfmake, sanitizes filename (`/\\:*?"<>|` → `-`), builds document definition with metadata header (title, date, duration, speakers) and a separator line
- [X] T003 Add inline markdown parser in `frontend-2/app/lib/pdf-export.ts`: line-by-line loop handling `#`/`##`/`###` headings (mapped to styled pdfmake Text nodes), `- ` bullet lists (pdfmake `ul` arrays), empty lines (spacer nodes), and plain paragraphs
- [X] T004 Add `applyInlineFormatting(text)` helper in `frontend-2/app/lib/pdf-export.ts` that regex-replaces `**bold**` → pdfmake `{text, bold: true}` and `*italic*` → `{text, italics: true}` inline nodes
- [X] T005 Add `action_items_text` section to the PDF body in `frontend-2/app/lib/pdf-export.ts`: if `meeting.action_items_text` is non-empty, append an "Action Items" heading node followed by the parsed action items content
- [X] T006 Run `npx tsc --noEmit` in `frontend-2/` and fix any TypeScript errors in `frontend-2/app/lib/pdf-export.ts`

**Checkpoint**: `pdf-export.ts` compiles cleanly; calling `exportSummaryAsPDF(mockMeeting)` in browser console produces a PDF download

---

## Phase 3: User Story 1 — Download Summary as PDF (Priority: P1) 🎯 MVP

**Goal**: "Download as PDF" menu item in the summary options dropdown triggers a browser download of a formatted PDF

**Independent Test**: Open any completed meeting → click `···` summary menu → "Download as PDF" → verify PDF file downloads with meeting title, date, and readable summary content

### Implementation for User Story 1

- [X] T007 [US1] Add "Download as PDF" button entry in the summary options menu in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` below the existing "Download as .txt" button, using a file/download SVG icon (14×14px stroke) and calling `exportSummaryAsPDF(meeting)` on click, then closing the menu
- [X] T008 [US1] Guard the "Download as PDF" menu item in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` so it only renders when `meeting.status === "completed"` AND `meeting.summary_text` is non-empty (matches existing menu guard logic)
- [X] T009 [US1] Run `npx tsc --noEmit` in `frontend-2/` and fix any TypeScript errors introduced in T007–T008

**Checkpoint**: User Story 1 complete — PDF downloads on click with correct content and filename

---

## Phase 4: User Story 2 — PDF Includes Meeting Metadata (Priority: P2)

**Goal**: The exported PDF header displays title, date, duration (if available), and speaker names (if available) as a professional metadata block above the summary body

**Independent Test**: Download a PDF from a meeting with known speakers and duration → open PDF → verify the header section shows all available metadata fields correctly

### Implementation for User Story 2

- [X] T010 [US2] Verify and update the metadata header block in `frontend-2/app/lib/pdf-export.ts` to: show formatted date (`toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })`), conditionally include "Duration: X min" row when `duration_seconds` is non-null, conditionally include "Speakers: Name1, Name2" row when `meeting.speakers` is non-empty (extract `Object.values(meeting.speakers).map(s => s.name)`)
- [X] T011 [US2] Run `npx tsc --noEmit` in `frontend-2/` and confirm no type errors after T010 changes

**Checkpoint**: User Stories 1 AND 2 complete — PDF includes correctly-formatted metadata header

---

## Phase 5: Polish & E2E Testing

**Purpose**: E2E test coverage (constitution requirement) and final validation

- [X] T012 Create E2E test file `tests/e2e/test_export_pdf.py` using Playwright/Python covering the primary happy path: navigate to a completed meeting → open summary options menu → click "Download as PDF" → verify a `.pdf` file is downloaded with a filename matching the meeting title
- [X] T013 Add edge-case assertion to `tests/e2e/test_export_pdf.py`: verify the "Download as PDF" option does NOT appear in the menu for a meeting with status other than "completed"
- [X] T014 [P] Run TypeScript type-check one final time: `npx tsc --noEmit` in `frontend-2/` and confirm zero errors
- [ ] T015 [P] Manually validate the exported PDF per quickstart.md checklist: header fields present, markdown rendered (no raw symbols), filename sanitized, opens in PDF viewer without errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001) — blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T002–T006)
- **User Story 2 (Phase 4)**: Depends on Foundational (T002–T006); builds on US1 utility but independently testable
- **Polish (Phase 5)**: Depends on US1 + US2 completion

### Within Each Phase

- T002 → T003 → T004 → T005 (sequential, same file)
- T007 → T008 → T009 (sequential, same file)
- T012 and T013 are in the same test file (sequential)
- T014 and T015 are independent (parallel)

### Parallel Opportunities

- T010 and T009 can run in parallel (different files)
- T014 and T015 can run in parallel

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Install pdfmake (T001)
2. Complete Phase 2: Build `pdf-export.ts` utility (T002–T006)
3. Complete Phase 3: Add menu item to meeting detail page (T007–T009)
4. **STOP and VALIDATE**: Test PDF download manually
5. Demo-ready MVP

### Full Delivery

1. MVP above
2. Phase 4: Verify/enhance metadata header (T010–T011)
3. Phase 5: E2E tests + final validation (T012–T015)

---

## Notes

- pdfmake must only run client-side — the `pdf-export.ts` file must be imported only from `"use client"` components
- `meeting.speakers` shape: `Record<string, { name: string; percentage: number }>` — use `Object.values()` to extract names
- Filename sanitization regex: `/[/\\:*?"<>|]/g` → replace with `"-"`
- The `···` menu is already rendered only when `meeting.status === "completed"`, but the "Download as PDF" item must additionally check for non-empty `summary_text` per FR-006
