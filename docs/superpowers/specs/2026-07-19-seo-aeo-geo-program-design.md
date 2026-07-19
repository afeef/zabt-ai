# zabt.ai SEO / AEO / GEO Program — Design Spec

**Date:** 2026-07-19
**Status:** Approved (design) — pending user review of this document
**Owner:** Afeef Janjua
**Surface:** `zabt-marketing/` (Next.js 16 marketing site) + `docs/seo/` (knowledge workspace)

---

## 1. Context

`zabt.ai` is self-hosted AI meeting intelligence — a privacy-first alternative to
Otter.ai and Fireflies where audio, transcripts, and summaries stay on infrastructure the
user controls (faster-whisper + pyannote + any OpenAI-compatible LLM).

The public site is a Next.js 16 / React 19 / Tailwind 4 app in `zabt-marketing/` with two
pages today: home (`app/page.tsx`) and pricing (`app/pricing/page.tsx`). Content is
data-driven from `content/*.ts`. Analytics (GA + Microsoft Clarity) are already wired.

**Current SEO/AEO/GEO baseline:**

- Basic `<title>` + `description` on both pages (in `app/layout.tsx` and `app/pricing/page.tsx`).
- No `robots.txt`, no `sitemap.xml`.
- No Open Graph / Twitter card metadata.
- No JSON-LD structured data.
- No canonical URLs, no `metadataBase`.
- No comparison / FAQ / answer-style content for answer engines and LLMs to cite.

**Existing content assets to reuse:** `content/pricing.ts` (`faqItems`, `tiers`,
`featureMatrix`), `content/landing.ts` (features, use cases, testimonials), brand assets in
`brand/` (icons, wordmarks, LinkedIn banner), `docs/faq.md`, `docs/self-hosting.md`.

## 2. Decisions (locked with user)

| Decision | Choice |
| --- | --- |
| Scope | **Full program**, phased (0 → 3) |
| Live status | Deployed but **pre-launch** (AlphaBanner present) |
| Positioning angles | All four: self-hosted alternative, data privacy/compliance, generic AI meeting notes, open-source/developer |
| Paid SEO tooling | **DataForSEO = plan of record, not activated yet.** Proceed on free tools until keys are provisioned ("decide later") |
| GEO citation monitor | **Build it** (Phase 0) |
| Indexing posture | **Index now** (age the domain / build authority before public launch) |
| Canonical domain | `https://zabt.ai` (assumed; no correction given) |
| Comparison competitors | Otter, Fireflies, Fathom, tl;dv, **Read.ai**, **Granola** + self-hosted/OSS rivals |

## 3. Program decomposition

The full program is too large for one implementation plan. It is split into phases; each
phase gets its own spec → plan → implementation cycle. **This document fully details
Phase 0 and Phase 1** (ready to plan/build) and **outlines Phases 2–3** (each to be
specced when reached).

- **Phase 0 — SEO capability layer** ("SEO powers"): data access + knowledge workspace + GEO monitor.
- **Phase 1 — Technical foundation**: metadata, OG, robots, sitemap, canonical, JSON-LD, favicons, semantic audit.
- **Phase 2 — Answer content (AEO/GEO)**: comparison / positioning / use-case / FAQ pages. *(Outline only.)*
- **Phase 3 — Ongoing structure + measurement**: blog/docs SEO scaffold, internal linking, scheduled GEO/SERP monitoring. *(Outline only.)*

---

## 4. Phase 0 — SEO capability layer

**Purpose:** give the agent durable, cross-session capabilities (keyword research, SERP
analysis, competitor gap analysis, GEO citation tracking) so Phases 2–3 run on real data.

### 4.1 Knowledge workspace — `docs/seo/`

Single source of truth for the program (markdown):

- `strategy.md` — positioning (4 angles) mapped to topic clusters and page targets.
- `keywords.md` — target keyword map: head terms, long-tail, comparison, by search intent.
  Volume/difficulty columns left as `TBD (DataForSEO)` until the API is provisioned; filled
  from free-tool estimates in the interim, clearly labeled as estimates.
