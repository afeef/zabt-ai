# Zabt — Design System

**Product:** AI meeting notes tool. Upload recordings, get transcripts, summaries, and action items.
**User:** Knowledge worker between back-to-back meetings. Wants clarity, not stimulation.
**Feel:** Warm notebook. Thoughtful, personal — not SaaS dashboard.

---

## Palette

**Theme: Rose** — configured via shadcn/ui CSS variables in `globals.css`.

| Role | Semantic class | Raw value |
|------|---------------|-----------|
| Ground | `bg-stone-50` | stone-50 |
| Surface | `bg-white` | white |
| Border | `border-stone-200` or `border-border` | stone-200 |
| Primary | `bg-primary` / `text-primary` | rose-600 (OKLCH) |
| Primary hover | `hover:bg-primary/90` | — |
| Primary light bg | `bg-primary/10` | — |
| Primary light text | `text-primary/60` | — |
| Danger | `text-destructive` / `bg-destructive` | red-600 |

**Rule: Use semantic tokens** (`text-primary`, `bg-primary`, `border-primary`) for all accent colors. Never hardcode `rose-*` classes for accent purposes — the theme may change.

**Text hierarchy:**
| Role | Class |
|------|-------|
| Page title | `text-stone-900` |
| Section heading | `text-stone-800` |
| Body | `text-stone-700` |
| Secondary | `text-stone-500` |
| Muted / hint | `text-stone-400` or `text-muted-foreground` |

**Status colors** (semantic, not themed — these are always the same):
| Status | Dot | Text | Left border |
|--------|-----|------|-------------|
| queued | `bg-stone-400` | `text-stone-500` | `border-l-stone-300` |
| processing | `bg-amber-500` | `text-amber-600` | `border-l-amber-400` |
| completed | `bg-emerald-500` | `text-emerald-600` | `border-l-emerald-400` |
| failed | `bg-red-500` | `text-red-500` | `border-l-red-400` |

**Speaker colors** (fixed palette, not themed):
| Speaker | Avatar | Progress bar |
|---------|--------|-------------|
| SPEAKER_00 | `bg-stone-500` | `bg-stone-500` |
| SPEAKER_01 | `bg-amber-500` | `bg-amber-600` |
| SPEAKER_02 | `bg-teal-500` | `bg-teal-600` |
| SPEAKER_03 | `bg-emerald-500` | — |

---

## Depth

**Rule: borders only. No shadows.**

- Cards: `border border-stone-200`
- Never use `shadow`, `shadow-sm`, `shadow-lg`, etc.
- All `--shadow-*` CSS variables neutralized to `0 0 #0000` in globals.css
- Exception: focus rings are allowed (`focus-visible:ring-3 focus-visible:ring-ring/50`)

---

## Spacing

Base unit: **4px** (Tailwind default)

Common patterns:
- Page padding: `px-6 py-4` (nav), `px-6 py-12` (content), `px-6 py-16` (hero)
- Card padding: `p-8` (main sections), `p-6` (content sections), `p-4` (list rows)
- Content max-width: `max-w-3xl mx-auto`

---

## Rounding

**Rule: `rounded-lg` everywhere.** One decision, no drift.

- Cards, inputs, buttons, badges, upload zones: `rounded-lg`
- Status badge dots: `rounded-full` (circles only)
- Small pill-style items (style list): `rounded-md`

---

## Typography

Font: **Inter** (via `next/font/google`) — variable `--font-inter`
Mono: **JetBrains Mono** — variable `--font-jetbrains-mono`

| Level | Classes |
|-------|---------|
| Page title | `text-2xl font-bold` or `text-4xl font-bold` |
| Section heading | `text-xl font-semibold` or `text-lg font-semibold` |
| Body | `text-sm leading-relaxed` |
| Label | `text-sm font-medium` |
| Caption / meta | `text-xs` |
| Overline | `text-xs font-medium uppercase tracking-wide` |

