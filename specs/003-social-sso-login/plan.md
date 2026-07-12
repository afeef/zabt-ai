# Implementation Plan: Social Login & SSO for Login Page

**Branch**: `003-social-sso-login` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-social-sso-login/spec.md`

## Summary

Extend the Meetily login page to match the reference design: add Google, Microsoft, and Apple
social login buttons via backend-redirected OAuth2; add on-submit SSO domain detection that
silently checks the email domain and redirects enterprise users to their IdP (with graceful
fallthrough if the lookup fails or returns no match); auto-register first-time social login
users; block social logins conflicting with existing email/password accounts with an actionable
error; enhance the email/password form with show/hide toggle, "Remember me", and a "Forgot
password?" stub link; add `/forgot-password` placeholder route.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20
**Primary Dependencies**: Next.js 16.1.6, React 19, Tailwind CSS 4, Axios, lucide-react, clsx
**Storage**: localStorage — `access_token` JWT (existing pattern); session lifetime controlled by backend via `remember_me` flag
**Testing**: ESLint only (no test runner currently in project)
**Target Platform**: Web — Next.js App Router (browser)
**Project Type**: Web application — `frontend-2/` frontend, separate FastAPI backend
**Performance Goals**: Login page interactive in <2s; SSO lookup completes in <500ms so Sign In click feels instant
**Constraints**: No new npm packages; design system compliance required; OAuth2 client secrets MUST stay server-side; callback token consumed and URL replaced immediately
**Scale/Scope**: 3 modified/new routes; 3 new API helper functions in `api.ts`; 0 new npm dependencies

## Constitution Check

*Gates defined in `.specify/memory/constitution.md` § Development Workflow.*

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | yes | pass | Social button is a new pattern — will be added to system.md post-implementation |
| API Contract — contracts/ populated | yes | pass | `contracts/auth.md` documents all new and modified endpoints |
| Auth/Security — no hardcoded secrets | yes | pass | Backend-redirect OAuth2; client secrets server-side; callback token consumed immediately, URL replaced |
| Env Config — vars in quickstart.md | yes | pass | `NEXT_PUBLIC_FRONTEND_URL` documented in quickstart.md |
| Scope Boundary — within spec | yes | pass | Forgot-password is stub only; no reset flow; no account linking |

## Project Structure

### Documentation (this feature)

```text
specs/003-social-sso-login/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── auth.md          # Phase 1 output — REST API contracts
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code

```text
frontend-2/
└── app/
    ├── lib/
    │   └── api.ts                    # Extended: socialLoginUrl(), ssoLookup(), loginWithRememberMe()
    ├── login/
    │   └── page.tsx                  # Replaced: social buttons + on-submit SSO + enhanced form
    ├── auth/
    │   └── callback/
    │       └── [provider]/
    │           └── page.tsx          # New: OAuth2 callback — reads ?token= or ?error=
    └── forgot-password/
        └── page.tsx                  # New: stub placeholder page
```

**Structure Decision**: Web application — frontend-only changes in `frontend-2/app/`. Backend
contract is specified in `contracts/auth.md` but backend implementation is out of scope for
this plan.
