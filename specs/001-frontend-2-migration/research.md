# Research: Frontend-2 Migration

**Branch**: `001-frontend-2-migration` | **Date**: 2026-02-19
**Status**: Complete — all unknowns resolved

---

## Decision 1: Technology Stack for frontend-2

**Decision**: Mirror the existing `frontend` stack exactly — Next.js 16, TypeScript 5, Tailwind CSS 4, Axios, lucide-react, npm.

**Rationale**: The user's goal is to switch frontend directories while keeping the same backend. Using an identical stack minimizes risk, avoids introducing new tooling decisions, and makes the migration verifiable by direct comparison to the old `frontend`. No new UI framework, styling approach, or build tool is warranted for this migration.

**Alternatives considered**:
- New framework (e.g., Vite + React, SvelteKit) — would require rewriting all components and reconsidering all API patterns. Out of scope for a directory migration.
- Different package manager (pnpm, bun) — introduces inconsistency with existing `frontend` which uses npm. No benefit for a project of this size.

---

## Decision 2: Scope of New Pages in frontend-2

**Decision**: Add two pages beyond the old `frontend`'s single home page: `/meetings` (real meetings list) and `/meetings/[id]` (meeting detail with AI output). These replace the mocked data in the old frontend and use the new backend endpoints from `002-api-alignment`.

**Rationale**: The old `frontend` had a mocked meetings list on the home page. Since `002-api-alignment` introduces `GET /meetings/` and `GET /meetings/{id}`, `frontend-2` should take full advantage of these — otherwise the new frontend is no more functional than the old one. Keeping the mock would defeat the purpose of the migration.

**Alternatives considered**:
- Strict 1:1 copy of `frontend` — possible but wasteful; would leave the new backend endpoints unused until a third feature is created.
- Full redesign with additional pages (search, filtering, user profile) — out of scope for this migration; can be added later.

---

## Decision 3: CORS Configuration Update

**Decision**: Replace the backend's current wildcard `allow_origins=["*"]` with an explicit list: `["http://localhost:3000"]` for development, with the option to extend via environment variable for production deployments.

**Rationale**: The spec explicitly requires tightening CORS as a backend change. The wildcard is a security concern. Explicitly listing `http://localhost:3000` is the minimum necessary for development to work and is consistent with the `NEXT_PUBLIC_API_URL` pointing to `localhost:8000`.

**Note**: In `docker-compose.yml`, the frontend reaches the backend via `http://localhost:8000` (the browser's perspective), not the internal Docker network hostname. So `http://localhost:3000` is the correct origin to allow.

**Alternatives considered**:
- Keep wildcard for simplicity — rejected because the spec explicitly lists this as a required backend change.
- Configurable via env var (`ALLOWED_ORIGINS`) — good practice but deferred to a future phase; hardcoding `localhost:3000` is sufficient for the MVP.

---

## Decision 4: Old `frontend` Directory Handling

**Decision**: Leave `frontend/` completely untouched. Only remove its reference from `docker-compose.yml` (`web` service context).

**Rationale**: The spec explicitly says the old directory should remain as an archive. No files are moved, renamed, or deleted. The only change that touches `frontend/` is removing the `docker-compose.yml` reference to it.

---

## Decision 5: Auth in frontend-2

**Decision**: Include login and registration pages in `frontend-2` so users can authenticate before uploading. The `api.ts` client will store the JWT token in `localStorage` and attach it as a Bearer token on all API requests.

**Rationale**: `002-api-alignment` enables authentication on the upload endpoint. If `frontend-2` doesn't include a login page, users will get 401 errors on all upload attempts. Authentication is a prerequisite for the core upload flow.

**Alternatives considered**:
- No login page (hardcode a token for development) — acceptable for local testing but leaves the app unusable without manual token management. Rejected.
- Session cookies — would require backend changes (CSRF, cookie handling). JWT Bearer is already implemented in the backend.

---

## Summary of All Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Stack | Mirror existing `frontend`: Next.js 16, TypeScript, Tailwind 4, npm |
| 2 | New pages | Add `/meetings` list + `/meetings/[id]` detail in addition to home page |
| 3 | CORS | Explicit `http://localhost:3000` (replace wildcard) |
| 4 | Old `frontend` | Keep directory untouched; only remove from docker-compose |
| 5 | Auth | Add login/register pages; store JWT in localStorage |
