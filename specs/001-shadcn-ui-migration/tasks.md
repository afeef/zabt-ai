# Tasks: Migrate to shadcn/ui Design System & Unified Summary Toolbar

**Input**: Design documents from `/specs/001-shadcn-ui-migration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/ui-summary-toolbar.md, quickstart.md

**Tests**: E2E test included (constitution requirement for user-facing features).

**Organization**: Three user stories — US1 (Foundation + Summary Toolbar), US2 (Component Migration), US3 (Design System Docs). US1 installs shadcn/ui and builds the toolbar; US2 migrates all remaining components; US3 updates documentation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Initialize shadcn/ui in the frontend-2 project

- [x] T001 Run `cd frontend-2 && npx shadcn@latest init` — select New York style, Stone base color, CSS variables enabled. This creates `components.json` and updates `globals.css`. After init, edit `components.json` to set aliases: `"components": "@/app/components"`, `"ui": "@/app/components/ui"`, `"lib": "@/app/lib"`, `"hooks": "@/app/hooks"`, `"utils": "@/app/lib/utils"`
- [x] T002 Update frontend-2/app/globals.css — apply rose theme CSS variables with stone neutrals, override `--primary` to indigo-600 OKLCH values, and add shadow overrides to neutralize all shadows (`--shadow-xs` through `--shadow-2xl` set to `0 0 #0000`) per research.md Decision 4
- [x] T003 Install shadcn/ui components — run `cd frontend-2 && npx shadcn@latest add button badge dropdown-menu alert-dialog dialog tabs input tooltip` — this installs all 8 components into `frontend-2/app/components/ui/` and their Radix UI dependencies into node_modules
- [x] T004 Verify shadcn/ui setup — run `cd frontend-2 && npx tsc --noEmit` to ensure TypeScript compiles with the new components; verify `frontend-2/app/lib/utils.ts` exists with `cn()` utility function

---

## Phase 2: Foundational — shadcn/ui Button Migration

**Purpose**: Replace the custom Button component that is imported across 7+ files — this MUST complete before any user story because every component depends on Button

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Back up existing Button API surface — read `frontend-2/app/components/ui/button.tsx` to understand current variants (primary, secondary, danger), sizes (md, sm), and loading state props. The shadcn/ui Button has been installed in T003 and overwrote this file. Verify the shadcn/ui Button is now at `frontend-2/app/components/ui/button.tsx` and customize it: add `danger` variant (`bg-red-600 text-white hover:bg-red-700`), ensure `primary` maps to `default` variant, ensure `secondary` maps to `secondary` variant, ensure sizes `sm` and `md` (default) are supported, add a `loading` prop that disables the button and shows a spinner/loading indicator
- [x] T006 Update all Button imports and usages across the codebase — the import path `@/app/components/ui/button` stays the same but prop names may change (e.g., `variant="primary"` → `variant="default"`, `size="md"` → `size="default"`). Update these files: `frontend-2/app/(dashboard)/meetings/[id]/page.tsx`, `frontend-2/app/components/right-panel.tsx`, `frontend-2/app/components/meeting-card.tsx`, `frontend-2/app/components/meeting-feed.tsx`, `frontend-2/app/components/upload-modal.tsx`, `frontend-2/app/login/page.tsx`, `frontend-2/app/register/page.tsx`, `frontend-2/app/forgot-password/page.tsx`
- [x] T007 Add `TooltipProvider` to dashboard layout — wrap the children in `frontend-2/app/(dashboard)/layout.tsx` with `<TooltipProvider>` from `@/app/components/ui/tooltip` (required for shadcn/ui Tooltip to work in any dashboard page)
- [x] T008 Run `cd frontend-2 && npx tsc --noEmit` to verify all Button usages compile cleanly after migration

**Checkpoint**: shadcn/ui foundation ready. Button component works across entire app. User story implementation can begin.

---

## Phase 3: User Story 1 — shadcn/ui Foundation & Summary Toolbar (Priority: P1) 🎯 MVP

**Goal**: Build the unified summary toolbar with Edit, Exports dropdown, and Templates dropdown using shadcn/ui components

**Independent Test**: Navigate to completed meeting → Summary tab → verify toolbar with Edit/Exports/Templates. Verify keyboard navigation works. Verify Transcript tab unchanged.

### Implementation

