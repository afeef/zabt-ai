# Implementation Plan: Frontend-2 Migration

**Branch**: `001-frontend-2-migration` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-frontend-2-migration/spec.md`

**Dependency**: Designed alongside `002-api-alignment`. New backend endpoints (list meetings, get meeting detail, delete meeting) from that feature are incorporated into `frontend-2`'s page structure.

## Summary

`frontend-2` is an empty directory containing only scaffolding config. This plan covers: (1) scaffolding a complete Next.js application in `frontend-2` with all features from the old `frontend` plus pages for the new backend endpoints introduced in `002-api-alignment`, (2) updating `docker-compose.yml` to serve `frontend-2` instead of `frontend`, and (3) tightening the backend CORS configuration. The old `frontend` directory is preserved untouched as an archive.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20
**Primary Dependencies**: Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react
**Storage**: No local storage; all state served by backend API
**Testing**: No test setup in existing `frontend`; not in scope for this migration
**Target Platform**: Linux (Docker container via `node:20-alpine`); modern browsers (Chrome, Firefox, Safari)
**Project Type**: Web application — Next.js frontend serving as the user-facing layer for the FastAPI backend
**Performance Goals**: Initial page load < 3 seconds; API call results reflected in UI within 2 seconds
**Constraints**: All API calls made client-side (no server-side auth for MVP); connects to backend via `NEXT_PUBLIC_API_URL` env var; Docker dev mode only for MVP
**Scale/Scope**: Single-user / small-team; 3 primary pages; ~10 components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> Project constitution is unpopulated (template only). Proceeding with general best practices:
> - Match the existing `frontend` technology stack exactly — no new frameworks
> - Keep npm as the package manager for consistency
> - No unused dependencies

**Gate result**: PASS

**Post-design re-check**: PASS — design mirrors the existing `frontend` stack. No new frameworks or tools introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-frontend-2-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output ✓
├── data-model.md        # Phase 1 output ✓
├── quickstart.md        # Phase 1 output ✓
├── contracts/           # Phase 1 output ✓
│   └── frontend-api.md  # API calls made by frontend-2
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend-2/                        # NEW: complete Next.js application
├── Dockerfile                     # Same as frontend/Dockerfile
├── package.json                   # Same deps as frontend
├── tsconfig.json                  # Same as frontend
├── next.config.ts                 # Same as frontend
├── postcss.config.mjs             # Tailwind PostCSS config
├── eslint.config.mjs              # ESLint config
├── public/                        # Static assets (empty)
└── app/
    ├── favicon.ico
    ├── globals.css                 # Tailwind base styles
    ├── layout.tsx                  # Root layout with app metadata
    ├── page.tsx                    # Home: audio upload + style upload
    ├── meetings/
    │   ├── page.tsx                # NEW: real meetings list
    │   └── [id]/
    │       └── page.tsx            # NEW: meeting detail with AI output
    ├── lib/
    │   └── api.ts                  # All backend API calls (replaces mocked getMeetings)
    └── components/
        └── ui/
            └── button.tsx          # Reusable button component

docker-compose.yml                  # CHANGED: web.context: ./frontend → ./frontend-2
backend/app/main.py                 # CHANGED: allow_origins tightened to explicit list
```

**Structure Decision**: Web application layout. `frontend-2` mirrors `frontend`'s directory structure and adds two new pages (`/meetings` and `/meetings/[id]`) that use the backend endpoints introduced in `002-api-alignment`.

## Complexity Tracking

> No constitution violations. No complexity justification required.
