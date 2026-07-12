# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a three-dot contextual menu to meeting items in the feed UI, containing a "Delete" action. This action will permanently remove the meeting record from the database and its associated media file from storage, updating the UI optimistically or seamlessly without a page reload. It is disabled while a meeting is actively processing.

## Technical Context

**Language/Version**: TypeScript 5 (Next.js 16 App Router) & Python 3.11 (FastAPI)
**Primary Dependencies**: React, Tailwind CSS v4, shadcn/ui DropdownMenu (or native styling), Axios, Supabase (Auth/DB), Playwright (E2E)
**Storage**: PostgreSQL (Supabase) for records, Object/File Storage for media
**Testing**: Playwright/Python for E2E user flows
**Target Platform**: Web (Desktop & Mobile responsive)
**Project Type**: web (frontend-2 + backend)
**Performance Goals**: Delete action visually completes in <500ms
**Constraints**: Must strictly prevent orphaned files; DB record and file must both be deleted.
**Scale/Scope**: Single endpoints modifications, single UI component update.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Planning to use 3-dot icon and standard styling |
| API Contract — contracts/ populated | yes | pass | Will document DELETE /api/v1/meetings/{id} |
| Auth/Security — no hardcoded secrets | yes | pass | Delete endpoint MUST verify user ownership |
| Env Config — vars in quickstart.md | no | n-a | No new services introduced |
| Scope Boundary — within spec | yes | pass | Strictly limited to deletion mechanism |
| E2E Testing — Playwright/Python in tests/e2e/ | yes | pass | Will add test_meeting_delete.py |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── meetings.py      # Where the DELETE endpoint lives
│   └── services/            # File deletion logic
└── tests/

frontend-2/
├── app/
│   ├── components/
│   │   ├── meeting-feed.tsx # Where the 3-dot menu goes
│   │   └── ui/              # Dropdown/Menu components if added
│   └── lib/
│       └── api.ts           # Delete meeting Axios call
└── tests/
    └── e2e/                 # Playwright tests
```

**Structure Decision**: Web application with separate `frontend-2` (Next.js) and `backend` (FastAPI) directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
