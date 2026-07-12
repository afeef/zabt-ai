# Quickstart: Product & Web Analytics

**Branch**: `001-product-analytics` | **Date**: 2026-03-05

## Prerequisites

1. A PostHog Cloud account at https://posthog.com — free tier (1M events/month)
2. A PostHog **Project API Key** (starts with `phc_`) — found in Project Settings → Project API Key

## Environment Variables

### `.env` (root — passed to docker-compose)

```env
# --- PostHog Analytics ---
POSTHOG_API_KEY=phc_your_project_api_key_here
POSTHOG_HOST=https://us.i.posthog.com
NEXT_PUBLIC_POSTHOG_KEY=phc_your_project_api_key_here
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
```

> **Note**: `NEXT_PUBLIC_POSTHOG_KEY` and `POSTHOG_API_KEY` use the **same** project API key. The `NEXT_PUBLIC_` prefix makes it available in the browser bundle. The PostHog project API key is safe to expose in the browser — it is used for event ingestion only.

### Backend `docker-compose.yml` additions

The following vars must be forwarded to the `api` and `worker`/`worker-gpu` services:

```yaml
- POSTHOG_API_KEY=${POSTHOG_API_KEY}
- POSTHOG_HOST=${POSTHOG_HOST:-https://us.i.posthog.com}
```

### Frontend `docker-compose.yml` additions

```yaml
- NEXT_PUBLIC_POSTHOG_KEY=${NEXT_PUBLIC_POSTHOG_KEY}
- NEXT_PUBLIC_POSTHOG_HOST=${NEXT_PUBLIC_POSTHOG_HOST:-https://us.i.posthog.com}
```

## Validation Scenarios

### Scenario 1: Pageview tracking

1. Open the application in a browser (signed in or not)
2. Navigate between pages (e.g., Dashboard → a meeting detail → back)
3. In PostHog → Activity → Live Events: verify `$pageview` events appear within 60 seconds with correct `$current_url` values

### Scenario 2: Named event — upload completed

1. Sign in and upload a meeting recording
2. In PostHog → Activity → Live Events: verify `upload_completed` event appears with `file_size_tier` and `file_type` properties

### Scenario 3: Named event — transcription completed

1. Let a meeting finish transcription (Celery worker)
2. In PostHog → Activity → Live Events: verify `transcription_completed` event appears with `duration_tier` property and the correct `distinct_id` (user ID)

### Scenario 4: User identity

1. Sign in as a known user
2. In PostHog → Persons: search for the user's ID
3. Verify their pageviews and events appear under a single person profile

### Scenario 5: Silent failure

1. Set `NEXT_PUBLIC_POSTHOG_KEY` to an invalid value
2. Reload the application
3. Verify: no UI errors appear, all application features continue to function normally

## PostHog Dashboard Setup (after first events arrive)

Recommended dashboards to create:
- **Engagement funnel**: `upload_completed` → `transcription_completed` → `summary_generated` → `summary_viewed`
- **Retention**: Weekly cohort retention chart (built-in)
- **Power users**: Top 10 users by `upload_completed` event count
