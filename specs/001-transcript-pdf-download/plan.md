# Implementation Plan: Download Transcript as PDF

**Branch**: `001-transcript-pdf-download` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-transcript-pdf-download/spec.md`

## Summary

Add a "Download PDF" button to the Transcript tab on the meeting detail page. Clicking it generates a styled PDF in the browser using pdfmake (already installed) containing the meeting metadata header and the full transcript with speaker labels and timestamps. Reuses the existing `pdf-export.ts` utility patterns (pdfmake initialization, filename sanitization, metadata header, styles). No backend changes needed.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20 + Next.js 16, React 19
**Primary Dependencies**: pdfmake (already installed), existing `pdf-export.ts` utility
**Storage**: N/A — no data model or storage changes
**Testing**: Playwright/Python E2E tests
**Target Platform**: Browser (client-side PDF generation)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: PDF generation in under 3 seconds for transcripts up to 2 hours
**Constraints**: Client-side only — no server round-trips for PDF generation
**Scale/Scope**: Single page change (meeting detail), one new export function

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | PASS | Download button follows existing UI patterns; PDF uses established stone/indigo styles from `pdf-export.ts` |
| API Contract | No | N/A | No backend API changes |
| Auth/Security | No | N/A | No auth changes; uses existing authenticated meeting data |
| Env Config | No | N/A | No new environment variables |
| Scope Boundary | Yes | PASS | Frontend-only; single new export function + button integration |
| E2E Testing | Yes | PASS | E2E test planned in `tests/e2e/test_transcript_pdf.py` |
| Repository Pattern | No | N/A | No data access changes |
| CLI/Typer | No | N/A | No CLI |
| Provider Abstraction | No | N/A | No external API integrations |
| Cost Awareness | No | N/A | No paid API calls |
| Migration Safety | No | N/A | No provider migration |
| DB Migration | No | N/A | No database schema changes |

## Project Structure

### Documentation (this feature)

```text
specs/001-transcript-pdf-download/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ui-transcript-pdf.md  # UI contract for the download button
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend-2/
├── app/
│   ├── lib/
│   │   └── pdf-export.ts           # Add exportTranscriptAsPDF() function
│   └── (dashboard)/
│       └── meetings/
│           └── [id]/
│               └── page.tsx        # Add Download PDF button to Transcript tab
└── package.json                    # No changes — pdfmake already installed

tests/
└── e2e/
    └── test_transcript_pdf.py      # E2E test for transcript PDF download
```

**Structure Decision**: Frontend-only change. New function added to existing `pdf-export.ts` utility. Button integrated into existing meeting detail page.

## Complexity Tracking

> No constitution violations — table intentionally empty.
