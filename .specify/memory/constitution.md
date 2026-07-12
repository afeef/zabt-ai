<!--
SYNC IMPACT REPORT
==================
Version change: 2.6.0 → 2.7.0 (MINOR — new principle added)
Modified principles: none
Added sections:
  - Principle XIV: Pydantic Settings for All Configuration — all
    environment variables and config MUST be read through a Pydantic
    Settings class; no direct os.environ usage
Removed sections: none
Templates requiring updates:
  ✅ .specify/templates/plan-template.md — no structural changes required
  ✅ .specify/templates/tasks-template.md — no structural changes required
  ✅ .specify/templates/spec-template.md — no structural changes required
Follow-up TODOs: none
-->

# Zabt Constitution

## Core Principles

### I. Spec-First Development (NON-NEGOTIABLE)

Every product change — feature, fix, or migration — MUST be captured in a feature spec before
implementation begins. The workflow is: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks`
→ `/speckit.implement`. No code MUST be written outside this workflow without explicit user
approval. Ad-hoc changes bypass traceability and break the task dependency graph.

### II. Design System Compliance

All UI changes MUST comply with the established design system at `.interface-design/system.md`.
Specifically:

- Background: `bg-stone-50`; surfaces: `bg-white`; borders: `border-stone-200`
- Depth: borders only — no `shadow`, `shadow-sm`, or `shadow-lg` classes anywhere
- Rounding: `rounded-lg` everywhere (exception: `rounded-xl` on prominent auth card;
  `rounded-full` for circular indicators; `rounded-md` for compact list items)
- Accent: `indigo-600` — no `blue-600` or any other accent color
- Spacing: 4px base grid — no half-unit spacing (no `py-0.5`, `mt-0.5`) except where explicitly
  justified in system.md
- New UI patterns MUST be documented in system.md after introduction

### III. API Contract Clarity

Any feature that adds, modifies, or removes a backend API endpoint MUST document the contract
in `specs/[###-feature]/contracts/` before frontend implementation begins. The contract MUST
specify: HTTP method, path, request body/params, success response, error responses. Frontend
and backend are independently changeable but both MUST honor the contract. No frontend code
MUST call an undocumented endpoint.

### IV. No Hardcoded Secrets or Configuration

All secrets (JWT signing keys, OAuth client secrets, API keys), URLs, and environment-specific
values MUST be stored in environment variables. No such value MUST appear in source code or be
committed to the repository. Environment variable names MUST be documented in the relevant
`quickstart.md`. This applies to both the Python backend and the TypeScript frontend.

### V. User-Scoped Data (NON-NEGOTIABLE)

Every resource (meeting, style example, social identity) MUST be associated with an
authenticated user. No endpoint MUST fall back to a hardcoded owner ID, a placeholder user, or
unauthenticated access for data-mutating operations. All list and detail endpoints MUST filter
by the authenticated user. Ownership checks MUST be enforced on update and delete operations.

### VI. End-to-End Testing Standard

All end-to-end (E2E) tests MUST be written in Python using Playwright. Specifically:

- E2E test files MUST reside under `tests/e2e/` and follow the naming convention
  `test_[feature_or_journey].py`
- Every feature with a user-facing flow MUST include at least one E2E test covering the
  primary happy path
- E2E tests MUST also cover the critical error states defined in the feature's acceptance
  scenarios (e.g., duplicate email, invalid credentials, service unavailable)
- E2E tests MUST be included in the task list (`tasks.md`) as explicit tasks — they are
  not optional for UI-touching features
- No other language or testing framework MUST be used for E2E tests; browser automation
  code outside of Playwright/Python is a constitution violation

**Rationale**: A single E2E framework and language eliminates context-switching, ensures
consistent test infrastructure, and enables direct reuse of backend Python fixtures alongside
browser automation.

### VII. Repository Pattern for Data Access (NON-NEGOTIABLE)

All data access logic in FastAPI MUST follow the Repository Pattern by inheriting from or
utilizing the `BaseService`. Direct session management (commits, refreshes, adds) within
API endpoints or specialized business logic MUST NOT be performed.

**Rationale**: Decoupling data access ensures consistent audit logging (via BaseService hooks),
centralized session management, and simplified unit testing through service-layer mocking.

### VIII. CLI Development with Typer (NON-NEGOTIABLE)

All command-line interfaces in the project MUST be built using the
[Typer](https://typer.tiangolo.com) Python package. Specifically:

- CLI entry points MUST use `typer.Typer()` as the application object
- CLI arguments and options MUST be declared via Typer's type-annotated function
  parameters (leveraging Pydantic validation under the hood)
- No other CLI framework (argparse, click directly, fire, etc.) MUST be used;
  Typer is the sole sanctioned CLI toolkit
- CLI commands MUST be registered in a dedicated module (e.g., `app/cli/`) and
  MUST NOT be embedded in service or API code

**Rationale**: Typer is built on top of Click and fully embraces Python type hints,
aligning with the project's existing use of Pydantic (data validation) and FastAPI
(type-annotated endpoints). Using Typer ensures consistent developer ergonomics,
automatic `--help` generation, shell completion support, and seamless interoperability
with the Pydantic/FastAPI ecosystem across the entire stack.

### IX. Provider Abstraction (NON-NEGOTIABLE)

All external API integrations (transcription, LLM summarization, storage) MUST be
behind abstract interfaces. Specifically:

- In Python: use `Protocol` (typing) or `ABC` (abc module) to define provider
  contracts
- In TypeScript: use `interface` or `type` to define provider contracts
- No service MUST directly import a specific provider's SDK — all access MUST go
  through the abstraction layer
- Each provider implementation MUST be a concrete class satisfying the abstract
  interface, registered via dependency injection or a factory function
- Swapping a provider (e.g., OpenAI Whisper → Google Chirp) MUST require only a
  new implementation class and a configuration change — zero modifications to
  consuming service code

**Rationale**: Provider abstraction decouples business logic from vendor lock-in,
enables seamless A/B testing of providers, simplifies unit testing via mock
implementations, and ensures migrations (e.g., Whisper → Chirp) are low-risk,
incremental operations rather than codebase-wide rewrites.

**Approved Provider Implementations**:

- **Local Transcription (WhisperProvider)**: MAY use either vanilla OpenAI
  Whisper (`whisper.load_model`) or faster-whisper via WhisperX
  (`whisperx.load_model`, CTranslate2 backend). The WhisperX/faster-whisper
  path is RECOMMENDED for production use — it provides batched inference,
  VAD-based chunking, and 4-6x performance improvement via the CTranslate2
  engine while using the same model weights and producing identical
  transcription quality.

### X. Cost Awareness

The system MUST default to the cheapest viable processing path for every external
API call. Specifically:

- Batch/asynchronous processing MUST be the default mode for transcription,
  summarization, and any other provider-mediated operation
- Real-time (synchronous) processing MUST only be activated when the user's
  subscription tier explicitly includes it
- Feature specs MUST document which processing modes are available and the
  tier-gating logic for each
- Cost-impacting design decisions MUST be called out in the plan.md Complexity
  Tracking table if they deviate from the cheapest path

**Rationale**: External API costs scale linearly with usage. Defaulting to batch
processing reduces per-unit cost significantly and ensures the platform remains
economically viable at scale. Tier-gating prevents accidental cost overruns from
ungated real-time usage.

### XI. Migration Safety

During any provider migration (e.g., Whisper → Chirp 3), backward compatibility
MUST be maintained. Specifically:

- The outgoing provider implementation MUST remain fully functional behind the
  same abstract interface (see Principle IX) until the incoming provider is
  validated in production
- A feature flag or configuration toggle MUST control which provider is active;
  rollback MUST be achievable by toggling the flag — no code changes required
- Migration validation MUST include: output quality parity checks, latency
  benchmarks, and cost comparisons documented in the feature's research.md
- The outgoing provider implementation MUST NOT be removed until the migration
  is explicitly marked complete in a constitution amendment or feature closeout

**Rationale**: Provider migrations carry risk of quality regressions, latency
changes, and unexpected cost shifts. Maintaining the old provider behind the same
interface guarantees instant rollback capability and allows gradual, data-driven
cutover rather than a risky big-bang switch.

### XII. Database Migration Discipline (NON-NEGOTIABLE)

All database schema changes MUST be managed through Alembic migrations. Specifically:

- Every schema change (new table, new column, altered constraint, index)
  MUST be captured in an Alembic migration file under `backend/alembic/versions/`
- Migration files MUST be committed to the repository alongside the code that
  depends on the schema change — no schema change MUST be deployed without a
  corresponding checked-in migration
- Direct `CREATE TABLE`, `ALTER TABLE`, or `DROP` statements executed manually
  against the database MUST NOT be used as the migration strategy; all DDL MUST
  flow through Alembic
- `SQLModel.metadata.create_all()` MUST NOT be relied upon for production schema
  management; it is acceptable only for ephemeral test databases
- Container startup MUST automatically execute `alembic upgrade head` before
  the application process starts — this ensures every deployment applies pending
  migrations without manual intervention
- Migration files MUST include both `upgrade()` and `downgrade()` functions to
  enable rollback
- Autogenerated migrations (`alembic revision --autogenerate`) MUST be reviewed
  before committing to ensure correctness

**Rationale**: Checked-in Alembic migrations provide a deterministic, version-
controlled history of every schema change. Auto-running on container startup
eliminates manual migration steps during deployment and guarantees that the
database schema always matches the code running against it.

### XIII. shadcn/ui Component Standard (NON-NEGOTIABLE)

All frontend UI components MUST be built using
[shadcn/ui](https://ui.shadcn.com) standard components. Specifically:

- Every interactive UI element (buttons, dropdowns, dialogs, inputs, badges,
  tabs, tooltips, menus) MUST use a shadcn/ui component as its foundation
- Hand-built custom equivalents of components that shadcn/ui provides MUST NOT
  be created; if shadcn/ui offers a component for the pattern, it MUST be used
- shadcn/ui components are installed via the CLI (`npx shadcn@latest add`) and
  live in `frontend-2/app/components/ui/` — they are project-owned source files
  that MAY be customized after installation
- Composite components (e.g., a toolbar combining multiple shadcn/ui primitives)
  MUST compose shadcn/ui components rather than reimplementing their behavior
- Components with no shadcn/ui equivalent (e.g., domain-specific visualizations
  like ProgressSteps, TranscriptViewer, or the Tiptap-based SummaryEditor) MAY
  remain custom but SHOULD use shadcn/ui primitives internally where applicable
- The shadcn/ui theme configuration (CSS variables in `globals.css`) MUST be the
  single source of truth for color tokens, spacing, and radius values — no
  competing theme systems

**Rationale**: shadcn/ui provides accessible, well-tested components built on
Radix UI primitives with consistent keyboard navigation, ARIA attributes, and
focus management. Using a single component library eliminates design drift
between hand-built components, reduces maintenance burden, and ensures every
interactive element meets accessibility standards by default. The copy-into-
project model gives full ownership without version-upgrade surprises.

### XIV. Pydantic Settings for All Configuration (NON-NEGOTIABLE)

All environment variables and configuration values MUST be read through a
Pydantic `BaseSettings` class. Specifically:

- Every Python service MUST define a `Settings` class inheriting from
  `pydantic_settings.BaseSettings` that declares all configuration fields
  with types and defaults
- Direct usage of `os.environ`, `os.getenv()`, or `os.environ.get()` MUST
  NOT appear anywhere in application or script code — all config access
  MUST go through the Settings instance
- Environment variable names MUST match the Settings field names exactly
  (Pydantic handles the env → field mapping)
- Third-party libraries that read env vars automatically (e.g.,
  `huggingface_hub` reads `HF_TOKEN`) MUST use the standard env var name
  as the Settings field name so both paths resolve to the same value
- TypeScript frontend configuration MUST follow the same principle using
  a centralized config module — no scattered `process.env.X` reads across
  components
- Settings classes MUST live in a dedicated config module (e.g.,
  `app/core/config.py`, `src/config.py`)

**Rationale**: Centralizing configuration through Pydantic Settings provides
type validation, default value management, and a single source of truth for
every configurable parameter. It eliminates inconsistent env var names
(e.g., `HF_AUTH_TOKEN` vs `HF_TOKEN`), prevents silent failures from
misspelled env var reads, and makes the full configuration surface
discoverable by reading one file.

## Security Requirements

- Authentication MUST be delegated to Supabase Cloud Service on the frontend; the local backend MUST NOT implement auth registration or login routes.
- The FastAPI backend is exclusively used for AI-related tasks (transcription, summarization) and MUST validate incoming requests by verifying the Supabase JWT.
- JWT tokens MUST be validated with the Supabase project secret (read from environment variables).
- OAuth2 client secrets MUST never be exposed to the browser or frontend code if used by backend; Supabase handles frontend social auth securely.
- CORS MUST explicitly list allowed origins; wildcard (`*`) is acceptable only in development and
  MUST be replaced with explicit origins before production deployment.
- Passwords MUST be hashed server-side securely (handled by Supabase); no plaintext password storage.

## Development Workflow

1. All features start with `/speckit.specify` on the active feature branch.
2. `/speckit.clarify` SHOULD be run for features with ambiguous requirements before planning.
3. `/speckit.plan` MUST be run before task generation; it produces `research.md`, `data-model.md`,
   `contracts/`, and `quickstart.md`.
4. `/speckit.tasks` generates the dependency-ordered task list.
5. `/speckit.implement` executes tasks in order.
6. UI changes MUST be followed by `/interface-design:audit` to verify design system compliance.
7. Features with user-facing flows MUST include E2E tests written in Playwright/Python under
   `tests/e2e/` — these MUST appear as tasks in `tasks.md`.
8. After each completed feature, `/speckit.analyze` MAY be run to verify cross-artifact
   consistency.
9. Features that include a CLI MUST use Typer as the CLI framework, with CLI code
   organized in a dedicated module (e.g., `app/cli/`).
10. Features that integrate with external APIs MUST define provider abstraction interfaces
    before implementing concrete provider classes. No direct SDK imports in service code.
11. Features involving external API calls MUST default to batch/async processing unless
    the spec explicitly documents real-time tier-gating.
12. Provider migrations MUST maintain backward compatibility with a feature flag for
    rollback; the outgoing provider MUST NOT be removed until migration closeout.
13. Features that modify database schema MUST include an Alembic migration file
    committed alongside the code. No raw DDL or `create_all()` for production.
14. All frontend UI components MUST use shadcn/ui standard components. No hand-built
    equivalents of components that shadcn/ui already provides.
15. All configuration and environment variables MUST be read through Pydantic Settings
    classes. No direct `os.environ` or `os.getenv()` usage in application or script code.

### Constitution Check (used in plan.md Constitution Check section)

Before Phase 0 research, verify each applicable gate:

| Gate | Applies When | Check |
|------|-------------|-------|
| Design System | Feature touches any UI | Confirm design system compliance planned; system.md will be updated if new patterns introduced |
| API Contract | Feature adds/modifies/removes endpoints | Confirm `contracts/` dir will be populated before frontend implementation |
| Auth/Security | Feature handles user data or auth flows | Confirm auth is enforced; no hardcoded credentials; env vars documented |
| Env Config | Feature introduces new environment variables | Confirm vars listed in `quickstart.md` |
| Scope Boundary | Feature implementation | Confirm implementation stays within spec scope; no undocumented additions |
| E2E Testing | Feature has any user-facing flow | Confirm E2E tests planned in Playwright/Python; test file paths listed in `tasks.md` under `tests/e2e/` |
| Repository Pattern | Feature involves data access | Confirm services used for all DB operations; no direct session use in endpoints |
| CLI/Typer | Feature includes a CLI | Confirm CLI built with Typer; no argparse/click/fire; CLI code in dedicated `app/cli/` module |
| Provider Abstraction | Feature integrates with any external API (transcription, LLM, storage) | Confirm abstract interface (Protocol/ABC or interface/type) defined before concrete implementation; no direct SDK imports in service code |
| Cost Awareness | Feature calls external paid APIs | Confirm batch/async is the default processing mode; real-time gated by subscription tier; cost implications documented in Complexity Tracking |
| Migration Safety | Feature replaces an existing provider | Confirm old provider retained behind same interface; feature flag controls active provider; rollback requires no code changes; validation criteria documented in research.md |
| DB Migration | Feature adds, modifies, or removes database schema | Confirm Alembic migration file created under `backend/alembic/versions/`; both upgrade and downgrade defined; no raw DDL or `create_all()` for production |
| shadcn/ui Components | Feature adds or modifies frontend UI components | Confirm all interactive elements use shadcn/ui components; no hand-built equivalents of components shadcn/ui provides |
| Pydantic Settings | Feature reads any environment variable or config value | Confirm all config access goes through a Pydantic `BaseSettings` class; no direct `os.environ`/`os.getenv()`; field names match env var names |

## Governance

This constitution supersedes all other development practices for the Zabt project. Any
practice that contradicts a principle here MUST be resolved in favor of the constitution or
a formal amendment MUST be filed.

**Amendments**:
- MAJOR (x.0.0): Removal or redefinition of an existing principle; requires explicit user
  approval and a migration note documenting what existing specs/code may be affected.
- MINOR (1.x.0): New principle or section added; requires user approval.
- PATCH (1.0.x): Clarification, wording fix, or non-semantic refinement; can be made without
  formal approval if it does not change the intent.

**Compliance**: All feature plans (plan.md) MUST include a completed Constitution Check section.
Any violation MUST be documented in the Complexity Tracking table with justification. Unjustified
violations are grounds to reject the plan before task generation.

**Version**: 2.7.0 | **Ratified**: 2026-02-19 | **Last Amended**: 2026-03-28
