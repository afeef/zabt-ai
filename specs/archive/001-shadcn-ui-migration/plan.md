# Implementation Plan: Migrate to shadcn/ui Design System & Unified Summary Toolbar

**Branch**: `001-shadcn-ui-migration` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-shadcn-ui-migration/spec.md`

## Summary

Replace all custom UI components with shadcn/ui (built on Radix UI primitives + Tailwind CSS). Install shadcn/ui with rose theme + stone neutrals, build a unified summary toolbar (Edit, Exports dropdown, Templates dropdown), migrate all existing custom components (Button, StatusBadge, SocialButton, ProfileMenu, modals, inputs) to shadcn/ui equivalents, and update the design system documentation. No backend changes.

## Technical Context

**Language/Version**: TypeScript 5 / Node.js 20 + Next.js 16, React 19, Tailwind CSS 4
**Primary Dependencies**: shadcn/ui (new), @radix-ui/* (new — installed by shadcn/ui), clsx (existing), tailwind-merge (existing), lucide-react (existing), Axios, @tiptap/* (unchanged)
**Storage**: N/A — frontend-only, no data model changes
**Testing**: Playwright/Python E2E tests in `tests/e2e/` (existing tests must pass), TypeScript compiler check (`npx tsc --noEmit`)
**Target Platform**: Web (desktop + mobile responsive)
**Project Type**: Web application (frontend)
**Performance Goals**: All toolbar interactions complete within 2 seconds (excluding network)
**Constraints**: No shadows (borders-only depth rule), rose theme with stone neutrals, indigo accent preserved
**Scale/Scope**: ~15 component files to migrate, ~8 page files affected, 1 new composite component (SummaryToolbar)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | Yes | PASS | Migrating to shadcn/ui — system.md will be updated in US3. Rose theme with stone neutrals and borders-only rule maintained. |
| API Contract | No | N/A | No backend changes, no new endpoints. |
| Auth/Security | No | N/A | No auth changes. Existing Supabase auth preserved. |
| Env Config | No | N/A | No new environment variables. |
| Scope Boundary | Yes | PASS | Purely frontend UI component migration + toolbar. No backend, no new features beyond toolbar consolidation. |
| E2E Testing | Yes | PASS | Existing E2E tests must pass. Selector updates may be needed if DOM structure changes. |
| Repository Pattern | No | N/A | No data access changes. |
| CLI/Typer | No | N/A | No CLI changes. |
| Provider Abstraction | No | N/A | No external API integrations changed. |
| Cost Awareness | No | N/A | No external API calls added. |
| Migration Safety | No | N/A | No provider migrations. |
| DB Migration | No | N/A | No database changes. |

## Project Structure

### Documentation (this feature)

```text
specs/001-shadcn-ui-migration/
├── plan.md              # This file
├── research.md          # Phase 0 — shadcn/ui + Tailwind v4 research
├── quickstart.md        # Phase 1 — setup and verification steps
├── contracts/
│   └── ui-summary-toolbar.md  # Summary toolbar UI contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend-2/
├── components.json                     # NEW — shadcn/ui CLI config
├── app/
│   ├── globals.css                     # MODIFIED — rose theme CSS variables + shadow overrides
│   ├── lib/
│   │   └── utils.ts                    # NEW — cn() utility (clsx + tailwind-merge)
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx              # REPLACED — shadcn/ui Button
│   │   │   ├── badge.tsx               # NEW — shadcn/ui Badge (replaces status-badge.tsx)
│   │   │   ├── dropdown-menu.tsx       # NEW — shadcn/ui DropdownMenu
│   │   │   ├── alert-dialog.tsx        # NEW — shadcn/ui AlertDialog
│   │   │   ├── dialog.tsx              # NEW — shadcn/ui Dialog
│   │   │   ├── tabs.tsx                # NEW — shadcn/ui Tabs
│   │   │   ├── input.tsx               # NEW — shadcn/ui Input
│   │   │   ├── tooltip.tsx             # NEW — shadcn/ui Tooltip
│   │   │   ├── progress-steps.tsx      # KEPT — custom (no shadcn equivalent)
│   │   │   └── social-button.tsx       # REPLACED — rebuilt on shadcn/ui Button
│   │   ├── summary-toolbar.tsx         # NEW — unified toolbar for Summary tab
│   │   ├── summary-menu.tsx            # MODIFIED — template selection only (exports removed)
│   │   ├── profile-menu.tsx            # REPLACED — shadcn/ui DropdownMenu
│   │   ├── meeting-card.tsx            # MODIFIED — use shadcn Badge + Button
│   │   ├── meeting-feed.tsx            # MODIFIED — use shadcn Badge + Button + AlertDialog
│   │   ├── upload-modal.tsx            # MODIFIED — use shadcn Dialog + Button
│   │   ├── template-picker-modal.tsx   # MODIFIED — use shadcn Dialog
│   │   ├── template-editor-modal.tsx   # MODIFIED — use shadcn Dialog
│   │   ├── paywall-modal.tsx           # MODIFIED — use shadcn Dialog
│   │   └── summary-editor.tsx          # UNCHANGED — Tiptap editor
│   └── (dashboard)/
│       ├── layout.tsx                  # MODIFIED — add TooltipProvider
│       ├── meetings/[id]/page.tsx      # MODIFIED — use SummaryToolbar, shadcn Tabs
│       └── templates/page.tsx          # MODIFIED — use shadcn Button, Dialog
├── login/page.tsx                      # MODIFIED — use shadcn Button, Input
├── register/page.tsx                   # MODIFIED — use shadcn Button, Input
└── forgot-password/page.tsx            # MODIFIED — use shadcn Button, Input
```

**Structure Decision**: Frontend-only changes. All shadcn/ui components go into `frontend-2/app/components/ui/` (matching the existing ui/ directory convention). The `cn()` utility goes in `frontend-2/app/lib/utils.ts`. `components.json` at `frontend-2/` root configures the shadcn/ui CLI.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
