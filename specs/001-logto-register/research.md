# Research: Logto-Based User Registration

**Feature**: 001-logto-register
**Date**: 2026-02-20
**Status**: Complete — all unknowns resolved

---

## Decision 1: Root Cause — Why Registration is Broken

**Decision**: The `POST /users/` endpoint (in `backend/app/api/users.py`) is not registered in
the backend router and would fail even if it were. Two reasons:

1. **Not registered**: `backend/app/api/api.py` only includes meetings, transcriptions, styles,
   and billing. `login.py` and `users.py` are not mounted anywhere.
2. **Incompatible model**: `users.py` references `security.get_password_hash` and
   `user.hashed_password` — neither exists in the current `security.py` or `User` model.
   The `User` model requires `logto_id: str` (non-nullable, unique) which the endpoint never
   sets, so it would fail with a DB constraint violation regardless.

The backend has been rewritten to be **Logto-only**: `security.py` validates Logto JWTs via
JWKS, and `deps.py` does JIT provisioning based on the Logto `sub` claim. The old
password-based code is dead code.

**Alternatives considered**: Fix `POST /users/` to work without Logto (rejected — creates a
dual-auth model with incompatible token formats; breaks the JIT provisioning contract).

---

## Decision 2: Registration Approach — Backend Management API + ROPC

**Decision**: Keep the existing custom registration form UI entirely unchanged. On form submit:
1. Frontend calls a **new backend endpoint** `POST /api/v1/auth/register` with `{email, password, full_name}`
2. Backend uses Logto's Management API (with M2M credentials) to create the user in Logto:
   `POST {LOGTO_ENDPOINT}/api/users` → Logto creates the identity, returns `logto_id`
3. Backend immediately exchanges for a user JWT using the **Resource Owner Password Credentials
   (ROPC)** grant: `POST {LOGTO_ENDPOINT}/oidc/token` with `grant_type=password` and the user's
   credentials → Logto issues a JWT
4. Backend returns the JWT to the frontend
5. Frontend stores the JWT in localStorage (unchanged pattern) and redirects to `/`

**Rationale**: This is the only approach that (a) keeps the custom form 100%, (b) auto-signs-in
the user after registration (satisfying FR-003), and (c) requires no new frontend packages.
The backend already has the `logto` Python SDK installed (`logto>=0.2.1` in pyproject.toml)
which can be used for the M2M token fetch.

**Alternatives considered**:
- `@logto/next` (hosted redirect) — abandons the custom form; user sees Logto's hosted sign-up
  page. Rejected: violates FR-008 (preserve visual design).
- Logto Experience API (browser calls Logto directly) — preserves form but requires complex
  PKCE session management and browser-to-Logto API calls. Rejected for MVP.
- Management API + redirect to /login (no ROPC) — simpler but user must sign in separately
  after registration. Rejected: violates FR-003 (auto sign-in).

**ROPC availability note**: ROPC (`grant_type=password`) requires the Logto app to be configured
as a "Machine-to-Machine" or "Native" app type in Logto Console, or for the password grant to be
explicitly enabled. This must be verified in Logto Console. If unavailable, fallback is to
redirect to `/login` after Management API user creation (two-step flow, FR-003 not satisfied).

---

## Decision 3: Social Login — Direct OIDC Authorize URL

