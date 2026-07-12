# Quickstart: Edit Summary Markdown In-App

**Feature**: 001-edit-summary | **Date**: 2026-03-09

## New Environment Variables

None. This feature requires no new environment variables.

## New Dependencies

### Frontend (`frontend-2/`)

```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-link tiptap-markdown
```

| Package | Purpose |
|---------|---------|
| `@tiptap/react` | React bindings for Tiptap editor |
| `@tiptap/starter-kit` | Bundle of common extensions (bold, italic, headings, lists, code, blockquote) |
| `@tiptap/extension-link` | Link editing support |
| `tiptap-markdown` | Markdown serialization/deserialization for Tiptap |

### Backend

No new backend dependencies.

## Database Migration

Add two columns to the `meeting` table:

```sql
ALTER TABLE meeting ADD COLUMN original_summary_text TEXT;
ALTER TABLE meeting ADD COLUMN summary_edited BOOLEAN NOT NULL DEFAULT FALSE;
```

No data migration needed — existing rows get `NULL` / `FALSE` defaults.

## Integration Test Scenario

1. Create a meeting and complete processing (ensure `summary_text` is populated)
2. `PATCH /api/v1/meetings/{id}/summary` with new markdown text
3. Verify response has `summary_edited: true` and `original_summary_text` equals the old summary
4. `GET /api/v1/meetings/{id}` — verify persisted changes
5. `POST /api/v1/meetings/{id}/summary/restore` — verify summary reverts
6. Frontend: open meeting → click Edit → modify text → Save → verify rendered output updates