- [x] T009 [US1] Create `frontend-2/app/components/summary-toolbar.tsx` — implement `SummaryToolbar` component per contracts/ui-summary-toolbar.md: horizontal flex row with left side (Edit button + Edited badge + View Original controls) and right side (Exports dropdown + Templates dropdown). Use shadcn/ui `Button` (ghost variant, size sm) for Edit, shadcn/ui `Badge` (secondary variant) for "Edited" indicator, shadcn/ui `DropdownMenu` for Exports and Templates, shadcn/ui `AlertDialog` for restore-original confirmation. Props per contract: `meeting`, `isEditing`, `showOriginal`, `onEdit`, `onCopySummary`, `onDownloadTxt`, `onDownloadPdf`, `onViewOriginal`, `onRestoreOriginal`, `currentTemplateId`, `currentTemplateName`, `onResummarizeStarted`, `disabled`
- [x] T010 [US1] Implement the Exports dropdown within `frontend-2/app/components/summary-toolbar.tsx` — use shadcn/ui `DropdownMenu` with trigger button ("Export" + ChevronDown icon). Items: "Copy summary" (Copy icon, calls `onCopySummary`), "Download as .txt" (FileText icon, calls `onDownloadTxt`), "Download as PDF" (FileDown icon, calls `onDownloadPdf`). All items use `DropdownMenuItem` with lucide-react icons
- [x] T011 [US1] Implement the Templates dropdown within `frontend-2/app/components/summary-toolbar.tsx` — use shadcn/ui `DropdownMenu` with trigger button showing "Template: {currentTemplateName}" + ChevronDown icon. On open, fetch templates via `getTemplates()` API. Show built-in templates section and "My Templates" section (hidden if empty). Current template has checkmark icon. Include header with "+" (link to `/templates?new=1`) and settings (link to `/templates`) icons. On template select, show shadcn/ui `AlertDialog` confirmation: "Re-summarize with '{name}'? This will replace the current summary." with Cancel and Confirm buttons. Confirm calls `resummarizeMeeting(meetingId, templateId)` then `onResummarizeStarted()`
- [x] T012 [US1] Integrate SummaryToolbar into `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — replace the existing `<SummaryMenu>` usage in the tab bar area with `<SummaryToolbar>` rendered between the tab bar and summary content. Pass all required props: meeting state, editing state, showOriginal state, and all callback handlers (onEdit, onCopySummary, onDownloadTxt, onDownloadPdf, onViewOriginal, onRestoreOriginal, template props). Remove the edit controls row (Pencil Edit button, Edited badge, View Original, Restore Original) from the summary section — these are now in the toolbar. Toolbar only renders when `meeting.status === "completed"` and `!isEditing`. Keep all PostHog event captures (`summary_exported`, etc.)
- [x] T013 [US1] Refactor `frontend-2/app/components/summary-menu.tsx` — remove the entire Export section (onCopySummary, onDownloadTxt, onDownloadPdf props and the export buttons). Remove the `hasSummary` prop. The component now only handles template selection with its confirmation dialog. Update the `SummaryMenuProps` interface accordingly. This component is no longer rendered directly in the meeting page — its logic has been absorbed into the SummaryToolbar's Templates dropdown
- [x] T014 [US1] Replace the tab buttons in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` with shadcn/ui Tabs — use `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` from `@/app/components/ui/tabs`. Map `activeTab` state to `value` prop. Style TabsTrigger to match existing indigo-600 active state. Move the summary content and transcript content into `TabsContent` components with `value="summary"` and `value="transcript"` respectively
- [x] T015 [US1] Run `cd frontend-2 && npx tsc --noEmit` to verify TypeScript compiles cleanly; then run `cd frontend-2 && npm run build` to verify production build succeeds

**Checkpoint**: Summary toolbar works end-to-end. Edit, Export, and Template actions all functional via shadcn/ui components.

---

## Phase 4: User Story 2 — Component Migration (Priority: P2)

**Goal**: Replace all remaining custom components with shadcn/ui equivalents across the entire app

**Independent Test**: Navigate through every page (login, register, dashboard, meetings, templates) — verify all interactive elements render correctly with no visual regressions

### Implementation

