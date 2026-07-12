# Data Model: Social Login & SSO

**Feature**: 003-social-sso-login
**Date**: 2026-02-19
**Clarifications incorporated**: all 5 from session 2026-02-19

---

## Entities

### User (existing — invariant extended)

No new fields required on the frontend `User` type. The key invariant clarified during
clarification: **a single email address MUST belong to exactly one authentication method**.
The system enforces this at login time (not registration time). First-time social login
silently creates the account.

```typescript
// Existing — no change to interface required
interface User {
  email: string;
  full_name: string | null;
  tier: "free" | "pro" | "enterprise";
  is_active: boolean;
  minutes_used_this_month: number;
}
```

### AuthToken (existing — unchanged)

```typescript
// Existing — no change required
interface AuthToken {
  access_token: string;
  token_type: "bearer";
}
```

### OAuthProvider (new — frontend enum)

```typescript
type OAuthProvider = "google" | "microsoft" | "apple";
```

### SSOLookupRequest (new)

```typescript
interface SSOLookupRequest {
  email: string;
}
```

### SSOLookupResponse (new)

```typescript
interface SSOLookupResponse {
  sso_enabled: boolean;
  redirect_url: string | null;       // present only when sso_enabled is true
  organisation_name: string | null;  // display name for UX ("Acme Corp")
}
```

### OAuthCallbackResult (new — frontend-only, parsed from URL query params)

```typescript
interface OAuthCallbackResult {
  token: string | null;
  error: string | null;
  provider: OAuthProvider;
}
```

---

## State Transitions

### Login Page State Machine

```
IDLE
  → [click social button]       → OAUTH_REDIRECT   (browser navigates away)
  → [click Sign In]             → SSO_CHECKING

SSO_CHECKING  (POST /auth/sso/lookup in flight)
  → [sso_enabled: true]         → SSO_REDIRECT      (browser navigates away)
  → [sso_enabled: false]        → EMAIL_AUTH
  → [lookup fails / times out]  → EMAIL_AUTH         (fallthrough — never blocks)

EMAIL_AUTH  (POST /login/access-token in flight)
  → [success]                   → AUTHENTICATED     (redirect to /)
  → [invalid credentials]       → ERROR
  → [other error]               → ERROR

OAUTH_REDIRECT  (browser at provider)
  → [callback ?token=...]       → AUTHENTICATED     (setToken, router.replace("/"))
  → [callback ?error=...]       → ERROR             (shown on /login via ?error= param or
                                                      directly on callback page)
  → [callback — email conflict] → ERROR_CONFLICT    (shown with switch-to-password CTA)
```

### OAuth Callback Page State Machine

```
MOUNT
  → [?token= present]     → store token → router.replace("/")
  → [?error= present]     → show error + link to /login
  → [?error=email_conflict] → show conflict message + link to /login with email pre-filled
  → [neither]             → router.replace("/login")
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| Email | Required; valid email format; validated before SSO lookup and before login submit |
| Password | Required; shown always (not hidden behind email-first step) |
| Remember me | Optional boolean; default false |
| Provider | Must be one of: `google`, `microsoft`, `apple` |

---

## Invariants (from clarifications)

1. **One email, one auth method**: A given email address MUST be associated with at most one
   of: email/password, Google, Microsoft, Apple, SSO. The backend enforces this; the frontend
   surfaces the conflict error (FR-011).

2. **SSO fallthrough**: A failed or absent SSO lookup MUST NOT block the email/password path.
   The frontend treats any non-`sso_enabled: true` outcome (including network errors) as
   "proceed with password auth".

3. **Auto-registration**: A social login for an unknown email auto-creates the account.
   The frontend has no awareness of whether this is a new or returning user — it only sees
   the returned JWT.

4. **Token consumed immediately**: The JWT received in the callback URL query param MUST be
   read by `setToken()` and the URL replaced with `router.replace("/")` before any other
   navigation. The token MUST NOT remain in browser history.

---

## Storage Contract (unchanged)

| Key | Storage | Type | Set by | Cleared by |
|-----|---------|------|--------|------------|
| `access_token` | localStorage | string (JWT) | `setToken()` in api.ts | `clearToken()` on 401 |
