# Implementation Plan: Social Login & Enhanced Registration Page

**Branch**: `001-social-register` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-social-register/spec.md`

## Summary

Replace the minimal Meetily registration page (`/register`) with a full-design layout
matching the login page: Meetily wordmark, "Create your account" heading, three social
sign-up buttons (Google, Microsoft, Apple) that reuse the existing OAuth2 callback flow,
an "or sign up with email" separator, a Full Name field (new), email, and password (with
show/hide toggle). Update `register()` in `api.ts` to forward `full_name` to the backend,
which already accepts it. All OAuth infrastructure from `003-social-sso-login` is reused
without modification.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20
**Primary Dependencies**: Next.js 16.1.6, React 19, Tailwind CSS 4, Axios, lucide-react, clsx
**Storage**: localStorage — `access_token` JWT (existing pattern; unchanged)
**Testing**: ESLint only (no test runner currently in project)
**Target Platform**: Web — Next.js App Router (browser)
**Project Type**: Web application — `frontend-2/` frontend, separate FastAPI backend
**Performance Goals**: Registration page interactive in <2s; social redirect instant on click
**Constraints**: No new npm packages; design system compliance required; OAuth2 client secrets stay server-side; no new backend endpoints needed
**Scale/Scope**: 2 modified files (`api.ts`, `register/page.tsx`); 0 new files; 0 new npm dependencies

## Constitution Check

*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Register card uses `max-w-md` + `rounded-xl` (documented login-card exception in system.md); all other tokens match system |
| API Contract — contracts/ populated | yes | pass | `contracts/registration.md` documents the extended `POST /users/` contract; no new endpoints |
| Auth/Security — no hardcoded secrets | yes | pass | Backend-redirect OAuth2; client secrets server-side; callback token consumed immediately |
| Env Config — vars in quickstart.md | yes | pass | No new env vars; existing `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_FRONTEND_URL` confirmed in quickstart.md |
| Scope Boundary — within spec | yes | pass | No SSO lookup, no auto-login, no new routes, no new pages |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-register/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── registration.md  # Phase 1 output — REST API contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code

```text
frontend-2/
└── app/
    ├── lib/
    │   └── api.ts           # Modified: register() gains fullName parameter
    └── register/
        └── page.tsx         # Replaced: new full design with social buttons + enhanced form
```

**Structure Decision**: Frontend-only changes in `frontend-2/app/`. No new files. No
backend changes — `POST /users/` already accepts `full_name` (confirmed in
`backend/app/api/users.py`).
