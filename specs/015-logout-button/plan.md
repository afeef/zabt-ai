# Implementation Plan: Logout Button

**Branch**: `015-logout-button` | **Date**: 2026-03-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-logout-button/spec.md`

## Summary

Add a logout button to the application sidebar. The user's existing profile section in the sidebar becomes clickable, opening a dropdown/popover menu (inspired by the Otter.ai reference screenshot) that includes a "Logout" option. Clicking Logout shows a confirmation dialog; confirming calls `supabase.auth.signOut()`, clears the session, and redirects to `/login`. The feature is frontend-only — no backend changes required. The `clearToken()` helper in `api.ts` already wraps `supabase.auth.signOut()`.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20 + Next.js 16, React 19
**Primary Dependencies**: Tailwind CSS 4, clsx, @supabase/supabase-js, @supabase/ssr, lucide-react
**Storage**: N/A — no data model changes; Supabase manages session cookies
**Testing**: Playwright (Python) for E2E tests
**Target Platform**: Web (desktop + mobile)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Logout completes (signOut + redirect) in under 2 seconds
**Constraints**: Must comply with design system (no shadows, indigo-600 accent, rounded-lg, borders only)
**Scale/Scope**: 1 component modified (sidebar.tsx), 1 new component (profile dropdown menu), E2E test

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate                   | Applies? | Status | Notes |
|------------------------|----------|--------|-------|
| Design System          | YES      | PASS   | Profile dropdown menu will use system.md tokens: `bg-white`, `border border-stone-200`, `rounded-lg`, no shadows, `indigo-600` accent. New "ProfileMenu" pattern will be documented in system.md. |
| API Contract           | NO       | N/A    | No new backend endpoints. Logout uses Supabase client-side `signOut()`. |
| Auth/Security          | YES      | PASS   | Logout calls `supabase.auth.signOut()` which clears cookies/tokens. No hardcoded credentials. Dashboard layout's `onAuthStateChange` listener handles redirect automatically. |
| Env Config             | NO       | N/A    | No new environment variables. |
| Scope Boundary         | YES      | PASS   | Limited to: sidebar profile dropdown + confirmation dialog + E2E test. |
| E2E Testing            | YES      | PASS   | E2E test planned at `tests/e2e/test_logout.py` using Playwright/Python. |
| Repository Pattern     | NO       | N/A    | No data access changes. |
| CLI/Typer              | NO       | N/A    | No CLI involvement. |
| Provider Abstraction   | NO       | N/A    | No external API integration. |
| Cost Awareness         | NO       | N/A    | No paid API calls. |
| Migration Safety       | NO       | N/A    | No provider migration. |

## Project Structure

### Documentation (this feature)

```text
specs/015-logout-button/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no data model changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend-2/
├── app/
│   ├── components/
│   │   ├── sidebar.tsx              # MODIFY — make profile section clickable, add dropdown trigger
│   │   └── profile-menu.tsx         # NEW — dropdown menu component with logout + future items
│   ├── lib/
│   │   ├── api.ts                   # EXISTING — clearToken() already wraps supabase.auth.signOut()
│   │   └── supabase/
│   │       └── client.ts            # EXISTING — Supabase browser client
│   └── (dashboard)/
│       └── layout.tsx               # EXISTING — onAuthStateChange already redirects on session loss

tests/
└── e2e/
    └── test_logout.py               # NEW — Playwright E2E test for logout flow

.interface-design/
└── system.md                        # MODIFY — document ProfileMenu pattern
```

**Structure Decision**: Frontend-only change within the existing `frontend-2/` web application structure. Single new component (`profile-menu.tsx`) plus modifications to `sidebar.tsx` and `system.md`.

## Complexity Tracking

> No constitution violations. No entries needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
