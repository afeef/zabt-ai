# Implementation Plan: Product & Web Analytics

**Branch**: `001-product-analytics` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-product-analytics/spec.md`

## Summary

Integrate PostHog Cloud for automatic pageview/session tracking (frontend) and named product event tracking (frontend + backend Celery worker). Users are identified by their Supabase user ID. No new database tables or API endpoints are required. Changes touch: Next.js root layout, two new provider/component files, a new `analytics.py` backend service module, `worker.py` Celery task completions, and `pyproject.toml`.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend)
**Primary Dependencies**:
- Frontend new: `posthog-js` (npm)
- Backend new: `posthog` (PyPI, added to base `[project.dependencies]`)
**Storage**: N/A — all analytics data lives in PostHog Cloud
**Testing**: pytest (backend unit), Playwright/Python (E2E — N/A for this feature, see Constitution Check)
**Target Platform**: Linux server (backend), Browser (frontend via Next.js 16 App Router)
**Project Type**: Web application (Next.js frontend + FastAPI backend + Celery workers)
**Performance Goals**: Analytics calls must be non-blocking; zero impact on page load time or API response time
**Constraints**: PostHog SDK fires asynchronously; `shutdown()` required before Celery/FastAPI process exit to flush buffered events
**Scale/Scope**: PostHog Cloud free tier (1M events/month); integration touches ~6 files

## Constitution Check

| Gate | Applies | Status | Notes |
|------|---------|--------|-------|
| Design System | No | N/A | No UI changes — analytics is invisible to users |
| API Contract | No | N/A | No new or modified API endpoints |
| Auth/Security | Yes | PASS | PostHog project API key stored in env vars; documented in quickstart.md; browser-safe key (`NEXT_PUBLIC_`) is safe to expose (ingestion only) |
| Env Config | Yes | PASS | 4 new vars: `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`, `POSTHOG_API_KEY`, `POSTHOG_HOST` — all documented in quickstart.md |
| Scope Boundary | Yes | PASS | Implementation limited to analytics instrumentation; no feature additions |
| E2E Testing | No | N/A | Analytics tracking produces no user-visible output; no visual flow to test. Existing E2E suite covers non-regression (any SDK crash would break existing tests) |
| Repository Pattern | No | N/A | No database access in this feature |
| CLI/Typer | No | N/A | No CLI commands added |
| Provider Abstraction | Partial | JUSTIFIED | Analytics is infrastructure telemetry, not a transcription/LLM/storage provider. Thin wrapper module (`analytics.py`) provides sufficient decoupling — consuming code never imports `posthog` directly. See research.md Decision 5. |
| Cost Awareness | No | N/A | PostHog Cloud free tier; no paid API calls |
| Migration Safety | No | N/A | No existing provider being replaced |

## Project Structure

### Documentation (this feature)

```text
specs/001-product-analytics/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── contracts/
│   └── events.md        ← Phase 1 output (event catalog)
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend-2/
├── app/
│   ├── layout.tsx                         (modify — wrap with PHProvider + PostHogPageView)
│   ├── providers/
│   │   └── posthog-provider.tsx           (new — PHProvider client component)
│   └── components/
│       └── posthog-pageview.tsx           (new — route-change pageview tracker)
└── package.json                           (modify — add posthog-js)

backend/
├── app/
│   ├── services/
│   │   └── analytics.py                   (new — PostHog singleton wrapper)
│   ├── main.py                            (modify — posthog.shutdown() in lifespan)
│   └── worker.py                          (modify — capture events + worker_shutdown signal)
└── pyproject.toml                         (modify — add posthog to [project.dependencies])

.env                                       (modify — add POSTHOG_* vars)
docker-compose.yml                         (modify — forward POSTHOG_* vars to api/worker/web)
```

**Structure Decision**: Web application layout (Option 2). Frontend changes are minimal (2 new files + 1 layout modification). Backend changes are additive (1 new service file + modifications to existing entry points).

## Implementation Details

### Frontend: PostHog Provider

`frontend-2/app/providers/posthog-provider.tsx` — client component:
```typescript
'use client'
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'
import { useEffect } from 'react'

