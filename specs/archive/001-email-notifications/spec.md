# Feature Specification: Email Notifications

**Feature Branch**: `001-email-notifications`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "As a user I want to receive email notifications for my meetings so that I can get my meeting summary delivered to my inbox when processing completes, and be notified if processing fails"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Meeting Summary Delivered by Email (Priority: P1)

When a meeting finishes processing, the user receives an email containing the full meeting summary. The email is sent automatically — no user action required. The user can open the email from any device and read their summary without logging into the app.

**Why this priority**: This is the core value proposition — delivering the output passively to the user's inbox. It directly reduces friction by eliminating the need to check the app dashboard after every upload.

**Independent Test**: Upload a meeting file, wait for processing to complete, and verify the summary email arrives in the inbox with the correct title, date, and summary content.

**Acceptance Scenarios**:

1. **Given** a user has uploaded a meeting file, **When** all processing stages complete successfully, **Then** an email is sent to the user's registered address within 2 minutes containing the meeting title, processing date, and full summary content.
2. **Given** a meeting summary email has been sent, **When** the user opens it, **Then** the email is readable on mobile and desktop, displays the summary in a clear format, and includes a link back to the meeting in the app.
3. **Given** a user has no registered email address, **When** processing completes, **Then** no email is sent and no error is raised.

---

### User Story 2 - Processing Failure Notification (Priority: P2)

When meeting processing fails at any stage (download, transcription, or summarization), the user receives an email informing them that processing failed and what they can do next (retry, contact support).

**Why this priority**: Without failure notifications, users are left waiting indefinitely with no feedback — leading to support inquiries and churn.

**Independent Test**: Trigger a processing failure (e.g., upload a corrupt file), and verify the failure notification email arrives with the meeting identifier and a link to retry.

**Acceptance Scenarios**:

1. **Given** a meeting is being processed, **When** any pipeline stage fails, **Then** the user receives an email within 2 minutes informing them processing failed and suggesting they retry or contact support.
2. **Given** a failure email has been sent, **When** the user opens it, **Then** the email clearly identifies which meeting failed and provides a direct link to that meeting in the app.
3. **Given** processing fails and the failure notification email cannot be delivered, **Then** the failure is logged silently and the application does not crash.

---

### Edge Cases

- What happens when the email delivery service is unavailable? The application must not crash — email sending failure is handled gracefully and logged.
- What if a meeting is reprocessed after a previous failure? A new summary email is sent upon successful completion of the retry.
- What if the user's email address is invalid or bounces? The bounce is logged; no retry storm occurs.
- What if processing completes for a meeting with no transcript content (e.g., silent audio)? A summary email is still sent noting that no spoken content was detected.
- What if two processing completions fire for the same meeting simultaneously? Exactly one email is sent (idempotent delivery).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST send an email to the user's registered address when meeting processing completes successfully, containing the meeting summary.
- **FR-002**: System MUST send an email to the user's registered address when meeting processing fails at any stage.
- **FR-003**: Summary emails MUST include the meeting title (or uploaded filename if no title exists), processing completion date and time, full summary text, and a direct link to the meeting in the app.
- **FR-004**: Failure emails MUST include the meeting identifier, a human-readable description of what failed, and a direct link to the meeting in the app.
- **FR-005**: Email sending MUST be non-blocking — a failure to send an email must not cause the meeting processing pipeline to fail or raise an unhandled error.
- **FR-006**: The system MUST NOT send duplicate emails for the same processing event (idempotent delivery per meeting per event type).
- **FR-007**: Emails MUST only be sent to users with a valid, non-empty registered email address.
- **FR-008**: Email content MUST render correctly on both desktop and mobile email clients.
- **FR-009**: All email delivery attempts (success and failure) MUST be logged with the meeting ID and timestamp for observability.

### Key Entities

- **EmailNotification**: A triggered notification event — linked to a meeting, has a type (summary or failure), target email address, sent timestamp, and delivery status (sent, failed).
- **Meeting**: Existing entity — provides meeting title, owner, processing status, and summary text used to populate email content.
- **User**: Existing entity — provides the recipient email address via the authentication system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive the summary email within 2 minutes of meeting processing completing successfully.
- **SC-002**: Users receive the failure notification email within 2 minutes of a processing stage failing.
- **SC-003**: Email sending failures do not affect the meeting processing pipeline success rate — the pipeline error rate is unchanged.
- **SC-004**: 100% of successfully processed meetings where the user has a registered email result in exactly one summary email (no duplicates, no omissions).
- **SC-005**: Both email types render without layout or content issues in Gmail, Outlook, and Apple Mail.

## Assumptions

- The user's email address is obtained from the existing authentication system — no new email capture UI is required.
- Email opt-out and unsubscribe controls are out of scope for this version.
- Email branding follows Zabt's existing visual identity; exact design detail is an implementation concern.
- A single template per notification type (summary, failure) — no per-user email template customization.
- Meeting title defaults to the uploaded filename if no user-provided title exists.
- The app URL used in email links is read from existing environment configuration.
- No email scheduling, batching, or digest features — each event triggers an immediate email.
- Email delivery is fire-and-forget from the pipeline's perspective; no retry logic for failed deliveries in this version.
