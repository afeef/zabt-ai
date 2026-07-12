# Tasks: Server-Side PDF Export

**Input**: Design documents from `/specs/001-server-pdf-export/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/api-pdf-export.md, contracts/ui-pdf-buttons.md, quickstart.md

**Tests**: E2E test included (constitution requirement for user-facing features).

**Organization**: Four user stories — US1 (Summary PDF), US2 (Transcript PDF), US3 (Multilingual), US4 (Cleanup). US1-US3 share the same backend service; US3 is inherently satisfied by WeasyPrint + Noto fonts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install dependencies and configure Docker for WeasyPrint

- [x] T001 Add `weasyprint>=68.0` and `mistune>=3.0` to backend/pyproject.toml under `[project.dependencies]` — run `cd backend && uv lock` to update lockfile
- [x] T002 Add WeasyPrint system dependencies and Noto fonts to backend/Dockerfile — in the `api` target's apt-get install line, add: `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libharfbuzz0b fonts-noto-core`
- [x] T003 Create HTML template directory at backend/app/templates/pdf/ — add empty `__init__.py` if needed for path resolution

---

## Phase 2: Foundational — PDF Generation Service

**Purpose**: Core PDF generation service that both US1 and US2 depend on

**⚠️ CRITICAL**: No user story endpoint work can begin until this phase is complete

- [x] T004 Create backend/app/services/pdf_export.py — implement `PdfExportService` with: (1) `_detect_direction(text: str) -> str` helper that returns `"rtl"` if text contains Arabic script range (U+0600–U+06FF, U+0750–U+077F, U+FB50–U+FDFF, U+FE70–U+FEFF), else `"ltr"`; (2) `_format_duration(seconds: int) -> str` helper (same logic as frontend: `X min` or `X sec`); (3) `_format_timestamp(seconds: float) -> str` helper returning `MM:SS` or `H:MM:SS`; (4) `_sanitize_filename(name: str) -> str` helper to strip invalid filename chars; (5) `_build_metadata_html(meeting) -> str` helper that generates the metadata header HTML block (title, date, duration, speakers); (6) private `_get_css() -> str` method returning the shared CSS string for all PDFs — Zabt brand styling with stone/indigo palette, A4 page margins, Noto font-family stack, RTL support via `[dir="rtl"]` selector
- [x] T005 Add `generate_summary_pdf(meeting) -> bytes` method to `PdfExportService` in backend/app/services/pdf_export.py — convert `meeting.summary_text` markdown to HTML using `mistune.html()`, append action_items_text if present (also via mistune), wrap in full HTML document with metadata header + CSS + `dir` attribute per block, call `weasyprint.HTML(string=html).write_pdf()`, return bytes
- [x] T006 Add `generate_transcript_pdf(meeting, segments, speakers) -> bytes` method to `PdfExportService` in backend/app/services/pdf_export.py — build HTML by iterating segments: for each segment render speaker name (bold, `color: #4f46e5`) + timestamp (`color: #78716c`) on one line, then spoken text as a `<p>` below with `dir` attribute set per-block based on `_detect_direction()`; wrap in full HTML document with metadata header + CSS; call `weasyprint.HTML(string=html).write_pdf()`, return bytes
- [x] T007 Create singleton instance `pdf_export_service = PdfExportService()` at bottom of backend/app/services/pdf_export.py

**Checkpoint**: PDF generation service ready — can generate summary and transcript PDFs from meeting data

---

## Phase 3: User Story 1 — Download Summary as PDF (Priority: P1) 🎯 MVP

**Goal**: Users can download a formatted summary PDF from the Summary tab

**Independent Test**: Navigate to completed meeting → Summary tab → click "Download PDF" → verify PDF downloads with metadata + formatted summary

### Implementation

