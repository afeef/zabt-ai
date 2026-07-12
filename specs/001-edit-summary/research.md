# Research: Edit Summary Markdown In-App

**Feature**: 001-edit-summary | **Date**: 2026-03-09

## R1: WYSIWYG Markdown Editor for React/Next.js

### Decision: **Tiptap** (ProseMirror-based)

### Rationale

Tiptap is a headless, extensible rich-text editor built on ProseMirror. It provides:
- **Headless UI**: No opinionated styles — we style everything with Tailwind to match our design system (stone/indigo palette, borders not shadows)
- **Markdown I/O**: The `@tiptap/pm` ecosystem + `tiptap-markdown` extension allows importing/exporting markdown while editing in WYSIWYG mode
- **React integration**: First-class `@tiptap/react` package with hooks (`useEditor`)
- **Toolbar-friendly**: Extensions for bold, italic, headings, lists, links are all built-in and togglable
- **Lightweight**: Only install the extensions you need — no monolithic bundle
- **Active maintenance**: Well-maintained open-source project with strong community

### Alternatives Considered

| Editor | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| **Milkdown** | ProseMirror-based, markdown-first | Smaller community, fewer examples | Less ecosystem support, harder to customize toolbar |
| **react-markdown + textarea** | Already installed (`react-markdown` in deps) | Not WYSIWYG — raw markdown editing | Spec requires WYSIWYG; users shouldn't see raw syntax |
| **Lexical (Meta)** | Modern, extensible | No native markdown round-trip; heavier setup | Markdown import/export requires significant custom work |
| **Slate.js** | Flexible, React-native | Low-level; markdown support requires plugins | Too much boilerplate for our scope |
| **CKEditor / TinyMCE** | Feature-rich WYSIWYG | Heavy, opinionated styles, license concerns | Violates "lightweight" requirement; hard to match design system |
| **MDXEditor** | React + markdown WYSIWYG | Heavier bundle, MDX-oriented | Over-scoped for plain markdown editing |

### Packages to Install

```
@tiptap/react
@tiptap/starter-kit        # bold, italic, headings, lists, code, blockquote, etc.
@tiptap/extension-link      # link support
tiptap-markdown             # markdown serialization/deserialization
```

Total estimated bundle addition: ~40-60KB gzipped (ProseMirror core + extensions).

## R2: Markdown Output Compatibility

### Decision: Editor stores markdown, not HTML

The WYSIWYG editor internally uses ProseMirror's document model (JSON), but on save it serializes to markdown via `tiptap-markdown`. This ensures:
- Existing `react-markdown` rendering continues to work unchanged in read-only mode
- PDF export (via `pdfmake`) continues to consume markdown
- The `summary_text` column stores markdown as it does today
- No migration needed for existing summaries

## R3: Backend Update Pattern

### Decision: Add a PATCH endpoint using existing Repository Pattern

The Meeting model gets two new nullable fields:
- `original_summary_text: Optional[str]` — frozen copy of the AI-generated summary
- `summary_edited: bool = False` — flag for UI badge

The PATCH endpoint updates `summary_text` and sets `summary_edited = True`. On first edit, if `original_summary_text` is null, it copies the current `summary_text` before overwriting. Restoring the original sets `summary_text = original_summary_text` and `summary_edited = False`.

This follows the Repository Pattern via `MeetingService` (constitution gate VII).

## R4: No New Environment Variables

This feature requires no new environment variables. All configuration is code-level:
- Tiptap is a client-side library (no API keys)
- The PATCH endpoint uses existing auth (Supabase JWT)
- No external service integrations
