# Implementation Plan: Home Page Redesign

**Branch**: `005-home-redesign` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/005-home-redesign/spec.md`

## Summary

Redesign the authenticated home/dashboard page for Zabt (`frontend-2`) to adopt a modern three-column layout: a persistent left sidebar (logo, nav, profile), a wide central content area (personalized greeting, AI query bar, meeting activity feed), and a contextual right panel (quick-action CTAs). The layout shell is scoped to a Next.js `(dashboard)` route group so all post-login pages inherit it automatically. No backend changes are required — the feature consumes existing `getMeetings()` and Supabase `getUser()` calls.

## Technical Context

**Language/Version**: TypeScript 5 / Next.js 15 (App Router)  
**Primary Dependencies**: Tailwind CSS v4, `clsx`, Supabase JS client, Axios  
**Storage**: N/A (read-only; no new data stored)  
**Testing**: Playwright/Python (E2E, required — `tests/e2e/`); no unit/integration tests needed for layout-only changes  
**Target Platform**: Browser (Web — desktop primary, responsive mobile secondary)  
**Project Type**: Web application (`frontend-2/`)  
**Performance Goals**: Shell renders complete layout in under 500 ms on first load; navigation between routes < 200 ms (no shell remount)  
**Constraints**: Design system compliance (stone/indigo palette, no shadows, `rounded-lg`); no new backend endpoints; no new npm dependencies  
**Scale/Scope**: Single Next.js frontend (frontend-2); ~6 new components, 2 route-group files, 2 E2E tests

## Constitution Check

| Gate | Applicable? | Status | Notes |
|------|------------|--------|-------|
| Design System — UI compliance | Yes | ✅ Pass | All new components use stone/indigo palette, `border-stone-200`, `rounded-lg`, no shadows. `system.md` will be updated with Sidebar and RightPanel patterns post-implementation. |
| API Contract — contracts/ populated | Yes | ✅ Pass | `contracts/api.md` documents both consumed endpoints (`GET /meetings/` and Supabase `getUser()`). No new endpoints added. |
| Auth/Security — no hardcoded secrets | Yes | ✅ Pass | Auth delegated to Supabase; session checked via `supabase.auth.getSession()`. No secrets in source code. Authenticated shell redirects to `/login` if no session found. |
| Env Config — vars in quickstart.md | Yes | ✅ Pass | No new env vars introduced. Existing vars documented in `quickstart.md`. |
| Scope Boundary — within spec | Yes | ✅ Pass | Implementation covers FR-001 through FR-010 only. No undocumented additions. |
| E2E Testing — Playwright/Python in tests/e2e/ | Yes | ✅ Pass | Two E2E tests planned: `test_home_layout.py` (three-column render) and `test_home_feed.py` (feed happy path + empty state). Both in `tests/e2e/`. |

## Project Structure

### Documentation (this feature)

```text
specs/005-home-redesign/
├── plan.md              ← this file
├── research.md          ← Phase 0 complete
├── data-model.md        ← Phase 1 complete
├── quickstart.md        ← Phase 1 complete
├── contracts/
│   └── api.md           ← Phase 1 complete
└── tasks.md             ← Phase 2 (/speckit.tasks — not yet created)
```

### Source Code Changes

```text
frontend-2/
├── app/
│   ├── (dashboard)/                        ← NEW route group (authenticated shell)
│   │   ├── layout.tsx                      ← NEW: AppShell wrapper + auth guard
│   │   ├── page.tsx                        ← NEW: home dashboard (greeting + feed)
│   │   ├── meetings/
│   │   │   ├── page.tsx                    ← MOVED from app/meetings/page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx                ← MOVED from app/meetings/[id]/page.tsx
│   ├── components/
│   │   ├── app-shell.tsx                   ← NEW: three-column layout wrapper
│   │   ├── sidebar.tsx                     ← NEW: left nav sidebar
│   │   ├── right-panel.tsx                 ← NEW: right contextual panel
│   │   ├── ai-query-bar.tsx                ← NEW: AI input component
│   │   └── meeting-feed.tsx                ← NEW: date-grouped feed + cards
│   ├── login/
│   │   └── page.tsx                        ← UNCHANGED (stays at root, not in dashboard group)
│   ├── register/
│   │   └── page.tsx                        ← UNCHANGED
│   ├── forgot-password/
│   │   └── page.tsx                        ← UNCHANGED
│   └── auth/
│       └── ...                             ← UNCHANGED
├── .interface-design/
│   └── system.md                           ← UPDATE: add Sidebar + RightPanel patterns

tests/
└── e2e/
    ├── test_home_layout.py                 ← NEW: shell render E2E test
    └── test_home_feed.py                   ← NEW: meeting feed E2E test
```

**Structure Decision**: Next.js App Router route group `(dashboard)` scopes the authenticated layout. Route groups do not affect URLs — `/meetings` remains accessible at the same path. Auth-exempt pages (login, register, auth) remain at the app root and will not render the shell.
