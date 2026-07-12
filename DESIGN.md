# Zabt Design System

## 1. Visual Theme & Atmosphere

Zabt's design is warm minimal — a productivity tool that feels approachable rather than clinical. The interface is built on warm stone neutrals with a pink/rose accent that adds energy without aggression. The aesthetic sits between Notion's papery warmth and Cal.com's monochromatic restraint.

The canvas is off-white (`oklch(0.985)`) — warmer than pure white, creating a subtle paper-like quality. Text uses warm near-black (`oklch(0.147)`) instead of pure black, softening the reading experience. The entire neutral scale carries warm undertones through OkLch color space, avoiding the cold blue-grays of typical UI frameworks.

Pink/rose (`oklch(0.586 0.253 17.585)`) is the single saturated color in the core UI. It appears on primary buttons, active navigation states, focus rings, and interactive accents. Everything else is warm neutral. This creates a calm interface where CTAs and active elements naturally draw the eye without competing for attention.

Depth comes from borders and background color changes, not shadows. All shadow tokens are reset to `0 0 #0000`. Borders are whisper-weight — `1px solid` using the border token — barely perceptible division lines that create structure without visual weight. The 10px base border radius gives components a generous, friendly rounding.

Dark mode uses rich warm charcoal backgrounds with semi-transparent white borders (`oklch(1 0 0 / 10%)`) that adapt naturally to any surface color.

**Key Characteristics:**
- Inter for all UI text, JetBrains Mono for code/technical content
- Warm stone neutral palette via OkLch color space
- Pink/rose as the singular accent color for CTAs and interactive elements
- Shadow-free depth — borders and background shifts only
- 10px base border radius, pill badges at full radius
- Full dark mode with semi-transparent borders
- shadcn/ui component library with @base-ui/react primitives

## 2. Color Palette & Roles

### Light Mode

| Role | Token | Value | Use |
|------|-------|-------|-----|
| Background | `--background` | `oklch(0.985 0.001 106.423)` | Page canvas, card surfaces, popovers |
| Foreground | `--foreground` | `oklch(0.147 0.004 49.25)` | Primary text, headings |
| Primary | `--primary` | `oklch(0.586 0.253 17.585)` | CTAs, active nav, focus rings, links |
| Primary Foreground | `--primary-foreground` | `oklch(0.985 0 0)` | Text on primary buttons |
| Secondary | `--secondary` | `oklch(0.97 0.001 106.424)` | Secondary button fills, hover backgrounds |
| Secondary Foreground | `--secondary-foreground` | `oklch(0.216 0.006 56.043)` | Text on secondary surfaces |
| Muted | `--muted` | `oklch(0.97 0.001 106.424)` | Disabled backgrounds, subtle fills |
| Muted Foreground | `--muted-foreground` | `oklch(0.553 0.013 58.071)` | Secondary text, placeholders, captions |
| Accent | `--accent` | `oklch(0.97 0.001 106.424)` | Hover states, subtle highlights |
| Border | `--border` | `oklch(0.923 0.003 48.717)` | Card outlines, dividers, input borders |
| Input | `--input` | `oklch(0.923 0.003 48.717)` | Input field borders |
| Ring | `--ring` | `oklch(0.586 0.253 17.585)` | Focus ring color (matches primary) |
| Destructive | `--destructive` | `oklch(0.577 0.245 27.325)` | Error states, delete actions |

### Dark Mode

| Role | Token | Value | Notes |
|------|-------|-------|-------|
| Background | `--background` | `oklch(0.147 0.004 49.25)` | Rich warm charcoal |
| Card | `--card` | `oklch(0.216 0.006 56.043)` | Elevated surface, slightly lighter than bg |
| Primary | `--primary` | `oklch(0.696 0.208 16.57)` | Lighter, less saturated for dark bg contrast |
| Secondary | `--secondary` | `oklch(0.268 0.007 34.298)` | Dark surface variant |
| Muted | `--muted` | `oklch(0.268 0.007 34.298)` | Matches secondary in dark mode |
| Muted Foreground | `--muted-foreground` | `oklch(0.709 0.01 56.259)` | Lighter for readability on dark bg |
| Accent | `--accent` | `oklch(0.371 0.01 67.558)` | Warm mid-gray for hover states |
| Border | `--border` | `oklch(1 0 0 / 10%)` | Semi-transparent white, adapts to any surface |
| Input | `--input` | `oklch(1 0 0 / 15%)` | Slightly more visible than border |
| Destructive | `--destructive` | `oklch(0.704 0.191 22.216)` | Brighter red for dark bg visibility |