- [x] T016 [P] [US2] Replace StatusBadge with shadcn/ui Badge — delete `frontend-2/app/components/ui/status-badge.tsx`. Create a new wrapper component `frontend-2/app/components/status-badge.tsx` (moved out of ui/) that uses shadcn/ui `Badge` with custom color variants per status: `completed` (emerald), `processing` (amber), `failed` (red), `queued` (stone), `pending_upload` (stone). Maintain the dot + text pattern. Update imports in `frontend-2/app/components/meeting-card.tsx` and `frontend-2/app/components/meeting-feed.tsx`
- [x] T017 [P] [US2] Replace ProfileMenu with shadcn/ui DropdownMenu — rewrite `frontend-2/app/components/profile-menu.tsx` to use shadcn/ui `DropdownMenu` for the profile dropdown and shadcn/ui `AlertDialog` for the logout confirmation dialog. Remove the custom click-outside handler and `createPortal` usage (Radix handles this). Keep all existing menu items and the inline confirmation flow for logout
- [x] T018 [P] [US2] Migrate upload-modal.tsx to use shadcn/ui Dialog — rewrite `frontend-2/app/components/upload-modal.tsx` to use shadcn/ui `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` instead of the custom modal overlay. Use shadcn/ui `Button` for actions. Keep ProgressSteps as-is (custom component, no shadcn equivalent)
- [x] T019 [P] [US2] Migrate template-picker-modal.tsx to use shadcn/ui Dialog — rewrite `frontend-2/app/components/template-picker-modal.tsx` to use shadcn/ui `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`. Use shadcn/ui `Button` for actions
- [x] T020 [P] [US2] Migrate template-editor-modal.tsx to use shadcn/ui Dialog + Input — rewrite `frontend-2/app/components/template-editor-modal.tsx` to use shadcn/ui `Dialog` for the modal and shadcn/ui `Input` for text fields. Use shadcn/ui `Button` for save/cancel actions
- [x] T021 [P] [US2] Migrate paywall-modal.tsx to use shadcn/ui Dialog — rewrite `frontend-2/app/components/paywall-modal.tsx` to use shadcn/ui `Dialog`, `DialogContent`. Use shadcn/ui `Button` for CTAs
- [x] T022 [P] [US2] Rebuild SocialButton on shadcn/ui Button — rewrite `frontend-2/app/components/ui/social-button.tsx` to extend shadcn/ui `Button` with `variant="outline"` as base. Keep custom SVG icons for Google, Microsoft. Full-width, 48px height (`size="lg"` or custom className)
- [x] T023 [US2] Migrate auth pages to shadcn/ui Input + Button — update `frontend-2/app/login/page.tsx`, `frontend-2/app/register/page.tsx`, and `frontend-2/app/forgot-password/page.tsx` to use shadcn/ui `Input` for form fields and verify shadcn/ui `Button` + rebuilt `SocialButton` work correctly
- [x] T024 [US2] Migrate meeting-feed.tsx delete confirmation to shadcn/ui AlertDialog — replace the custom inline confirmation pattern in `frontend-2/app/components/meeting-feed.tsx` with shadcn/ui `AlertDialog` for the delete meeting confirmation
- [x] T025 [US2] Migrate templates page to shadcn/ui — update `frontend-2/app/(dashboard)/templates/page.tsx` to use shadcn/ui `Button`, `Input`, and `Dialog` components where applicable
- [x] T026 [US2] Clean up old custom component files — delete `frontend-2/app/components/ui/status-badge.tsx` (replaced by wrapper + shadcn Badge in T016). Verify no stale imports remain anywhere. Run `cd frontend-2 && grep -r "status-badge" app/ --include="*.tsx" --include="*.ts"` to confirm zero references
- [x] T027 [US2] Run `cd frontend-2 && npx tsc --noEmit` to verify TypeScript compiles; run `cd frontend-2 && npm run build` to verify production build succeeds

**Checkpoint**: All custom components migrated to shadcn/ui. Entire app uses consistent component library.

---

## Phase 5: User Story 3 — Design System Documentation Update (Priority: P3)

**Goal**: Update design system docs to reflect shadcn/ui as the standard

**Independent Test**: Read `.interface-design/system.md` — verify it documents shadcn/ui, rose theme, and has no references to old custom components

### Implementation

