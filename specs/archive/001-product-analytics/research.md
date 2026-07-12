# Research: Product & Web Analytics

**Branch**: `001-product-analytics` | **Date**: 2026-03-05

## Decision 1: Analytics Platform

**Decision**: PostHog Cloud (free tier, `us.i.posthog.com`)

**Rationale**: Agreed with user in prior discussion. PostHog provides pageviews, sessions, named events, user identity, and cohort analysis in a single platform. Free tier covers 1 million events/month — sufficient for current scale. No self-hosting overhead.

**Alternatives considered**:
- Self-hosted PostHog: Requires ClickHouse + Kafka + 8–10 GB RAM on a dedicated server. Eliminated — no dedicated server and no data-residency requirement.
- Mixpanel/Amplitude: Product analytics only, no web/session analytics. More expensive. Eliminated.
- Google Analytics 4: No product events API for backend. Privacy concerns. Eliminated.

---

## Decision 2: Frontend Integration Pattern (Next.js App Router)

**Decision**: `posthog-js` package + client-side `PHProvider` wrapping root layout + manual pageview via `usePathname` hook.

**Rationale**: Next.js App Router does not fire traditional page load events on client-side navigation. PostHog's `capture_pageview: false` init option disables the built-in auto-capture, and a dedicated `PostHogPageView` client component (using `usePathname` + `useEffect`) fires `$pageview` on every route change. A `<Suspense>` boundary is required around `PostHogPageView` to prevent hydration mismatches caused by `useSearchParams`.

**Key init options**:
```
capture_pageview: false   — manual pageview tracking for App Router
capture_pageleave: true   — track session exit signals
```

**Alternatives considered**:
- Auto pageview (`capture_pageview: true`): Only fires on full page reload, misses SPA navigation. Eliminated.
- `posthog/next` wrapper package: Not a distinct package; same `posthog-js` used. N/A.

---

## Decision 3: Backend Integration Pattern (FastAPI + Celery)

**Decision**: `posthog` (Python) package, singleton `Posthog` client initialized at module level in `backend/app/services/analytics.py`. Celery worker registers `worker_shutdown` signal to call `posthog.shutdown()`. FastAPI uses `lifespan` context manager for the same.

**Rationale**: PostHog Python SDK batches events in memory and flushes on a background thread. A singleton ensures one connection pool and consistent batching. `shutdown()` must be called before process exit to flush buffered events — critical for Celery workers which may be killed between task completions. Celery's `worker_shutdown` signal is the canonical hook.

**User ID availability in Celery tasks**: The `user_id` is passed as an argument to Celery tasks (already the pattern in `worker.py`), so it's always available for `distinct_id`.

**Alternatives considered**:
- Per-request PostHog client: Higher overhead, no batching benefit. Eliminated.
- Fire-and-forget HTTP calls directly: No retry, no batching, more code. Eliminated.

---

## Decision 4: Environment Variable Naming

**Decision**:

| Variable | Location | Purpose |
|----------|----------|---------|
| `NEXT_PUBLIC_POSTHOG_KEY` | Frontend (browser) | Project API key (phc_...) |
| `NEXT_PUBLIC_POSTHOG_HOST` | Frontend (browser) | PostHog ingest host |
| `POSTHOG_API_KEY` | Backend (server) | Same project API key |
| `POSTHOG_HOST` | Backend (server) | Same ingest host |

**Rationale**: `NEXT_PUBLIC_` prefix required for Next.js to expose env vars to the browser bundle. The same PostHog project API key is used for both client and server — PostHog uses the key for event ingestion, not server-to-server API calls.

**Note**: The PostHog project API key (used for ingestion) is safe to expose in the browser. It is distinct from the PostHog Personal API Key (used for management API calls), which must never be exposed.

---

## Decision 5: Provider Abstraction (Constitution Gate IX)

**Decision**: Thin wrapper module (`analytics.py`) exposes a simple `capture(user_id, event, properties)` function. No full Protocol/ABC abstraction required at this stage.

**Rationale**: Constitution Principle IX applies to "transcription, LLM summarization, storage" providers — external API integrations where provider-swapping is a realistic concern. Analytics is infrastructure telemetry; swapping analytics vendors is an infrequent, low-risk migration. A thin wrapper module (not a direct SDK call in business logic) provides sufficient decoupling without over-engineering.

**Complexity tracking note**: This is a justified deviation from full Protocol abstraction. The wrapper means consuming code never imports `posthog` directly — SDK swap requires only changing `analytics.py`.

---

## Decision 6: E2E Testing Scope

**Decision**: No dedicated E2E test for analytics tracking. Analytics events are invisible to users and do not affect any visual flow.

**Rationale**: Constitution Principle VI requires E2E tests for "user-facing flows." Analytics is a pure side-effect with no visual output. Verifying PostHog receives events would require calling the PostHog API — this is integration testing of a third-party service, outside the scope of this codebase's E2E suite. The non-breakage guarantee is provided by the existing E2E suite: if analytics init crashes the app, all existing E2E tests will fail.

---

## Decision 7: URL Rewriting / Ad Blocker Bypass

**Decision**: Not implemented at this stage.

**Rationale**: The spec requires ≥95% capture rate "accounting for ad blockers." For an internal/B2B tool with a small known user base, ad blocker prevalence is expected to be low. URL rewriting adds complexity (Next.js rewrites config + Cloudflare routing considerations). Deferred until capture rate data shows a meaningful gap.