- `competitors.md` — Otter, Fireflies, Fathom, tl;dv, Read.ai, Granola, plus self-hosted/OSS
  rivals; positioning, target keywords, and gap notes per competitor.
- `geo-questions.md` — the buyer-question prompt bank we want LLMs to answer with "zabt"
  (e.g. "best self-hosted Otter.ai alternative", "private on-premise meeting transcription",
  "open source meeting notes with Docker"). Consumed by the GEO monitor.
- `tooling.md` — DataForSEO MCP setup (endpoints used, cost model, exact `claude mcp add`
  command to run in an interactive session) + free-tool workflow + GSC/Bing setup steps.

### 4.2 Data tooling

- **DataForSEO (plan of record, not activated):** documented in `tooling.md`. Endpoints of
  interest: Keywords Data (volume/CPC), SERP (live results, PAA, featured snippets),
  DataForSEO Labs (ranked-keywords / competitor gap), Backlinks. Setup is a manual step the
  user runs interactively (`claude mcp add`) — this session is non-interactive and cannot run
  the auth flow.
- **Free layer (used now):** WebSearch, firecrawl / `/scrape`, Google autocomplete, `/browse`
  for live SERP inspection. All already available.
- **First-party (free):** Google Search Console + Bing Webmaster. Verified via meta tags
  added in Phase 1 (`metadata.verification`). Empty pre-launch; set up now so data
  accumulates. Bing matters because it powers ChatGPT search.

### 4.3 GEO citation monitor — `zabt-marketing/scripts/geo-monitor/`

Self-contained TypeScript tool (runnable via `npx tsx`), isolated from the site build.

- **Input:** prompt bank from `docs/seo/geo-questions.md` (or a co-located `questions.json`);
  engine config + API keys from a local `.env` (never committed).
- **Engines:** OpenAI-compatible endpoint (keys already available), Anthropic/Claude, and
  Perplexity API (for real citations) — each engine behind a small adapter; missing keys skip
  that engine gracefully.
- **Detection per response:** (a) is "zabt"/"zabt.ai" **mentioned**; (b) is it **cited with a
  URL**; (c) which **competitors** appear (share-of-voice).
- **Output:** append one record per (question × engine × run) to `results/*.jsonl`, each
  stamped with the run timestamp, enabling trend tracking over time. A small summary printer
  aggregates the latest run (mention rate, citation rate, competitor share-of-voice).
- **Cadence:** manual now; cron-able in Phase 3.

### 4.4 Phase 0 verification

- `docs/seo/` files exist and are internally consistent (no orphan `TBD` beyond the
  explicitly-labeled DataForSEO volume columns).
- GEO monitor runs end-to-end against at least one configured engine and writes a valid JSONL
  record; gracefully skips engines with no key.
- `tooling.md` contains a copy-pasteable DataForSEO MCP setup command and cost summary.

---

## 5. Phase 1 — Technical foundation

**Purpose:** the buildable SEO core. All work in `zabt-marketing/`. Centralized so SEO copy
and structured data have one source of truth.

### 5.1 Central config — `lib/seo/config.ts`

Exports site constants: `SITE_URL` (`https://zabt.ai`), default title template, default
description, default OG image path, social handles, and organization info (name, logo,
sameAs links). Every page and builder imports from here — no hard-coded URLs elsewhere.

### 5.2 Structured data — `lib/seo/json-ld.ts` + `components/seo/json-ld.tsx`

Typed builder functions returning schema.org JSON objects, rendered through a tiny
`<JsonLd>` component (`<script type="application/ld+json">`):

- `Organization` — name, url, logo (brand icon), `sameAs` socials. Site-wide.
- `SoftwareApplication` — `applicationCategory: BusinessApplication`, `operatingSystem`,
  description, and `offers` **derived from real `content/pricing.ts` tiers**. Site-wide.
- `FAQPage` — built from existing `faqItems` in `content/pricing.ts`. On pricing page.
- `BreadcrumbList` — on non-home routes.

Builders take content as input (dependency-injected) so they stay pure and testable.

### 5.3 Metadata

