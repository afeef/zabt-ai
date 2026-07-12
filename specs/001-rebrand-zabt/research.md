# Research: Zabt Rebranding & Logto Removal

**Feature**: `001-rebrand-zabt`
**Date**: 2026-02-22
**Status**: Complete — no NEEDS CLARIFICATION items

---

## Decision 1: Rename Scope

**Decision**: Rename all occurrences of "pareto", "Pareto AI", "Meetily", and any hyphenated variations (e.g., `pareto-ai`, `pareto_ai`) to the canonical "zabt" / "Zabt" in all tracked source, configuration, and documentation files.

**Rationale**: The brand transition is total — the old names are marketing/project names for the same codebase. A partial rename leaves inconsistency that confuses contributors and search tooling.

**Alternatives considered**:
- Rename only user-visible surfaces (UI copy only) — rejected because package.json names, Docker service names, and DB names would remain inconsistent with the new brand.
- Create a parallel namespace — rejected as unnecessary complexity for a rename operation.

---

## Decision 2: Database Name Change Strategy

**Decision**: Rename `POSTGRES_DB` from `pareto_ai` → `zabt` in `.env` and `docker-compose.yml`. The backend `DATABASE_URL` will be derived from the env var so no additional code changes are needed for the connection string itself.

**Rationale**: The database name is embedded in the Docker Compose environment chain. Changing the env var propagates to the backend automatically. Developers need to run `docker-compose down -v` once to destroy the old volume.

**Alternatives considered**:
- Keep `pareto_ai` as the internal DB name but rename UI only — rejected per FR-004 which requires the database name to reflect "zabt".

---

## Decision 3: Logto Artifact Sweep Strategy

**Decision**: Use project-wide grep to locate every remaining string containing "logto" (case-insensitive) in all tracked text files, then delete or update each occurrence via targeted file edits. The sweep includes: source files, markdown docs, spec files, YAML configs, SQL files, and `.env` files.

**Rationale**: The prior migration (`001-migrate-supabase`) removed the main Logto code paths. What remains are scattered string literals in comments, spec documents, and diagnostic messages.

**Alternatives considered**:
- Scripted sed replacement — feasible but riskier for partial words and markdown tables. Manual targeted edits are safer for accuracy.

---

## Decision 4: Constitution Title

**Decision**: Update the constitution file at `.specify/memory/constitution.md` to rename "Meetily Constitution" → "Zabt Constitution".

**Rationale**: The constitution is the project's foundational governance document and must carry the correct brand name to avoid confusion.

**Alternatives considered**: Leave documents as-is — rejected per FR-001 which explicitly covers documentation.

---

## Findings: files with "pareto" or "logto" references (tracked source only)

Identified via prior grep sweeps during `001-migrate-supabase` and current spec audit:

| File | Type of reference |
|------|------------------|
| `docker-compose.yml` | `POSTGRES_DB=pareto_ai`, service/volume description comments |
| `.env` | `POSTGRES_DB=pareto_ai` |
| `backend/app/core/config.py` | `POSTGRES_DB = "pareto_ai"`, `PROJECT_NAME = "Pareto AI"` |
| `backend/pyproject.toml` | `name = "backend"` (acceptable generic — keep or rename to "zabt-backend") |
| `frontend-2/package.json` | `name: "frontend-2"` (rename to "zabt-web") |
| `frontend-2/app/login/page.tsx` | UI text "Meetily" |
| `frontend-2/app/register/page.tsx` | UI text "Meetily" |
| `.specify/memory/constitution.md` | Title: "Meetily Constitution" |
| `specs/001-migrate-supabase/` | Logto described as historically removed — review for any active-present-tense language |
| `CLAUDE.md` | May contain "Pareto AI" project name reference |
| `README.md` (if exists) | May contain "Pareto AI" or "Meetily" |

No API contract changes are needed — this is a pure rename with no behavioral change.
