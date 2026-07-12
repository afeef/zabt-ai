<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
List of modified principles:
- I. Privacy-First (moved to Template Structure)
- II. OpenAI Interoperability (moved to Template Structure)
- III. Few-Shot Style Learning (moved to Template Structure)
- IV. Enterprise Security & RBAC (moved to Template Structure)
- V. Test-Driven Development (TDD) (moved to Template Structure)
Added sections:
- Technical Standards & Stack
- Development & Design System
Removed sections:
- Technical Standards (renamed to Section 2)
Templates requiring updates:
- .specify/templates/plan-template.md (✅ updated/aligned)
- .specify/templates/spec-template.md (✅ updated/aligned)
- .specify/templates/tasks-template.md (✅ updated/aligned)
Follow-up TODOs:
- None
-->
# Zabt Constitution

## Core Principles

### I. Privacy-First
Privacy is the foundational tenet of Zabt. All data processing, storage, and AI inference MUST occur within user-controlled infrastructure or via privacy-preserving local servers. No user data SHOULD ever be transmitted to proprietary third-party services without explicit, informed consent.

### II. OpenAI Interoperability
The system MUST maintain strict compatibility with the OpenAI API specification. This ensures that users can transition between backend providers (LM Studio, Ollama, vLLM, or proprietary APIs) without requiring changes to the core application logic.

### III. Few-Shot Style Learning
The AI's generation style MUST be fully customizable via few-shot learning. The system MUST allow users to upload reference documents to calibrate the tone, format, and complexity of meeting summaries and action items.

### IV. Enterprise Security & RBAC
Security is not an afterthought. Role-Based Access Control (RBAC), usage quotas, and industry-standard encryption (AES-256 for data at rest) MUST be integrated into every feature. Compliance with enterprise security standards is a prerequisite for all production deployments.

### V. Test-Driven Development (TDD)
We adhere to a strict TDD lifecycle: Define requirements in `spec.md` → Write failing tests → Implementation → Refactor. This ensures that the complex orchestration of AI models remains reliable and maintainable.

## Technical Standards & Stack

The Zabt stack is designed for performance, modularity, and containerization:
- **Backend**: Python 3.11+ using FastAPI for the web layer and SQLModel for database interactions.
- **Frontend**: TypeScript-based Next.js 15+ for the UI layer, utilizing Tailwind CSS and Radix UI (Shadcn) for consistency.
- **Async Tasks**: Celery with Redis for heavy-duty audio processing and AI inference orchestration.
- **Persistence**: PostgreSQL for relational data and local file storage for media.
- **Deployment**: Every component MUST be deployable via Docker and managed through Docker Compose.

## Development & Design System

To maintain high development velocity and code quality:
- **Documentation**: Every feature MUST have a corresponding specification in `.specify/memory`.
- **UI Consistency**: Use only approved components from `frontend/app/components/ui`. Ad-hoc styling SHOULD be avoided in favor of utility-first CSS via Tailwind.
- **Code Quality**: Linting (ESLint, Ruff) and type checking (TypeScript, Pyright/Mypy) MUST pass before any code is merged.
- **Testing Gates**: All PRs REQUIRE passing unit and integration tests. Critical paths involving AI inference MUST have contract tests to prevent regression.

## Governance

The Project Constitution supersedes all other documentation and practices.
- **Amendments**: Changes to this document require a formal amendment process, a version bump (Semantic Versioning), and an updated Sync Impact Report.
- **Versioning**: MAJOR bumps for principle removals; MINOR for new sections/principles; PATCH for clarifications.
- **Compliance**: AI-assisted agents MUST verify compliance with these principles during plan generation and task execution.

**Version**: 1.1.0 | **Ratified**: 2026-02-15 | **Last Amended**: 2026-02-15
