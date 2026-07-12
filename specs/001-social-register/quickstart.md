# Quickstart: Social Login & Enhanced Registration Page

**Feature**: 001-social-register
**Date**: 2026-02-20

---

## What's changing

| File | Change |
|------|--------|
| `app/lib/api.ts` | Update `register()` to accept `fullName` parameter |
| `app/register/page.tsx` | Replace — new layout: social buttons, separator, full name + email + password + show/hide |

**No new files.** The OAuth callback page, `SocialButton` component, `socialLoginUrl()`,
and `OAuthProvider` type are all reused from feature `003-social-sso-login`.

---

## Environment variables

No new variables. Confirm these already exist in `frontend-2/.env.local`:

```env
# Already exists — confirm it matches your backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Required for OAuth redirect_uri construction (added in 003-social-sso-login)
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

---

## Running locally

```bash
cd frontend-2
npm run dev
```

Visit `http://localhost:3000/register`

---

## Testing each path

### Social sign-up — happy path

1. Click "Sign up with Google" on `/register`
2. Browser navigates to `{API_URL}/auth/oauth/google/authorize?redirect_uri=...&state=...`
3. Backend must be running with Google OAuth credentials configured
4. On success → lands on `/auth/callback/google?token={jwt}` → token stored → redirect to `/`

**Without backend OAuth configured — test callback directly:**
```
http://localhost:3000/auth/callback/google?token=<any-jwt-from-normal-login>
```

### Social sign-up — email conflict

Visit:
```
http://localhost:3000/auth/callback/google?error=email_conflict
```
Verify the conflict error message and switch-to-sign-in link appear.

### Email/password registration — happy path

1. Visit `/register`
2. Enter Full Name, a valid email, and a password of ≥ 8 characters
3. Click "Sign up"
4. Redirected to `/login`
5. Verify the full name was stored by signing in and checking profile

### Email/password registration — duplicate email

1. Attempt to register with an email that already exists in the system
2. Verify inline error "This email is already registered. Try signing in instead." appears
3. Verify no redirect occurs and the form remains editable

### Show/hide password

Click the eye icon — password revealed. Click again — re-masked.

### Already have an account link

Click "Already have an account? Sign in" — navigates to `/login`.

---

## Backend endpoints used (no changes needed)

| Endpoint | Status |
|----------|--------|
| `GET /auth/oauth/{provider}/authorize` | Existing (from 003-social-sso-login) |
| `GET /auth/oauth/{provider}/callback` | Existing (from 003-social-sso-login) |
| `POST /users/` | Existing — already accepts `full_name` |

---

## New URL routes after implementation

| Route | Purpose |
|-------|---------|
| `/register` | Replaced registration page with full design |

*(No new routes — `/auth/callback/[provider]` already exists from 003-social-sso-login)*
