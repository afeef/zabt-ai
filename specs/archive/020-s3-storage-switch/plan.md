# Implementation Plan: S3/MinIO Storage Provider Switch

**Branch**: `020-s3-storage-switch` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-s3-storage-switch/spec.md`

## Summary

Refactor the storage layer to support both MinIO (local dev) and any S3-compatible cloud provider (Cloudflare R2, AWS S3) via environment variables. The existing `S3StorageService` already uses boto3 — the main changes are: (1) add a `STORAGE_PROVIDER` env var toggle, (2) abstract the storage behind a Protocol interface, (3) add an application-level pipeline trigger for non-MinIO providers (since MinIO webhooks won't exist), and (4) make MinIO docker services conditional via profiles.

## Technical Context

**Language/Version**: Python 3.11 (backend)
**Primary Dependencies**: FastAPI, boto3, Celery (Redis broker), pydantic-settings
**Storage**: PostgreSQL (via SQLModel), MinIO/S3 (object storage)
**Testing**: Manual E2E validation (backend-only infrastructure change)
**Target Platform**: Linux server (Contabo VPS) + local Docker dev
**Project Type**: Web service (backend API)
**Performance Goals**: No degradation — presigned URL generation <100ms
**Constraints**: Zero frontend code changes; env-var-only switching
**Scale/Scope**: Single-tenant, ~10 concurrent users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | SKIP | No UI changes |
| API Contract | Yes | PASS | New `POST /api/v1/meetings/{id}/confirm-upload` endpoint needs contract; existing endpoints unchanged |
| Auth/Security | Yes | PASS | S3 credentials via env vars only; no hardcoded secrets; webhook auth preserved for MinIO mode |
| Env Config | Yes | PASS | New vars (`STORAGE_PROVIDER`, `S3_*`) documented in quickstart.md |
| Scope Boundary | Yes | PASS | Storage abstraction + pipeline trigger only; no other changes |
| E2E Testing | No | SKIP | No user-facing flow changes; backend infrastructure refactor |
| Repository Pattern | Yes | PASS | MeetingService used for all DB operations; no direct session access |
| CLI/Typer | No | SKIP | No CLI involved |
| Provider Abstraction | Yes | PASS | StorageProvider Protocol defined; MinioStorage and S3Storage are concrete implementations; factory function selects based on `STORAGE_PROVIDER` |
| Cost Awareness | No | SKIP | No paid API calls — S3/R2 is storage, not a per-call API |
| Migration Safety | Yes | PASS | MinIO implementation retained; `STORAGE_PROVIDER` env var toggles; rollback = change env var back to `minio` |

## Project Structure

### Documentation (this feature)

```text
specs/020-s3-storage-switch/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py           # Add STORAGE_PROVIDER + S3_* settings
│   ├── services/
│   │   └── storage.py          # Refactor: Protocol + MinIO/S3 implementations + factory
│   └── api/v1/endpoints/
│       ├── meetings.py         # Add confirm-upload endpoint
│       └── webhooks.py         # Unchanged (MinIO webhook stays for MinIO mode)

docker-compose.yml              # MinIO services get profiles: ["minio"] for conditional start
```

**Structure Decision**: Backend-only changes in existing files. The storage.py file is refactored to use a Protocol with two concrete implementations (MinIO + S3). No new files needed.
