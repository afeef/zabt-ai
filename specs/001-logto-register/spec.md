# Feature Specification: Logto-Based User Registration

**Feature Branch**: `001-logto-register`
**Created**: 2026-02-20
**Status**: Draft
**Input**: User description: "I have tried creating user but I'm getting an error that the email is already registered. Try signing in instead. Even though i have not created any user before. I need this register page to now work with logto to register users"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Email/Password Registration via Identity Provider (Priority: P1)

A new user visits the Meetily registration page and creates an account using their email and password. Currently this always fails with "This email is already registered" even for brand-new emails — because the backend requires every user to have an identity in Logto (the external identity provider) and the current registration path bypasses Logto entirely. This story fixes that: email/password registration must go through the identity provider so new users can actually create accounts.

**Why this priority**: This is the core broken feature. Email/password registration fails for 100% of new users. Until fixed, no new user can create an account via email — the product cannot onboard anyone who doesn't use social login.

**Independent Test**: Visit `/register` → fill Full Name, a fresh email, and a password ≥ 8 characters → click "Sign up" → user is signed in and lands at `/` (not an error page, not `/login`). Repeat with the same email → a "already registered" message appears with a Sign in link.

**Acceptance Scenarios**:

1. **Given** a visitor with no existing Meetily account, **When** they enter a valid full name, email, and password (≥ 8 characters) and submit the registration form, **Then** their account is created in the identity system, they are automatically signed in, and they are redirected to the main dashboard at `/`
2. **Given** a user whose email is already registered, **When** they attempt to register with that email, **Then** they see a message stating the email is taken with a direct link to the sign-in page
3. **Given** a user submitting the registration form, **When** the identity service is temporarily unavailable, **Then** they see a descriptive error message that does not falsely indicate "email already registered"
4. **Given** a user who has just registered via email/password, **When** they visit any protected page, **Then** they are recognised as authenticated and not redirected to login

---

### User Story 2 - Social Provider Registration Verified End-to-End (Priority: P2)

A new user creates a Meetily account by clicking "Sign up with Google", "Sign up with Microsoft", or "Sign up with Apple". This path uses the same backend-redirected OAuth2 flow as social sign-in and routes through Logto, so it is currently functional. This story ensures social registration is explicitly verified and continues to work correctly after the P1 changes.

**Why this priority**: Social registration already works mechanically, but it must be explicitly validated after the identity-provider integration changes introduced for P1 to confirm nothing regressed.

**Independent Test**: Visit `/register` → click "Sign up with Google" → complete Google OAuth in the popup/redirect → user lands at `/` signed in. Attempt again with the same Google account → user is signed in to the existing account (no duplicate created).

**Acceptance Scenarios**:

1. **Given** a new visitor, **When** they click "Sign up with Google/Microsoft/Apple" and complete the provider's authentication, **Then** a Meetily account is created for them, they are signed in, and they land on `/`
2. **Given** a user who previously registered via a social provider, **When** they click "Sign up with [same provider]", **Then** they are signed in to their existing account without creating a duplicate

---

### Edge Cases

- What happens when a user registers via email/password, then later tries to sign in via Google with the same email address?
- What happens when registration succeeds in the identity provider but the local user record fails to be created (partial failure)?
- What happens if the user abandons the registration flow mid-way (closes the browser before the redirect completes)?
- What happens when password is fewer than 8 characters — does the form prevent submission or does the identity provider return an error?
- What happens when the user submits the form multiple times rapidly (double-click)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create new user accounts through the external identity provider — not via direct local database insertion
- **FR-002**: System MUST accept full name, email address, and password (minimum 8 characters) as inputs for email-based registration
- **FR-003**: System MUST automatically sign the user in immediately after successful registration, without requiring a separate sign-in step
- **FR-004**: System MUST redirect newly registered users to the main dashboard (`/`) upon successful registration
- **FR-005**: System MUST display a clear, accurate error when a supplied email address is already registered, with a link to the sign-in page
- **FR-006**: System MUST distinguish registration failure reasons — "email taken" must not appear for identity-service outages or other unrelated errors
- **FR-007**: Social provider registration (Google, Microsoft, Apple) MUST continue to function without regression
- **FR-008**: The registration page MUST preserve the current visual design: social sign-up buttons, full name field, email field, password field with show/hide toggle, and the "Already have an account? Sign in" link

### Key Entities

- **User**: A Meetily account holder identified by a unique identity within the external identity provider. Has an email address, full name, and a linked identity record. The local user record is provisioned automatically upon first successful authentication.
- **Identity**: The record in the external identity provider (Logto) that holds the user's credentials. For email/password accounts this is a Logto-managed username/password credential; for social accounts this is an OAuth-linked identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New users can complete email/password registration in under 60 seconds from landing on the register page to reaching the main dashboard
- **SC-002**: Zero false "email already registered" errors for users who have never registered before — registration failure rate drops from 100% to 0% for genuinely new email addresses
- **SC-003**: Error messages displayed during registration accurately describe the actual failure reason in all cases
- **SC-004**: Social provider registration (Google/Microsoft/Apple) continues to work with no measurable regression in success rate

## Assumptions

- The external identity provider (Logto) is running and accessible from the backend during registration
- Social login via the existing OAuth2 backend-redirect flow continues to serve as the mechanism for social registration (no change to that path required)
- Account linking between email/password and social identities for the same email address is handled by the identity provider's built-in logic and is out of scope for this feature
- The registration page's visual design (established in the `001-social-register` feature) is the target UI — no design changes are required
