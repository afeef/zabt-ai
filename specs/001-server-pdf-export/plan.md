# Implementation Plan: Server-Side PDF Export

**Branch**: `001-server-pdf-export` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-server-pdf-export/spec.md`

## Summary

Replace fragile client-side pdfmake PDF generation with robust server-side WeasyPrint-based generation. The backend gets a new FastAPI endpoint that converts meeting data to HTML (using mistune for markdown) and renders it to PDF via WeasyPrint with Pango/HarfBuzz for native multilingual support. Frontend buttons are rewired to call the API endpoint. Client-side pdfmake code, dependencies, and font files are removed.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend-2)
**Primary Dependencies**: FastAPI, WeasyPrint (v68+), mistune (v3+), existing SQLModel/Celery stack; Next.js 16, React 19, Axios, lucide-react
**Storage**: PostgreSQL (via SQLModel) — read-only access to existing meeting data. No new tables.
**Testing**: Playwright/Python E2E tests under `tests/e2e/`
**Target Platform**: Linux server (Docker, python:3.11-slim base) + Vercel (frontend)
**Project Type**: Web application (FastAPI backend + Next.js frontend)
**Performance Goals**: Summary PDF in <5s, Transcript PDF in <10s for meetings up to 2 hours
**Constraints**: Docker image size increase ~50-60 MB for WeasyPrint system libs + Noto fonts
**Scale/Scope**: Single-user PDF generation per request, no concurrent PDF worker needed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | PASS | Existing button styles unchanged; no new UI patterns |
| API Contract | Yes | PASS | `contracts/api-pdf-export.md` documents the endpoint |
| Auth/Security | Yes | PASS | JWT auth + ownership check enforced on endpoint |
| Env Config | No | N/A | No new environment variables |
| Scope Boundary | Yes | PASS | Implementation matches spec scope exactly |
| E2E Testing | Yes | PASS | E2E test planned for PDF download flow |
| Repository Pattern | Yes | PASS | Uses `meeting_service` for data access |
| CLI/Typer | No | N/A | No CLI component |
| Provider Abstraction | No | N/A | WeasyPrint is an internal utility, not an external API provider |
| Cost Awareness | No | N/A | No external paid APIs called |
| Migration Safety | No | N/A | Not replacing a provider — replacing client-side code with server-side |
| DB Migration | No | N/A | No schema changes |

## Project Structure

### Documentation (this feature)

```text
specs/001-server-pdf-export/
├── spec.md
├── plan.md              # This file
├── research.md          # Technology decisions
├── quickstart.md        # Setup and testing guide
├── contracts/
│   ├── api-pdf-export.md    # API endpoint contract
│   └── ui-pdf-buttons.md    # Frontend button behavior contract
└── checklists/
    └── requirements.md      # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── meetings.py           # Add export/pdf endpoint
│   ├── services/
│   │   └── pdf_export.py         # NEW: PDF generation service
│   └── templates/
│       └── pdf/
│           ├── summary.html      # NEW: Summary PDF HTML template
│           └── transcript.html   # NEW: Transcript PDF HTML template
├── Dockerfile                    # Add WeasyPrint system deps + fonts
└── pyproject.toml                # Add weasyprint, mistune

frontend-2/
├── app/
│   ├── (dashboard)/meetings/[id]/
│   │   └── page.tsx              # Rewire Download PDF buttons
│   ├── lib/
│   │   ├── api.ts                # Add exportPdf() API function
│   │   └── pdf-export.ts         # REMOVE entirely
│   └── public/fonts/             # REMOVE Noto font files
└── package.json                  # Remove pdfmake, @types/pdfmake

tests/
└── e2e/
    └── test_pdf_export.py        # NEW: E2E test for PDF download
```

**Structure Decision**: Web application pattern — backend adds a new service + endpoint + HTML templates; frontend rewires existing buttons and removes client-side PDF code.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
