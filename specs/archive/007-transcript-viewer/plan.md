# Implementation Plan: Transcript Viewer

**Branch**: `007-transcript-viewer` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-transcript-viewer/spec.md`

## Summary

Build a complex, high-performance transcription viewer and sticky media player. The feature relies heavily on frontend state management (using refs/Zustand) to sync word-highlighting at 60fps with native media playback, alongside a 30-minute free-tier paywall overlay constraint. 

## Technical Context

**Language/Version**: TypeScript 5, Python 3.11  
**Primary Dependencies**: Next.js 16 (App Router), React 19, Tailwind CSS v4, `react-virtuoso` (virtualized lists)  
**Storage**: N/A (read-only frontend consumption of existing JSON payload/media URL)  
**Testing**: Playwright/Python (E2E testing REQUIRED for user-facing player logic)
**Target Platform**: Desktop Web, Chrome/Safari  
**Project Type**: Web application (Frontend Next.js, Backend FastAPI)  
**Performance Goals**: 60fps scroll and highlight sync; parse large JSON (>50k words) without UI blocking.
**Constraints**: Avoid global React state wrapping the list to prevent `requestAnimationFrame` re-renders of the DOM tree.  
**Scale/Scope**: Up to 4-hour meeting JSON payloads.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Using system.md Tailwind values; no external player libraries. |
| API Contract — contracts/ populated | yes | pass | Defining the JSON payload contract from the FastAPI worker. |
| Auth/Security — no hardcoded secrets | yes | pass | Media playback URLs will use Supabase signed URLs. |
| Env Config — vars in quickstart.md | no | n-a | No new env vars required. |
| Scope Boundary — within spec | yes | pass | Delivering exactly the 3 User Stories in spec.md. |
| E2E Testing — Playwright/Python in tests/e2e/ | yes | pass | Testing word-highlighting sync and modal bounds via Python. |

## Project Structure

### Documentation (this feature)

```text
specs/007-transcript-viewer/
├── plan.md              
├── research.md          
├── data-model.md        
├── quickstart.md        
├── contracts/           
└── tasks.md             
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/           # Define the TranscriptSegment schema
│   └── api/              # Refine the get_meeting JSON payload

frontend-2/
├── app/
│   ├── components/
│   │   ├── transcript-viewer.tsx    # The virtualized list component
│   │   ├── sticky-media-player.tsx  # The synchronized bottom wrapper
│   │   └── paywall-modal.tsx        # The Absolute positioned blur overlay
└── tests/
    └── e2e/
        └── test_transcript_viewer.py # Playwright suite for sync logic
```

**Structure Decision**: Standard Web Application structure. Frontend components segregated by state responsibility to maintain 60FPS sync paths between the sticky player and the virtualized transcript rows.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None      | N/A | N/A |
