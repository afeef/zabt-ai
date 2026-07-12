# Feature Specification: Owner Notifications via Telegram Bot

**Feature Branch**: `023-telegram-notifications`
**Created**: 2026-03-14
**Status**: Draft
**Input**: User description: "As the platform owner, I want to receive real-time Telegram notifications when key user events occur so that I have instant visibility into platform activity without checking dashboards."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Event Notifications (Priority: P1)

As the platform owner, I want to receive a Telegram message whenever a key event occurs on the platform — user login, file upload, transcription completed, summary generated, or PDF downloaded — so I can monitor activity in real time from my phone.

**Why this priority**: This is the core value of the feature. Without event notifications, the feature has no purpose.

**Independent Test**: Can be fully tested by triggering each event type (login, upload, transcribe, summarize, export) and verifying a Telegram message arrives with the correct event details within seconds.

**Acceptance Scenarios**:

1. **Given** a user logs in for the first time, **When** the login completes, **Then** the owner receives a Telegram message containing: event type ("New User"), user email, and timestamp.
2. **Given** a user logs in (returning user), **When** the login completes, **Then** the owner receives a Telegram message containing: event type ("User Login"), user email, and timestamp.
3. **Given** a user uploads an audio file, **When** the upload is confirmed and processing begins, **Then** the owner receives a Telegram message containing: event type ("Upload Started"), user email, meeting title, and timestamp.
4. **Given** a transcription completes, **When** the Celery task finishes, **Then** the owner receives a Telegram message containing: event type ("Transcription Completed"), user email, meeting title, audio duration, and timestamp.
5. **Given** a summary is generated, **When** the summarize task finishes, **Then** the owner receives a Telegram message containing: event type ("Summary Generated"), user email, meeting title, and timestamp.
6. **Given** a user downloads a PDF, **When** the export endpoint responds, **Then** the owner receives a Telegram message containing: event type ("PDF Downloaded"), user email, meeting title, PDF type (summary/transcript), and timestamp.

---

### User Story 2 - Notification Provider Extensibility (Priority: P2)

As a developer, I want the notification system to use a provider abstraction so that new channels (WhatsApp, Slack, email) can be added in the future without modifying event-firing code.

**Why this priority**: Ensures the architecture supports future channels without refactoring, but the feature delivers value with Telegram alone.

**Independent Test**: Can be tested by implementing a mock/test provider alongside Telegram and verifying both receive events when configured.

**Acceptance Scenarios**:

1. **Given** the notification system is implemented, **When** a new provider is added, **Then** only a new provider class and env var configuration are required — no changes to event-firing code.
2. **Given** the Telegram bot token or chat ID is not configured, **When** an event fires, **Then** the notification is silently skipped (no errors, no crashes).

---

### User Story 3 - Non-blocking Delivery (Priority: P1)

As a platform user, I want notifications to never slow down or break my experience — notifications must be sent asynchronously and failures must be silently handled.

**Why this priority**: Critical for reliability. A Telegram API outage must never break uploads, transcriptions, or any user-facing flow.

**Independent Test**: Can be tested by disabling the Telegram bot token and verifying all user flows (upload, transcribe, export) complete normally without errors.

**Acceptance Scenarios**:

1. **Given** the Telegram API is unreachable, **When** a notification event fires, **Then** the user's request completes normally and the failure is logged but not raised.
2. **Given** an event fires during a Celery task, **When** the notification is dispatched, **Then** the Celery task does not wait for the Telegram response before proceeding.

---

### Edge Cases

- What happens when `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is not set? Notifications are silently disabled; no errors logged at event time (a single warning at startup is acceptable).
- What happens when the Telegram API rate-limits the bot? The notification is dropped and a warning is logged. No retry queue — notifications are best-effort.
- What happens when a user has no email (e.g., first-time OAuth before profile sync)? Display the user's Supabase ID as fallback identifier.
- What happens during high-volume batch processing (e.g., 50 uploads)? Each event sends its own message — no batching or deduplication. Telegram's rate limit (~30 msgs/sec for bots) is well above expected volume.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST send a Telegram message to a configured chat when any of the following events occur: user login (new and returning), upload confirmed, transcription completed, summary generated, PDF exported.
- **FR-002**: Each notification message MUST include: event type emoji and label, user email (or Supabase ID fallback), meeting title (where applicable), and timestamp.
- **FR-003**: Notification dispatch MUST be asynchronous — it MUST NOT block or delay the triggering request or Celery task.
- **FR-004**: System MUST silently skip notifications when Telegram credentials are not configured (no errors, no crashes).
- **FR-005**: System MUST handle Telegram API failures gracefully — log warnings but never raise exceptions to the caller.
- **FR-006**: System MUST use a provider abstraction (protocol/interface) so that new notification channels can be added without modifying event-firing code.
- **FR-007**: Telegram bot token and chat ID MUST be configurable via environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).

### Key Entities

- **NotificationEvent**: Represents an event to be notified — includes event type, user identifier, optional meeting context, and timestamp.
- **NotificationProvider**: Abstraction for a delivery channel (Telegram, future: WhatsApp, Slack). Receives a NotificationEvent and delivers it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Owner receives a Telegram notification within 5 seconds of each tracked event occurring.
- **SC-002**: Zero user-facing errors or latency increase when notifications are enabled — all existing flows behave identically with or without the feature.
- **SC-003**: Zero user-facing errors when Telegram credentials are missing or the Telegram API is down — the system degrades gracefully.
- **SC-004**: Adding a new notification channel requires only a new provider class and env var configuration — no changes to existing event-firing code.

## Assumptions

- The platform owner will create a Telegram bot via BotFather and obtain the bot token and chat ID before deployment.
- Notifications are one-way (bot → owner). No interactive bot commands or responses are needed.
- Message volume is low (< 100/day at current scale), well within Telegram Bot API limits.
- Notifications are best-effort — no persistence, no retry queue, no delivery guarantees.
- Only one recipient (the owner's chat ID) is supported. Multi-recipient or per-user notifications are out of scope.
