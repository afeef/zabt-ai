# Research: Social Login & Enhanced Registration Page

**Feature**: 001-social-register
**Date**: 2026-02-20

---

## Decision 1: Reuse OAuth2 Pattern from Feature 003

**Decision**: The registration page reuses the identical backend-redirect OAuth2 pattern
from `003-social-sso-login`. Clicking a social button on `/register` calls the same
`socialLoginUrl()` helper and navigates to the same backend authorize URL. The existing
`/auth/callback/[provider]` page handles the token and error cases without any modification.

**Rationale**: The backend's OAuth2 callback already handles both new and existing users:
- New email → auto-creates Meetily account and issues JWT
- Existing email/password account → returns `email_conflict` error

From the registration page's perspective, clicking "Sign up with Google" is mechanically
identical to clicking "Sign in with Google" on the login page. No new routes, no new
backend work, no new frontend pages needed.

**Alternatives considered**: A dedicated `/register/callback/[provider]` page (rejected —
identical logic, unnecessary duplication); pre-checking email before redirect (rejected —
adds latency and complexity with no UX benefit since the backend handles the conflict).

---

## Decision 2: Social Button Labels — "Sign up with" on Register Page

**Decision**: The social buttons on `/register` use the label "Sign up with Google /
Microsoft / Apple" (not "Sign in with"). The `SocialButton` component's `label` prop
makes this trivial — no component changes needed.

**Rationale**: "Sign up with Google" is more semantically correct on a registration form
and avoids confusion about whether the user is creating a new account or signing into an
existing one. The reference design (Pareto.ai) uses "Sign in with" on both pages because
their OAuth flow is user-facing; Meetily can be slightly more precise.

**Alternatives considered**: "Continue with Google" (acceptable but generic); "Sign in
with Google" (matches login page and the Pareto.ai reference, but slightly confusing on
a registration form).

---

## Decision 3: `register()` Extended with `full_name`

**Decision**: The `register()` function in `api.ts` is extended to accept an optional
`full_name: string` parameter. When provided, it is included in the `POST /users/` body.
The backend already accepts `full_name: str = Body(None)` (confirmed in
`backend/app/api/users.py` — optional, defaults to `null`).

**Rationale**: Collecting full name at registration improves profile completeness from
day one without requiring a separate profile-update step. The backend change is already
in place — no backend work required.

**Alternatives considered**: Separate profile page after registration (rejected — adds
friction, loses the data if users skip it); not collecting at all (rejected — the reference
design includes it, and it improves user experience in the app).

---

## Decision 4: Post-Registration Redirect — to `/login`

**Decision**: After successful email/password registration, the user is redirected to
`/login`. This matches the current behaviour and the spec clarification.

**Rationale**: Auto-login after registration would require the backend to issue a JWT on
the `POST /users/` response (it currently returns a `UserBase` object, not a token).
Changing that is out of scope. Redirecting to `/login` is a known, working flow.

**Alternatives considered**: Auto-login via a follow-up `POST /login/access-token` call
(rejected — out of scope for this feature; adds two API calls and error-handling
complexity); redirect to `/` directly (rejected — user would not be authenticated).

---

## Decision 5: Form Layout — Mirrors Login Page

**Decision**: The registration page uses the same card dimensions and visual design as
the updated login page: `max-w-md` (wider than the old `max-w-sm`), `rounded-xl`
(documented one-off exception in system.md), `p-8`, `border border-stone-200`,
`bg-white` surface on `bg-stone-50` ground.

**Rationale**: Visual consistency across auth pages reduces cognitive overhead and ensures
the Meetily design system is upheld. The `rounded-xl` exception is already documented in
`.interface-design/system.md` as the auth card exception.

**Alternatives considered**: Keep `max-w-sm` `rounded-lg` (rejected — visually
inconsistent with the new login page; the wider card is needed to comfortably fit three
social buttons plus three form fields).

---

## Decision 6: Full Name Field — Required

**Decision**: Full Name is a required field (`required` attribute on the `<input>`).
HTML5 native validation prevents submission when empty.

**Rationale**: Confirmed in spec clarifications. The reference design shows it as a
required field. Without a full name, the profile is incomplete and the app's personal
feel (warm notebook) is diminished.

**Alternatives considered**: Optional with placeholder defaulting to email prefix (rejected
— spec explicitly requires it as required).

---

## Decision 7: Show/Hide Password — Identical to Login Page

**Decision**: The password field wraps the `<input>` in a `relative <div>` with an
absolutely-positioned `<button>` toggling `Eye` / `EyeOff` icons from `lucide-react`.
Identical implementation to the login page.

**Rationale**: Consistent UX pattern. No new patterns needed — already in system.md.

---

## Design Reference Layout (Registration Page)

```
┌──────────────────────────────────┐
│  [Logo]  Meetily                 │  ← centred, text-stone-900
│  Create your account             │  ← text-2xl font-bold
│  Please enter your details.      │  ← text-sm text-stone-500
│                                  │
│  [G]  Sign up with Google        │  ← social button (border, rounded-lg, h-12)
│  [M]  Sign up with Microsoft     │
│  [🍎] Sign up with Apple         │
│                                  │
│  ──── or sign up with email ──── │  ← separator
│                                  │
│  Full name                       │
│  [John Doe              👤]     │  ← input
│                                  │
│  Email address                   │
│  [name@company.com      ✉]     │  ← input
│                                  │
│  Password                        │
│  [•••••••              👁/👁‍🗨] │  ← input + show/hide
│                                  │
│  [        Sign up          ]     │  ← full-width indigo button
│                                  │
│  Already have an account? Sign in│
└──────────────────────────────────┘
```