- [x] T008 [US1] Add `GET /{meeting_id}/export/pdf` endpoint to backend/app/api/v1/endpoints/meetings.py — accept `type: str` query param (Literal["summary", "transcript"]); authenticate via `current_user = Depends(deps.get_current_active_user)`; fetch meeting via `meeting_service.get_meeting(meeting_id)`; verify ownership (`meeting.owner_id != current_user.id` → 403); verify status is `completed` (else 400); for `type="summary"` call `pdf_export_service.generate_summary_pdf(meeting)` and return `Response(content=pdf_bytes, media_type="application/pdf")` with `Content-Disposition: attachment; filename="{sanitized_title}-summary.pdf"` header; for `type="transcript"` validate segments exist (else 400), call `pdf_export_service.generate_transcript_pdf(meeting, meeting.segments, speakers_dict)` and return similarly; wrap PDF generation in try/except returning 500 on failure
- [x] T009 [US1] Add `exportPdf(meetingId: number, type: "summary" | "transcript"): Promise<void>` function to frontend-2/app/lib/api.ts — make authenticated GET request to `/meetings/${meetingId}/export/pdf?type=${type}` with `responseType: "blob"`; create a temporary object URL from the blob; create an anchor element, set href to the object URL, set download attribute to the filename from Content-Disposition header (parse it or use fallback `meeting-${type}.pdf`), programmatically click it, then revoke the object URL
- [x] T010 [US1] Rewire the Summary tab "Download PDF" button in frontend-2/app/(dashboard)/meetings/[id]/page.tsx — replace the `exportSummaryAsPDF(meeting)` call with `exportPdf(meeting.id, "summary")`; keep the PostHog event `summary_exported`; add error handling (try/catch with alert on failure); add loading state (disable button while request is in-flight)
- [x] T011 [US1] Run `cd backend && uv run python -c "from app.services.pdf_export import pdf_export_service; print('OK')"` to verify import works, then run `cd frontend-2 && npx tsc --noEmit` to verify TypeScript compiles

**Checkpoint**: Summary PDF download works end-to-end via server

---

## Phase 4: User Story 2 — Download Transcript as PDF (Priority: P1)

**Goal**: Users can download a formatted transcript PDF from the Transcript tab

**Independent Test**: Navigate to completed meeting → Transcript tab → click "Download PDF" → verify PDF downloads with speaker labels, timestamps, and text

### Implementation

- [x] T012 [US2] Rewire the Transcript tab "Download PDF" button in frontend-2/app/(dashboard)/meetings/[id]/page.tsx — replace the `exportTranscriptAsPDF(meeting)` call with `exportPdf(meeting.id, "transcript")`; keep the PostHog event `transcript_exported`; add error handling (try/catch with alert on failure); add loading state (disable button and show spinner while request is in-flight)
- [x] T013 [US2] Run `cd frontend-2 && npx tsc --noEmit` to verify TypeScript compiles cleanly

**Checkpoint**: Both summary and transcript PDF downloads work via server. Multilingual support (US3) is inherently provided by WeasyPrint + Noto fonts — no additional code needed.

---

## Phase 5: User Story 4 — Remove Client-Side PDF Dependencies (Priority: P2)

**Goal**: Remove pdfmake, font files, and client-side PDF code from frontend

**Independent Test**: Frontend builds without errors; both PDF buttons still work via server endpoint; pdfmake no longer in bundle

### Implementation

- [x] T014 [US4] Delete frontend-2/app/lib/pdf-export.ts entirely
- [x] T015 [P] [US4] Delete font files from frontend-2/public/fonts/ — remove NotoNaskhArabic-Regular.ttf, NotoNaskhArabic-Bold.ttf, NotoSansDevanagari-Regular.ttf, NotoSansDevanagari-Bold.ttf
- [x] T016 [US4] Remove all imports of `exportSummaryAsPDF` and `exportTranscriptAsPDF` from frontend-2/app/(dashboard)/meetings/[id]/page.tsx — these should already be replaced by `exportPdf` in T010/T012, but verify no stale imports remain
- [x] T017 [US4] Uninstall pdfmake and @types/pdfmake from frontend-2 — run `cd frontend-2 && npm uninstall pdfmake @types/pdfmake`
- [x] T018 [US4] Run `cd frontend-2 && npx tsc --noEmit` to verify no TypeScript errors after removal; run `cd frontend-2 && npm run build` to verify production build succeeds

