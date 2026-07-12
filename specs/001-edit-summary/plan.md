# Implementation Plan: Edit Summary Markdown In-App

**Branch**: `001-edit-summary` | **Date**: 2026-03-09 | **Spec**: [spec.md](specs/001-edit-summary/spec.md)
**Input**: Feature specification from `/specs/001-edit-summary/spec.md`

## Summary

Users can edit AI-generated meeting summaries in a WYSIWYG markdown editor (Tiptap) directly on the meeting detail page. The backend gets a PATCH endpoint to persist edits and a restore endpoint to revert to the original AI summary. Two new columns on the Meeting model track the original summary and edited state.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend)
**Primary Dependencies**: FastAPI, SQLModel (backend); Next.js 16, React 19, Tailwind CSS 4, Tiptap (new — `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-link`, `tiptap-markdown`)
**Storage**: PostgreSQL (via SQLModel) — two new columns on `meeting` table
**Testing**: Playwright/Python (E2E), manual testing (frontend)
**Target Platform**: Web (desktop, ≥768px)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Editor load < 200ms; save round-trip < 1s
**Constraints**: WYSIWYG editor must output markdown (not HTML) for compatibility with existing rendering and PDF export
**Scale/Scope**: Single-user editing; no concurrent edit handling needed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | ✅ PASS | Tiptap is headless — all styling via Tailwind using stone/indigo palette, borders not shadows |
| API Contract | Yes | ✅ PASS | Contracts defined in `contracts/meetings-summary.md` before frontend work |
| Auth/Security | Yes | ✅ PASS | Existing Supabase JWT auth; owner check on PATCH/POST; no new env vars |
| Env Config | No | N/A | No new environment variables |
| Scope Boundary | Yes | ✅ PASS | Only summary editing; no transcript editing, no collaborative editing |
| E2E Testing | Yes | ✅ PASS | E2E test planned in `tests/e2e/test_edit_summary.py` |
| Repository Pattern | Yes | ✅ PASS | `MeetingService` handles all DB operations via `BaseService` |
| CLI/Typer | No | N/A | No CLI component |
| Provider Abstraction | No | N/A | No external API integration |
| Cost Awareness | No | N/A | No external paid API calls |
| Migration Safety | No | N/A | No provider migration |

## Project Structure

### Documentation (this feature)

```text
specs/001-edit-summary/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: editor selection research
├── data-model.md        # Phase 1: Meeting model extensions
├── quickstart.md        # Phase 1: setup & integration guide
├── contracts/
│   └── meetings-summary.md  # PATCH + restore endpoint contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py                          # Meeting: +original_summary_text, +summary_edited
│   ├── services/
│   │   └── meeting.py                     # +update_summary(), +restore_summary()
│   └── api/v1/endpoints/
│       └── meetings.py                    # +PATCH /{id}/summary, +POST /{id}/summary/restore

frontend-2/
├── app/
│   ├── lib/
│   │   └── api.ts                         # +updateMeetingSummary(), +restoreMeetingSummary(); Meeting type extended
│   ├── components/
│   │   └── summary-editor.tsx             # New: Tiptap WYSIWYG editor component
│   └── dashboard/meetings/[id]/
│       └── page.tsx                        # Modified: toggle between read-only and editor

tests/
└── e2e/
    └── test_edit_summary.py               # E2E: edit, save, restore flow
```

**Structure Decision**: Web application (Option 2) — changes span both `backend/` and `frontend-2/` directories. No new top-level directories needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
