# Zabt Roadmap

Tracking feature requests, priorities, and implementation progress.

## Completed

| # | Feature | Branch | Shipped |
|---|---------|--------|---------|
| 1 | Infra migration (Contabo VPS + RunPod Serverless) | `019-vps-lift-shift`, `020-s3-storage-switch`, `021-runpod-worker` | 2026-03 |
| 2 | Edit summary markdown (Tiptap editor) | `001-edit-summary` | 2026-03 |
| 3 | PDF download (transcript + summary) | `001-export-summary-pdf`, `001-transcript-pdf-download`, `001-server-pdf-export` | 2026-03 |
| 4 | YouTube URL ingestion | `001-youtube-ingestion` | 2026-03 |
| 5 | DB migration to Supabase Postgres | `022-supabase-db-migration` | 2026-03 |
| 6 | Telegram owner notifications | `023-telegram-notifications` | 2026-03 |
| 7 | Observability upgrade (Sentry + Langfuse) | `024-sentry-langfuse` | 2026-03 |
| 8 | GPU worker extraction | `025-gpu-worker-extraction` | 2026-03 |
| 9 | Medical transcription (MedASR) | `026-medical-transcription` | 2026-03 |
| 10 | Microsoft Integration (Phase 1-3): OAuth, calendar sync, recording pickup, email summaries | `main` | 2026-04 |
| 11 | Microsoft Integration (Phase 4): Teams bot worker (headless browser) | `main` | 2026-04 |
| 12 | Meeting Intelligence Phase 1: structured output, action items, chapters, highlights | `feat/headless-browser-bot` | 2026-04 |
| 13 | Meeting detail page redesign: toolbar bars, decluttered header | `main` | 2026-04 |
| 14 | Microsoft social login via Supabase | `feat/microsoft-social-auth` | 2026-04 |
| 15 | Quick wins: sidebar removal, date fallback (via AI prompt), title inference, monthly usage display, audio player fixes (transcript-only, presigned URL, no overlap) | `feat/quick-wins` (PR #92) | 2026-04-10 |
| 16 | Title + duration fixes: title via dedicated LLM call (template-agnostic), duration written from `result.audio_duration_seconds` during `stage_transcribe` | `main` | 2026-04-10 |
| 17 | Structured output fixes: Pydantic-enforced LLM outputs via `beta.chat.completions.parse`, CardGrid field-name detection for varied LLM returns, MeetingRead accepts `Any` for structured_output | `main` | 2026-04-10 |
| 18 | Docker Compose cleanup: removed Qdrant container + volume (deferred to when RAG is actually built) | `main` | 2026-04-09 |
| 19 | zabt.ai domain migration: Cloudflare DNS, Vercel domains, Kong hosts, MinIO CORS, OAuth redirect URIs, Resend sending domain, VPS + Vercel env cutover, Graph webhook re-pinning | `main` | 2026-04 |
| 20 | Mobile app (Expo / React Native, iOS + Android) — Supabase auth, TanStack Query, Sentry, shared logic via `@zabt/shared` monorepo workspace. Scaffolded at `zabt-mobile/`. | `zabt-mobile/` | 2026-04 |

## In Progress

| # | Feature | Branch | Status |
|---|---------|--------|--------|
| 21 | **Visual breakdown** — detect screen changes in uploaded videos via Qwen3-VL on a stateless `zabt-vision-worker`, group transcript lines by detected screen, render in a two-pane viewer on the meeting page. Spec at `docs/superpowers/specs/2026-04-19-visual-breakdown-design.md`. Three-PR stack: Plan 1 (worker, PR #128, ready for review), Plan 2 (backend wiring, PR #130, ready for review), Plan 3 (frontend, branch `feat/visual-breakdown-frontend`, plan written, execution pending). Calibration of detection thresholds on RTX 3090 happens between Plan 1 merge and Plan 3 ship. | `feat/visual-breakdown*` (3 branches) | PRs #128 + #130 open · Plan 3 plan written |

## Deferred / Needs Planning

| # | Task | Effort | Notes |
|---|------|--------|-------|
| D1 | Supabase Custom Domain add-on: front Supabase API as `db.zabt.ai` to replace `fnacjfxunoxmjacwjvbc.supabase.co` | Small + $10/mo | Requires Pro plan. Cosmetic fix — current URL works fine. Do on target region project to avoid paying twice. |
| D2 | **Supabase region migration**: `us-west-2` → `eu-central-1` to co-locate DB with Contabo VPS (Germany). Latency gain is the real value. Create new project, `pg_dump`/`pg_restore` via Session Pooler, re-wire Google/Microsoft OAuth in new project dashboard, invalidate sessions, flip `DATABASE_URL` on VPS + `SUPABASE_URL`/anon key on Vercel, verify, pause old project. | Large | 1-day downtime window. OAuth client IDs/secrets don't transfer. |
| D3 | **Self-host Supabase on Contabo** — evaluated, NOT recommended pre-PMF. Saves ~$20–25/mo cash but costs ~4–8 hrs/mo ops time, loses PITR/backups/Supavisor/dashboard. Revisit only if managed bill exceeds ~$50/mo or compliance requires it. | — | Decision, not a task. |

## Backlog (Sorted by Complexity: Easy → Hard)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 12 | LLM selection for summaries | Small | User preference for summary model (OpenAI, Deepseek, etc.) |
| 13 | In-app meeting recording | Medium | Enable the Record button on home page. MediaRecorder API for mic capture, pause/resume/stop controls, upload recorded audio into existing transcription pipeline. Frontend-heavy (small backend). |
| 14 | AI Chat over meetings (RAG or long context) | Medium | Chat over transcripts/summaries. Two approaches to evaluate: (a) RAG via Qdrant embeddings + retrieval, (b) long-context window — stuff full transcripts directly into prompt. Could hybrid: long context for single-meeting chat, RAG for cross-meeting search. |
| 15 | Admin control plane dashboard | Medium | Internal admin dashboard showing all user activity, meetings processed (total/per-user), credits used/remaining, system health metrics. Separate admin route with auth guard. Backend aggregation queries + frontend dashboard with tables and summary cards. |
| 16 | Credits/usage pricing system | Medium | Usage tracking, credit purchase, rate limiting |
| 17 | Google Calendar + Meet integration | Medium | Same provider-agnostic pattern as Microsoft — OAuth, calendar sync, headless browser bot for Meet |
| 18 | Zoom integration | Medium | Zoom Meeting SDK for bot join + audio capture, calendar sync via Zoom OAuth |
| 19 | MSP multi-tenant admin | Large | Org/tenant model, RBAC, admin dashboard, cross-meeting analytics |
| 20 | **Microsoft Graph webhook subscriptions** — replace the no-op `renew_graph_subscriptions` task with a real implementation. Requires: (a) pass correct args to `MicrosoftGraphClient.create_subscription` (access_token, notification_url derived from APP_URL, resource paths like `/me/drive/root` + `/me/events`), (b) persist subscription IDs on the `Integration` model so renewal uses PATCH instead of always creating new, (c) validate `clientState` in the webhook handler at `backend/app/api/v1/endpoints/webhooks.py`, (d) handle Graph subscription expiration (max 4230 minutes per call). | Medium | Polling handles calendar + recording sync today (every 5 min). This is a latency optimization (webhooks ~1s vs polling 5min), not a correctness fix. Low priority until real user load justifies it. |

## User Requests (Unsorted)

New feature requests from users go here. Move them to Backlog once prioritized.

| Date | Request | Source | Priority | Notes |
|------|---------|--------|----------|-------|
| 2026-04-10 | API key generation for mobile app integration | User (mobile dev) | High | User building mobile app needs API keys to authenticate. Requires: API key model, generation/revocation UI in settings, key-based auth middleware alongside existing JWT auth. |
| 2026-04-10 | Redis caching for frequent queries | Internal | Medium | Cache frequently accessed data (meetings list, templates, user profile) using existing Redis service. Celery already uses Redis as broker, add caching layer. |
| 2026-04-10 | Google Analytics / Tag Manager integration | Internal | Low | Add GA4 or GTM to frontend for traffic analytics. Evaluate current gold standard (GA4 vs Plausible vs PostHog web analytics, which is already installed). |
| 2026-04-10 | Multiple integrations per provider (multi-account) | User | High | **Re-raised 2026-04-16** — users explicitly asking for this. Allow multiple Microsoft integrations per user (personal, work, school accounts). Currently limited to one integration per provider. Requires lifting unique constraint on (owner_id, provider), UI for managing multiple connected accounts. |
| 2026-04-10 | OpenRouter-style topup and usage billing | Internal | Large | Prepaid minutes model: users buy minute packs, each transcription deducts from balance. Requires: balance/transaction model, payment integration (Stripe checkout already exists), usage enforcement (block processing when balance is zero), usage dashboard with history. Similar to OpenRouter's credit system. |
| 2026-04-16 | Language preferences for transcription and summaries | User | High | Per-user language setting: transcription language (Whisper supports ~100; Chirp supports 100+) + summary output language. Surfaces as a settings dropdown and per-meeting override. Smallest feature on this list, unblocks all non-English users. Backend: add `language` column to user + meeting, pass through to transcription provider and LLM prompt. |
| 2026-04-16 | Google Meet bot (audio capture) | User | Medium | Join Google Meet meetings as a bot and capture audio — parallel to existing Teams bot. Existing `zabt-bot-worker` architecture reusable. Google Meet has no official bot SDK, likely requires headless browser (same as Teams headless bot path). Tied to calendar integration #17. |
| 2026-04-16 | Zoom bot (audio capture) | User | Medium | Zoom Meeting SDK supports bot join natively (unlike Meet). Cleaner technical path than Meet. Covered by backlog #18 — users are now explicitly asking for it. |

---

## How to Use

1. **New request**: Add a row to "User Requests (Unsorted)"
2. **Prioritize**: Move from Unsorted to Backlog with a priority number
3. **Start work**: Move from Backlog to "In Progress", create branch via `/speckit.specify`
4. **Ship**: Move from "In Progress" to "Completed" with ship date