**Checkpoint**: Client-side PDF code fully removed. Frontend bundle size reduced.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing, validation, and final checks

- [x] T019 Write E2E test in tests/e2e/test_pdf_export.py — Playwright/Python: log in, navigate to a completed meeting, verify Summary tab "Download PDF" triggers a download with `-summary.pdf` filename pattern; switch to Transcript tab, verify "Download PDF" button visible, click it, verify download triggers with `-transcript.pdf` filename pattern
- [x] T020 Verify design system compliance — audit Download PDF buttons for: no shadows, border-stone-200, rounded-lg, stone text hierarchy, consistent with existing button patterns; confirm no new UI patterns were introduced
- [x] T021 Run full TypeScript check and backend import verification — `cd frontend-2 && npx tsc --noEmit` and `cd backend && uv run python -c "from app.services.pdf_export import pdf_export_service"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (deps installed, Docker configured)
- **US1 — Summary PDF (Phase 3)**: Depends on Phase 2 (PDF service ready)
- **US2 — Transcript PDF (Phase 4)**: Depends on Phase 2 (PDF service ready) + T008 (endpoint already handles transcript type)
- **US3 — Multilingual (no phase)**: Inherently satisfied by WeasyPrint + Noto fonts. Tested as part of US1/US2.
- **US4 — Cleanup (Phase 5)**: Depends on Phase 3 + Phase 4 (both buttons rewired before removing old code)
- **Polish (Phase 6)**: Depends on Phase 5 (all changes complete)

### Within Each Phase

- T001 → T002 → T003 (sequential — deps before Docker before templates)
- T004 → T005 → T006 → T007 (sequential — helpers before methods before singleton)
- T008 → T009 → T010 → T011 (sequential — endpoint before API client before button rewire before verify)
- T012 → T013 (sequential — rewire before verify)
- T014 through T018 (mostly sequential — delete code, delete fonts, clean imports, uninstall deps, verify)

### Parallel Opportunities

- T014 and T015 can run in parallel (different files)
- US1 (Phase 3) and US2 (Phase 4) could run in parallel after Phase 2, since T008 handles both types, but T012 depends on T009 (shared `exportPdf` function)

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Install deps, configure Docker
2. Complete Phase 2: Build PDF generation service
3. Complete Phase 3: Summary PDF endpoint + frontend integration
4. **STOP and VALIDATE**: Test summary PDF download on a real meeting (including Urdu/Hindi content)
5. Deploy — users can now download summary PDFs server-side

### Incremental Delivery

1. Setup + Foundational → PDF service ready
2. User Story 1 → Summary PDF works → Deploy (MVP!)
3. User Story 2 → Transcript PDF works → Deploy
4. User Story 4 → Client-side cleanup → Deploy (smaller bundle)
5. Polish → E2E tests + audit → Confidence for production

---

## Notes

- User Story 3 (Multilingual) has no dedicated tasks — it's inherently provided by WeasyPrint's Pango/HarfBuzz stack + `fonts-noto-core` system package. Validated as part of US1/US2 testing with Urdu/Hindi content.
- The backend endpoint handles both summary and transcript types in a single route (T008), so US2 only needs frontend rewiring.
- No database changes, no Alembic migrations needed — reads existing meeting data.
- HTML templates are built as string concatenation in the service (not Jinja2 files) to keep it simple — the templates are small and don't need inheritance/partials.
- Speaker names for transcript: resolved from `meeting.segments[].speaker` against `meeting.speakers` dict (same pattern as existing frontend code).