- [x] T028 [US3] Update `.interface-design/system.md` — replace all custom component documentation (Button variants, StatusBadge, SocialButton, ProfileMenu, FileUploadZone, Input, Nav, auth pages sections) with shadcn/ui equivalents. Document: shadcn/ui as the component library, rose theme with stone neutrals, indigo accent via `--primary` override, borders-only depth rule enforced via shadow token overrides, list of installed components (button, badge, dropdown-menu, alert-dialog, dialog, tabs, input, tooltip), `cn()` utility usage pattern, and the convention that domain-specific components (ProgressSteps, TranscriptViewer, SummaryEditor) remain custom
- [x] T029 [US3] Add SummaryToolbar documentation to `.interface-design/system.md` — document the toolbar as a new composite component pattern: horizontal flex row, visibility rules (completed meetings + summary tab only), dropdown triggers, and keyboard accessibility

**Checkpoint**: Design system documentation fully updated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: E2E testing, verification, and final cleanup

- [x] T030 Write E2E test in tests/e2e/test_summary_toolbar.py — Playwright/Python: log in, navigate to a completed meeting, verify Summary tab shows toolbar with Edit, Exports, and Templates buttons; click Exports dropdown → verify 3 items visible; click Templates dropdown → verify templates load; switch to Transcript tab → verify toolbar is NOT visible; verify Download PDF button exists on Transcript tab
- [x] T031 Verify shadow-free compliance — run a grep across all rendered component files: `cd frontend-2 && grep -rn "shadow-" app/components/ui/ --include="*.tsx"` and verify any shadow classes in shadcn/ui component files are neutralized by the global theme override. Confirm the `@theme inline` shadow overrides in globals.css are present
- [x] T032 Run full verification — `cd frontend-2 && npx tsc --noEmit` (TypeScript), `cd frontend-2 && npm run build` (production build), and verify all existing E2E tests still pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (shadcn/ui installed, components available)
- **US1 — Summary Toolbar (Phase 3)**: Depends on Phase 2 (Button migrated, TooltipProvider added)
- **US2 — Component Migration (Phase 4)**: Depends on Phase 2 (Button migrated). Can start in parallel with US1 since they touch different files
- **US3 — Docs Update (Phase 5)**: Depends on Phase 3 + Phase 4 (all components migrated before documenting)
- **Polish (Phase 6)**: Depends on Phase 5 (all changes complete)

### Within Each Phase

- T001 → T002 → T003 → T004 (sequential — init before theme before components before verify)
- T005 → T006 → T007 → T008 (sequential — customize Button before updating usages)
- T009 → T010 → T011 → T012 → T013 → T014 → T015 (sequential — build toolbar before integrating)
- T016 through T022 can run in parallel (different files, no dependencies)
- T023 → T024 → T025 → T026 → T027 (sequential — auth pages, then feed, then templates, then cleanup)

### Parallel Opportunities

- T016, T017, T018, T019, T020, T021, T022 can all run in parallel (US2 component migrations, different files)
- US1 (Phase 3) and US2 parallel tasks (T016-T022) could run concurrently after Phase 2

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Install shadcn/ui, configure theme
2. Complete Phase 2: Migrate Button, add TooltipProvider
3. Complete Phase 3: Build SummaryToolbar, integrate into meeting page
4. **STOP and VALIDATE**: Test toolbar on a real completed meeting
5. Deploy — users see the new unified toolbar immediately

### Incremental Delivery

1. Setup + Foundational → shadcn/ui ready, Button migrated
2. User Story 1 → Summary Toolbar works → Deploy (MVP!)
3. User Story 2 → All components migrated → Deploy (consistency!)
4. User Story 3 → Docs updated → Deploy (maintainability!)
5. Polish → E2E tests + verification → Confidence for production

---

## Notes

- No backend changes needed — purely frontend migration.
- No database changes — no Alembic migrations.
- ProgressSteps, TranscriptViewer, SummaryEditor, StickyMediaPlayer are explicitly out of scope — they remain custom.
- The custom `SummaryMenu` component's template logic is absorbed into the `SummaryToolbar` Templates dropdown. The old file can be deleted or kept as a simpler template-only component.
- PostHog events (`summary_exported`, `summary_edited`, `summary_restored`, `transcript_exported`) must continue firing with the same names.
- The shadcn/ui `Dialog` component renders via Radix Portal — this replaces all custom `createPortal` usage in profile-menu.tsx and modal components.
