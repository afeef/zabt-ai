# UI Contract: Export Summary as PDF

**Feature**: `001-export-summary-pdf`
**Type**: UI interaction contract (no backend API changes)

---

## Export Trigger

**Location**: Summary options menu (three-dot `···` button in the summary tab header), below the existing "Download as .txt" item.

**Label**: "Download as PDF"

**Icon**: Download/file icon (consistent with existing Download as .txt icon style — 14×14px stroke SVG)

**Visibility rules**:
- The menu item is **only rendered** when `meeting.status === "completed"` AND `meeting.summary_text` is non-empty
- While `pdfmake` is generating (async), the button shows a loading state or is temporarily disabled

---

## Exported PDF Content Contract

### Header Section (top of document)

| Field | Source | Condition |
|-------|--------|-----------|
| Meeting title | `meeting.title` | Always included |
| Date | `meeting.created_at` formatted as "Mon, Mar 4, 2026, 6:50 AM" | Always included |
| Duration | `meeting.duration_seconds` converted to "X min" | Included if `duration_seconds` is not null |
| Speakers | `meeting.speakers` — all speaker names joined by ", " | Included if `speakers` object is non-empty |
| Horizontal rule | Static separator line | Always included |

### Body Section

| Content | Source | Rendering |
|---------|--------|-----------|
| Summary | `meeting.summary_text` | Markdown parsed: headings, bold, italic, bullet lists → formatted PDF nodes |
| Action items | `meeting.action_items_text` | Appended below summary if non-empty, with "Action Items" section heading |

### Document Metadata (PDF file properties)

| Property | Value |
|----------|-------|
| Title | `meeting.title` |
| Author | "Zabt" |
| Subject | "Meeting Summary" |
| Creator | "Zabt AI" |

---

## Filename Contract

```
{sanitized_title}-summary.pdf
```

- `sanitized_title`: `meeting.title` with characters `/ \ : * ? " < > |` replaced by `-`, trimmed of leading/trailing whitespace and hyphens
- Example: `"Afeef with Irfan Lodhi.mp4"` → `"Afeef with Irfan Lodhi.mp4-summary.pdf"`
- Example: `"Q1/2026 Planning: Strategy"` → `"Q1-2026 Planning- Strategy-summary.pdf"`

---

## Error States

| Scenario | Behaviour |
|----------|-----------|
| `summary_text` is null or empty | Menu item is not rendered |
| `pdfmake` load failure (rare) | `console.error` logged; user sees no download (silent fail for MVP) |
| Browser blocks auto-download | Browser's native download prompt appears (acceptable fallback) |
