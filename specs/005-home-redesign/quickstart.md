# Quickstart: Home Page Redesign (005-home-redesign)

**Branch**: `005-home-redesign`  
**Date**: 2026-02-22

---

## No New Environment Variables

This feature introduces **no new environment variables**. All required configuration is already present:

| Variable | Purpose | Already in `.env`? |
|----------|---------|-------------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | ✅ Yes |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | ✅ Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | ✅ Yes |
| `NEXT_PUBLIC_FRONTEND_URL` | OAuth redirect base URL | ✅ Yes |

---

## Development Setup

```bash
# Start the frontend dev server
cd frontend-2
npm install   # if not already done
npm run dev   # starts on http://localhost:3000
```

---

## Testing the Feature

```bash
# Run E2E tests (requires the dev server to be running)
cd tests/e2e
pip install playwright pytest-playwright
playwright install chromium
pytest test_home_layout.py test_home_feed.py -v
```

---

## Key Files Changed

| File | Change |
|------|--------|
| `frontend-2/app/(dashboard)/layout.tsx` | NEW — authenticated shell layout with AppShell |
| `frontend-2/app/(dashboard)/page.tsx` | NEW — home dashboard (moved from root) |
| `frontend-2/app/(dashboard)/meetings/page.tsx` | MOVED — from root meetings/ into dashboard group |
| `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` | MOVED — from root meetings/[id]/ |
| `frontend-2/app/components/app-shell.tsx` | NEW — three-column layout wrapper |
| `frontend-2/app/components/sidebar.tsx` | NEW — left nav sidebar |
| `frontend-2/app/components/right-panel.tsx` | NEW — right contextual panel |
| `frontend-2/app/components/ai-query-bar.tsx` | NEW — AI input bar |
| `frontend-2/app/components/meeting-feed.tsx` | NEW — date-grouped meeting activity feed |
| `.interface-design/system.md` | UPDATE — document Sidebar and RightPanel patterns |
| `tests/e2e/test_home_layout.py` | NEW — E2E: three-column layout renders correctly |
| `tests/e2e/test_home_feed.py` | NEW — E2E: meeting feed happy path and empty state |
