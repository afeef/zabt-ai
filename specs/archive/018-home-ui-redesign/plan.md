# Implementation Plan: Home Page UI Redesign

**Branch**: `018-home-ui-redesign` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-home-ui-redesign/spec.md`

## Summary

Redesign the Zabt home page to match the Otter.ai-style layout: richer meeting cards with summary previews and metadata, a top action bar with Meeting URL / Import / Record buttons, removal of the dedicated Meetings page and nav item, and relabeling the right panel's quick action to "Import". This is a frontend-only change — no backend modifications required.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20
**Primary Dependencies**: Next.js 16, React 19, Tailwind CSS 4, lucide-react, clsx, Axios
**Storage**: N/A — no data model or storage changes
**Testing**: Playwright/Python (E2E under `tests/e2e/`)
**Target Platform**: Web (desktop + mobile responsive)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: N/A — no new API calls or heavy computation
**Constraints**: Must comply with Zabt design system (stone/indigo palette, no shadows, borders only)
**Scale/Scope**: ~6 files modified/created in `frontend-2/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — all gates still PASS.*

| Gate               | Applies? | Status | Notes                                                                                       |
|--------------------|----------|--------|---------------------------------------------------------------------------------------------|
| Design System      | YES      | PASS   | All changes use existing design system (stone/indigo, borders, rounded-lg). No new patterns. |
| API Contract       | NO       | N/A    | No backend changes. Existing `/api/v1/meetings` endpoint unchanged.                         |
| Auth/Security      | NO       | N/A    | No auth changes.                                                                            |
| Env Config         | NO       | N/A    | No new environment variables.                                                               |
| Scope Boundary     | YES      | PASS   | Changes confined to frontend-2 UI components per spec.                                      |
| E2E Testing        | YES      | PASS   | E2E test planned for home page meeting list and import button flow.                         |
| Repository Pattern | NO       | N/A    | No data access changes.                                                                     |
| CLI/Typer          | NO       | N/A    | No CLI changes.                                                                             |
| Provider Abstraction | NO     | N/A    | No external API integration changes.                                                        |
| Cost Awareness     | NO       | N/A    | No paid API calls.                                                                          |
| Migration Safety   | NO       | N/A    | No provider migration.                                                                      |

## Project Structure

### Documentation (this feature)

```text
specs/018-home-ui-redesign/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 — minimal (frontend-only, no unknowns)
├── contracts/
│   └── ui-contracts.md  # UI component contracts
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (files to modify)

```text
frontend-2/
├── app/
│   ├── (dashboard)/
│   │   ├── page.tsx                    # Home page — add action bar, update layout
│   │   └── meetings/
│   │       └── page.tsx                # DELETE or replace with redirect
│   ├── components/
│   │   ├── sidebar.tsx                 # Remove "Meetings" nav item
│   │   ├── meeting-feed.tsx            # Redesign cards — richer layout with summary
│   │   ├── right-panel.tsx             # Relabel "Upload a meeting" → "Import"
│   │   ├── action-bar.tsx              # NEW — Meeting URL + Import + Record buttons
│   │   └── ui/
│   │       └── status-badge.tsx        # Minor — ensure compatible with new card layout
│   └── lib/
│       └── api.ts                      # No changes expected
└── tests/
    └── e2e/                            # Playwright E2E test (if exists, or create)
```

**Structure Decision**: Frontend-only changes within the existing `frontend-2/` Next.js app. No new directories needed except the `action-bar.tsx` component.

## Key Design Decisions

### 1. Meeting Card Redesign

The current `meeting-feed.tsx` card shows: avatar + title + truncated summary (one line) + status badge + 3-dot menu.

**New card layout** (matching Otter.ai):
- **Left**: Avatar/initials badge (existing)
- **Center**: Title (as bold heading), subtitle line (time + duration + speaker name), summary preview (2-3 lines, "Show more" text)
- **Right**: Status badge (existing, for non-completed), action item count badges (future, skip for now)
- Cards are white surface with `border-stone-200` and `rounded-lg` (design system compliant)

### 2. Top Action Bar

New `action-bar.tsx` component placed between the AI query bar and the meeting feed (or in the top-right of the content area, matching Otter.ai's placement).

**Button layout** (left to right):
- Meeting URL button: camera icon + no label (icon-only, outlined style)
- Import button: text "Import" (outlined/secondary style)
- Record button: red/primary with microphone icon + "Record" text

Import opens the existing `upload-modal.tsx`. Meeting URL and Record show "Coming soon" tooltip via `title` attribute.

### 3. Meetings Page Removal

- Remove `Meetings` from sidebar nav items array in `sidebar.tsx`
- Replace `frontend-2/app/(dashboard)/meetings/page.tsx` with a redirect to `/`
- Keep `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` intact (meeting detail page)

### 4. Right Panel Update

Change the "Upload a meeting" button label to "Import" in `right-panel.tsx`. Same `onClick` handler (opens upload modal).

## File Change Details

| File | Action | Description |
|------|--------|-------------|
| `frontend-2/app/components/meeting-feed.tsx` | MODIFY | Redesign meeting cards with title heading, metadata subtitle, summary preview |
| `frontend-2/app/components/action-bar.tsx` | CREATE | New component with Meeting URL + Import + Record buttons |
| `frontend-2/app/(dashboard)/page.tsx` | MODIFY | Add ActionBar component, adjust layout |
| `frontend-2/app/components/sidebar.tsx` | MODIFY | Remove "Meetings" nav item from array |
| `frontend-2/app/(dashboard)/meetings/page.tsx` | MODIFY | Replace with redirect to `/` |
| `frontend-2/app/components/right-panel.tsx` | MODIFY | Relabel button to "Import" |
| `tests/e2e/test_home_page.py` | CREATE | E2E test for home page meeting list and import flow |
