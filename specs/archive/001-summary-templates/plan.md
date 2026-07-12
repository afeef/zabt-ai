# Implementation Plan: Summary Templates

**Branch**: `001-summary-templates` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-summary-templates/spec.md`

---

## Summary

Add a markdown summary template system to Zabt. Users select from built-in templates (General Summary, Meeting Minutes, Action Items, Retrospective) or create custom ones. Meetings are auto-summarized on upload using the user's active default template. Users can re-summarize any meeting with a different template from the summary tab. Templates are managed on a dedicated `/templates` page with preview and set-as-default capability.

The backend extends the existing Celery summarization pipeline to accept a `template_id`; the template body is injected into the LLM system prompt. The frontend adds a template dropdown on the summary tab and a full templates management page.

---

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend)
**Primary Dependencies**: FastAPI, SQLModel, Celery (Redis broker), pydantic-ai / OpenAI client; Next.js 16, React 19, Tailwind CSS 4, Axios, lucide-react
**Storage**: PostgreSQL (via SQLModel) — new `summarytemplate` table; `user` and `meeting` tables extended
**Testing**: pytest (backend unit), Playwright/Python (E2E under `tests/e2e/`)
**Target Platform**: Linux server (backend), Next.js SSR (frontend)
**Project Type**: Web application (backend API + frontend)
**Performance Goals**: Re-summarization enqueued and acknowledged in < 500ms; LLM response time unchanged (async, Celery)
**Constraints**: Custom template body ≤ 4,000 characters; no new environment variables
**Scale/Scope**: Per-user custom templates; 4 built-in templates seeded at startup

---

## Constitution Check

| Gate | Applies | Status | Notes |
|------|---------|--------|-------|
| Design System | ✅ UI changes | ✅ PASS | New components (template dropdown, picker modal, templates page) will comply with stone/indigo/rounded-lg system; system.md will be updated for new patterns |
| API Contract | ✅ New endpoints | ✅ PASS | `contracts/templates-api.md` populated before frontend implementation |
| Auth/Security | ✅ User-scoped data | ✅ PASS | All template CRUD enforces ownership; JWT validated on all endpoints; built-in templates visible to all, custom templates owner-scoped |
| Env Config | ❌ No new env vars | ✅ N/A | Uses existing OPENAI_API_KEY, OPENAI_MODEL, DB settings |
| Scope Boundary | ✅ All features | ✅ PASS | Implementation stays within spec scope |
| E2E Testing | ✅ User-facing flows | ✅ PASS | `tests/e2e/test_summary_templates.py` planned; listed in tasks.md |
| Repository Pattern | ✅ DB access | ✅ PASS | `TemplateService` extends `BaseService`; no direct session in endpoints |
| CLI/Typer | ❌ No CLI | ✅ N/A | |
| Provider Abstraction | ❌ No new provider | ✅ N/A | Uses existing LLM provider (ai_agent.py); template content is passed as a prompt parameter, not a new provider |
| Cost Awareness | ✅ LLM calls | ✅ PASS | Re-summarization is async via Celery (consistent with existing pipeline); user-initiated on-demand only; no real-time LLM call |
| Migration Safety | ❌ No provider migration | ✅ N/A | |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-summary-templates/
├── plan.md              ← This file
├── research.md          ← Phase 0 complete
├── data-model.md        ← Phase 1 complete
├── quickstart.md        ← Phase 1 complete
├── contracts/
│   └── templates-api.md ← Phase 1 complete
├── checklists/
│   └── requirements.md
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code

```text
backend/
├── app/
│   ├── models.py                        ← Extend: SummaryTemplate, User.default_template_id, Meeting.template_id/template_name
│   ├── worker.py                        ← Extend: stage_summarize accepts template_id; fetch active template
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── templates.py         ← NEW: CRUD + set-default endpoints
│   │           └── meetings.py          ← Extend: POST /{id}/summarize endpoint
│   ├── services/
│   │   ├── template.py                  ← NEW: TemplateService (extends BaseService)
│   │   ├── template_seed.py             ← NEW: seed_built_in_templates()
│   │   └── ai_agent.py                  ← Extend: summarize_transcript() accepts template_body param
│   └── main.py                          ← Extend: call seed_built_in_templates() in lifespan hook

frontend-2/
├── app/
│   ├── (dashboard)/
│   │   ├── meetings/
│   │   │   └── [id]/
│   │   │       └── page.tsx             ← Extend: template dropdown on summary tab; re-summarize confirmation
│   │   └── templates/
│   │       └── page.tsx                 ← NEW: templates management page
│   ├── components/
│   │   ├── template-dropdown.tsx        ← NEW: summary tab lightweight dropdown
│   │   └── template-picker-modal.tsx    ← NEW: left-list + right-preview modal for templates page
│   └── lib/
│       └── api.ts                       ← Extend: template CRUD + resummary API functions

tests/
└── e2e/
    └── test_summary_templates.py        ← NEW: E2E tests (Playwright/Python)