- **`app/layout.tsx`:** add `metadataBase: new URL(SITE_URL)`, default `openGraph`
  (type/site_name/images), default `twitter` (`summary_large_image`), `robots: { index: true,
  follow: true }` (index now), `alternates.canonical`, and `verification` (GSC + Bing token
  placeholders). Inject `Organization` + `SoftwareApplication` JSON-LD.
- **Per page:** explicit `metadata` with page-specific title/description and canonical.
  Pricing keeps its own; home gets an explicit block.

### 5.4 OG images

- Dynamic `app/opengraph-image.tsx` via Next `ImageResponse` (1200×630): brand wordmark +
  tagline on brand background, using `brand/` assets. Per-route override for pricing.
- Static 1200×630 fallback PNG in `public/` referenced by the default `openGraph.images`.

### 5.5 Crawl files (Next file conventions)

- `app/robots.ts` — allow all, reference `sitemap.xml`, index now.
- `app/sitemap.ts` — enumerate current routes (`/`, `/pricing`) with `lastModified`;
  structured so Phase 2 content routes slot in.

### 5.6 Brand-entity signals

- `app/icon` / `app/apple-icon` / `app/manifest.ts` from `brand/` icons — strengthens the
  brand-as-entity signal that AEO/GEO engines use for disambiguation.

### 5.7 Semantic / heading audit

- Ensure exactly one `<h1>` per page and a correct heading hierarchy across landing
  components (`components/landing/*`). Cheap AEO extractability win.

### 5.8 Phase 1 verification (evidence required before "done")

- `next build` passes.
- `robots.txt` and `sitemap.xml` resolve and contain expected content.
- JSON-LD validates (Google Rich Results / schema.org validator) with no errors for
  Organization, SoftwareApplication, and FAQPage.
- OG image renders at 1200×630; `opengraph-image` route returns an image.
- One `<h1>` per page confirmed.

---

## 6. Phase 2 — Answer content (AEO/GEO) — *outline*

To be detailed in its own spec. Target pages, each authored **answer-first** (question as
H2, direct 40–60 word answer, then supporting detail) so LLMs and People-Also-Ask boxes can
quote them:

- Comparison pages: `/vs/otter`, `/vs/fireflies`, `/vs/fathom`, `/vs/tldv`, `/vs/read-ai`,
  `/vs/granola` (+ a comparison hub).
- Positioning pages: `/self-hosted`, `/private` (data privacy / compliance angle).
- Use-case pages (from `content/landing.ts` use cases).
- FAQ hub (expand `docs/faq.md` + pricing `faqItems`).

Keyword targets and priority come from Phase 0 data. Each new route registers in
`app/sitemap.ts` and gets its own metadata + JSON-LD (`FAQPage`, `BreadcrumbList`, and where
apt `Article`/`WebPage`).

## 7. Phase 3 — Structure + measurement — *outline*

To be detailed in its own spec:

- Blog/docs SEO scaffold (content model + metadata pattern for scalable publishing).
- Internal-linking system (topic-cluster hub-and-spoke).
- GEO monitor on a schedule + a monthly SERP/citation review loop feeding `docs/seo/`.
- Keyword-strategy maintenance cadence.

---

## 8. Architecture principles applied

- **One source of truth:** `lib/seo/config.ts` for constants; content-derived JSON-LD so
  pricing/FAQ copy is never duplicated.
- **Well-bounded units:** config, JSON-LD builders, the `<JsonLd>` renderer, and the GEO
  monitor are each independently understandable and testable, communicating through typed
  interfaces.
- **No unrelated refactoring:** changes stay within SEO scope; existing components are only
  touched for the heading audit.
- **Follow existing patterns:** data-driven content in `content/*.ts`, SPDX headers, Tailwind
  4 + design-system tokens (stone neutrals, rose accent) per `DESIGN.md`.

## 9. Out of scope (YAGNI)

- Paid SEO API activation (deferred until user provisions DataForSEO keys).
- Multi-language / i18n SEO.
- Programmatic content generation at scale (revisit in Phase 3 if warranted).
- Link-building / off-page campaigns (marketing ops, not this build).