export function PHProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
      capture_pageview: false,  // Manual pageview via PostHogPageView
      capture_pageleave: true,
    })
  }, [])
  return <PostHogProvider client={posthog}>{children}</PostHogProvider>
}
```

### Frontend: Pageview Component

`frontend-2/app/components/posthog-pageview.tsx` — client component:
```typescript
'use client'
import { useEffect } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import { usePostHog } from 'posthog-js/react'

export function PostHogPageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const posthog = usePostHog()
  useEffect(() => {
    if (posthog) {
      const url = window.location.origin + pathname +
        (searchParams.toString() ? '?' + searchParams.toString() : '')
      posthog.capture('$pageview', { $current_url: url })
    }
  }, [pathname, searchParams, posthog])
  return null
}
```

### Frontend: Root Layout

`frontend-2/app/layout.tsx` — wrap existing content:
```tsx
import { PHProvider } from '@/app/providers/posthog-provider'
import { PostHogPageView } from '@/app/components/posthog-pageview'
import { Suspense } from 'react'

// Inside <body>:
<PHProvider>
  <Suspense fallback={null}>
    <PostHogPageView />
  </Suspense>
  {/* existing children */}
</PHProvider>
```

### Frontend: User Identification

In the dashboard layout component (wherever `onAuthStateChange` or session check occurs), add:
```typescript
import { usePostHog } from 'posthog-js/react'
const posthog = usePostHog()
// After confirming user session:
posthog.identify(user.id, { email: user.email })
```

### Frontend: Named Event — upload_completed

In the upload handler (after successful upload response):
```typescript
posthog.capture('upload_completed', {
  file_size_tier: getFileSizeTier(file.size),  // 'small'|'medium'|'large'
  file_type: file.type,
})
```

### Frontend: Named Event — summary_viewed / summary_exported

In the summary tab component and PDF export handler:
```typescript
posthog.capture('summary_viewed', { meeting_id: meetingId })
posthog.capture('summary_exported', { meeting_id: meetingId })
```

### Backend: Analytics Service

`backend/app/services/analytics.py`:
```python
import posthog as ph
from app.core.config import settings

ph.api_key = settings.POSTHOG_API_KEY
ph.host = settings.POSTHOG_HOST

def capture(user_id: str | int, event: str, properties: dict | None = None) -> None:
    """Fire a server-side analytics event. Fails silently if PostHog is unavailable."""
    try:
        ph.capture(str(user_id), event, properties or {})
    except Exception:
        pass  # Analytics must never break application flow

def shutdown() -> None:
    ph.shutdown()
```

### Backend: Config additions

`backend/app/core/config.py` — add:
```python
POSTHOG_API_KEY: str = ""
POSTHOG_HOST: str = "https://us.i.posthog.com"
```

### Backend: FastAPI lifespan shutdown

`backend/app/main.py` — in `lifespan` context manager:
```python
from app.services.analytics import shutdown as analytics_shutdown
# In lifespan finally/after yield:
analytics_shutdown()
```

### Backend: Celery worker events

`backend/app/worker.py` additions:
```python
from celery.signals import worker_shutdown
from app.services import analytics

@worker_shutdown.connect
def flush_analytics(**kwargs):
    analytics.shutdown()

# Inside transcribe_and_diarize task, after saving segments:
analytics.capture(meeting.user_id, 'transcription_completed', {
    'meeting_id': meeting.id,
    'duration_tier': get_duration_tier(audio_duration_seconds),
})

# Inside summarize task, after saving summary:
analytics.capture(meeting.user_id, 'summary_generated', {
    'meeting_id': meeting.id,
    'template_id': template_id,
    'word_count_tier': get_word_count_tier(len(summary.split())),
})
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| No full Protocol abstraction for analytics (Constitution IX) | Analytics is infrastructure telemetry, not a swappable business-logic provider | Full Protocol/ABC overhead not justified for a thin fire-and-forget wrapper; `analytics.py` module provides sufficient isolation — swap requires only editing one file |
