# Data Model: Logto-Based User Registration

**Feature**: 001-logto-register
**Date**: 2026-02-20

---

## Entities

### User (existing — no schema changes)

The local `User` table in PostgreSQL remains unchanged. This feature does not add, remove, or
modify any columns.

| Field | Type | Notes |
|-------|------|-------|
| `id` | int (PK, auto) | Local database primary key |
| `email` | str (unique, indexed) | From Logto's ID token `email` claim |
| `full_name` | Optional[str] | From Logto's ID token `name` claim (set by JIT) |
| `picture` | Optional[str] | From Logto's ID token `picture` claim |
| `tier` | UserTier (FREE default) | Subscription tier |
| `is_active` | bool (default True) | Account active flag |
| `minutes_used_this_month` | int (default 0) | Usage tracking |
| `logto_id` | str (unique, indexed) | Maps to Logto's `sub` claim — identity link |

**Creation**: Users are created via JIT provisioning in `deps.py:get_current_user()` when a
valid Logto JWT is presented for the first time. No code change required.

---

### Logto Identity (external — in Logto's datastore)

Logto manages its own identity records. The local system treats these as opaque.

| Concept | Notes |
|---------|-------|
| Logto User ID (`sub`) | UUID string; maps to local `User.logto_id` |
| Email identity | Email + hashed password credential (for email/password users) |
| Social identity | OAuth provider + provider user ID (for Google/Microsoft/Apple users) |
| Session | Managed by Logto's OIDC server; local system only sees JWTs |

---

### Logto SDK Session (frontend — in-memory / encrypted HTTP-only cookie)

`@logto/next` stores the authenticated session in an encrypted HTTP-only cookie on the
Next.js server. Client components never access the raw token.

| Field | Notes |
|-------|-------|
| Access token | Scoped to backend API resource (`http://localhost:8000`); expires per Logto config |
| Refresh token | Used by SDK to renew access token silently |
| ID token claims | `sub`, `email`, `name`, `picture` |
| Is authenticated | Boolean derived from session presence |

---

## State Transitions

### Registration Flow

```
[Anonymous visitor]
       │
       ▼
[Register page] ──── social button ──────────────────────────────┐
       │                                                           │
       │── "Sign up with email" button                            │
       │                                                           │
       ▼                                                           ▼
[Logto hosted sign-up]                               [OAuth provider (Google/etc)]
       │                                                           │
       │ (enters email + password + email verification)           │
       ▼                                                           ▼
[Logto issues authorization code]                   [Logto exchanges OAuth code]
       │                                                           │
       └────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
              [/api/logto/callback — Next.js SDK]
                            │
                            │ (code exchange → tokens → encrypted cookie)
                            │
                            ▼
              [JIT provisioning — backend deps.py]
                  (first protected API call creates User record)
                            │
                            ▼
                     [/ — dashboard]
                  [Authenticated user]
```

### Token Refresh Flow

```
[Client component needs access token]
       │
       ▼
[useLogto().getAccessToken(resource)]
       │
       ├── token still valid ──► returns token
       │
       └── token expired ──► SDK uses refresh token ──► returns new token
                                (transparent to client code)
```
