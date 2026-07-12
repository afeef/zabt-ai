# Data Model: Social Login & Enhanced Registration Page

**Feature**: 001-social-register
**Date**: 2026-02-20

---

## Entities

### User (existing — extended)

`full_name` is now collected at registration and forwarded to the backend. The backend
already stores it as `Optional[str]`.

```typescript
// Existing — no change to interface required (full_name already present)
interface User {
  email: string;
  full_name: string | null;
  tier: "free" | "pro" | "enterprise";
  is_active: boolean;
  minutes_used_this_month: number;
}
```

### OAuthProvider (existing — reused from 003-social-sso-login)

```typescript
// No change — reused as-is
type OAuthProvider = "google" | "microsoft" | "apple";
```

### UserCreateRequest (new — frontend-only, for register() call)

```typescript
interface UserCreateRequest {
  email: string;
  password: string;
  full_name: string;   // required on the form; optional at the API boundary
}
```

---

## API Function Changes

### `register()` — updated signature

```typescript
// Before:
register(email: string, password: string): Promise<User>

// After:
register(email: string, password: string, fullName: string): Promise<User>
// Passes { email, password, full_name: fullName } to POST /users/
```

---

## State Transitions

### Registration Page State Machine

```
IDLE
  → [click social button]       → OAUTH_REDIRECT    (browser navigates away)
  → [click Sign up]             → SUBMITTING

SUBMITTING  (POST /users/ in flight)
  → [201 Created]               → REGISTERED       (router.push("/login"))
  → [400 email already exists]  → ERROR            (inline error shown)
  → [network error]             → ERROR            (inline error shown)

OAUTH_REDIRECT  (browser at provider)
  → [callback ?token=...]       → AUTHENTICATED    (setToken, router.replace("/"))
  → [callback ?error=email_conflict] → ERROR_CONFLICT (shown on /auth/callback/[provider])
  → [callback ?error=...]       → ERROR            (shown on /auth/callback/[provider])
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| Full Name | Required; non-empty string |
| Email | Required; valid email format |
| Password | Required; minimum 8 characters |
| Provider | Must be one of: `google`, `microsoft`, `apple` |

---

## Invariants (inherited from 003-social-sso-login)

1. **One email, one auth method**: A given email address MUST be associated with at most
   one of: email/password, Google, Microsoft, Apple. The backend enforces this.

2. **Auto-registration for social**: A social sign-up for an unknown email auto-creates
   the account. The frontend has no awareness of whether this is new or returning.

3. **Token consumed immediately**: The JWT received in the callback URL MUST be read by
   `setToken()` and the URL replaced before any other navigation.

---

## Storage Contract (unchanged)

| Key | Storage | Type | Set by | Cleared by |
|-----|---------|------|--------|------------|
| `access_token` | localStorage | string (JWT) | `setToken()` in api.ts | `clearToken()` on 401 |
