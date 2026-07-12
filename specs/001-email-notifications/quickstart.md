# Quickstart: Email Notifications

**Feature**: 001-email-notifications
**Platform**: Resend (resend.com)

---

## Prerequisites

1. Create a Resend account at [resend.com](https://resend.com)
2. Verify your sending domain (e.g., `zabt.ai`) in **Resend → Domains**
3. Create an API key in **Resend → API Keys**
4. Copy the key (starts with `re_...`)

> **Development shortcut**: Before domain verification, you can send to `delivered@resend.dev` using `onboarding@resend.dev` as the sender. The email will be accepted but not actually delivered to an inbox — useful for smoke testing the integration.

---

## Environment Variables

Add to `.env` (root) and to deployment secrets for the backend:

```env
# --- Email (Resend) ---
RESEND_API_KEY=re_<your-api-key-here>
RESEND_FROM_EMAIL=no-reply@zabt.ai
APP_URL=https://zabt.ai
```

| Variable | Description | Required |
|---|---|---|
| `RESEND_API_KEY` | Resend write API key (starts with `re_`) | Yes (production) |
| `RESEND_FROM_EMAIL` | Verified sender address | Yes |
| `APP_URL` | Frontend base URL used for meeting deep-links in emails | Yes |

When `RESEND_API_KEY` is empty, email sending is skipped silently — the app continues normally.

---

## Docker Compose Wiring

The following services receive email env vars in `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      RESEND_API_KEY: ${RESEND_API_KEY:-}
      RESEND_FROM_EMAIL: ${RESEND_FROM_EMAIL:-}
      APP_URL: ${APP_URL:-}

  worker:
    environment:
      RESEND_API_KEY: ${RESEND_API_KEY:-}
      RESEND_FROM_EMAIL: ${RESEND_FROM_EMAIL:-}
      APP_URL: ${APP_URL:-}

  worker-gpu:
    environment:
      RESEND_API_KEY: ${RESEND_API_KEY:-}
      RESEND_FROM_EMAIL: ${RESEND_FROM_EMAIL:-}
      APP_URL: ${APP_URL:-}
```

---

## Validation Scenarios

### Scenario 1: Summary email sent on processing completion

1. Upload a meeting file via the frontend
2. Wait for the 3-stage pipeline to complete (status → `completed`)
3. ✅ Check the inbox of the authenticated user — a summary email should arrive within 2 minutes
4. ✅ Email contains the meeting title, completion date, full summary, and a link to the meeting

### Scenario 2: Failure email sent when processing fails

1. Upload a malformed or empty audio file to trigger a pipeline failure
2. ✅ Check the inbox — a failure notification should arrive within 2 minutes
3. ✅ Email identifies the meeting and provides a direct link to retry

### Scenario 3: No email sent when API key is absent

1. Remove `RESEND_API_KEY` from `.env` and restart the backend
2. Upload and process a meeting file
3. ✅ The pipeline completes normally (no error thrown)
4. ✅ No email is sent; a log entry notes the skip

### Scenario 4: Duplicate emails not sent on retry

1. Process a meeting that has already been processed (reprocessing scenario)
2. ✅ Only one summary email arrives — the Resend idempotency key prevents a duplicate

---

## Development Without a Real API Key

When `RESEND_API_KEY` is not set or empty, the `ResendEmailProvider` logs a message and returns immediately. No API call is made. The app functions normally.

To test actual email delivery without a verified domain:
- Set `RESEND_FROM_EMAIL=onboarding@resend.dev`
- Set recipient to `delivered@resend.dev` — accepts delivery silently (good for smoke tests)
