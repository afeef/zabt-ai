# Research: shadcn/ui Migration

## Decision 1: shadcn/ui + Tailwind CSS v4 Compatibility

**Decision**: shadcn/ui fully supports Tailwind CSS v4. Use `npx shadcn@latest init` — the CLI auto-detects v4 and configures accordingly.

**Rationale**: shadcn/ui added Tailwind v4 support in February 2025. The CLI detects the CSS-first config (`@import "tailwindcss"` + `@theme inline` in globals.css, `@tailwindcss/postcss` in postcss.config) and generates v4-compatible components. Colors use OKLCH color space. The project already has the correct v4 setup — no tailwind.config.js exists or is needed.

**Alternatives considered**: Manual component copying without CLI — rejected because the CLI handles dependency installation, path configuration, and v4-specific color format conversions automatically.

## Decision 2: Theme Selection — Rose + Stone Neutrals

**Decision**: Use the shadcn/ui "rose" base theme with "stone" neutral palette. Override `--primary` to use indigo-600 for accent color consistency.

**Rationale**: The rose theme paired with stone neutrals closely matches the existing Zabt design system (stone backgrounds/borders, indigo accent). The rose theme provides warm tones that align with the "warm notebook" feel described in system.md. Overriding `--primary` to indigo is a single CSS variable change in globals.css.

**Alternatives considered**:
- Default theme — too neutral/cold, doesn't match the "warm notebook" feel.
- Custom theme from scratch — unnecessary work when rose + stone gives us 95% of what we need.

## Decision 3: Component Output Path

**Decision**: Configure `components.json` aliases to output shadcn/ui components to `app/components/ui/` (matching existing convention).

**Rationale**: The project already has custom components at `frontend-2/app/components/ui/`. Using the same path means shadcn/ui components will replace custom ones in-place. The `components.json` aliases section supports this: `"ui": "@/app/components/ui"`. The `cn()` utility will go to `app/lib/utils.ts`.

**Alternatives considered**: Using `components/ui/` at project root — rejected because it breaks the established convention and requires import path changes across all files.

## Decision 4: Shadow Removal (Borders-Only Depth Rule)

**Decision**: Override all Tailwind shadow theme tokens to transparent in globals.css `@theme inline` block. This globally neutralizes all shadow utilities project-wide.

**Rationale**: shadcn/ui components use Tailwind shadow classes (`shadow-sm`, `shadow-md`, etc.). Rather than editing each generated component file, a single theme override enforces the borders-only rule globally:
```css
@theme inline {
  --shadow-xs: 0 0 #0000;
  --shadow-sm: 0 0 #0000;
  --shadow: 0 0 #0000;
  --shadow-md: 0 0 #0000;
  --shadow-lg: 0 0 #0000;
  --shadow-xl: 0 0 #0000;
  --shadow-2xl: 0 0 #0000;
}
```
This is the cleanest approach — one change, project-wide effect, no per-component maintenance.

**Alternatives considered**: Per-component shadow class removal — more work, fragile (new components would need manual editing each time).

## Decision 5: Components to Install

**Decision**: Install these shadcn/ui components via CLI:

| Component | Replaces | Used By |
|-----------|----------|---------|
| button | Custom Button (button.tsx) | All pages, modals, toolbar |
| badge | Custom StatusBadge (status-badge.tsx) | MeetingCard, meeting detail, toolbar "Edited" indicator |
| dropdown-menu | Custom SummaryMenu dropdown, ProfileMenu | Summary toolbar (exports + templates), sidebar profile |
| alert-dialog | Custom confirmation modals (inline) | Re-summarize confirmation, logout confirmation, delete meeting |
| dialog | Custom modal patterns (inline) | Upload modal, template picker, template editor, paywall |
| tabs | Custom tab buttons (inline) | Meeting detail page (Summary/Transcript tabs) |
| input | Custom input fields (inline) | Login, register, forgot-password, template editor |
| tooltip | None (new) | Toolbar icon buttons |

**Rationale**: These cover all interactive patterns in the app. Each component is built on Radix UI primitives, providing keyboard accessibility and consistent behavior by default.

**Not installing**: Separator (can use `<hr>` or border), Label (simple enough with plain elements), Form (would require form library integration that's out of scope).

## Decision 6: SummaryToolbar Architecture

**Decision**: Create a new `SummaryToolbar` composite component that contains Edit button, Exports DropdownMenu, and Templates DropdownMenu. The existing `SummaryMenu` component will be refactored to only handle template selection (removing the export section) and will be inlined into the toolbar's Templates dropdown.

**Rationale**: Separating the toolbar into its own component keeps the meeting detail page clean. The toolbar only renders for completed meetings on the Summary tab. The old SummaryMenu mixed concerns (templates + exports) — splitting them into separate dropdowns follows single-responsibility principle.

**Alternatives considered**: Modifying SummaryMenu to be the toolbar — rejected because the component structure would become unwieldy (it already has complex template fetching + confirmation dialog logic).

## Decision 7: TooltipProvider Placement

**Decision**: Wrap the dashboard layout with `<TooltipProvider>` since shadcn/ui Tooltip requires it as a context provider.

**Rationale**: All tooltip-using components are within the dashboard layout. Adding it there covers the toolbar and all other dashboard pages. It doesn't need to be at the root layout since auth pages don't use tooltips.

**Alternatives considered**: Root layout — would work but unnecessarily wraps auth pages. Per-component — too much boilerplate.
