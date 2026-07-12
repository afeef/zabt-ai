# Implementation Plan: Meeting Upload Progress

**Branch**: `001-meeting-upload` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-meeting-upload/spec.md`

## Summary

Implement a modal dialog for uploading meeting audio/video files with real-time progress feedback. The frontend will hook into Axios' `onUploadProgress` to drive a progress bar, format file sizes, and handle active/cancelled upload states, matching the provided reference design.

## Technical Context

**Language/Version**: TypeScript 5 / React (Next.js 16 App Router) & Python 3 (FastAPI)
**Primary Dependencies**: Axios (for upload progress), shadcn/ui (for the Dialog/modal components), Tailwind CSS v4
**Storage**: Server local filesystem or object storage (handled by existing backend endpoint)
**Testing**: Playwright/Python (E2E in `tests/e2e/test_meeting_upload.py`)
**Target Platform**: Web Application
**Project Type**: Next.js App Router frontend consuming a FastAPI backend
**Performance Goals**: UI must remain highly responsive during large file uploads (up to 2GB).
**Constraints**: Must match existing design system (no shadows, stone/indigo palette). Must gracefully handle network cancellation.
**Scale/Scope**: Single modal component + state management for uploads.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Modal will use shadcn/ui `Dialog` component styled with `bg-white`, `border-stone-200`, `rounded-lg`, and no shadows. Accent is `indigo-600`. |
| API Contract — contracts/ populated | yes | pass | `contracts/api.md` will document the multipart/form-data payload for `POST /api/v1/meetings/upload`. |
| Auth/Security — no hardcoded secrets | yes | pass | Relies on existing Supabase token injection via Axios interceptor. |
| Env Config — vars in quickstart.md | yes | pass | No new env vars required. |
| Scope Boundary — within spec | yes | pass | Kept strictly to the upload flow and progress bar as defined. |
| E2E Testing — Playwright/Python in tests/e2e/ | yes | pass | Planned task to write `test_meeting_upload.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-meeting-upload/
├── plan.md              # This file
├── research.md          # Architecture decisions 
├── data-model.md        # State definitions
├── quickstart.md        # Feature setup docs
├── contracts/
│   └── api.md           # Upload API contract
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
frontend-2/
├── app/
│   ├── components/
│   │   ├── upload-modal.tsx      # NEW: The modal UI and state logic
│   │   └── right-panel.tsx       # MODIFIED: Wire up the upload button
│   └── (dashboard)/
│       └── page.tsx              # MODIFIED: Host the UploadModal state
└── tests/
    └── e2e/
        └── test_meeting_upload.py # NEW: Playwright E2E test
```

**Structure Decision**: The feature is purely a frontend component addition. We will create a robust client-side `UploadModal` component that encapsulates the file picker, progress state, and cancellation logic. It will be rendered at the `app/(dashboard)/page.tsx` level (since the right panel and feed are children of the dashboard layout/page) to ensure it stays mounted while navigating within the dashboard area.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None) | N/A | N/A |
