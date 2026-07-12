# Feature Specification: Product & Web Analytics

**Feature Branch**: `001-product-analytics`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "As a user, i want to track the web and product analytics on the application to learn about my user's behaviors"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Page & Session Tracking (Priority: P1)

As an admin/owner of the application, I want every page visit and user session automatically captured so I can understand how users navigate the app without any manual instrumentation per page.

**Why this priority**: Foundational visibility — without this, no other analytics is possible. Every page, including login, dashboard, meetings list, and meeting detail, should be tracked automatically.

**Independent Test**: Can be fully tested by visiting several pages while signed in and verifying that sessions and pageviews appear in the analytics dashboard within 60 seconds.

**Acceptance Scenarios**:

1. **Given** a user visits any page of the application, **When** the page loads, **Then** a pageview event is captured including the page URL, referrer, and session identifier.
2. **Given** a user's session starts (first visit or new browser session), **When** they land on any page, **Then** a new session is recorded with entry source (direct, referral, search).
3. **Given** a user is signed in, **When** they navigate between pages, **Then** their pageviews are associated with their user identity.
4. **Given** a user is not signed in (unauthenticated), **When** they visit the login page, **Then** an anonymous pageview is still recorded.

---

### User Story 2 - Key Product Event Tracking (Priority: P2)

As an admin/owner, I want specific in-app actions tracked as named events so I can measure feature adoption and identify drop-off points in critical workflows.

**Why this priority**: Pageviews alone don't reveal how users interact with core features. Named events (e.g. "meeting uploaded", "summary viewed") are needed to understand product health.

**Independent Test**: Can be fully tested by performing each tracked action once and verifying the corresponding named event appears in the analytics dashboard with correct properties.

**Acceptance Scenarios**:

1. **Given** a user uploads a meeting recording, **When** the upload completes, **Then** an "upload_completed" event is captured with properties: file size tier (small/medium/large), file type.
2. **Given** a meeting finishes transcription, **When** the transcription result is saved, **Then** a "transcription_completed" event is captured with: meeting duration tier, language.
3. **Given** a meeting summary is generated, **When** the summary is ready, **Then** a "summary_generated" event is captured with: template used, word count tier.
4. **Given** a user views a meeting summary, **When** they open the summary tab, **Then** a "summary_viewed" event is captured.
5. **Given** a user exports a summary as PDF, **When** the download completes, **Then** a "summary_exported" event is captured.

---

### User Story 3 - User Identity & Cohort Analysis (Priority: P3)

As an admin/owner, I want each tracked event to be associated with the authenticated user's identity so I can analyze behavior by user, identify power users, and segment by signup cohort.

**Why this priority**: Without identity linking, analytics data is fragmented across anonymous sessions and cannot be attributed to specific users or used for cohort analysis.

**Independent Test**: Can be fully tested by signing in as a known test user, performing actions, and verifying those events appear under that user's profile in the analytics dashboard.

**Acceptance Scenarios**:

1. **Given** a user signs in, **When** the session starts, **Then** all subsequent events in that session are associated with their user ID.
2. **Given** a user was browsing anonymously before sign-in, **When** they sign in, **Then** any anonymous events from the same session are linked to their user profile (identity merge).
3. **Given** the analytics dashboard is open, **When** filtering by a specific user, **Then** all their events across all sessions are visible in chronological order.
4. **Given** a new user signs up, **When** the account is created, **Then** a "user_signed_up" event is captured with the signup date for cohort tracking.

---

### Edge Cases

- What happens when a user has an ad blocker that blocks analytics scripts? Analytics events are silently dropped; no error is shown to the user and app functionality is unaffected.
- What happens when the analytics service is unreachable? Tracking calls fail silently; the application continues to function normally.
- What happens when a user visits from a country with strict cookie/tracking laws (e.g. GDPR)? Assumption: no consent banner is required for this stage (internal/B2B tool); revisit if user base expands to EU consumers.
- What happens if the same user signs in on multiple devices simultaneously? Each device is tracked as a separate session; identity is the same user ID across all devices.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST automatically capture a pageview event each time any application page is loaded or navigated to (including client-side route changes).
- **FR-002**: The system MUST capture a session event at the start of each new user session, including session source (direct, referral, organic search).
- **FR-003**: The system MUST capture the following named product events: `upload_completed`, `transcription_completed`, `summary_generated`, `summary_viewed`, `summary_exported`, `user_signed_up`.
- **FR-004**: Each event MUST include at minimum: event name, timestamp, user identity (authenticated user ID or anonymous ID), and session ID.
- **FR-005**: The system MUST associate all events with the authenticated user's stable identity when the user is signed in.
- **FR-006**: The system MUST merge anonymous session events with the user's profile upon sign-in within the same session.
- **FR-007**: Analytics tracking MUST NOT affect application performance — tracking calls must be non-blocking and fire asynchronously.
- **FR-008**: Analytics tracking MUST fail silently — any error in the tracking layer must not cause UI errors or disrupt core application functionality.
- **FR-009**: Backend-originated events (transcription completed, summary generated) MUST be captured server-side and associated with the correct user identity.
- **FR-010**: The analytics platform MUST support filtering events by user, event type, and date range in its built-in dashboard.

### Key Entities

- **Event**: A discrete action with a name, timestamp, user/session association, and optional properties (key-value pairs describing the action context).
- **Session**: A continuous visit period for a user, bounded by inactivity timeout or browser close, containing one or more events.
- **User Identity**: The stable identifier for a signed-in user (mapped to their application user ID), used to link all events across sessions.
- **Anonymous Identity**: A temporary identifier assigned to unauthenticated visitors, which is merged with the user identity upon sign-in.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of application page loads result in a captured pageview event within 5 seconds of the page rendering.
- **SC-002**: All 6 named product events are captured for at least 95% of the corresponding user actions (accounting for ad blockers and network failures).
- **SC-003**: Events can be queried and visualised in the analytics dashboard within 60 seconds of the action occurring.
- **SC-004**: Zero user-facing errors are introduced by the analytics layer — the application error rate does not increase after instrumentation is deployed.
- **SC-005**: The admin can identify the top 10 most active users and view their complete event history within 3 clicks in the analytics dashboard.
- **SC-006**: Cohort analysis is available showing user retention by signup week within 30 days of the feature going live.

## Assumptions

- The application owner (admin) is the sole consumer of analytics data; no in-app analytics dashboard is being built — an external analytics product's own dashboard is used.
- PostHog Cloud (free tier) is the analytics platform, as agreed in prior discussion. No self-hosting is required at this stage.
- GDPR consent banners are out of scope; the product is used in a B2B/internal context where end users are aware of company monitoring.
- "File size tier" means bucketed categories (e.g. <10MB, 10–100MB, >100MB) rather than exact byte counts, to avoid high-cardinality data.
- The analytics integration does not require any new backend database tables; all data lives in the analytics platform.
