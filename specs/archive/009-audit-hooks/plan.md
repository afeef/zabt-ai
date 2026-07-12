# Implementation Plan: BaseService Audit Hooks

**Branch**: `009-audit-hooks` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-audit-hooks/spec.md`

## Summary

Enhance the core `BaseService` with generic pre-action (`on_before_action`) and post-action (`on_after_action`) hooks. This provides a unified architectural pattern for audit logging across all database entities without requiring changes to every individual service method.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: SQLModel, FastAPI  
**Storage**: PostgreSQL (via SQLModel)  
**Testing**: pytest (unit/integration)
**Target Platform**: Linux server (Docker)
**Project Type**: Backend service layer  
**Performance Goals**: < 1ms overhead per hook invocation (empty)  
**Constraints**: Must maintain bounded generics (TypeVar T bound to SQLModel)  
**Scale/Scope**: Impacts all services inheriting from BaseService

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | no | n/a | |
| API Contract — contracts/ populated | no | n/a | |
| Auth/Security — no hardcoded secrets | yes | pass | Audit logging enhances security; no secrets involved. |
| Env Config — vars in quickstart.md | no | n/a | |
| Scope Boundary — within spec | yes | pass | implementation stays within generic hook framework. |
| E2E Testing — Playwright/Python in tests/e2e/ | no | n/a | No user-facing flows to test via browser. |

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
backend/app/
├── services/
│   ├── base.py          # TARGET: Add generic hooks here
│   ├── meeting.py       # VERIFY: Inheritance compliance
│   └── styles.py        # VERIFY: Inheritance compliance
```

**Structure Decision**: Standard FastAPI/SQLModel backend structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
