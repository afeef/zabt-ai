# Quickstart: Social Login & SSO

**Feature**: 003-social-sso-login
**Date**: 2026-02-19

---

## What's changing

| File | Change |
|------|--------|
| `app/lib/api.ts` | Add `socialLoginUrl()`, `ssoLookup()`, `loginWithRememberMe()` |
| `app/login/page.tsx` | Replace — new layout: social buttons, separator, SSO on-submit, enhanced form |
| `app/auth/callback/[provider]/page.tsx` | New — OAuth2 callback handler |
| `app/forgot-password/page.tsx` | New — stub placeholder page |

---

## Environment variables

Add to `frontend-2/.env.local`:

```env
# Already exists — confirm it matches your backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Required for OAuth redirect_uri construction
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

---

## Running locally

```bash
cd frontend-2
npm run dev
```

Visit `http://localhost:3000/login`

---

## Testing each auth path

### Social login — happy path

1. Click "Sign in with Google"
2. Browser navigates to `{API_URL}/auth/oauth/google/authorize?redirect_uri=...&state=...`
3. Backend must be running with Google OAuth credentials configured
4. On success → lands on `/auth/callback/google?token={jwt}` → token stored → redirect to `/`

**Without backend OAuth configured — test callback directly:**
```
http://localhost:3000/auth/callback/google?token=<any-jwt-from-normal-login>
```

### Social login — email conflict

Visit:
```
http://localhost:3000/auth/callback/google?error=email_conflict
```
Verify the conflict error message and switch-to-password link appear.

### SSO — happy path

1. Enter a work email whose domain is SSO-configured in the backend
2. Click Sign In
3. Frontend calls `POST /auth/sso/lookup` → `sso_enabled: true` → redirect to `redirect_url`

**Without SSO configured:** Enter any email → lookup returns `sso_enabled: false` → falls
through to email/password auth. No visible change to the user.

### SSO — lookup failure fallthrough

Simulate by temporarily pointing `NEXT_PUBLIC_API_URL` to an unreachable host, then clicking
Sign In. The frontend should fall through to the email/password submit without blocking.

### Email/password with Remember Me

1. Enter valid email + password
2. Check "Remember me"
3. Click Sign In
4. Backend receives `remember_me=true` and issues a long-lived token (backend-controlled)

### Show/Hide password

Click the eye icon — password revealed. Click again — re-masked.

### Forgot Password stub

Click "Forgot password?" — navigates to `/forgot-password`. Placeholder message shown.
No backend call made.

---

## Backend endpoints needed (see `contracts/auth.md`)

| Endpoint | Status |
|----------|--------|
| `GET /auth/oauth/{provider}/authorize` | New — backend must implement |
| `GET /auth/oauth/{provider}/callback` | New — backend must implement (with auto-register + conflict detection) |
| `POST /auth/sso/lookup` | New — backend must implement |
| `POST /login/access-token` | Existing — extend with `remember_me` param |

The frontend gracefully handles missing backend endpoints: social buttons redirect and return
an error (surfaced via callback), SSO lookup failures fall through to email/password.

---

## New URL routes after implementation

| Route | Purpose |
|-------|---------|
| `/login` | Replaced login page with full design |
| `/auth/callback/[provider]` | New OAuth callback handler |
| `/forgot-password` | New stub placeholder |
