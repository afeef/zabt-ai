# Implementation Plan: Email Notifications

**Branch**: `001-email-notifications` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-email-notifications/spec.md`

---

## Summary

Add automated transactional email notifications to the Zabt backend using Resend. When meeting processing completes, the pipeline sends the user a summary email. When processing fails, it sends a failure notification. Email sending is fire-and-forget — failure never affects the processing pipeline. The `EmailProvider` Protocol satisfies Constitution Principle IX (Provider Abstraction). No new database tables, no new API endpoints, no frontend changes.

---

## Technical Context

**Language/Version**: Python 3.11 (backend only — no frontend changes)
**Primary Dependencies**: Resend Python SDK v2.x (`resend` package), FastAPI, Celery 5.6+, SQLModel (unchanged)
**Storage**: PostgreSQL via SQLModel (unchanged — no new tables)
**Testing**: No automated tests (validated via Resend dashboard and inbox inspection — see quickstart.md)
**Target Platform**: Linux (Docker Compose local, Cloudflare tunnel for external access)
**Performance Goals**: Email delivered within 2 minutes of pipeline event (SC-001, SC-002)
**Constraints**: Fail-silent — `RESEND_API_KEY` absent must not crash the app; empty key triggers no-op mode
**Scale/Scope**: Single developer; Resend free tier (100 emails/day); 5 files modified, 1 new file

---

## Constitution Check

| Gate | Applies | Status | Notes |
|------|---------|--------|-------|
| Design System | No UI changes | SKIP | Backend-only |
| API Contract | No new endpoints | SKIP | Email triggered from worker, not API |
| Auth/Security | New env vars | PASS | `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_URL` documented in quickstart.md; never hardcoded |
| Env Config | 3 new env vars | PASS | Listed in quickstart.md; added to docker-compose.yml |
| Scope Boundary | Backend email service only | PASS | No frontend, no new endpoints, no new DB tables |
| E2E Testing | No browser-facing flow | SKIP | Email delivery verified via inbox inspection (see quickstart.md scenarios) |
| Repository Pattern | No new DB access | SKIP | No new entities; worker reads User/Meeting via existing services and sessions |
| CLI/Typer | No CLI changes | SKIP | |
| **Provider Abstraction** | Resend is external API | **PASS** | `EmailProvider` Protocol defined before `ResendEmailProvider` — see Implementation Details §1 |
| Cost Awareness | Resend free tier (100/day) | PASS | No significant cost; no paid API calls above free tier at current scale |
| Migration Safety | No existing provider | SKIP | |

---

## Complexity Tracking

> No constitution violations — no entries required.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-email-notifications/
├── plan.md          ← this file
├── research.md      ← Phase 0 output
├── quickstart.md    ← Phase 1 output
└── tasks.md         ← Phase 2 output (/speckit.tasks)
```

No `data-model.md` — no new database entities.
No `contracts/` directory — no new API endpoints.

### Source Code Changes

```text
backend/
├── pyproject.toml                        # Add resend>=2.0.0
├── app/
│   ├── core/
│   │   └── config.py                     # Add RESEND_API_KEY, RESEND_FROM_EMAIL, APP_URL settings
│   ├── services/
│   │   └── email.py                      # NEW: EmailProvider Protocol + ResendEmailProvider
│   └── worker.py                         # Call email_service in stage_summarize + on_stage_failure
.env                                      # Add RESEND_API_KEY, RESEND_FROM_EMAIL, APP_URL
docker-compose.yml                        # Add vars to api, worker, worker-gpu services
```

---

## Implementation Details

### 1. EmailProvider Protocol + ResendEmailProvider (`backend/app/services/email.py` — NEW)

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable
import resend
import logfire
from app.core.config import settings
from app.models import Meeting


# ── Abstract interface (satisfies Constitution Principle IX) ──────────────────

@runtime_checkable
class EmailProvider(Protocol):
    def send_summary_email(self, to: str, meeting: Meeting) -> None: ...
    def send_failure_email(self, to: str, meeting: Meeting, error: str) -> None: ...


# ── Concrete implementation ───────────────────────────────────────────────────