### Chart Colors (Both Modes)

Five-step blue-purple scale for data visualization:
- Chart 1: `oklch(0.809 0.105 251.813)` — lightest blue
- Chart 2: `oklch(0.623 0.214 259.815)`
- Chart 3: `oklch(0.546 0.245 262.881)`
- Chart 4: `oklch(0.488 0.243 264.376)`
- Chart 5: `oklch(0.424 0.199 265.638)` — deepest purple

### Sidebar (Both Modes)

The sidebar uses its own token set that mirrors the main palette:
- Light: white background, pink primary, warm stone accents
- Dark: charcoal background (`oklch(0.216)`), lighter pink primary, semi-transparent border

### Color Principles
- Pink is the only saturated color in core UI chrome
- Warm neutrals throughout — never blue-gray
- Dark mode inverts luminance but preserves warmth
- Semi-transparent borders in dark mode (`oklch(1 0 0 / 10%)`) adapt to any surface
- Destructive red is the only other saturated color, reserved for errors and delete actions

## 3. Typography Rules

### Font Stack
- **Sans:** Inter (`--font-inter`) — all UI text, headings, body, navigation
- **Mono:** JetBrains Mono (`--font-jetbrains-mono`) — code blocks, transcript timestamps, technical data

### Hierarchy

| Role | Size | Weight | Tailwind | Use |
|------|------|--------|----------|-----|
| Page Title | 24px | 700 | `text-2xl font-bold` | Page headings ("Integrations", greeting) |
| Section Heading | 18px | 600 | `text-lg font-semibold` | Section titles within pages |
| Card Title | 16px | 600 | `text-base font-semibold` | Card headings, list item titles |
| Body | 14px | 400 | `text-sm` | Standard reading text, descriptions |
| Body Medium | 14px | 500 | `text-sm font-medium` | Nav links, form labels, interactive text |
| Caption | 12px | 500 | `text-xs font-medium` | Section headers, metadata labels |
| Badge Text | 12px | 400 | `text-xs` | Status badges, tags, timestamps |

### Color Hierarchy
Text color carries as much hierarchy as weight:
- `text-stone-900` / `--foreground` — primary text, headings, active nav
- `text-stone-600` — secondary text, inactive nav items, descriptions
- `text-stone-500` / `--muted-foreground` — tertiary text, subtitles, helper text
- `text-stone-400` — muted text, section labels, disabled states
- `text-primary` — interactive text, links, active states

### Principles
- Three weights in practice: 400 (read), 500 (interact), 600-700 (announce)
- `text-sm` (14px) is the workhorse — body, labels, nav links all live here
- No custom letter-spacing — Inter handles this well at all sizes
- Line heights use Tailwind defaults (tighter for headings, relaxed for body)
- Uppercase `text-xs` with `text-stone-400` for section labels (e.g., sidebar groups)

## 4. Component Patterns

### Buttons (shadcn/ui + CVA)

| Variant | Background | Text | Border | Use |
|---------|-----------|------|--------|-----|
| Default | `--primary` (pink) | `--primary-foreground` | none | Primary CTAs — "Connect", "Send", "Sign in" |
| Outline | transparent | foreground | `--border` | Secondary actions — "Disconnect", "Cancel" |
| Secondary | `--secondary` | `--secondary-foreground` | none | Tertiary actions |
| Ghost | transparent | foreground | none | Inline actions, icon buttons, nav items |
| Destructive | `--destructive` | white | none | Delete, remove actions |
| Link | transparent | `--primary` | none | Inline text links |

- Sizes: `xs` (h-6), `sm` (h-7), `default` (h-8), `lg` (h-9), plus icon variants
- All use `rounded-lg` (10px base radius)
- Loading state: spinner replaces content, button disabled
- Focus: border + ring at 50% opacity
- Built on `@base-ui/react` headless primitives

