# Research: Social Login & SSO for Login Page

**Feature**: 003-social-sso-login
**Date**: 2026-02-19
**Clarifications incorporated**: all 5 from session 2026-02-19

---

## Decision 1: OAuth2 Pattern — Backend Redirect

**Decision**: Backend-redirect OAuth2. Frontend navigates to
`{API_URL}/auth/oauth/{provider}/authorize?redirect_uri=...&state=...`. Backend handles
provider token exchange and redirects back with JWT in query param.

**Rationale**: Consistent with existing auth pattern (backend issues JWT, frontend stores in
localStorage). No new npm packages. Client secrets stay server-side (constitution security
requirement). Works identically for all three providers.

**Alternatives considered**: NextAuth.js (too heavyweight), client-side PKCE (exposes more
to browser, harder to correlate with existing user accounts).

---

## Decision 2: Account Conflict — Block, No Auto-Link (clarified)

**Decision**: When a social login returns an email that already belongs to an email/password
account, the backend MUST return an error (HTTP 409). The frontend displays:
"An account with this email already exists. Sign in with your password instead." with a link
that scrolls to / focuses the email/password form.

**Rationale**: Prevents silent data merges. Standard SaaS pattern (Notion, Linear). Keeps
the one-email-one-auth-method invariant clean and testable.

**Alternatives considered**: Auto-link (rejected — silent merges create support confusion);
allow duplicate emails (rejected — breaks email-as-identity-key assumption).

---

## Decision 3: SSO Trigger — On Sign In Click, with Fallthrough (clarified)

**Decision**: Email and password fields are visible simultaneously. When Sign In is clicked,
the frontend calls `POST /auth/sso/lookup` with the email before attempting password auth.
If `sso_enabled: true` → redirect to `redirect_url`. If `sso_enabled: false` OR the lookup
request fails (network error, timeout, 5xx) → proceed with email/password auth immediately.

**Rationale**: Matches the reference design (both fields visible). Fallthrough on lookup
failure ensures SSO detection never blocks legitimate email/password users.

**Alternatives considered**: On-email-blur (adds latency noise); email-first step (requires
page restructure not in design).

---

## Decision 4: Auto-Registration on First Social Login (clarified)

**Decision**: If the backend receives a social callback for an email with no existing Meetily
account, it MUST create the account automatically using the provider email. No confirmation
step or additional form. User lands on the home page immediately.

**Rationale**: Standard expectation for social login. Confirmation steps introduce unnecessary
friction for a new-user path.

**Alternatives considered**: Confirmation step (rejected — adds friction, no UX benefit for
this product's user type).

---

## Decision 5: Provider Unavailability — No Proactive Detection (clarified)

**Decision**: Social login buttons have no proactive availability check. When clicked, the
browser navigates to the backend authorize URL. If the backend authorize endpoint or the
provider itself is unavailable, the callback returns with `?error=...` and the standard error
banner is shown on the login page.

**Rationale**: Proactive detection (pinging providers before click) adds complexity with no
reliability benefit — provider status can change between the check and the actual click. The
error path already handles all failure cases.

**Alternatives considered**: Disable buttons on detect (rejected — complexity, false positives);
auto-retry (rejected — adds unexpected delays, hides real errors).

---

## Decision 6: Forgot Password — Stub Route Only (clarified)

**Decision**: "Forgot password?" link navigates to `/forgot-password`. That route renders
a placeholder: "Password reset coming soon." No email is sent, no backend call is made.
A full reset flow is a separate future feature.

**Rationale**: Keeps this feature's scope clean. The link must be present per design (FR-008),
but building the reset flow now would be out of scope and unspecified.

---

## Decision 7: Show/Hide Password Toggle

**Decision**: Client-side `useState` toggling input `type` between `"password"` and `"text"`.
Icons: `Eye` / `EyeOff` from `lucide-react` (already installed).

**Rationale**: Zero new dependencies. Standard pattern.

---

## Decision 8: OAuth Callback Route

**Decision**: `app/auth/callback/[provider]/page.tsx`. On mount:
1. Read `?token=` from URL — call `setToken(token)`, replace URL state (remove query params),
   redirect to `/`.
2. Read `?error=` from URL — display error message with link back to `/login`.
3. Neither present — redirect to `/login`.

Token is consumed immediately and the URL is cleaned (`router.replace('/')`) so the JWT
never lingers in browser history.

**Rationale**: Matches existing token storage pattern. `router.replace` satisfies the
constitution security requirement to not leave tokens in browser history.

---

## Decision 9: Social Button Icons

**Decision**: Inline SVG for Google (G logo), Microsoft (four-colour grid), Apple (apple
logo). No external image CDN.

**Rationale**: No external dependency. Consistent sizing. Google and Apple have specific
brand guidelines best satisfied with inline SVG rather than emoji or text.

---

## Design Reference Layout (from attached screenshot)

```
┌──────────────────────────────────┐
│  [Logo]  Meetily                 │  ← centred, text-stone-900
│  Welcome back                    │  ← text-2xl font-bold
│  Please enter your details...    │  ← text-sm text-stone-500
│                                  │
│  [G]  Sign in with Google        │  ← social button (border, rounded-lg, h-12)
│  [M]  Sign in with Microsoft     │
│  [🍎] Sign in with Apple         │
│                                  │
│  ──── or sign in with email ──── │  ← separator
│                                  │
│  Email address                   │
│  [name@company.com        ✉]     │  ← input + icon right
│                                  │
│  Password                        │
│  [•••••••               👁/👁‍🗨]  │  ← input + show/hide
│                                  │
│  ○ Remember me  Forgot password? │  ← checkbox left, link right
│                                  │
│  [        Sign in          ]     │  ← full-width indigo button
│                                  │
│  Don't have an account? Register │
└──────────────────────────────────┘
```

**Auth card rounding**: Design uses larger radius than `rounded-lg`. Use `rounded-xl` on the
auth card — one-off exception documented in system.md (already noted in current system.md).
