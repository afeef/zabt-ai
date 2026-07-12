# Feature Specification: Social Login & Enhanced Registration Page

**Feature Branch**: `001-social-register`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "The current registration page is very simple (email + password only). We need to add social sign-up (Google, Microsoft, Apple), a full name field, a show/hide password toggle, and update the layout to match the new login page design."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Social Sign-Up (Priority: P1)

A new user who prefers not to create a password can register by clicking "Sign up with Google", "Sign up with Microsoft", or "Sign up with Apple". They are redirected to the provider's authorisation page, and on return their Meetily account is automatically created and they land on the home page. If their email is already registered via email/password, they see a clear error and a link to sign in instead.

**Why this priority**: Social sign-up removes the biggest friction point in registration (choosing and remembering a password). It shares the same backend OAuth2 callback flow already built for the login page, so implementation cost is low and the payoff is high.

**Independent Test**: Visit `/register` → click "Sign up with Google" → browser navigates to `{API_URL}/auth/oauth/google/authorize?...`. Simulate a successful callback by visiting `/auth/callback/google?token=<any-valid-jwt>` → token stored → redirected to `/`. Visit `/auth/callback/google?error=email_conflict` → conflict message with link to `/login` shown.

**Acceptance Scenarios**:

1. **Given** a new user on `/register`, **When** they click "Sign up with Google", **Then** the browser navigates to the backend Google OAuth authorisation URL (including a `redirect_uri` pointing back to `/auth/callback/google` and a CSRF `state` parameter).
2. **Given** the backend has processed the OAuth callback and issued a token, **When** the user lands on `/auth/callback/google?token=<jwt>`, **Then** the token is stored and the user is redirected to `/` without the token remaining in browser history.
3. **Given** the social provider email already belongs to an email/password account, **When** the backend redirects to `/auth/callback/google?error=email_conflict`, **Then** the page displays "An account with this email already exists. Sign in with your password instead." with a link to `/login`.
4. **Given** any other provider error, **When** the callback page receives `?error=<code>`, **Then** a generic "Sign up failed. Please try again." message is shown with a link to `/login`.

---

### User Story 2 — Enhanced Email/Password Registration Form (Priority: P2)

A new user who prefers email/password registration is presented with a modern, full-design form that includes their full name, email, and a password field with a show/hide toggle. The form matches the visual style of the updated login page.

**Why this priority**: The email/password path is the fallback for users who cannot use social sign-up, and the current form is visually inconsistent with the new login page. Adding full name collection here improves profile completeness from day one.

**Independent Test**: Visit `/register` → fill in Full Name, Email, Password (≥ 8 characters) → click "Sign up" → account created → redirected to `/login`. Click the eye icon on the password field → password characters revealed; click again → re-masked.

**Acceptance Scenarios**:

1. **Given** a user on `/register`, **When** they enter a full name, a valid email, and a password of at least 8 characters, then click "Sign up", **Then** the account is created and the user is redirected to `/login`.
2. **Given** a user on `/register`, **When** they submit with an email that is already registered, **Then** an inline error "This email is already registered. Try signing in instead." is shown; no redirect occurs.
3. **Given** a user entering their password, **When** they click the show/hide toggle, **Then** the password characters become visible; clicking again masks them.
4. **Given** a user on `/register`, **When** they click "Already have an account? Sign in", **Then** they are navigated to `/login`.

---

### Edge Cases

- What happens when a user clicks a social sign-up button but cancels at the provider consent screen? → The callback receives `?error=access_denied`; the standard generic error message is shown.
- What happens when the password is shorter than 8 characters? → The form prevents submission with a validation message.
- What happens when Full Name is left blank? → The form prevents submission; the field is required.
- What happens if the network fails during form submission? → An inline error is shown; the form remains editable and no redirect occurs.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The registration page MUST display social sign-up buttons for Google, Microsoft, and Apple above the email/password form, separated by an "or sign up with email" divider.
- **FR-002**: Each social button MUST navigate the browser to the backend OAuth2 authorisation URL for the selected provider, including a `redirect_uri` pointing to the existing `/auth/callback/[provider]` page and a unique CSRF `state` parameter.
- **FR-003**: The email/password form MUST include a Full Name field (required, placeholder "John Doe") in addition to email and password.
- **FR-004**: The password field MUST include a show/hide toggle that reveals or masks the password characters on click.
- **FR-005**: On successful email/password registration, the system MUST redirect the user to `/login`.
- **FR-006**: On a duplicate-email submission, the system MUST display an inline error message without navigating away.
- **FR-007**: The page layout MUST match the updated login page design: Meetily wordmark, "Create your account" heading, a subtitle, and a centred card with the same proportions and border style as the login card.
- **FR-008**: The page MUST display a "Already have an account? Sign in" link navigating to `/login`.
- **FR-009**: Social sign-up MUST reuse the existing OAuth callback page already implemented for the login flow; no new callback page is needed.

### Key Entities

- **User**: Represents a Meetily account. Key attributes: full name (optional, collected at registration), email (unique identity key), authentication method (email/password or social provider). One email maps to exactly one authentication method.
- **OAuthProvider**: The selected social sign-up provider — one of: Google, Microsoft, Apple.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can complete social sign-up in under 30 seconds (from clicking a provider button to landing on the home page).
- **SC-002**: A new user can complete email/password registration in under 2 minutes (from page load to redirect to `/login`).
- **SC-003**: The registration page renders identically to the login page's visual style — same card dimensions, social buttons, separator, and input design.
- **SC-004**: A duplicate-email attempt surfaces an error without a page reload or redirect — the user remains on `/register` with their entered data intact.
- **SC-005**: The show/hide password toggle works on the first click with no perceptible delay.

---

## Assumptions

- The OAuth callback page (from feature `003-social-sso-login`) is already deployed and handles token storage and error display. No changes to that page are needed.
- The social login button component and the URL helper for constructing provider authorisation URLs (both from feature `003-social-sso-login`) are already available and can be reused directly.
- The backend `/users/` registration endpoint accepts an optional `full_name` field in addition to `email` and `password`. If the backend does not yet accept `full_name`, the field will be collected in the form and forwarded once the backend is updated (out of scope for this feature's backend work).
- After email/password registration, the user is redirected to `/login` to sign in — auto-login after registration is out of scope.
- SSO domain lookup is a sign-in feature only; the registration page does not perform SSO lookup on submit.
- Password minimum length of 8 characters matches the existing registration validation.

---

## Clarifications

### Session 2026-02-20

- Q: Should SSO domain lookup be triggered on the registration page (like on the login page)? → A: No — SSO is a sign-in feature. The registration page does not perform SSO lookup.
- Q: Should registration auto-login the user after account creation, or redirect to `/login`? → A: Redirect to `/login` (matching current behaviour; auto-login is a separate future enhancement).
- Q: Is Full Name a required or optional field on the registration form? → A: Required (matches the reference design and improves profile completeness).