### Cards & Containers
- Background: `--card` (white in light, charcoal in dark)
- Border: `1px solid` using `--border` token
- Radius: `rounded-lg` (10px)
- No box shadows — depth from border + background contrast only
- Padding: `p-4` to `p-5` depending on content density

### Inputs
- Height: `h-8`
- Border: `--input` token, `rounded-lg`
- Focus: border shifts + 3px ring at `ring/50` opacity
- Dark mode: `bg-input/30` (semi-transparent fill)
- Placeholder: `--muted-foreground` color
- Built on `@base-ui/react/input`

### Badges
- Shape: pill (`rounded-4xl`), height `h-5`
- Variants mirror button variants (default, secondary, outline, destructive)
- Used for: status ("Connected", "Teams"), categories, tags
- Font: `text-xs`

### Toggle Switch (Custom)
- Track: 20px height, 36px width, `rounded-full`
- Active: `bg-stone-900` (dark track), inactive: `bg-stone-200`
- Thumb: 14px white circle with transform transition
- Used for: auto-join toggles on calendar events

### Dialogs (shadcn/ui)
- Overlay: semi-transparent black backdrop
- Content: `--card` background, `rounded-lg`, `--border`
- Header: title + optional description
- Footer: action buttons right-aligned
- Used for: upload modal, share email, confirmations

### Dropdown Menus (shadcn/ui)
- Background: `--popover`, border: `--border`
- Items: `text-sm`, hover with `--accent` background
- Separators: `--border` with margin
- Used for: profile menu, summary toolbar actions

## 5. Layout Principles

### Spacing System
- Tailwind's default scale: 1 (4px), 2 (8px), 3 (12px), 4 (16px), 5 (20px), 6 (24px), 8 (32px)
- Component internal padding: `p-4` (16px) to `p-5` (20px)
- Section gaps: `mb-8` (32px) to `mb-10` (40px)
- Page padding: `px-8 py-8` (32px)

### Page Structure
- Fixed sidebar (220px) on the left with border-right
- Content area fills remaining width
- Max content width: `max-w-3xl` (768px) for form-like pages (integrations, templates)
- No max-width constraint for feed pages (home, meetings list)
- Content vertically scrolls, sidebar is fixed

### Grid Patterns
- Meeting feed: single column, full width cards
- Calendar events: single column, grouped by date
- Template grid: responsive cards
- Integration cards: single column, stacked

### Whitespace Philosophy
- Generous vertical rhythm between sections (32-40px)
- Compact within components (8-16px internal padding)
- Page titles get their own breathing room (`mb-8`)
- Lists use `space-y-2` to `space-y-3` for item gaps

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | No border, no shadow | Page background, section fills |
| Surface | `1px solid --border` | Cards, containers, inputs, sidebar |
| Elevated | `--card` background + border | Popovers, dropdowns, dialogs |
| Overlay | Semi-transparent backdrop | Modal overlays, dialog backgrounds |
| Focus | Ring at `ring/50` opacity | Keyboard focus on interactive elements |

**Depth Philosophy:** Zabt uses a flat, border-driven depth model. There are no box shadows anywhere in the system (all shadow tokens are `0 0 #0000`). Elevation is communicated through:
1. Background color shifts (white card on off-white page)
2. Borders (whisper-weight `1px solid`)
3. Overlays (backdrop blur for modals)

This creates a clean, paper-like layering that feels physical without the visual noise of drop shadows. In dark mode, semi-transparent white borders (`oklch(1 0 0 / 10%)`) create subtle light-edge depth.

## 7. Responsive Behavior

### Breakpoints
Standard Tailwind breakpoints:

| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <640px (`sm`) | Sidebar collapses, single column, reduced padding |
| Tablet | 640-1024px (`md`) | Sidebar toggleable, content fills width |
| Desktop | 1024px+ (`lg`) | Fixed sidebar + content area, full layout |

### Collapsing Strategy
- **Sidebar:** Fixed at desktop, collapsible drawer at mobile/tablet
- **Page content:** `px-8` desktop, reduces to `px-4` mobile
- **Cards:** Full width at all breakpoints (single column layout)
- **Dialogs:** Centered overlay at desktop, bottom sheet pattern at mobile
- **Meeting detail tabs:** Horizontal tab bar persists at all sizes

