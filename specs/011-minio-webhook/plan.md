# Implementation Plan: MinIO Webhook Trigger & API Refactoring

**Branch**: `011-minio-webhook` | **Date**: 2026-02-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-minio-webhook/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Configure MinIO to send `s3:ObjectCreated:Put` bucket notifications to a new FastAPI webhook endpoint. The webhook parses the S3 event payload, resolves the associated meeting record by `file_path`, and enqueues the Celery `process_meeting` task — decoupling transcription triggering from the API layer. Additionally, the duplicated meeting-creation logic in `create_meeting` and `upload_meeting` is consolidated into a single service method, and the deprecated `upload_meeting` (multipart) endpoint is removed.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript / Node.js 20 (frontend-2)
**Primary Dependencies**: FastAPI, SQLModel, Celery (Redis broker), boto3, pydantic-settings
**Storage**: PostgreSQL (via SQLModel), MinIO (S3-compatible object storage)
**Testing**: pytest (unit/contract), Playwright/Python (E2E — not applicable: no user-facing flow changes)
**Target Platform**: Linux server (Docker Compose)
**Project Type**: web (backend + frontend)
**Performance Goals**: Webhook must trigger Celery task within 5 seconds of upload completion (SC-001)
**Constraints**: MinIO and backend are on the same Docker network; webhook delivery is internal
**Scale/Scope**: Single MinIO bucket (`zabt-media`), single webhook endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | no | n-a | No UI changes; frontend only reorders existing API calls |
| API Contract — contracts/ populated | yes | pass | New webhook endpoint + refactored POST /meetings/ documented in contracts/ |
| Auth/Security — no hardcoded secrets | yes | pass | Webhook secret via `MINIO_WEBHOOK_SECRET` env var; no hardcoded values |
| Env Config — vars in quickstart.md | yes | pass | New env vars documented in quickstart.md |
| Scope Boundary — within spec | yes | pass | Changes limited to webhook endpoint, meeting service consolidation, and frontend call reordering |
| E2E Testing — Playwright/Python in tests/e2e/ | no | n-a | No user-facing flow changes; backend-only webhook + refactor. Contract tests sufficient. |
| Repository Pattern — services/ follow base | yes | pass | All new DB operations go through MeetingService (extends BaseService) |

## Project Structure

### Documentation (this feature)

```text
specs/011-minio-webhook/
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
│   │   ├── api.py                          # Register new webhook router
│   │   ├── deps.py                         # Existing auth deps (unchanged)
│   │   └── v1/endpoints/
│   │       ├── meetings.py                 # Refactored: remove upload_meeting, remove Celery trigger from create_meeting
│   │       └── webhooks.py                 # NEW: MinIO S3 event webhook endpoint
│   ├── core/
│   │   └── config.py                       # Add MINIO_WEBHOOK_SECRET
│   ├── services/
│   │   ├── meeting.py                      # Add initiate_processing() consolidated method
│   │   └── storage.py                      # Unchanged
│   └── worker.py                           # Unchanged
├── tests/
│   ├── contract/
│   │   ├── test_meetings.py                # Update for refactored endpoint
│   │   └── test_webhooks.py                # NEW: webhook contract tests
│   └── integration/
│       └── test_uploads.py                 # Update for new flow
└── pyproject.toml                          # No new dependencies

frontend-2/
└── app/
    └── lib/
        └── api.ts                          # Reorder: create meeting before upload
```

**Structure Decision**: Web application (backend + frontend). Changes are scoped to the existing `backend/app/` and `frontend-2/app/` directories. One new file (`webhooks.py`) in the endpoints directory; all other changes are modifications to existing files.

## Complexity Tracking

| ID | Principle | Deviation | Justification |
|----|-----------|-----------|---------------|
| CT-001 | Security Requirements — "FastAPI backend MUST validate incoming requests by verifying the Supabase JWT" | Webhook endpoint uses shared Bearer token (`MINIO_WEBHOOK_SECRET`) instead of Supabase JWT | MinIO is a system-to-system caller that cannot produce Supabase JWTs. The webhook is an internal Docker-network endpoint, not a user-facing API. The shared secret is stored in environment variables (constitution-compliant) and validated on every POST. The unauthenticated HEAD is a known MinIO limitation (issue #14507) restricted to a no-op health check. |
