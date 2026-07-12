# Contract: Authentication — Registration & Social Login

**Feature**: 001-logto-register
**Date**: 2026-02-20

---

## New Backend Endpoint: POST /api/v1/auth/register

Registers a new user through Logto's Management API and returns a JWT for immediate sign-in.

**Route**: `POST /api/v1/auth/register`
**Auth required**: None (public endpoint)

**Request body**:
```json
{
  "email": "user@example.com",
  "password": "mysecretpassword",
  "full_name": "Jane Smith"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email format |
| `password` | string | Yes | Minimum 8 characters |
| `full_name` | string | No | Null/omitted → user has no display name |

**Success response** — `200 OK`:
```json
{
  "access_token": "<logto-issued-jwt>",
  "token_type": "bearer"
}
```

The `access_token` is a Logto-issued JWT valid for the backend API resource
(`http://localhost:8000`). It is identical in format to the JWT issued after social login,
and is already validated by `backend/app/core/security.py:verify_token()`.

**Error responses**:

| HTTP | Body detail | Condition |
|------|-------------|-----------|
| `400` | `"Email already registered"` | Logto's Management API returns a duplicate email error |
| `503` | `"Identity service unavailable"` | Logto is unreachable or returns a non-200 response |
| `422` | Validation error | Missing required fields or invalid email format |

**Internal flow** (backend implementation):
1. Fetch M2M access token: `POST {LOGTO_ENDPOINT}/oidc/token` with `grant_type=client_credentials`, `client_id=LOGTO_M2M_APP_ID`, `client_secret=LOGTO_M2M_APP_SECRET`, `scope=all`, `resource=https://default.logto.app/api`
2. Create user: `POST {LOGTO_ENDPOINT}/api/users` with `{primaryEmail: email, password: password, name: full_name}`
3. Exchange for user JWT: `POST {LOGTO_ENDPOINT}/oidc/token` with `grant_type=password`, `client_id=LOGTO_APP_ID`, `username=email`, `password=password`, `scope=openid email profile`, `resource=http://localhost:8000`
4. Return `{access_token, token_type: "bearer"}` from step 3

---

## Updated Frontend Helper: socialLoginUrl()

The existing `socialLoginUrl()` function in `frontend-2/app/lib/api.ts` is updated to
construct Logto's OIDC authorize URL directly (instead of a backend proxy URL that doesn't
exist).

**Old** (broken — `/api/v1/auth/oauth/{provider}/authorize` endpoint does not exist):
```typescript
`${API_URL}/auth/oauth/${provider}/authorize?redirect_uri=${redirectUri}&state=${state}`
```

**New** (direct Logto OIDC authorize URL with `direct_sign_in` hint):
```typescript
const LOGTO_ENDPOINT = process.env.NEXT_PUBLIC_LOGTO_ENDPOINT || "http://localhost:3001";
const LOGTO_APP_ID   = process.env.NEXT_PUBLIC_LOGTO_APP_ID   || "";

// connector_id maps: google → "google-universal", microsoft → "azure-ad", apple → "apple-universal"
// (exact IDs depend on Logto Console configuration)
`${LOGTO_ENDPOINT}/oidc/auth
  ?client_id=${LOGTO_APP_ID}
  &redirect_uri=${redirectUri}
  &response_type=code
  &scope=openid%20email%20profile
  &state=${state}
  &direct_sign_in=social%3A${connectorId}`
```

The callback at `/auth/callback/[provider]` receives `?code=...&state=...` and exchanges
the code for a token via a new backend endpoint or a PKCE exchange.

---

## Updated Frontend: api.ts register() function

**Old**:
```typescript
export const register = async (email, password, fullName): Promise<User> => {
  const res = await apiClient.post<User>("/users/", { email, password, full_name: fullName });
  return res.data;
};
```

**New**:
```typescript
export const register = async (email: string, password: string, fullName: string): Promise<void> => {
  const res = await apiClient.post<AuthToken>("/auth/register", { email, password, full_name: fullName });
  setToken(res.data.access_token);
};
```

After `register()` resolves, the token is stored and the caller redirects to `/` (not `/login`
as previously).

---

## Dead Code Removed (not new contracts)

| Endpoint | File | Reason |
|----------|------|--------|
| `POST /login/access-token` | `backend/app/api/login.py` | Not registered; uses non-existent `user.hashed_password`; superseded by Logto auth |
| `POST /users/` | `backend/app/api/users.py` | Not registered; cannot set `logto_id`; superseded by `POST /auth/register` |

---

## Backend API (existing — unchanged)

All existing protected endpoints continue to accept Logto-issued JWTs via
`Authorization: Bearer <token>`. JIT provisioning in `deps.py` creates the local User record
on the first authenticated API call. No changes to these endpoints.