### Touch Targets
- All buttons minimum h-7 (28px) for touch
- Navigation items have comfortable padding
- Toggle switches sized for finger interaction (36px wide)
- Badge tap targets have adequate padding

## 8. Accessibility & States

### Interactive States

| State | Treatment |
|-------|-----------|
| Default | Standard appearance with border token |
| Hover | Background shifts to `--accent`, text darkens |
| Active/Pressed | Slightly darker background, scale optional |
| Focus | Border + 3px ring at `ring/50` opacity |
| Disabled | `opacity-50`, pointer-events none |
| Loading | Spinner replaces content, element disabled |

### Focus System
- All interactive elements receive visible focus indicators
- Focus ring: `outline-ring/50` (applied globally via `@layer base`)
- Ring width: 3px for inputs, 2px for buttons
- Tab navigation supported throughout
- Focus ring uses primary pink color for consistent visual language

### Color Contrast
- Primary text on background: warm near-black on off-white exceeds WCAG AAA
- Muted foreground on background: meets WCAG AA
- Primary pink on white: meets WCAG AA for large text (buttons)
- Dark mode: all contrast ratios maintained through token inversion

### Screen Reader Support
- Semantic HTML elements throughout (nav, main, section, button)
- ARIA labels on icon-only buttons
- Role attributes on custom controls (toggle switches use `role="switch"`)
- Status badges use appropriate ARIA attributes

## 9. Agent Prompt Guide

### Quick Token Reference

**Light mode:**
- Background: `oklch(0.985 0.001 106.423)` — off-white canvas
- Foreground: `oklch(0.147 0.004 49.25)` — warm near-black text
- Primary: `oklch(0.586 0.253 17.585)` — pink/rose accent
- Border: `oklch(0.923 0.003 48.717)` — whisper-weight stone
- Muted text: `oklch(0.553 0.013 58.071)` — warm medium gray
- Radius: `0.625rem` (10px)

**Dark mode:**
- Background: `oklch(0.147 0.004 49.25)` — warm charcoal
- Card: `oklch(0.216 0.006 56.043)` — elevated charcoal
- Primary: `oklch(0.696 0.208 16.57)` — lighter pink
- Border: `oklch(1 0 0 / 10%)` — semi-transparent white

### Component Creation Prompts

- "Create a page section: off-white background (`--background`). Page title at `text-2xl font-bold text-stone-900`. Subtitle at `text-sm text-stone-500 mt-1`. Content area with `px-8 py-8`. Max width `max-w-3xl` for form pages."

- "Create a card: `--card` background, `1px solid --border`, `rounded-lg`. Internal padding `p-5`. Title at `text-base font-semibold text-stone-900`. Description at `text-sm text-stone-500`. No shadows."

- "Create a primary button: `--primary` background (pink), `--primary-foreground` text (white), `rounded-lg`, `h-8 px-4`. Hover darkens slightly. Focus shows ring at 50% opacity. Use shadcn Button component with `size='sm'`."

- "Create a status badge: pill shape (`rounded-4xl`), `h-5`, `text-xs`. Use `variant='outline'` from shadcn Badge. For connected status: green text + green border + green-50 background."

- "Create a list with toggles: items in `space-y-2`. Each item: `border rounded-lg p-4 bg-white`. Title at `font-medium text-stone-900`. Metadata at `text-sm text-stone-500`. Toggle switch right-aligned with `bg-stone-900` active, `bg-stone-200` inactive."

### Design Guardrails
1. Pink is the ONLY saturated color in core UI — do not introduce new accent colors
2. No box shadows — use borders and background shifts for depth
3. Warm stone neutrals only — never blue-gray (`slate`, `gray`, `zinc` are wrong, use `stone`)
4. `text-sm` (14px) for all body text — do not use `text-base` (16px) for standard UI text
5. `rounded-lg` (10px) for all containers — do not use sharp corners or excessive rounding
6. Borders are whisper-weight (`--border` token) — never use `border-2` or darker borders
7. Three font weights: 400, 500, 600-700. Do not use 300 (thin) or 800-900 (heavy)
8. Dark mode uses semi-transparent borders — never use solid light-colored borders on dark
9. Icons from lucide-react only — consistent stroke width and style
10. Spacing uses Tailwind scale — no arbitrary pixel values
