# Implementation Plan: Kong API Gateway

**Branch**: `001-kong-api-gateway` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-kong-api-gateway/spec.md`

## Summary

Add Kong API Gateway (DB-less mode) to the Docker Compose stack as the single public entry point for all external traffic. Route `/api/*` to the FastAPI backend and `/storage/*` to MinIO (with `preserve_host: true` for S3 signature compatibility). Update `MINIO_PUBLIC_ENDPOINT` to the public gateway hostname so presigned URLs resolve through Kong. Remove direct host port bindings from `api` and `minio` services. Update the Cloudflare tunnel to point at Kong's port.

## Technical Context

**Language/Version**: YAML (Docker Compose + Kong declarative config); Python 3.11 env var change only — no code changes required
**Primary Dependencies**: Kong Gateway 3.6 (Docker image `kong:3.6`), existing Docker Compose stack
**Storage**: MinIO (S3-compatible) — unchanged; access pattern changes (routed through Kong)
**Testing**: Manual validation + E2E curl scenarios (see quickstart.md); Playwright E2E in `tests/e2e/`
**Target Platform**: Linux single-host Docker Compose deployment
**Project Type**: Infrastructure / deployment configuration
**Performance Goals**: Gateway adds ≤20 ms additional latency (SC-006); Kong typically adds <5 ms for in-process routing
**Constraints**: No backend code changes; no Cloudflare tunnel reconfiguration after initial setup; MinIO must remain internal
**Scale/Scope**: Single host, single Kong instance, two upstreams (api, minio), one rate-limiting plugin

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First Development | ✓ PASS | Full speckit workflow followed |
| II. Design System Compliance | N/A | No UI changes |
| III. API Contract Clarity | ✓ PASS | contracts/infra-gateway.md documents routing table before implementation |
| IV. No Hardcoded Secrets | ✓ PASS | Gateway hostname in env var (`MINIO_PUBLIC_ENDPOINT`); no secrets in kong.yml |
| V. User-Scoped Data | N/A | Gateway is pass-through; auth remains in backend |
| VI. End-to-End Testing Standard | ✓ PASS | E2E validation scenarios defined in quickstart.md |
| VII. Repository Pattern | N/A | No data access changes |
| VIII. CLI Development with Typer | N/A | No CLI component |
| IX. Provider Abstraction | ✓ PASS | Storage service already abstracts `MINIO_PUBLIC_ENDPOINT`; no Protocol changes needed |
| X. Cost Awareness | ✓ PASS | Kong DB-less is free/open-source; no license cost |
| XI. Migration Safety | ✓ PASS | Port binding removal is reversible; `MINIO_PUBLIC_ENDPOINT` change is a single env var |

**Post-design re-check**: All gates pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-kong-api-gateway/
├── plan.md              # This file
├── research.md          # Phase 0 output — Kong DB-less, MinIO presigned URL proxying
├── contracts/
│   └── infra-gateway.md # Routing table, port assignments, env var contracts
├── quickstart.md        # Validation scenarios, config snippets, reload procedure
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
kong/                          # NEW — Kong declarative config
└── kong.yml                   # DB-less gateway routing config

docker-compose.yml             # MODIFIED — add kong service, remove api/minio port bindings
config.yml                     # MODIFIED — Cloudflare tunnel: localhost:8000 → localhost:8100
```

**No backend or frontend source files are modified.** The only changes are:
1. New file: `kong/kong.yml`
2. Modified: `docker-compose.yml` (new service + env var + port binding changes)
3. Modified: `config.yml` (Cloudflare tunnel target port)

**Structure Decision**: Single-project infrastructure change. No new language projects; all changes are YAML configuration files within the existing Docker Compose stack.
