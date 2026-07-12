# Implementation Plan: Enterprise AI Meeting Assistant

**Branch**: `001-ai-meeting-assistant` | **Date**: 2026-02-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-meeting-assistant/spec.md`

## Summary

Implement a privacy-first, web-based AI meeting assistant capable of real-time transcription (Whisper) and post-meeting analysis (OpenAI-compatible LLM). Features include file uploads, few-shot style learning, and role-based access control, built on a FastAPI + Next.js stack.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5+ (Frontend)
**Primary Dependencies**: 
- Backend: FastAPI, Pydantic (AI, Settings), SQLModel, Celery, OpenAI SDK (for compatible APIs), Whisper (local/server-side), Logto (OIDC Auth).
- Frontend: Next.js 15+, React 19, Tailwind CSS, Shadcn/UI, Lucide React.
**Storage**: PostgreSQL (Relational), Redis (Celery Broker/Cache), File System (Media storage).
**Testing**: pytest (Backend), pyright (Linting).
**Target Platform**: Docker (Linux containers).
**Project Type**: Web application.
**Performance Goals**: <2s latency for real-time transcription chunks; <5min processing for 1hr audio upload.
**Constraints**: GDPR compliance (Right to Access/Erasure), AES-256 encryption at rest.
**Scale/Scope**: Enterprise-grade, support for concurrent meetings (scaled via Celery workers).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Privacy-First**: PASSED. Transcription uses local Whisper on server; LLM calls use OpenAI-compatible API (can be local or private instance). Data stays within user capabilities.
- **OpenAI Interoperability**: PASSED. Explicitly requested for summary/notes generation.
- **Few-Shot Style Learning**: PASSED. Included in `spec.md` as User Story 3.
- **Enterprise Security & RBAC**: PASSED. Explicitly requested (FR-006).
- **TDD**: PASSED. Testing with pytest and strict linting with pyright requested.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-meeting-assistant/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── meetings.py
│   │   │   │   ├── styles.py
│   │   │   │   └── transcriptions.py
│   │   │   └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── meeting.py
│   │   ├── note.py
│   │   └── user.py
│   ├── services/
│   │   ├── transcription.py (Whisper)
│   │   ├── llm.py (Pydantic-AI)
│   │   └── storage.py
│   └── worker.py (Celery)
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── pyproject.toml

frontend/
├── app/
│   ├── dashboard/
│   │   ├── meetings/
│   │   ├── styles/
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/ (Shadcn)
│   │   ├── meeting-recorder.tsx
│   │   └── transcription-view.tsx
│   └── lib/
│       ├── api.ts
│       └── utils.ts
└── package.json
```

**Structure Decision**: Web application structure with separate backend (FastAPI) and frontend (Next.js) directories, containerized via Docker.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Celery | Heavy audio processing (Whisper) blocks main thread | Background tasks required for transcription scalability |
| SQLModel | Type safety + ORM | Raw SQL or SQLAlchemy core less integrated with Pydantic |
