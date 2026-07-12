# Implementation Plan: Unified Processing Queue

**Branch**: `001-unified-processing-queue` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-unified-processing-queue/spec.md`

## Summary

Replace the in-modal worker stage tracking with a persistent processing queue panel on the dashboard. File upload byte progress stays in the import dialog; YouTube URL validation stays in its dialog. Only worker pipeline stages (transcribing → aligning → diarizing → summarizing → done) move to a new collapsible queue panel anchored at the bottom-right of the dashboard page. The queue is session-only, supports both file upload and YouTube ingestion items, and auto-hides after all items complete.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20
**Primary Dependencies**: Next.js 16, React 19, Tailwind CSS 4, shadcn/ui, lucide-react, Axios
**Storage**: N/A — session-only React state (no persistence)
**Testing**: Playwright/Python E2E tests (per constitution)
**Target Platform**: Web browser (dashboard page)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Queue polls every 3 seconds per active item; stage updates reflected within 5 seconds
**Constraints**: Max 5 concurrent queue items; session-only state (resets on page refresh)
**Scale/Scope**: 3 new components, 1 context provider, modifications to 3 existing components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | PASS | Queue panel uses existing design tokens (bg-white, border-stone-200, rounded-lg, indigo-600 accent). New pattern (floating panel) will be documented in system.md |
| API Contract | No | N/A | No new backend endpoints — uses existing `GET /meetings/{id}` for polling |
| Auth/Security | No | N/A | No auth changes; queue polls authenticated endpoints via existing Axios interceptor |
| Env Config | No | N/A | No new environment variables |
| Scope Boundary | Yes | PASS | Frontend-only; no backend changes per spec |
| E2E Testing | Yes | PASS | E2E tests planned in `tests/e2e/test_processing_queue.py` |
| Repository Pattern | No | N/A | No backend data access changes |
| CLI/Typer | No | N/A | No CLI involved |
| Provider Abstraction | No | N/A | No external API integration changes |
| Cost Awareness | No | N/A | No new external API calls; reuses existing polling |
| Migration Safety | No | N/A | No provider migration |
| DB Migration | No | N/A | No database schema changes |
| shadcn/ui Components | Yes | PASS | Queue panel uses shadcn/ui Card, Button, Badge, Collapsible. ProgressSteps remains custom (domain-specific, no shadcn/ui equivalent) |

## Project Structure

### Documentation (this feature)

```text
specs/001-unified-processing-queue/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui-contracts.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend-2/app/
├── contexts/
│   └── processing-queue-context.tsx    # NEW — React context + provider for queue state
├── components/
│   ├── processing-queue.tsx            # NEW — floating queue panel component
│   ├── processing-queue-item.tsx       # NEW — individual queue item row
│   ├── upload-modal.tsx                # MODIFIED — remove post-upload polling/stage tracking
│   ├── youtube-url-dialog.tsx          # MODIFIED — push item to queue on success
│   ├── meeting-feed.tsx                # MODIFIED — consolidate polling with queue
│   └── ui/
│       └── progress-steps.tsx          # EXISTING — reused as-is
├── lib/
│   └── stage-utils.ts                  # EXISTING — reused as-is
└── (dashboard)/
    └── page.tsx                        # MODIFIED — wrap with ProcessingQueueProvider, render ProcessingQueue

tests/e2e/
└── test_processing_queue.py            # NEW — E2E tests for queue panel
```

**Structure Decision**: Frontend-only changes within the existing `frontend-2/` directory. New components follow the established flat component structure in `frontend-2/app/components/`. A new `contexts/` directory is introduced for the shared queue state provider (React Context pattern, consistent with Next.js conventions).

## Complexity Tracking

No constitution violations. No complexity tracking entries needed.
