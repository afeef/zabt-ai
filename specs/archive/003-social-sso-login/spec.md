# Feature Specification: Social Login & SSO for Login Page

**Feature Branch**: `003-social-sso-login`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "The attached login screen does not match the design. The design has social login as well as sso but the implementation in the frontend-2 project only has a simple username/password. You need to fix this"

## Clarifications

### Session 2026-02-19

- Q: When a social login email matches an existing email/password account, what should happen? → A: Block with a prompt — show an error directing the user to sign in with their password instead; no auto-linking.
- Q: When does the SSO domain lookup trigger? → A: On Sign In click — email and password fields are both visible simultaneously; the SSO lookup runs on submit before attempting email/password auth.
- Q: Is "Forgot password?" a working reset flow or a stub? → A: Stub only — link is present and navigates to /forgot-password which shows a placeholder; reset flow is out of scope for this feature.
- Q: When a first-time user signs in with a social provider (no existing Meetily account), what happens? → A: Auto-register — account is created silently from the provider email; user lands on home page immediately with no confirmation step.
- Q: When a social provider is temporarily unavailable, what should the UI do? → A: No proactive detection — allow the click and redirect normally; if the backend or callback returns an error, show it via the standard auth error path on the login page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Social Login (Priority: P1)

A user arrives at the login page and signs in using their existing Google, Microsoft, or Apple account — without needing to remember a separate Meetily password.

**Why this priority**: Social login reduces friction for the most common new and returning user path. It is the most visible gap between the current implementation and the design.

**Independent Test**: Fully testable by clicking "Sign in with Google" on the login page, completing the OAuth flow, and landing on the authenticated home page.

**Acceptance Scenarios**:

1. **Given** a user is on the login page, **When** they click "Sign in with Google", **Then** they are redirected to Google's authentication flow and, upon success, returned to the app as an authenticated user.
2. **Given** a user is on the login page, **When** they click "Sign in with Microsoft", **Then** they are redirected to Microsoft's authentication flow and returned to the app as an authenticated user.
3. **Given** a user is on the login page, **When** they click "Sign in with Apple", **Then** they are redirected to Apple's authentication flow and returned to the app as an authenticated user.
4. **Given** a social login flow fails or is cancelled, **When** the user is returned to the login page, **Then** a clear error message is shown and they can try again.
5. **Given** a social login returns an email that already has an email/password account, **When** the backend detects the conflict, **Then** the user sees an error: "An account with this email already exists. Sign in with your password instead." with a link to the email/password form.

---

### User Story 2 - SSO Login (Priority: P2)

A user from an enterprise organisation signs in using their company's Single Sign-On provider by entering their work email address and being routed to their identity provider automatically.

**Why this priority**: SSO is required for enterprise users but is less common than social login for individual users. It represents the second distinct authentication path in the design.

**Independent Test**: Testable by entering a work email on the login page and verifying the user is redirected to the correct identity provider.

**Acceptance Scenarios**:

1. **Given** a user has entered a work email and clicks Sign In, **When** the frontend calls the SSO domain lookup, **Then** if the domain is SSO-enabled, the user is redirected to that organisation's identity provider without submitting the password.
2. **Given** a user has entered a personal email and clicks Sign In, **When** the SSO lookup returns no match, **Then** the standard email/password authentication proceeds using the already-entered password.
3. **Given** the SSO lookup call itself fails (network error, timeout), **When** the user clicks Sign In, **Then** the system falls through to email/password auth and does not block the user.
4. **Given** an SSO flow fails at the identity provider, **When** the user is returned to the login page, **Then** a meaningful error is shown.

---

### User Story 3 - Email/Password Login with Enhanced UI (Priority: P3)

Existing email/password login continues to work but is now presented below a visual separator ("or sign in with email"), and includes additional affordances: a show/hide password toggle, a "Remember me" checkbox, and a "Forgot password?" link.

**Why this priority**: This enhances an already-working flow. It is lower priority than adding the missing social/SSO paths but is part of the design.

**Independent Test**: Testable by signing in with a valid email/password credential and verifying the enhanced UI elements are present and functional.

**Acceptance Scenarios**:

1. **Given** a user enters a valid email and password, **When** they click "Sign in", **Then** they are authenticated and redirected to the home page.
2. **Given** a user clicks the show/hide toggle on the password field, **When** toggled, **Then** the password is revealed or re-masked.
3. **Given** a user checks "Remember me", **When** they return to the app after closing the browser, **Then** they remain authenticated.
4. **Given** a user clicks "Forgot password?", **When** clicked, **Then** they are navigated to `/forgot-password` which displays a placeholder page; no reset email is sent in this feature.