class ResendEmailProvider:
    """Sends transactional emails via Resend. Fails silently if API key is absent."""

    def __init__(self, api_key: str, from_email: str, app_url: str) -> None:
        self._from_email = from_email
        self._app_url = app_url
        if api_key:
            resend.api_key = api_key
        self._enabled = bool(api_key)

    def send_summary_email(self, to: str, meeting: Meeting) -> None:
        if not self._enabled:
            logfire.info("email_skipped: no RESEND_API_KEY", meeting_id=meeting.id)
            return
        meeting_url = f"{self._app_url}/meetings/{meeting.id}"
        summary = meeting.summary_text or "No summary was generated."
        html = f"""
        <h2>Your meeting summary is ready</h2>
        <p><strong>{meeting.title}</strong></p>
        <hr/>
        <div style="white-space:pre-wrap">{summary}</div>
        <hr/>
        <p><a href="{meeting_url}">View in Zabt →</a></p>
        """
        try:
            resp = resend.Emails.send(
                {"from": self._from_email, "to": [to],
                 "subject": f"Summary: {meeting.title}", "html": html},
                options={"idempotency_key": f"meeting-{meeting.id}-summary"},
            )
            logfire.info("summary_email_sent", meeting_id=meeting.id, resend_id=resp["id"])
        except Exception:
            logfire.exception("summary_email_failed", meeting_id=meeting.id, to=to)

    def send_failure_email(self, to: str, meeting: Meeting, error: str) -> None:
        if not self._enabled:
            logfire.info("email_skipped: no RESEND_API_KEY", meeting_id=meeting.id)
            return
        meeting_url = f"{self._app_url}/meetings/{meeting.id}"
        html = f"""
        <h2>Processing failed for your meeting</h2>
        <p><strong>{meeting.title}</strong> could not be processed.</p>
        <p>You can retry from the meeting page or contact support.</p>
        <p><a href="{meeting_url}">View in Zabt →</a></p>
        """
        try:
            resp = resend.Emails.send(
                {"from": self._from_email, "to": [to],
                 "subject": f"Processing failed: {meeting.title}", "html": html},
                options={"idempotency_key": f"meeting-{meeting.id}-failure"},
            )
            logfire.info("failure_email_sent", meeting_id=meeting.id, resend_id=resp["id"])
        except Exception:
            logfire.exception("failure_email_failed", meeting_id=meeting.id, to=to)


# ── Singleton ─────────────────────────────────────────────────────────────────

email_service: EmailProvider = ResendEmailProvider(
    api_key=settings.RESEND_API_KEY,
    from_email=settings.RESEND_FROM_EMAIL,
    app_url=settings.APP_URL,
)
```

---

### 2. config.py — Add Three Settings

```python
# backend/app/core/config.py — add to Settings class:

# --- Email (Resend) ---
RESEND_API_KEY: str = ""
RESEND_FROM_EMAIL: str = "no-reply@zabt.ai"
APP_URL: str = "https://zabt.ai"
```

---

### 3. worker.py — Call email_service in stage_summarize

Add after `meeting_service.mark_completed(...)`, using the already-fetched `meeting` object:

```python
# Send summary email (fire-and-forget — never raises)
if meeting.owner_id:
    try:
        from app.services.email import email_service
        with Session(engine) as session:
            user = session.get(User, meeting.owner_id)
        if user and user.email:
            email_service.send_summary_email(user.email, meeting)
    except Exception:
        logfire.exception("stage_summarize email lookup failed", meeting_id=meeting_id)
```

---

### 4. worker.py — Call email_service in on_stage_failure

Add after `meeting_service.mark_failed(meeting_id, str(exc))`:

```python
# Send failure email (fire-and-forget — never raises)
try:
    from app.services.email import email_service
    failed_meeting = meeting_service.get(Meeting, meeting_id)
    if failed_meeting and failed_meeting.owner_id:
        with Session(engine) as session:
            user = session.get(User, failed_meeting.owner_id)
        if user and user.email:
            email_service.send_failure_email(user.email, failed_meeting, str(exc))
except Exception:
    logfire.exception("on_stage_failure email lookup failed", meeting_id=meeting_id)
```

---

### 5. .env — Add Placeholders

```env
# --- Email (Resend) ---
# Get your API key from resend.com → API Keys (starts with re_)
RESEND_API_KEY=
RESEND_FROM_EMAIL=no-reply@zabt.ai
APP_URL=https://zabt.ai
```

---

### 6. docker-compose.yml — Wire Env Vars

```yaml
# Add to api, worker, and worker-gpu environment sections:
- RESEND_API_KEY=${RESEND_API_KEY:-}
- RESEND_FROM_EMAIL=${RESEND_FROM_EMAIL:-no-reply@zabt.ai}
- APP_URL=${APP_URL:-https://zabt.ai}
```

---

## Implementation Strategy

**MVP (US1 — Summary Email)**:

1. T001: Add `resend>=2.0.0` to `backend/pyproject.toml`
2. T002: Add `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_URL` to `config.py`
3. T003 [P]: Add placeholders to `.env`
4. T004 [P]: Add env vars to `docker-compose.yml`
5. T005: Create `backend/app/services/email.py` (Protocol + ResendEmailProvider)
6. T006: Wire `email_service.send_summary_email()` into `stage_summarize` in `worker.py`
7. **STOP and VALIDATE**: Process a meeting → verify summary email arrives in inbox

**Full value (US2 — Failure Email)**:

8. T007: Wire `email_service.send_failure_email()` into `on_stage_failure` in `worker.py`
9. **VALIDATE**: Trigger a processing failure → verify failure email arrives
