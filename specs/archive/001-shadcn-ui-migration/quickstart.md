# Quickstart: shadcn/ui Migration

## Prerequisites

- Node.js 20+
- npm (project package manager)
- Frontend dev server: `cd frontend-2 && npm run dev`

## Setup Steps

### 1. Initialize shadcn/ui

```bash
cd frontend-2
npx shadcn@latest init
```

When prompted:
- Style: **New York** (default for new projects)
- Base color: **Stone**
- CSS variables: **Yes**

This creates `components.json` and updates `globals.css` with theme CSS variables.

### 2. Configure component paths

Edit `frontend-2/components.json` to set aliases:

```json
{
  "aliases": {
    "components": "@/app/components",
    "ui": "@/app/components/ui",
    "lib": "@/app/lib",
    "hooks": "@/app/hooks",
    "utils": "@/app/lib/utils"
  }
}
```

### 3. Install components

```bash
cd frontend-2
npx shadcn@latest add button badge dropdown-menu alert-dialog dialog tabs input tooltip
```

### 4. Apply rose theme + shadow overrides

Update `frontend-2/app/globals.css`:
- Replace CSS variables with rose theme values (OKLCH color space for Tailwind v4)
- Override `--primary` with indigo-600 OKLCH values
- Add shadow overrides to neutralize all shadows

### 5. Verify

```bash
cd frontend-2 && npx tsc --noEmit   # TypeScript check
cd frontend-2 && npm run build       # Production build
```

## Verification Scenarios

### Summary Toolbar (US1)

1. Navigate to a completed meeting → Summary tab
2. Verify toolbar appears with Edit, Exports, Templates buttons
3. Click Exports → verify Copy, Download .txt, Download PDF options
4. Click Templates → verify template list loads with current template checked
5. Select different template → verify confirmation dialog appears
6. Click Edit → verify editor opens (toolbar hides)

### Component Migration (US2)

1. Login page → verify OAuth buttons and form inputs render correctly
2. Dashboard → verify meeting cards show status badges
3. Click profile → verify dropdown menu appears with logout option
4. Upload a file → verify upload modal uses standard dialog
5. Inspect any page → verify zero shadow classes in rendered output

### Design System (US3)

1. Open `.interface-design/system.md`
2. Verify shadcn/ui documented as component library
3. Verify rose theme + stone neutrals documented
4. Verify no references to old custom components