.interface-design/
└── system.md                            ← Update: document template dropdown + picker modal patterns
```

---

## Complexity Tracking

No constitution violations.

---

## Implementation Phases

### Phase A: Backend Data Layer

1. Add `SummaryTemplate` model to `models.py`
2. Add `default_template_id` FK to `User` model
3. Add `template_id` + `template_name` fields to `Meeting` model
4. Create `TemplateService` in `services/template.py` (CRUD, ownership checks, set-default)
5. Create `services/template_seed.py` with `seed_built_in_templates()` and the 4 built-in template bodies
6. Hook `seed_built_in_templates()` into `main.py` lifespan startup
7. Generate and apply Alembic migration

### Phase B: Backend API Layer

8. Create `api/v1/endpoints/templates.py` with all 6 template endpoints
9. Register templates router in `api/api.py`
10. Extend `meetings.py` with `POST /{meeting_id}/summarize` endpoint
11. Extend `ai_agent.py::summarize_transcript()` to accept optional `template_body: str | None` parameter; inject into system prompt when provided
12. Extend `worker.py::stage_summarize` to accept `template_id`, fetch the template, pass `template_body` to `summarize_transcript()`, and store `template_id` + `template_name` on the meeting

### Phase C: Frontend API Integration

13. Add TypeScript types for `SummaryTemplate`, `SummaryTemplateListItem` to `api.ts`
14. Extend `Meeting` type with `template_id`, `template_name` fields
15. Add API functions: `getTemplates()`, `getTemplate(id)`, `createTemplate()`, `updateTemplate()`, `deleteTemplate()`, `setDefaultTemplate()`, `resummmarizeMeeting(id, templateId?)`

### Phase D: Frontend Summary Tab

16. Create `template-dropdown.tsx` — lightweight dropdown matching Otter's "Template: [Name] ▾" pattern:
    - Shows current template name with chevron
    - Opens dropdown with "Templates" header, `+` icon (links to `/templates?new=1`), `⚙` icon (links to `/templates`)
    - Lists all templates by name; checkmark on active; clicking a different one triggers confirmation
    - Confirmation banner: "Re-summarize with [Template Name]?" with confirm button
17. Extend `meetings/[id]/page.tsx` summary tab:
    - Render `TemplateDropdown` in top-right of summary tab header
    - Handle re-summarize API call + poll for completion
    - Show in-progress state during re-summarization

### Phase E: Frontend Templates Page

18. Create `templates/page.tsx` — table view:
    - Columns: Template name, Type (Built-in / Custom), Last edited
    - "New Template" button (top-right) → opens `TemplatePicker` modal in create mode
    - Clicking a row → opens `TemplatePicker` modal in view mode (with Set as Default / Edit / Delete actions for custom)
19. Create `template-picker-modal.tsx` — split-panel modal:
    - Left panel: scrollable list of template names, checkmark on selected
    - Right panel: rendered preview of selected template body (styled card, not raw markdown)
    - Bottom: "Use Template" button (for meeting context) or "Set as Default" + "Edit" + "Delete" (for management context)
    - Modal receives context prop to adapt behavior

### Phase F: Design System & E2E

20. Update `.interface-design/system.md` to document template dropdown and picker modal patterns
21. Write `tests/e2e/test_summary_templates.py` covering:
    - Upload → auto-summarize with system default → verify template label on summary tab
    - Change template in summary tab → confirm → verify re-summarization with new template
    - Create custom template → select it on a meeting → verify output structure
    - Set personal default → upload new meeting → verify it uses new default
    - Re-summarization failure recovery
    - Custom template body > 4000 chars → validation error

---

## UI Design Reference

Based on provided Otter.ai screenshots, adapted to Zabt design system (stone/indigo, no shadows, rounded-lg):

### Summary Tab Template Dropdown

```
┌─────────────────────────────────────────────────────────┐
│ Summary    Transcript              Template: General  ▾  │
├─────────────────────────────────────────────────────────┤
│                                    ┌──────────────────┐  │
│  ## Overview                       │ Templates    + ⚙ │  │
│  ...                               │──────────────────│  │
│                                    │ ✓ General        │  │
│                                    │   Meeting Minutes│  │
│                                    │   Action Items   │  │
│                                    │   Retrospective  │  │
│                                    │─ My Templates ───│  │
│                                    │   My Custom One  │  │
│                                    └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

After selecting a different template, a confirmation prompt appears below the dropdown:

```
┌──────────────────────────────────────────────────────────┐
│  Re-summarize with "Meeting Minutes"?                     │
│  This will replace the current summary.   [Cancel] [Go]  │
└──────────────────────────────────────────────────────────┘
```

### Templates Page (`/templates`)

```
┌─────────────────────────────────────────────────────────┐
│ Templates                              [New Template]    │
├──────────────────────┬──────────────┬───────────────────┤
│ Template             │ Type         │ Last edited       │
├──────────────────────┼──────────────┼───────────────────┤
│ General Summary  ★   │ Built-in     │ —                 │
│ Meeting Minutes      │ Built-in     │ —                 │
│ Action Items         │ Built-in     │ —                 │
│ Retrospective        │ Built-in     │ —                 │
│ My Custom Template   │ Custom       │ Mar 4, 2026       │
└──────────────────────┴──────────────┴───────────────────┘
  ★ = system default (or user's personal default)
```

### Template Picker Modal (for Templates page)

```
┌─────────────────────────────────────────────────────────┐
│ Templates                                            ✕   │
├──────────────────┬──────────────────────────────────────┤
│ AVAILABLE        │  ┌─────────────────────────────────┐ │
│ General        ✓ │  │  Meeting Minutes                 │ │
│ Meeting Minutes  │  │                                  │ │
│ Action Items     │  │  ## Attendees                    │ │
│ Retrospective    │  │  [List participants...]          │ │
│                  │  │                                  │ │
│ MY TEMPLATES     │  │  ## Decisions Made               │ │
│ My Custom One    │  │  [List formal decisions...]      │ │
│                  │  │                                  │ │
│                  │  │  ## Action Items                 │ │
│                  │  │  [List tasks assigned...]        │ │
│                  └──┴──────────────────────────────────┘ │
│                         [Set as Default]  [Edit]  [Del]  │
└─────────────────────────────────────────────────────────┘
```
