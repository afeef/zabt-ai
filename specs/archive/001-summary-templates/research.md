# Research: Summary Templates

**Feature**: `001-summary-templates`
**Date**: 2026-03-04
**Status**: Complete

---

## Decision 1: Template Storage Strategy

**Decision**: Store templates in the PostgreSQL database via a new `SummaryTemplate` table.

**Rationale**: Templates need to be user-owned (custom), queryable by the API, previewed, and associated with meetings. DB storage enables CRUD operations, user scoping, and relational linking to meetings. Hardcoding templates in code would prevent user customization and make the picker dynamic (adding/removing user templates) impossible.

**Alternatives considered**:
- Hardcoded in Python: Simple, no migration, but prevents custom templates and user ownership.
- JSON file on disk: No DB dependency, but no user scoping, no FK relationships, not queryable.

---

## Decision 2: Built-in Template Delivery

**Decision**: Seed built-in templates into the DB at application startup (idempotent upsert by name). Built-in templates have `template_type = "built_in"` and `owner_id = NULL`.

**Rationale**: Seeding at startup ensures built-ins are always present after any fresh deployment or DB reset, without requiring a separate migration step. Idempotent upsert prevents duplication on restart.

**Built-in templates to seed** (4 total):
1. **General Summary** (system default) — Overview, key decisions, action items, open questions
2. **Meeting Minutes** — Attendees, agenda items, decisions, action items, next steps
3. **Action Items** — Focused list of tasks with owners and due dates extracted from discussion
4. **Retrospective** — What went well, what didn't, action items for improvement

**Alternatives considered**:
- Alembic migration: More controlled, but requires a manual migration step and doesn't auto-repair if templates are deleted.
- Separate seed script run by CI: Good for production, but adds deployment complexity for a small dataset.

---

## Decision 3: User Default Template Storage

**Decision**: Add a `default_template_id` foreign key field directly to the existing `User` model.

**Rationale**: The user-to-default-template relationship is 1:1. Adding a column to the User model is the simplest implementation. A separate `UserTemplatePreference` table would be justified only if multiple preference dimensions existed.

**Alternatives considered**:
- Separate `UserTemplatePreference` table: Over-engineered for a single preference field; adds a join to every upload event.

---

## Decision 4: Re-summarization Execution Model

**Decision**: Re-summarization (triggered from summary tab or on upload) runs as a Celery task (`stage_summarize`), identical to the initial summarization. A new `POST /meetings/{id}/summarize` endpoint enqueues the task with an explicit `template_id`.

**Rationale**: Consistent with the existing pipeline architecture. Prevents blocking the API thread on LLM latency. The meeting's `status` and `sub_status` fields already support tracking in-progress states that the frontend can poll.

**Alternatives considered**:
- Synchronous API call: Simpler, but blocks for potentially 10–30 seconds on large transcripts.
- New dedicated Celery task `task_resummary`: Unnecessary code duplication; `stage_summarize` can be called standalone with a template parameter.

---

## Decision 5: Template Injection into LLM Prompt

**Decision**: Append the template's markdown body as an additional instruction block at the end of the existing system prompt, not replacing it.

**Rationale**: The existing system prompt encodes Zabt's core behavior (tone, citation format, markdown output). Replacing it wholesale with a user template would lose these guardrails. Appending a "Format your response according to the following template structure:" instruction preserves existing quality while directing output structure.

**Prompt structure**:
```
[existing SYSTEM_PROMPT — Zabt core instructions]

---
FORMAT INSTRUCTION:
The user has selected a custom output template. Structure your response to match the following template format:

[template.body]
```

**Alternatives considered**:
- Replace system prompt entirely with template body: Maximum flexibility but loses Zabt behavior guardrails; low quality risk for poorly-written templates.
- Inject template as user message prefix: Weaker influence on LLM output structure; system-level instruction is more reliable.

---

## Decision 6: Meeting Template Reference

**Decision**: Store both a `template_id` FK and a denormalized `template_name` string on the `Meeting` row at summarization time.

**Rationale**: The FK enables relational integrity; the denormalized name enables displaying "Summarized with: Meeting Minutes" on the summary tab even after the template is deleted. Without the denormalized name, deletion of a custom template would break the display for historical meetings.

**Alternatives considered**:
- FK only: Summary tab UI breaks when template is deleted.
- Name only (no FK): Loses referential integrity; no ability to detect template changes.

---

## Decision 7: Summary Tab UX Pattern

**Decision**: Match the Otter UI pattern shown in screenshots:
- "Template: [Name] ▾" clickable label in the summary tab header (right side)
- Clicking opens a lightweight dropdown with:
  - "Templates" header with `+` icon (opens create-template inline or navigates to templates page) and `⚙` icon (navigates to `/templates` page)
  - Template list: name only, checkmark on active template
- Selecting a different template: shows a confirmation banner or button ("Re-summarize with [Template Name]") — does not immediately trigger re-summarization
- Confirming triggers the `POST /meetings/{id}/summarize` endpoint

**Templates page**: Separate `/templates` route with a table showing name, type (Built-in / Custom), last edited. "New Template" button in top-right. Clicking a row opens a template detail view (left list + right preview panel, consistent with Otter's modal pattern) where user can set as default, edit, or delete.

---

## Decision 8: Character Limit for Custom Templates

**Decision**: 4,000 characters maximum for the template body, enforced at the API level (validation error on save) with a clear frontend error message.

**Rationale**: The existing system prompt is ~3,000 characters. A 4,000-character template body keeps the total system prompt under ~7,000 characters, well within GPT-4o's context window for this use case.

---

## E2E Test Plan

Test file: `tests/e2e/test_summary_templates.py`

**Happy path scenarios**:
1. Upload meeting → auto-summarizes using system default template → verify summary tab shows "General" template label
2. Navigate to summary tab → open template dropdown → select "Meeting Minutes" → confirm → verify re-summarization completes and template label updates
3. Navigate to `/templates` → click "New Template" → fill name + body → save → verify template appears in meeting dropdown
4. Navigate to `/templates` → click a template → click "Set as Default" → upload new meeting → verify it uses new default

**Error scenarios**:
1. Re-summarization fails → verify previous summary is restored and error state shown
2. Save custom template with body > 4000 chars → verify validation error shown
3. Delete a custom template that was set as default → upload new meeting → verify falls back to system default