**Decision**: Social buttons (Google/Microsoft/Apple) construct Logto's OIDC authorize URL
directly from the frontend, with a `direct_sign_in=social:{provider_id}` parameter. This
skips both the backend proxy (`/auth/oauth/{provider}/authorize` which doesn't exist) and
Logto's hosted selection screen:

```
{LOGTO_ENDPOINT}/oidc/auth
  ?client_id={NEXT_PUBLIC_LOGTO_APP_ID}
  &redirect_uri={FRONTEND_URL}/auth/callback
  &response_type=code
  &scope=openid email profile
  &state={uuid}
  &direct_sign_in=social:{connector_id}
```

After OAuth, Logto redirects to `/auth/callback?code=...`. The callback page exchanges the
code for a JWT (PKCE flow or client-secret via a backend proxy).

**Rationale**: Keeps the social button UX exactly as designed (clicking "Sign up with Google"
goes directly to Google). No backend proxy needed since the OIDC authorize endpoint is on Logto
(not the FastAPI backend). The existing `/auth/callback/[provider]` page handles the redirect;
it just needs to be updated to do code exchange instead of reading `?token=`.

**Connector IDs**: The `connector_id` value for each provider must match what is configured in
Logto Console (e.g., `google-universal`, `azure-ad`, `apple-universal`). Documented in quickstart.

**Alternatives considered**: `@logto/next` SDK `directSignIn` — requires installing and
configuring the SDK's server-side route handlers; overkill when direct OIDC URL works.

---

## Decision 4: Backend Changes Required

**New endpoint** (for email/password registration):
```
POST /api/v1/auth/register
  Body: { email: str, password: str, full_name: str | None }
  1. Fetch M2M token: POST {LOGTO_ENDPOINT}/oidc/token (client_credentials)
  2. Create user: POST {LOGTO_ENDPOINT}/api/users
  3. Issue JWT: POST {LOGTO_ENDPOINT}/oidc/token (password grant)
  4. Return: { access_token: str, token_type: "bearer" }
```

**New env vars** (backend):
- `LOGTO_M2M_APP_ID` — Logto M2M application Client ID (for Management API access)
- `LOGTO_M2M_APP_SECRET` — Logto M2M application Client Secret

**Dead code removal**:
- `backend/app/api/login.py` — not registered; references non-existent `user.hashed_password`
- `backend/app/api/users.py` — not registered; references non-existent fields; bypasses Logto

**Unchanged**:
- `security.py` `verify_token()` — already correct for all Logto JWTs (email/password + social)
- `deps.py` `get_current_user()` JIT provisioning — already correct

---

## Decision 5: Token Flow — Unchanged (localStorage)

**Decision**: Keep the existing localStorage-based token pattern in `api.ts`. The new
`POST /api/v1/auth/register` endpoint returns `{ access_token, token_type: "bearer" }` in
the same format as the existing login flow. The frontend stores the token with `setToken()`
and all subsequent API calls include `Authorization: Bearer <token>` via the existing axios
interceptor.

**No changes** to `api.ts`'s token storage or the axios interceptor. The only change to
`api.ts` is updating the `register()` function to call `/auth/register` and return a token
(instead of calling `/users/` which returns a User object).

**Rationale**: Consistency with the existing pattern. The JWT issued via ROPC is a standard
Logto JWT that `verify_token()` already validates correctly.

---

## Decision 6: Environment Variables

**New variables needed**:

| Variable | Where | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_LOGTO_ENDPOINT` | frontend `.env.local` | `http://localhost:3001` — already in docker-compose, add to .env.local |
| `NEXT_PUBLIC_LOGTO_APP_ID` | frontend `.env.local` | Logto app ID — already in docker-compose, add to .env.local |
| `LOGTO_M2M_APP_ID` | backend env / docker-compose | Logto M2M app Client ID for Management API |
| `LOGTO_M2M_APP_SECRET` | backend env / docker-compose | Logto M2M app Client Secret for Management API |

The existing `LOGTO_APP_ID` / `LOGTO_APP_SECRET` in the backend docker-compose may already be
an M2M app — confirm in Logto Console. If so, `LOGTO_M2M_APP_ID` and `LOGTO_M2M_APP_SECRET`
can reuse those values.

---

## Decision 7: Logto Console Configuration (Operations)

**Decision**: Before the feature works, a Logto administrator must configure:

1. Open Logto Admin Console at `http://localhost:3002`
2. Verify or create a **Machine-to-Machine** app for the backend (note Client ID + Secret)
3. Confirm that the M2M app has `Management API` access scoped in Logto Console
4. Enable **Email/Password** sign-in in Sign-in Experience
5. Enable **Resource Owner Password Credentials** grant (if not already — needed for ROPC)
6. Configure social connectors: **Google**, **Microsoft**, **Apple** (note connector IDs)
7. Verify or create a regular app (SPA or Traditional Web) for the frontend social callback
   — set redirect URI to `http://localhost:3000/auth/callback`

These are documented in detail in `quickstart.md`.

---

## Summary of Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Why broken | `POST /users/` not registered; no logto_id set; dead code |
| 2 | Registration approach | Backend Management API creates user in Logto; ROPC issues JWT; custom form preserved |
| 3 | Social login | Direct OIDC authorize URL with `direct_sign_in=social:{connector_id}` param |
| 4 | Backend changes | New `POST /auth/register` endpoint; remove dead login.py + users.py |
| 5 | Token flow | Unchanged — localStorage + axios interceptor (register returns same JWT format) |
| 6 | Env vars | 2 new backend env vars (M2M credentials); 2 frontend env vars (Logto endpoint + app ID) |
| 7 | Logto Console | M2M app for backend, ROPC enabled, social connectors configured |
