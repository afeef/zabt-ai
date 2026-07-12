# Data Model: Home Page Redesign

**Feature**: 005-home-redesign  
**Date**: 2026-02-22

---

## Entities

This feature is a **read-only frontend layout change**. No new database entities or backend models are introduced. The following existing entities are consumed by the new UI components:

---

### Meeting (existing, read-only in this feature)

Source: `GET /api/v1/meetings/` → `MeetingList.items`

| Field | Type | Used By |
|-------|------|---------|
| `id` | `number` | Navigation link to `/meetings/[id]` |
| `title` | `string` | MeetingFeedCard title |
| `summary_text` | `string \| null` | MeetingFeedCard preview (first 150 chars) |
| `created_at` | `string` (ISO 8601) | Date group header; relative timestamp |
| `status` | `"queued" \| "processing" \| "completed" \| "failed"` | StatusBadge in feed card |

No new fields are required on this entity.

---

### User (existing, read-only)

Source: Supabase `getUser()` → `user.user_metadata`

| Field | Path | Used By |
|-------|------|---------|
| `full_name` | `user.user_metadata.full_name` | Greeting, sidebar avatar initials |
| `email` | `user.email` | Sidebar secondary label |

---

## UI State Model

Client-side state managed per component (no global state store introduced):

### AppShell
| State | Type | Purpose |
|-------|------|---------|
| `sidebarOpen` | `boolean` | Mobile: toggle off-canvas drawer |

### HomePage
| State | Type | Purpose |
|-------|------|---------|
| `meetings` | `Meeting[]` | Feed data |
| `loading` | `boolean` | Skeleton display |
| `error` | `string \| null` | Error banner |
| `query` | `string` | AI query bar controlled input |
| `userName` | `string` | Greeting personalization |

### Sidebar
| State | Type | Purpose |
|-------|------|---------|
| `userName` | `string` | Display name |
| `userEmail` | `string` | Email hint |
| `channelsOpen` | `boolean` | Collapsible section |
| `dmOpen` | `boolean` | Collapsible section |
| `foldersOpen` | `boolean` | Collapsible section |

---

## Date Grouping Logic (feed)

Meetings from `getMeetings()` are grouped client-side by `created_at` date:

```
groups = groupBy(meetings, formatDateLabel(created_at))

formatDateLabel(date):
  if same calendar day as today → "Today, [Month Day]"
  if yesterday               → "Yesterday"
  else                       → "[Weekday], [Month Day]"
```

No backend changes needed — grouping is purely client-side.
