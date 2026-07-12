# API Contracts: Registration Extensions for Social Sign-Up

**Feature**: 001-social-register
**Date**: 2026-02-20
**Base URL**: `http://localhost:8000/api/v1`

---

## Modified Endpoints

### 1. Create User (existing — extended)

```
POST /users/
Content-Type: application/json
```

**Request body (extended):**
```json
{
  "email": "user@example.com",
  "password": "mysecretpass",
  "full_name": "Jane Smith"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| email | string | yes | User's email address; must be unique |
| password | string | yes | Minimum 8 characters |
| full_name | string | no | Optional at API boundary; required on frontend form |

**Response 201 — success:**
```json
{
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "tier": "free",
  "is_active": true,
  "minutes_used_this_month": 0
}
```

**Response 400 — email already exists:**
```json
{
  "detail": "The user with this email already exists in the system"
}
```

**Frontend behaviour:**

| Outcome | Frontend action |
|---------|----------------|
| 201 Created | `router.push("/login")` |
| 400 duplicate email | Show inline error "This email is already registered. Try signing in instead." |
| Network error / 5xx | Show inline error "Something went wrong. Please try again." |

---

## Unchanged / Reused Endpoints (from 003-social-sso-login)

### 2. Initiate Social OAuth Flow — unchanged

```
GET /auth/oauth/{provider}/authorize
```

Used identically from the registration page. See `specs/003-social-sso-login/contracts/auth.md`
for full specification.

**Frontend usage** (browser navigation, not Axios):
```
window.location.href = `${API_URL}/auth/oauth/${provider}/authorize?redirect_uri=...&state=...`
```

---

### 3. OAuth Callback — unchanged

The backend's `GET /auth/oauth/{provider}/callback` already handles:
- New email → auto-creates Meetily account → redirects to `{FRONTEND_URL}/auth/callback/{provider}?token={jwt}`
- Existing email/password → redirects to `{FRONTEND_URL}/auth/callback/{provider}?error=email_conflict`

No changes needed. Full spec in `specs/003-social-sso-login/contracts/auth.md`.

---

## Frontend-Only Routes

### Registration Page

```
GET /register
```

Next.js route at `app/register/page.tsx`.

**On social button click:**
1. `window.location.href = socialLoginUrl(provider, crypto.randomUUID())`

**On email/password form submit:**
1. Call `register(email, password, fullName)` → `POST /users/`
2. On 201 → `router.push("/login")`
3. On 400 → show inline error
4. On other error → show generic inline error

### OAuth Callback — no changes

```
GET /auth/callback/{provider}?token={jwt}
GET /auth/callback/{provider}?error={code}
```

Already implemented in feature `003-social-sso-login`. Handles token storage, conflict
error display, and generic error display. Not modified by this feature.

---

## No New Endpoints Required

All backend endpoints needed for this feature are either:
- Already implemented (`GET /auth/oauth/{provider}/authorize`, callback, `POST /users/`)
- Already accept the new `full_name` field (`POST /users/` — confirmed in backend)

No new backend work is required for this feature.