---

### Edge Cases

- When a social provider is temporarily unavailable, the redirect proceeds normally; the resulting error is surfaced via the standard callback error path (same as a cancelled or failed auth). No proactive button disabling is required.
- A social login email that matches an existing email/password account MUST be blocked with a prompt directing the user to sign in with their password; no silent account merging.
- What if a user's SSO organisation is configured but their account is not provisioned in the IdP?
- What happens if the user denies the permissions requested by the social login provider?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The login page MUST display social login buttons for Google, Microsoft, and Apple above the email/password form.
- **FR-002**: Each social login button MUST initiate the respective OAuth2 authentication flow when clicked.
- **FR-003**: Upon successful social login, the system MUST automatically create a new Meetily account using the provider email if none exists, or retrieve the existing social account if it does. No confirmation step is required. If the returned email already belongs to an email/password account, the system MUST return an error and NOT create a new account or link the social identity.
- **FR-004**: The login page MUST show email and password fields simultaneously. When the user clicks Sign In, the system MUST call the SSO domain lookup first; if the domain is SSO-enabled, the user is redirected to the identity provider and the password is not submitted. If the lookup returns no match or fails, email/password authentication proceeds normally.
- **FR-005**: A visual separator labelled "or sign in with email" MUST appear between the social login buttons and the email/password form.
- **FR-006**: The password field MUST include a show/hide toggle.
- **FR-007**: The login form MUST include a "Remember me" checkbox that extends session persistence.
- **FR-008**: The login form MUST include a "Forgot password?" link that navigates to `/forgot-password`. That route MUST render a placeholder page. A full password reset flow is out of scope for this feature.
- **FR-009**: All authentication error states (cancelled flow, invalid credentials, provider unavailable, email conflict) MUST display user-friendly messages.
- **FR-010**: The login page layout MUST match the provided design: logo/product name at top, social buttons, separator, email field, password field with toggle, remember me + forgot password row, sign in button, register link at bottom.
- **FR-011**: When a social login is blocked due to an existing email/password account, the error message MUST include a direct link or action to switch to the email/password form.

### Key Entities

- **User**: A person with an account in the system. May be authenticated via email/password, social provider, or SSO. Identified by email address. A single email address MUST belong to exactly one authentication method (no cross-method merging). First-time social login auto-creates the account; no separate registration step.
- **Social Identity**: A link between a User and a third-party provider account (Google, Microsoft, Apple). A user may have multiple social identities but only one per provider.
- **SSO Organisation**: A company whose users authenticate via a configured enterprise identity provider. Mapped by email domain.
- **Session**: An authenticated period for a user. Optionally extended via "Remember me".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete Google social login in under 30 seconds from clicking the button to landing on the authenticated home page.
- **SC-002**: 100% of login paths visible in the design (social, SSO, email/password) are available in the UI.
- **SC-003**: Social login errors and cancellations are handled gracefully with no unhandled error states or blank screens.
- **SC-004**: A user who checks "Remember me" remains authenticated across browser sessions without being prompted to sign in again.
- **SC-005**: The login page layout matches the provided design reference with all visual elements present (logo, social buttons, separator, form fields, remember me, forgot password, register link).
- **SC-006**: 100% of social login attempts that would conflict with an existing email/password account are blocked with a clear, actionable error message; zero silent account merges occur.

## Assumptions

- The backend already supports or will be extended to support OAuth2 token exchange for Google, Microsoft, and Apple; this spec describes front-end behaviour and the required contract with the backend.
- SSO is email-domain-based routing (i.e., entering a work email triggers SSO detection); no separate "Sign in with SSO" button is required unless the domain check is insufficient.
- "Remember me" extends the session beyond browser close; the exact duration is a backend configuration detail.
- The "Forgot password?" link navigates to `/forgot-password`, which renders a stub placeholder page. A functional password reset flow is explicitly out of scope and will be addressed in a future feature.
- The design reference (Pareto.ai screenshot) is used as a structural and visual layout guide. The product name and logo shown in the design are Pareto.ai's and should be replaced with Meetily branding.
- Email address is the canonical identity key; duplicate emails across auth methods are not permitted and the system enforces this at login time rather than at registration.
