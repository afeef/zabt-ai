# Research: Home Page Redesign

**Feature**: 005-home-redesign  
**Date**: 2026-02-22

---

## Decision: Layout Pattern — Persistent Three-Column Shell via Next.js Nested Layout

**Decision**: Use Next.js App Router's `layout.tsx` nesting to wrap all authenticated routes in a single `AppShell` component. The shell renders the left sidebar and right panel as persistent UI; the `children` slot fills the main content area per-route.

**Rationale**: This is idiomatic Next.js App Router architecture and requires zero additional routing libraries. The sidebar and right panel do not remount between navigations because they live in the parent layout — exactly matching the reference design's behaviour.

**Alternatives considered**:
- Context + Portal-based shell rendered inside each page — rejected: causes remounting on every navigation, breaks active-link highlighting.
- A separate `_shell` directory with a catch-all route — rejected: unnecessarily complex for this scale.

---

## Decision: Authentication Guard — Supabase Session Check in Layout

**Decision**: In the authenticated layout (a new `app/(dashboard)/layout.tsx` route group), read the Supabase session server-side using `createServerClient`. Redirect to `/login` if no session is present.

**Rationale**: The existing `getToken()` helper reads the Supabase session. Replicating this pattern at the layout level (server component redirect) is aligned with how auth works today in the codebase and avoids client-side flashing of authenticated content.

**Alternatives considered**:
- Client-side `useEffect` redirect in each page — rejected: causes flash of unauthenticated content.
- Middleware-based redirect — viable but not currently used in the project; keeping consistency with the existing approach.

---

## Decision: No New Backend API Endpoints Needed

**Decision**: The home page redesign is a pure frontend layout change. All data required (meetings list, user identity) is available via existing API calls: `getMeetings()` and Supabase `getUser()`.

**Rationale**: The spec's FR-005 (meeting activity feed) maps directly to the existing `GET /meetings/` endpoint. No new backend work is required for the initial delivery.

---

## Decision: Design System Extensions — Sidebar and Right Panel Patterns

**Decision**: The sidebar and right panel introduce two new component patterns. Both must be documented in `.interface-design/system.md` after implementation (constitution Principle II requires this for any new UI pattern).

Key design system decisions for new patterns:
- Sidebar background: `bg-white` with `border-r border-stone-200` (consistent with nav)
- Active nav link: `bg-indigo-50 text-indigo-700` accent pill (uses indigo-600 accent family)
- Right panel: `bg-white` with `border-l border-stone-200`
- No shadows on any panel — borders only (constitution compliant)
- Section labels in sidebar: `text-xs font-medium uppercase tracking-wide text-stone-400` (existing overline pattern)

---

## Decision: Route Group for Authenticated Shell

**Decision**: Create an `(dashboard)` route group in `frontend-2/app/` that wraps all post-login pages. Auth-exempt pages (login, register, forgot-password, auth callback) remain at the root.

**Rationale**: Next.js route groups (`(name)`) are folder-based scoping with no URL impact. This correctly scopes the shell layout without changing any existing URLs.

---

## Decision: AI Query Bar — Submit Behaviour

**Decision**: Submitting the AI query bar routes to `/meetings?q=<query>` for now. When a dedicated `/ai-chat` route is built, the target updates to that route. The query bar component accepts a configurable `onSubmit` prop so it can be wired to any target without component changes.

---

## Decision: E2E Test Scope (Constitution Requirement)

**Decision**: Two E2E tests will be written in Playwright/Python under `tests/e2e/`:
1. `test_home_layout.py` — verifies the authenticated three-column layout renders (P1 story)
2. `test_home_feed.py` — verifies the meeting feed shows meetings or an empty state (P3 story)

These are required by constitution Principle VI for any user-facing feature.
