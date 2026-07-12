# Data Model: Edit Summary Markdown In-App

**Feature**: 001-edit-summary | **Date**: 2026-03-09

## Entity Changes

### Meeting (existing — extended)

| Field | Type | Default | New? | Description |
|-------|------|---------|------|-------------|
| `id` | `int` (PK) | auto | No | — |
| `summary_text` | `Optional[str]` | `None` | No | Current summary content (markdown). Updated by AI pipeline or user edits. |
| `original_summary_text` | `Optional[str]` | `None` | **Yes** | Frozen copy of the first AI-generated summary. Set on first user edit; never overwritten by subsequent edits. Cleared only on "restore original" action. |
| `summary_edited` | `bool` | `False` | **Yes** | `True` when user has modified the summary. Used by frontend to show "Edited" badge. Reset to `False` on restore. |

### State Transitions

```text
Initial state (AI completes summary):
  summary_text = "<AI output>"
  original_summary_text = NULL
  summary_edited = False

First user edit:
  original_summary_text = summary_text  (copy before overwrite)
  summary_text = "<user edit>"
  summary_edited = True

Subsequent user edits:
  summary_text = "<user edit>"          (original_summary_text unchanged)
  summary_edited = True

Restore original:
  summary_text = original_summary_text
  summary_edited = False
  original_summary_text = (preserved — still available for future edits)
```

### Migration Notes

- Two new nullable columns on the `meeting` table: `original_summary_text TEXT NULL`, `summary_edited BOOLEAN NOT NULL DEFAULT FALSE`
- Existing rows: `original_summary_text` stays `NULL`, `summary_edited` defaults to `FALSE` — no data migration needed
- No index needed on either field (not queried/filtered by these columns)

## Response Model Changes

### MeetingRead (extended)

Add two fields to the existing `MeetingRead` SQLModel:

| Field | Type | Description |
|-------|------|-------------|
| `original_summary_text` | `Optional[str]` | Original AI summary (null if never edited) |
| `summary_edited` | `bool` | Whether the summary has been user-edited |

### MeetingSummaryUpdate (new request model)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary_text` | `str` | Yes | Updated markdown content |

### MeetingSummaryRestore (no body)

The restore endpoint takes no request body — it copies `original_summary_text` back to `summary_text`.
