# Tasks: Product & Web Analytics

**Input**: Design documents from `/specs/001-product-analytics/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/events.md ✓, quickstart.md ✓

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Dependencies)

**Purpose**: Install new packages in frontend and backend before any implementation begins.

- [X] T001 [P] Add `posthog-js` to `frontend-2/package.json` dependencies and run `npm install` in `frontend-2/`
- [X] T002 [P] Add `posthog>=3.0` to `[project.dependencies]` in `backend/pyproject.toml` and run `uv sync` in `backend/`

---

## Phase 2: Foundational (Analytics Service + Environment)

**Purpose**: Core analytics infrastructure that ALL user stories depend on — must be complete before any instrumentation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add `POSTHOG_API_KEY: str = ""` and `POSTHOG_HOST: str = "https://us.i.posthog.com"` to the Settings class in `backend/app/core/config.py`
- [X] T004 Create `backend/app/services/analytics.py` — PostHog singleton wrapper with `capture(user_id, event, properties)` and `shutdown()` functions; set `ph.api_key` and `ph.host` from settings; wrap all calls in try/except to fail silently (see plan.md Implementation Details)
- [X] T005 [P] Add `POSTHOG_API_KEY`, `POSTHOG_HOST`, `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` vars to `.env` with placeholder values and inline comments per `quickstart.md`
- [X] T006 Forward `POSTHOG_API_KEY` and `POSTHOG_HOST` env vars to `api`, `worker`, and `worker-gpu` services; forward `NEXT_PUBLIC_POSTHOG_KEY` and `NEXT_PUBLIC_POSTHOG_HOST` to `web` service in `docker-compose.yml`
- [X] T007 Add `analytics.shutdown()` call (import from `app.services.analytics`) in the FastAPI lifespan shutdown handler in `backend/app/main.py`
- [X] T008 Register `worker_shutdown` Celery signal handler calling `analytics.shutdown()` at the top of `backend/app/worker.py` (after existing imports)

**Checkpoint**: Analytics service is wired up and env vars are configured. No events fire yet — user story implementation can now begin.

---

## Phase 3: User Story 1 — Page & Session Tracking (Priority: P1) 🎯 MVP

**Goal**: Every page load in the Next.js app fires a `$pageview` event automatically — zero per-page instrumentation needed.

**Independent Test**: Open the app, navigate between pages, open PostHog → Activity → Live Events, confirm `$pageview` events with correct `$current_url` appear within 60 seconds.

- [X] T009 [US1] Create `frontend-2/app/providers/posthog-provider.tsx` — `'use client'` component that initialises `posthog.init()` in `useEffect` with `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST`, `capture_pageview: false`, `capture_pageleave: true`, and returns `<PostHogProvider client={posthog}>{children}</PostHogProvider>` (see plan.md Implementation Details)
- [X] T010 [US1] Create `frontend-2/app/components/posthog-pageview.tsx` — `'use client'` component that uses `usePathname`, `useSearchParams`, and `usePostHog` to fire `posthog.capture('$pageview', { $current_url })` in a `useEffect` on every route change (see plan.md Implementation Details)
- [X] T011 [US1] Modify `frontend-2/app/layout.tsx` to wrap the existing body content with `<PHProvider>` (from `posthog-provider.tsx`) and render `<Suspense fallback={null}><PostHogPageView /></Suspense>` inside the provider, above children

**Checkpoint**: P1 complete. Every page navigation fires `$pageview`. Verify in PostHog Live Events.

---

## Phase 4: User Story 2 — Key Product Event Tracking (Priority: P2)

**Goal**: Six named events are captured for the core product workflow: upload → transcription → summary → view → export.

**Independent Test**: Perform each action once (upload a file, wait for transcription, view the summary, export as PDF). Verify all 6 named events appear in PostHog with correct properties per `contracts/events.md`.

- [X] T012 [P] [US2] Fire `upload_completed` event in `frontend-2/app/components/upload-modal.tsx` — after the successful `axios.put(presignedData.upload_url, ...)` call (step 3), call `posthog.capture('upload_completed', { file_size_tier: getFileSizeTier(item.file.size), file_type: item.file.type })` where `getFileSizeTier` returns `'small'`/`'medium'`/`'large'` per `contracts/events.md`; add helper function in the same file
- [X] T013 [P] [US2] Fire `summary_viewed` event in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — detect when the summary tab becomes active (e.g. when summary content is rendered / tab state changes) and call `posthog.capture('summary_viewed', { meeting_id: meeting.id })` using `usePostHog()`
- [X] T014 [P] [US2] Fire `summary_exported` event in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — in the `onDownloadPdf` handler (called via `exportSummaryAsPDF`), call `posthog.capture('summary_exported', { meeting_id: meeting.id })` using `usePostHog()` before or after the export call
- [X] T015 [P] [US2] Fire `transcription_completed` in `backend/app/worker.py` — at the end of `stage_transcribe` (after `meeting_service.update_status` and before `return meeting_id`), call `analytics.capture(meeting.owner_id, 'transcription_completed', { 'meeting_id': meeting_id, 'duration_tier': get_duration_tier(audio_duration_seconds) })`; add `get_duration_tier` helper returning `'short'`/`'medium'`/`'long'` per `contracts/events.md`; import `analytics` from `app.services.analytics`
- [X] T016 [P] [US2] Fire `summary_generated` in `backend/app/worker.py` — at the end of `stage_summarize` (after summary is saved, before `return meeting_id`), call `analytics.capture(meeting.owner_id, 'summary_generated', { 'meeting_id': meeting_id, 'template_id': active_template.id if active_template else None, 'word_count_tier': get_word_count_tier(len(summary_text.split()) if summary_text else 0) })`; add `get_word_count_tier` helper returning `'short'`/`'medium'`/`'long'` per `contracts/events.md`

**Checkpoint**: P2 complete. All 6 product events fire. Verify in PostHog Live Events after each action.

---

## Phase 5: User Story 3 — User Identity & Cohort Analysis (Priority: P3)

**Goal**: All events are linked to the authenticated user's Supabase ID so per-user analysis and cohort tracking are possible.

**Independent Test**: Sign in as a known test user, perform any action, search for the user's ID in PostHog → Persons, confirm all events appear under a single profile.

- [X] T017 [US3] Call `posthog.identify(user.id, { email: user.email })` in `frontend-2/app/(dashboard)/layout.tsx` — after the Supabase session/user is confirmed (in the existing `onAuthStateChange` listener or equivalent user-fetch effect); use `usePostHog()` hook to get the posthog instance
- [X] T018 [US3] Fire `user_signed_up` event in `frontend-2/app/(dashboard)/layout.tsx` — detect first-ever sign-in by checking if `user.created_at` equals today (or if a `localStorage` flag like `posthog_signup_tracked` is absent); call `posthog.capture('user_signed_up', { signup_date: user.created_at })`; set the flag after firing to prevent duplicate events

**Checkpoint**: P3 complete. All events are attributed to users. Cohort analysis is available in PostHog.

---

## Phase 6: Polish & Validation

**Purpose**: End-to-end validation against the quickstart.md scenarios.

- [X] T019 Run all 5 validation scenarios from `specs/001-product-analytics/quickstart.md` — confirm pageviews, named events, user identity, and silent failure all pass; note any discrepancies

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately; T001 and T002 run in parallel
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
  - T003 → T004 (config before analytics service)
  - T005 and T006 can run in parallel after T003
  - T007 and T008 can run in parallel after T004
- **Phase 3 (US1)**: Depends on Phase 2 — T009 → T010 → T011 (sequential: provider before pageview before layout)
- **Phase 4 (US2)**: Depends on Phase 2 — all T012–T016 are [P] (different files, independent)
- **Phase 5 (US3)**: Depends on Phase 3 (posthog must be initialised) — T017 then T018
- **Phase 6 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 — no dependency on US2/US3
- **US2 (P2)**: Starts after Phase 2 — no dependency on US1/US3 (events fire regardless of provider setup, but provider must be initialised for frontend events to reach PostHog)
- **US3 (P3)**: Starts after Phase 3 (US1) — requires PostHog provider to be initialised in layout

### Parallel Opportunities

- T001 ‖ T002 (different package managers)
- T005 ‖ T006 (after T003)
- T007 ‖ T008 (after T004)
- T009, T010 can be written independently (different files); T011 depends on both
- T012 ‖ T013 ‖ T014 ‖ T015 ‖ T016 (all Phase 4 — all different files)

---

## Implementation Strategy

### MVP First (US1 Only — Pageviews)

1. Complete Phase 1 (T001, T002)
2. Complete Phase 2 (T003–T008)
3. Complete Phase 3 (T009–T011)
4. **STOP and VALIDATE**: Confirm `$pageview` events in PostHog Live Events
5. Deploy — product now has basic web analytics

### Incremental Delivery

1. Phase 1 + 2 → analytics service ready
2. Phase 3 (US1) → pageview/session tracking live ← deploy
3. Phase 4 (US2) → all 6 product events live ← deploy
4. Phase 5 (US3) → user identity + cohort analysis live ← deploy
5. Phase 6 → validated

---

## Notes

- `posthog-js/react` exports `PostHogProvider` and `usePostHog` — both come from the single `posthog-js` npm package
- Backend events require `meeting.owner_id` as `distinct_id` — already available in both `stage_transcribe` and `stage_summarize`
- PostHog project API key (`phc_...`) is safe to expose in the browser — it is ingestion-only
- `analytics.py` wraps all calls in try/except — analytics failures MUST NOT surface to users or disrupt task pipelines
- `posthog.shutdown()` is blocking — call only at process exit (lifespan teardown / worker_shutdown signal)
