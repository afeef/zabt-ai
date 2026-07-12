# UI Contract: Summary Toolbar

**Component**: `SummaryToolbar`
**Location**: `frontend-2/app/components/summary-toolbar.tsx`
**Rendered In**: Meeting detail page, Summary tab only, completed meetings only

## Layout

Horizontal toolbar row positioned between the tab bar and the summary content area.

```
┌──────────────────────────────────────────────────────────────┐
│ [Edit] [Edited badge?] [View Original?] │ [Exports ▾] [Templates ▾] │
└──────────────────────────────────────────────────────────────┘
```

Left side: Edit button + contextual controls (Edited badge, View Original, Restore Original)
Right side: Exports dropdown + Templates dropdown

## Props

```typescript
interface SummaryToolbarProps {
  meeting: Meeting;
  isEditing: boolean;
  showOriginal: boolean;
  onEdit: () => void;
  onCopySummary: () => void;
  onDownloadTxt: () => void;
  onDownloadPdf: () => Promise<void>;
  onViewOriginal: () => void;
  onRestoreOriginal: () => Promise<void>;
  // Template props
  currentTemplateId: number | null;
  currentTemplateName: string | null;
  onResummarizeStarted: () => void;
  disabled?: boolean;
}
```

## Visibility Rules

| Condition | Toolbar Visible? |
|-----------|-----------------|
| Summary tab + completed meeting | Yes |
| Summary tab + processing/queued/failed meeting | No |
| Transcript tab | No |
| Currently editing (isEditing=true) | No (editor has its own save/cancel buttons) |
| Viewing original (showOriginal=true) | Partial — only View Current + Restore buttons shown |

## Edit Button

- Icon: Pencil (lucide-react)
- Label: "Edit" (text visible on desktop, icon-only on mobile with tooltip)
- Action: Calls `onEdit()` to enter editing mode
- Hidden when `isEditing` is true

## Edited Badge + Original Controls

Visible only when `meeting.summary_edited === true`:

- **Edited badge**: shadcn/ui Badge (secondary variant), text "Edited"
- **View Original / View Current**: Toggle button calling `onViewOriginal()`
- **Restore Original**: Visible only when `showOriginal === true`, calls `onRestoreOriginal()`, uses shadcn/ui AlertDialog for confirmation

## Exports Dropdown

- Trigger: Button with "Export" label + ChevronDown icon
- Component: shadcn/ui DropdownMenu

| Item | Icon | Action |
|------|------|--------|
| Copy summary | Copy (lucide) | `onCopySummary()` — copies markdown to clipboard |
| Download as .txt | FileText (lucide) | `onDownloadTxt()` — downloads plain text file |
| Download as PDF | FileDown (lucide) | `onDownloadPdf()` — calls server PDF export endpoint |

## Templates Dropdown

- Trigger: Button showing "Template: {name}" + ChevronDown icon
- Component: shadcn/ui DropdownMenu
- On open: Fetches templates list from API

| Section | Content |
|---------|---------|
| Header | "Templates" label + New (plus icon) + Manage (settings icon) links |
| Built-in | List of built-in templates, current template has checkmark |
| My Templates | List of custom templates (hidden if none), current template has checkmark |

- Selecting a template triggers shadcn/ui AlertDialog confirmation: "Re-summarize with '{name}'? This will replace the current summary."
- Confirm button calls `resummarizeMeeting(meetingId, templateId)` API

## PostHog Events Preserved

| Event | When |
|-------|------|
| `summary_exported` | After successful PDF export from Exports dropdown |
| `summary_edited` | After saving an edit (handled by parent, not toolbar) |
| `summary_restored` | After restoring original (handled by parent, not toolbar) |

## Keyboard Accessibility

- All buttons reachable via Tab
- Dropdowns open with Enter/Space, navigate with Arrow keys, close with Escape
- AlertDialog traps focus, Cancel via Escape, Confirm via Enter
- Provided by shadcn/ui (Radix UI primitives) by default
