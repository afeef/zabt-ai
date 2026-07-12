# Quickstart: Logout Button

**Feature**: 015-logout-button | **Date**: 2026-03-01

## Prerequisites

- Node.js 20+
- npm
- Running Supabase project (for auth session)

## Environment Variables

No new environment variables required. The feature uses existing Supabase config:

| Variable | Purpose | Already exists? |
|----------|---------|-----------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | YES |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | YES |

## Development

```bash
cd frontend-2 && npm run dev
```

## Testing

### Manual

1. Log in to the application
2. Click on the profile section in the sidebar (user name + avatar area)
3. Verify the dropdown menu appears with a "Logout" option
4. Click "Logout"
5. Verify the confirmation prompt appears
6. Click "Confirm" — verify redirect to `/login`
7. Try accessing `/` directly — verify redirect back to `/login`

### E2E (automated)

```bash
cd tests/e2e && python -m pytest test_logout.py -v
```

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend-2/app/components/sidebar.tsx` | MODIFY | Make profile section clickable, trigger dropdown |
| `frontend-2/app/components/profile-menu.tsx` | NEW | Dropdown menu with Logout + confirmation |
| `.interface-design/system.md` | MODIFY | Document ProfileMenu pattern |
| `tests/e2e/test_logout.py` | NEW | E2E test for logout flow |
