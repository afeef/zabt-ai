# UI Contracts: Home Page UI Redesign

## 1. MeetingFeedCard (redesigned)

**Component**: `meeting-feed.tsx` (existing, modified)

**Props** (unchanged from existing Meeting type):
- `id`: number
- `title`: string
- `created_at`: string (ISO datetime)
- `status`: "pending_upload" | "queued" | "processing" | "completed" | "failed"
- `sub_status`: string | null
- `summary_text`: string | null
- `file_name`: string | null
- `duration_seconds`: number | null (from API, if available)
- `owner_name`: string | null (from API, if available)

**Rendered Layout**:
```
┌─────────────────────────────────────────────────────┐
│ [Avatar]  Meeting Title (bold heading)              │
│           10:23 AM · 37 sec · Speaker Name          │
│                                                     │
│           Summary preview text that can span up     │
│           to 2-3 lines before being truncated with  │
│           a "Show more" affordance...               │
│           Show more                                 │
│                                                     │
│                                          [badges]   │
└─────────────────────────────────────────────────────┘
```

**States**:
- Completed with summary: Full card with summary preview
- Processing: Title + metadata + status badge (no summary area)
- Failed: Title + metadata + red status badge + error subtitle
- Pending: Title + metadata + gray status badge

---

## 2. ActionBar (new)

**Component**: `action-bar.tsx` (new)

**Props**:
- `onImportClick`: () => void — opens the upload modal

**Rendered Layout**:
```
                              [📹 URL]  [Import]  [🔴 Record]
```

**Button Specs**:
- **Meeting URL**: Icon-only button (camera/video icon), outlined style, `title="Coming soon"`
- **Import**: Text button, outlined/secondary style, opens upload modal via `onImportClick`
- **Record**: Primary button with red accent, microphone icon + "Record" text, `title="Coming soon"`

---

## 3. Sidebar Navigation (modified)

**Current items**: Home, AI Chat, Meetings, Integrations
**New items**: Home, AI Chat, Integrations

Remove the "Meetings" entry from the navigation items array.

---

## 4. Right Panel Quick Actions (modified)

**Current**: "Upload a meeting" (primary button)
**New**: "Import" (primary button, same onClick behavior)

---

## 5. Meetings List Page (redirect)

**Route**: `/meetings`
**Behavior**: Immediate redirect to `/` (home page)
**Note**: `/meetings/[id]` (detail page) remains unchanged.
