# Research: Email Notifications

**Feature**: 001-email-notifications
**Date**: 2026-03-05
**Status**: Complete

---

## Decision 1: Email Delivery Provider — Resend

**Decision**: Use Resend (`resend` Python SDK v2.23.0+) as the transactional email provider.

**Rationale**: Resend has a dead-simple Python SDK, excellent deliverability, and a free tier (100 emails/day) sufficient for early-stage use. The SDK initialization is a single `resend.api_key = ...` module-level assignment — no client class instantiation. `resend.Emails.send(params)` raises typed exceptions on failure, which integrates cleanly with the existing logfire exception logging pattern.

**Alternatives considered**: SendGrid (heavier SDK, more complex setup), Postmark (no free tier), AWS SES (requires AWS credentials, more infra overhead), SMTP directly (no deliverability guarantees, no bounce handling).

---

## Decision 2: Provider Abstraction — EmailProvider Protocol (Constitution Principle IX)

**Decision**: Define an `EmailProvider` Protocol in `backend/app/services/email.py` before implementing `ResendEmailProvider`. All worker code will call the abstract interface, not the Resend SDK directly.

**Rationale**: Constitution Principle IX is non-negotiable — external API integrations must be behind abstract interfaces. Practically, this lets us test with a `MockEmailProvider` and swap to a different provider with zero worker changes.

```python
from typing import Protocol
from app.models import Meeting

class EmailProvider(Protocol):
    def send_summary_email(self, to: str, meeting: Meeting) -> None: ...
    def send_failure_email(self, to: str, meeting: Meeting, error: str) -> None: ...
```

**Alternatives considered**: Skipping abstraction (constitution violation, rejected).

---

## Decision 3: Idempotency — Resend Idempotency Key Header

**Decision**: Use Resend's built-in `idempotency_key` option with the key pattern `meeting-{meeting_id}-summary` and `meeting-{meeting_id}-failure`. No `EmailNotification` database table required.

**Rationale**: Resend deduplicates sends server-side when the same `idempotency_key` is submitted within a window. This satisfies FR-006 without a migration. Combined with logfire logging (FR-009), there is no need for a new DB entity.

```python
resend.Emails.send(
    params,
    options={"idempotency_key": f"meeting-{meeting_id}-summary"}
)
```

**Alternatives considered**: `EmailNotification` DB table with a unique constraint on `(meeting_id, event_type)` — rejected as unnecessary complexity for fire-and-forget delivery with no retry logic.

---

## Decision 4: Trigger Points — Worker Tasks

**Decision**: Trigger emails directly from `stage_summarize` (success) and `on_stage_failure` (failure) in `backend/app/worker.py`.

**Rationale**: Both trigger points already have access to `meeting_id` and the full meeting object. `stage_summarize` fires after `mark_completed()`, so the summary text is available. `on_stage_failure` fires after `mark_failed()` and has the exception message. Both calls are wrapped in try/except so email failure never propagates to the pipeline.

**Key finding from codebase**: `on_stage_failure` receives `meeting_id = request.args[0]`. The user email must be looked up via a `Session(engine)` query using `meeting.owner_id`. The `User.email` field exists (`str`, unique, indexed) in `backend/app/models.py`.

---

## Decision 5: Email Content — Inline HTML, No Template Engine

**Decision**: Build HTML email content with inline Python f-strings. No Jinja2 or external template engine.

**Rationale**: Two email types with predictable, stable content. A template engine adds a dependency for minimal benefit at this stage. Email HTML is inherently simple (no complex conditionals). If the templates grow complex in future, Jinja2 can be added incrementally.

---

## Decision 6: Fail-Silent Implementation

**Decision**: Wrap all Resend calls with `try/except Exception`. Log failures with `logfire.exception()`. Never re-raise.

**Rationale**: FR-005 is absolute — email failure must never affect the processing pipeline. The pipeline is the primary user-facing product; email is supplementary. This matches the existing pattern from PostHog analytics (`analytics.capture()` is also fire-and-forget).

---

## Decision 7: App URL for Email Links

**Decision**: Read the frontend app URL from an existing or new `APP_URL` environment variable (e.g., `https://zabt.ai`). Meeting deep-link: `{APP_URL}/meetings/{meeting_id}`.

**Rationale**: The URL is already in `.env` as `NEXT_PUBLIC_FRONTEND_URL`. Add `APP_URL` (backend-readable) pointing to the same value. The backend cannot read `NEXT_PUBLIC_*` vars — they are Next.js public vars and not passed to the API/worker containers.

---

## Key Integration Points

| File | Change |
|------|--------|
| `backend/pyproject.toml` | Add `resend>=2.0.0` |
| `backend/app/core/config.py` | Add `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_URL` |
| `backend/app/services/email.py` | NEW: `EmailProvider` Protocol + `ResendEmailProvider` + `email_service` singleton |
| `backend/app/worker.py` | Call `email_service` in `stage_summarize` and `on_stage_failure` |
| `.env` | Add `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_URL` |
| `docker-compose.yml` | Add env vars to `api`, `worker`, `worker-gpu` |
