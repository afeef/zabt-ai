# Analytics Event Catalog

**Feature**: `001-product-analytics` | **Date**: 2026-03-05

This document defines the canonical schema for all analytics events fired by the application. Both frontend (browser) and backend (server) events MUST conform to these schemas.

---

## Standard Properties (all events)

Every event automatically includes these properties via the PostHog SDK:

| Property | Source | Description |
|----------|--------|-------------|
| `distinct_id` | SDK | User ID (authenticated) or anonymous ID |
| `$session_id` | SDK | Session identifier |
| `timestamp` | SDK | ISO 8601 UTC timestamp |
| `$lib` | SDK | `posthog-js` (frontend) or `posthog-python` (backend) |

---

## Pageview Events (frontend, automatic)

### `$pageview`

**Fired by**: `PostHogPageView` component on every route change
**Origin**: Frontend

| Property | Type | Description |
|----------|------|-------------|
| `$current_url` | string | Full URL including query string |

---

## Product Events

### `upload_completed`

**Fired when**: A meeting recording upload finishes successfully
**Origin**: Frontend (on upload success response)

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `file_size_tier` | string | `small` (<10MB), `medium` (10–100MB), `large` (>100MB) | Bucketed file size |
| `file_type` | string | `video/mp4`, `audio/mpeg`, etc. | MIME type |

---

### `transcription_completed`

**Fired when**: Celery worker finishes transcribing a meeting
**Origin**: Backend (Celery worker)

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `duration_tier` | string | `short` (<10min), `medium` (10–60min), `long` (>60min) | Bucketed audio duration |
| `meeting_id` | integer | — | Meeting database ID |

---

### `summary_generated`

**Fired when**: Celery worker finishes generating a meeting summary
**Origin**: Backend (Celery worker)

| Property | Type | Values | Description |
|----------|------|--------|-------------|
| `template_id` | integer \| null | — | Summary template used (`null` = default) |
| `word_count_tier` | string | `short` (<200), `medium` (200–500), `long` (>500) | Bucketed summary length |
| `meeting_id` | integer | — | Meeting database ID |

---

### `summary_viewed`

**Fired when**: User opens the summary tab on a meeting detail page
**Origin**: Frontend

| Property | Type | Description |
|----------|------|-------------|
| `meeting_id` | integer | Meeting database ID |

---

### `summary_exported`

**Fired when**: User downloads a meeting summary as PDF
**Origin**: Frontend

| Property | Type | Description |
|----------|------|-------------|
| `meeting_id` | integer | Meeting database ID |

---

### `user_signed_up`

**Fired when**: A new user account is created (via Supabase auth webhook or post-login check)
**Origin**: Frontend (first sign-in detection)

| Property | Type | Description |
|----------|------|-------------|
| `signup_date` | string | ISO 8601 date (for cohort analysis) |

---

## Identity Events

### `posthog.identify()` call

**Fired when**: User signs in (authenticated session begins)
**Origin**: Frontend

| Parameter | Value |
|-----------|-------|
| `distinctId` | Supabase user UUID |
| `properties.email` | User email address |

> **Note**: The `identify()` call is not an event — it links the anonymous ID to the authenticated user ID and sets person properties. It must be called once per sign-in, after the Supabase session is established.
