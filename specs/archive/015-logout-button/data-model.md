# Data Model: Logout Button

**Feature**: 015-logout-button | **Date**: 2026-03-01

## Summary

No data model changes required. This feature is entirely frontend UI. Session management is handled by Supabase's client-side SDK (`@supabase/ssr` manages cookies automatically).

## Existing Entities (read-only usage)

### Supabase Auth Session

The logout feature interacts with the existing Supabase auth session but does not modify any schema.

- **Session**: Managed by `@supabase/ssr` via cookies. `signOut()` clears the session cookie.
- **User metadata**: Read by the sidebar to display `full_name` and `email`. No writes.

No database migrations, no new tables, no schema changes.