---

## Component Library: shadcn/ui (base-nova)

**All UI components MUST use shadcn/ui.** Custom components are only allowed for domain-specific widgets (ProgressSteps, TranscriptViewer, SummaryEditor, StickyMediaPlayer).

- **Style**: base-nova (uses `@base-ui/react` primitives)
- **Theme**: Rose with stone neutrals, `--primary` set via OKLCH in globals.css
- **Utility**: `cn()` from `@/app/lib/utils` (clsx + tailwind-merge)
- **Trigger pattern**: Use `render` prop (NOT `asChild`) for composed triggers
- **DropdownMenuLabel**: MUST be inside `DropdownMenuGroup` (Base UI error #31)

### Installed Components

`button`, `badge`, `dropdown-menu`, `alert-dialog`, `dialog`, `tabs`, `input`, `tooltip`

All at `frontend-2/app/components/ui/`.

### Button

shadcn/ui Button with custom `loading` prop. Variants: `default`, `secondary`, `destructive`, `outline`, `ghost`, `link`. Sizes: `default`, `sm`, `lg`, `icon`.

```tsx
import { Button } from "@/app/components/ui/button";
<Button variant="default" loading={saving}>Save</Button>
<Button variant="ghost" size="sm"><Pencil className="size-4" /></Button>
<Button variant="destructive">Delete</Button>
```

### Badge

shadcn/ui Badge. Used for status indicators and labels.

```tsx
import { Badge } from "@/app/components/ui/badge";
<Badge variant="secondary">Custom</Badge>
<Badge variant="secondary" className="text-amber-600">★ Default</Badge>
```

### StatusBadge (wrapper)

At `frontend-2/app/components/status-badge.tsx`. Wraps shadcn Badge with status-specific colors.

```tsx
import { StatusBadge } from "@/app/components/status-badge";
<StatusBadge status="completed" /> // emerald
<StatusBadge status="processing" /> // amber
<StatusBadge status="failed" />     // red
```

### DropdownMenu

shadcn/ui DropdownMenu. Used for ProfileMenu, Exports, Templates.

```tsx
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/app/components/ui/dropdown-menu";
// Trigger uses render prop (base-nova pattern):
<DropdownMenuTrigger render={<Button variant="outline" size="sm" />}>
  Export <ChevronDown />
</DropdownMenuTrigger>
```

### AlertDialog

shadcn/ui AlertDialog. Used for destructive confirmations (logout, delete, restore, re-summarize).

```tsx
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from "@/app/components/ui/alert-dialog";
```

### Dialog

shadcn/ui Dialog. Used for modals (upload, template editor, template picker).

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/app/components/ui/dialog";
<Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
  <DialogContent showCloseButton={false}>...</DialogContent>
</Dialog>
```

### Tabs

shadcn/ui Tabs. Used for meeting detail page (Summary/Transcript).

```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/app/components/ui/tabs";
<Tabs value={activeTab} onValueChange={setActiveTab}>
  <TabsList><TabsTrigger value="summary">Summary</TabsTrigger></TabsList>
  <TabsContent value="summary">...</TabsContent>
</Tabs>
```

### Input

shadcn/ui Input. Used in forms (auth pages, template editor).

```tsx
import { Input } from "@/app/components/ui/input";
<Input type="email" placeholder="name@company.com" />
```

### SocialButton

At `frontend-2/app/components/ui/social-button.tsx`. Built on shadcn Button with `variant="outline"`.

```tsx
import { SocialButton } from "@/app/components/ui/social-button";
<SocialButton provider="google" label="Sign in with Google" onClick={...} />
```

### Card (section)

```tsx
<section className="bg-white rounded-lg border border-stone-200 p-6">
```

No shadow. Always `rounded-lg`. Always `border-stone-200`.

### Card (list row) — MeetingCard

```tsx
// Left border stripe communicates status
<div className="bg-white rounded-lg border border-stone-200 border-l-4 border-l-{status-color} p-4">
```

### FileUploadZone

Custom component (no shadcn equivalent). Uses shadcn Button internally.

```tsx
// border-2 border-dashed border-stone-300 rounded-lg p-10
// hover:bg-stone-50
// Icon: text-stone-300
// Label: text-stone-500
// Selected file name: text-primary font-medium
```

---

### AppShell (Authenticated Layout Shell)

Three-column flex container for all authenticated routes.

```tsx
// Outer: flex h-screen overflow-hidden bg-stone-50
// Sidebar: 220px fixed-width, border-r border-stone-200
// Main: flex-1 overflow-y-auto
// Right panel: 280px fixed-width, border-l border-stone-200, hidden below lg breakpoint
// Mobile: sidebar becomes fixed off-canvas drawer with stone-900/30 backdrop overlay
```

### Sidebar

Left navigation sidebar. `bg-white`, `border-r border-stone-200`, `220px` wide.

```tsx
// Logo mark: w-7 h-7 rounded-lg bg-primary text-primary-foreground
// Profile: avatar initials bg-primary/15 text-primary rounded-full
// Nav link (inactive): text-stone-600 hover:bg-stone-100 rounded-lg
// Nav link (active): bg-primary/10 text-primary rounded-lg
// Section labels: text-xs font-medium uppercase tracking-wide text-stone-400
// Plan bar: bg-stone-50 rounded-lg border border-stone-200 px-3 py-2
```

### RightPanel

Right contextual sidebar. `bg-white`, `border-l border-stone-200`, `280px` wide, hidden below `lg` breakpoint.

```tsx
// Section heading: text-xs font-medium uppercase tracking-wide text-stone-400
// CTA buttons: use standard Button component (primary / secondary)
// Calendar buttons: use Button variant="outline" size="sm"
// Quick-start checklist items: rounded-lg border border-stone-200 bg-white px-3 py-2
// Checklist done state: border-primary bg-primary (circle indicator)
// Empty calendar state: bg-stone-50 rounded-lg border border-stone-200
```

### ProfileMenu

shadcn/ui DropdownMenu + AlertDialog for logout confirmation. At `frontend-2/app/components/profile-menu.tsx`.

```tsx
// Uses children pattern — wrap trigger content as <ProfileMenu>{...}</ProfileMenu>
// DropdownMenuTrigger uses render prop for sidebar profile button
// Logout confirmation via AlertDialog (not inline state)
// Menu items: Settings, Help, Logout (destructive)
```

### SummaryToolbar

Unified toolbar for the Summary tab on completed meetings. At `frontend-2/app/components/summary-toolbar.tsx`.

```tsx
// Layout: horizontal flex row, items-center justify-between
// Left side: Edit button (ghost, sm) + "Edited" Badge + "View Original" button
// Right side: Exports DropdownMenu + Templates DropdownMenu
// Visibility: only when meeting.status === "completed" && !isEditing
// Hidden when showOriginal is true (shows only "Back to Edited" button)
//
// Exports dropdown items: Copy summary, Download .txt, Download PDF
// Templates dropdown: fetches once on mount, shows Built-in + My Templates sections
// Re-summarize: AlertDialog confirmation before calling API
// Restore original: AlertDialog confirmation
//
// All triggers use render prop pattern for DropdownMenuTrigger
// Keyboard accessible via shadcn/ui Base UI primitives
```

### SummaryEditor

Tiptap WYSIWYG markdown editor. At `frontend-2/app/components/summary-editor.tsx`.

```tsx
// Toolbar: bg-stone-50 border-b with formatting buttons
// Active toolbar button: bg-primary/15 text-primary
// Save/Cancel: shadcn/ui Button (default + ghost variants)
// Links in editor: text-primary underline
```

### AiQueryBar

Pill-shaped AI input bar. `bg-white border border-stone-200 rounded-lg`.

```tsx
// Layout: flex items-center gap-2 px-4 py-3
// Leading icon (sparkle): text-primary/60 w-4 h-4
// Input: flex-1 text-sm placeholder-stone-400 bg-transparent
// Advanced toggle (inactive): text-stone-400; (active): text-primary bg-primary/10 rounded-lg
// Submit button: w-7 h-7 rounded-lg bg-primary text-primary-foreground; disabled: bg-stone-200 text-stone-400
```

### ProgressSteps

Horizontal multi-step indicator for processing pipelines.

```tsx
// Container: flex items-center w-full gap-0
// Each step: circle (w-6 h-6 rounded-full) + label (text-[10px] font-medium)
// States:
//   Completed: bg-primary text-primary-foreground (check icon)
//   Active: ring-2 ring-primary bg-white text-primary animate-pulse
//   Pending: border-2 border-stone-200 bg-white text-stone-400
// Connecting lines: flex-1 h-0.5
//   Completed: bg-primary
//   Pending: bg-stone-200
// Labels: text-[10px] font-medium, color matches circle state
// Used in: upload modal (below progress bar), meeting detail page (in processing banner)
```

---

## State / Alert Banners

```tsx
// Success
"bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg px-4 py-3 text-sm"

// Warning / processing
"bg-amber-50 border border-amber-200 text-amber-800 rounded-lg px-5 py-4 text-sm"

// Error
"bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm"
```

---

## Auth Pages (Login / Register)

Centered single-column form card. Uses shadcn/ui `Input` for form fields, shadcn/ui `Button` for submit, `SocialButton` (shadcn Button variant) for OAuth.

```tsx
<main className="min-h-screen flex items-center justify-center bg-stone-50 px-4">
  <div className="w-full max-w-md bg-white rounded-lg border border-stone-200 p-8">
```

No shadow on auth card. Uses `max-w-md` to accommodate social buttons + form fields.

---

## Floating Queue Panel

Persistent progress panel for background worker tasks (transcription, summarization). Anchored to viewport bottom-right, visible above page content but below modals.

```tsx
<div className="fixed bottom-4 right-4 z-50 w-80 bg-white border border-stone-200 rounded-lg overflow-hidden">
```

| Property | Value | Rationale |
|----------|-------|-----------|
| Position | `fixed bottom-4 right-4` | Viewport-anchored, always visible |
| Width | `w-80` (320px) | Compact, doesn't compete with main content |
| Max height | `max-h-64` on items list | Scrollable when >4 items |
| Z-index | `z-50` | Above page, below modals (`z-50` < dialog overlay) |
| Surface | `bg-white border border-stone-200 rounded-lg` | Standard surface treatment |
| Depth | No shadow (borders only) | Design system compliant |
| Header border | `border-stone-100` | Lighter than outer border — whispers separation |
| Item dividers | `divide-y divide-stone-100` | On parent, not per-item `border-b` |

**Collapsed state**: Compact pill with active count and status dot. Uses `bg-primary animate-pulse` dot for active, `bg-emerald-500` for complete.

**Item layout**: `items-start` flex with `gap-2.5`. Icon at top-aligned with first text line (`mt-0.5`). Content column holds name, stage label, and compact segmented progress bar. No magic-number `ml-[]` offsets — content flows naturally inside the flex column.

**Compact progress bar**: 6 thin segments (`h-1 rounded-full gap-0.5`), one per pipeline stage. Pending: `bg-stone-100`. Active: `bg-primary animate-pulse`. Complete: `bg-emerald-500`. Each segment has a `title` tooltip with the stage name. Only rendered during processing state.

**Item states**: Processing (spinner + stage label + progress bar), done (emerald checkmark, clickable with `active:bg-stone-100`), failed (red X + red error text).

**Interactive feedback**: All buttons have `hover:bg-stone-50 active:bg-stone-100`. Done items respond to hover and press. Header action icons use `p-1.5 rounded-lg` hit targets.
