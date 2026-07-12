# Tasks: Summary Templates

**Input**: Design documents from `/specs/001-summary-templates/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tech Stack**: Python 3.11 / FastAPI / SQLModel / Celery (backend) · TypeScript / Next.js 16 / React 19 / Tailwind CSS 4 (frontend)
**E2E Tests**: Required by constitution (Playwright/Python under `tests/e2e/`)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase
- **[Story]**: Maps to user story from spec.md (US1–US5)

---

## Phase 1: Setup (Schema & Core Model Changes)

**Purpose**: Add all new DB entities and extend existing models. Must complete before any service or API work.

**⚠️ CRITICAL**: Nothing else can start until the migration runs successfully.

- [X] T001 Add `SummaryTemplate` SQLModel class to `backend/app/models.py` (fields: id, name, body, template_type, is_system_default, owner_id FK→user.id, created_at, updated_at)
- [X] T002 Add `default_template_id` optional FK field to existing `User` model in `backend/app/models.py` (FK→summarytemplate.id, nullable)
- [X] T003 Add `template_id` (optional FK→summarytemplate.id) and `template_name` (optional str) fields to existing `Meeting` model in `backend/app/models.py`
- [X] T004 Extend `MeetingRead` response model in `backend/app/models.py` to include `template_id: Optional[int]` and `template_name: Optional[str]`
- [X] T005 Generate Alembic migration: `uv run alembic revision --autogenerate -m "add summary templates"` and verify generated migration file in `backend/alembic/versions/`
- [X] T006 Apply migration: `uv run alembic upgrade head` and confirm all three schema changes are present (new table + two column additions)
- [X] T007 Create `backend/app/services/template_seed.py` with `seed_built_in_templates()` function that idempotently upserts the 4 built-in templates (General Summary as system default, Meeting Minutes, Action Items, Retrospective) with their full markdown bodies from `data-model.md`
- [X] T008 Hook `seed_built_in_templates()` into the FastAPI lifespan startup in `backend/app/main.py` (call after DB engine is ready)
- [X] T009 Verify seeding: start backend, confirm 4 rows exist in `summarytemplate` table with correct `is_system_default` and `owner_id=NULL`

**Checkpoint**: DB schema complete, 4 built-in templates seeded, existing app still starts without errors.

---

## Phase 2: Foundational (Service Layer & Shared Infrastructure)

**Purpose**: Core service, prompt extension, router registration, and TypeScript types. Blocks all user story implementation.

**⚠️ CRITICAL**: Depends on Phase 1. All user story phases depend on this phase.

- [X] T010 Create `backend/app/services/template.py` with `TemplateService` extending `BaseService`. Methods: `list_for_user(user_id)` (returns built-ins + user's custom), `get_accessible(template_id, user_id)` (built-in or owned), `create_custom(user_id, name, body)` (validates body ≤4000 chars), `update_custom(template_id, user_id, name, body)`, `delete_custom(template_id, user_id)` (clears user defaults pointing to it), `set_user_default(user_id, template_id)`, `get_active_default(user_id)` (personal default → system default → hardcoded fallback)
- [X] T011 Extend `backend/app/services/ai_agent.py::summarize_transcript()` to accept an optional `template_body: str | None = None` parameter; when provided, append a "FORMAT INSTRUCTION:" block to the system prompt containing the template body before sending to the LLM
- [X] T012 Create `backend/app/api/v1/endpoints/templates.py` scaffold file (empty router with `router = APIRouter()`) — full endpoints added per user story phase
- [X] T013 Register the templates router in `backend/app/api/api.py` with `prefix="/templates"` and `tags=["templates"]`
- [X] T014 [P] Add `SummaryTemplateRead` and `SummaryTemplateListItem` Pydantic response models to `backend/app/models.py`
- [X] T015 [P] Add TypeScript types `SummaryTemplate` and `SummaryTemplateListItem` to `frontend-2/app/lib/api.ts`
- [X] T016 [P] Extend the `Meeting` TypeScript interface in `frontend-2/app/lib/api.ts` with `template_id: number | null` and `template_name: string | null`

**Checkpoint**: Backend starts, templates router registered (no endpoints yet), TypeScript types compile without errors.

---

## Phase 3: User Story 1 — Auto-summarize on Upload Using Default Template (Priority: P1) 🎯 MVP

**Goal**: Every meeting upload automatically uses the user's active default template (personal → system → General Summary fallback). No user action required.

**Independent Test**: Upload a meeting file, wait for completion, open the summary tab — verify the summary is generated and the template label shows the correct default template name.

- [X] T017 [US1] Extend `backend/app/worker.py::stage_summarize` task to: (1) fetch the meeting's owner, (2) call `template_service.get_active_default(owner_id)` to get the active template, (3) pass `template_body=template.body` to `summarize_transcript()`, (4) store `template_id` and `template_name` on the meeting row via `meeting_service`
- [X] T018 [US1] Extend `backend/app/services/meeting.py::mark_completed()` to accept optional `template_id: int | None` and `template_name: str | None` parameters and persist them on the meeting row
- [X] T019 [US1] Verify `GET /meetings/{id}` response includes `template_id` and `template_name` fields (already added to `MeetingRead` in T004 — confirm no further changes needed or fix gaps)
- [X] T020 [US1] Add "Template: [name]" label to the summary tab header in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx` — display `meeting.template_name` when present, positioned in top-right of summary tab panel (no dropdown yet; static label only for US1)
- [X] T021 [US1] E2E test in `tests/e2e/test_summary_templates.py`: upload a meeting → wait for completion → assert summary tab shows a non-empty template label matching the system default ("General Summary")

**Checkpoint**: Upload a meeting → summary generated → template label visible on summary tab. US1 fully functional.

---

## Phase 4: User Story 2 — Change Template in Summary Tab (Priority: P2)

**Goal**: User can open a dropdown from the template label, pick a different template, confirm, and trigger re-summarization. The new summary replaces the old one.

**Independent Test**: On any completed meeting's summary tab, open the template dropdown, select "Meeting Minutes", confirm the prompt, wait for re-summarization — verify summary content reflects the Meeting Minutes structure and the label updates.

- [X] T022 [US2] Implement `GET /api/v1/templates/` endpoint in `backend/app/api/v1/endpoints/templates.py`: returns all built-in templates + authenticated user's custom templates; uses `template_service.list_for_user(current_user.id)`
- [X] T023 [US2] Implement `POST /api/v1/meetings/{meeting_id}/summarize` endpoint in `backend/app/api/v1/endpoints/meetings.py`: validates meeting ownership + current status (must be `completed` or `failed`), accepts optional `template_id` in request body, updates meeting status to `processing`/`summarizing`, enqueues `stage_summarize` Celery task with `template_id` param, returns `202 Accepted`
- [X] T024 [US2] Extend `backend/app/worker.py::stage_summarize` to accept `template_id: int | None = None` as a task parameter — when provided, fetch that specific template instead of the user's active default (preserves T017 behavior for upload path)
- [X] T025 [US2] Add `getTemplates()` and `resummarizeMeeting(meetingId: number, templateId?: number)` functions to `frontend-2/app/lib/api.ts`
- [X] T026 [US2] Create `frontend-2/app/components/template-dropdown.tsx`: renders "Template: [name] ▾" clickable label; on click opens a dropdown listing all templates by name (fetched via `getTemplates()`), with a checkmark on the currently active template; selecting a different template shows an inline confirmation prompt ("Re-summarize with [Template Name]?" with Cancel and Confirm buttons); Confirm calls `resummarizeMeeting()`; closes on outside click; shows spinner during loading
- [X] T027 [US2] Replace the static template label from T020 with `<TemplateDropdown>` in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx`; handle the in-progress state (disable dropdown, show "Summarizing…" state in summary area) and poll `getMeeting(id)` until `status === "completed"` to refresh the summary
- [X] T028 [US2] E2E test in `tests/e2e/test_summary_templates.py`: on a completed meeting → open dropdown → select "Meeting Minutes" → confirm → wait for re-summarization → assert template label shows "Meeting Minutes" and summary content differs from original

**Checkpoint**: Template dropdown functional on summary tab; re-summarization triggered and reflected correctly. US2 fully functional.

---

## Phase 5: User Story 3 — Set Personal Default Template (Priority: P3)

**Goal**: User can designate any template as their personal default from the Templates page. Future uploads use this template automatically.

**Independent Test**: Set "Meeting Minutes" as default on `/templates` page → upload a new meeting → verify summary tab shows "Meeting Minutes" as the template label.

- [X] T029 [US3] Implement `POST /api/v1/templates/{template_id}/set-default` endpoint in `backend/app/api/v1/endpoints/templates.py`: validates the template is accessible to the user (built-in or owned custom), calls `template_service.set_user_default(current_user.id, template_id)`, returns updated default template info
- [X] T030 [US3] Add `setDefaultTemplate(templateId: number)` function to `frontend-2/app/lib/api.ts`
- [X] T031 [US3] Create `frontend-2/app/(dashboard)/templates/page.tsx` — initial version: page shell with "Templates" heading and a table showing template name, type (Built-in / Custom), and a "Set as Default" action button per row; fetches templates via `getTemplates()`; active default shown with a star/badge indicator; calls `setDefaultTemplate()` on button click and refreshes the list
- [X] T032 [US3] Add `/templates` route to the dashboard sidebar navigation in `frontend-2/app/components/app-shell.tsx` (or sidebar component) with an appropriate icon
- [X] T033 [US3] E2E test in `tests/e2e/test_summary_templates.py`: navigate to `/templates` → click "Set as Default" on "Meeting Minutes" → verify star indicator moves to Meeting Minutes → upload a new meeting → assert template label shows "Meeting Minutes"

**Checkpoint**: `/templates` page accessible, personal default settable, new uploads respect it. US3 fully functional.

---

## Phase 6: User Story 4 — Create a Custom Template (Priority: P4)

**Goal**: User can author a new markdown template with a name and body, save it, and use it on any meeting.

**Independent Test**: On `/templates` page, click "New Template", enter a name and a markdown body, save — verify the template appears in the list and in the meeting summary dropdown, and produces a correspondingly structured summary when selected.

- [X] T034 [US4] Implement `POST /api/v1/templates/` endpoint in `backend/app/api/v1/endpoints/templates.py`: validates name (non-empty, ≤100 chars) and body (non-empty, ≤4000 chars), calls `template_service.create_custom()`, returns `201 Created` with `SummaryTemplateRead`
- [X] T035 [US4] Add `createTemplate(name: string, body: string)` function to `frontend-2/app/lib/api.ts`
- [X] T036 [US4] Create `frontend-2/app/components/template-editor-modal.tsx`: modal with a "Template name" text input and a `<textarea>` for the markdown body (with character counter showing remaining chars of 4000 limit); Save and Cancel buttons; shows validation error inline when body exceeds limit; calls `createTemplate()` on save; closes and calls an `onSaved` callback
- [X] T037 [US4] Wire "New Template" button on `/templates` page (`frontend-2/app/(dashboard)/templates/page.tsx`) to open `TemplateEditorModal` in create mode; refresh template list on `onSaved`
- [X] T038 [US4] E2E test in `tests/e2e/test_summary_templates.py`: click "New Template" → enter name "My Custom" and a markdown body → save → assert template appears in list → select it on a meeting summary tab → confirm re-summarize → verify summary reflects custom template structure; also: attempt to save a body > 4000 chars → assert validation error shown

**Checkpoint**: Custom template creation end-to-end functional. US4 fully functional.

---

## Phase 7: User Story 5 — Manage Templates (Edit, Delete, Preview) (Priority: P5)

**Goal**: Full template management — view, preview, edit custom templates, delete custom templates, with the picker modal pattern (left list + right preview).

**Independent Test**: On `/templates` page, click a template row to open the picker modal — verify right panel shows formatted preview; edit a custom template's body — verify change reflected in picker and meeting dropdown; delete a custom template — verify it disappears from all pickers.

- [X] T039 [US5] Implement `GET /api/v1/templates/{template_id}` endpoint in `backend/app/api/v1/endpoints/templates.py`: returns full `SummaryTemplateRead` for built-in or owned custom templates; `403` for other users' templates
- [X] T040 [US5] Implement `PUT /api/v1/templates/{template_id}` endpoint in `backend/app/api/v1/endpoints/templates.py`: validates ownership and non-built-in type, validates name + body, calls `template_service.update_custom()`, returns updated `SummaryTemplateRead`; returns `403` with `"Built-in templates cannot be modified."` for built-ins
- [X] T041 [US5] Implement `DELETE /api/v1/templates/{template_id}` endpoint in `backend/app/api/v1/endpoints/templates.py`: validates ownership and non-built-in type, calls `template_service.delete_custom()` (which also clears any `user.default_template_id` pointing to it), returns `204 No Content`
- [X] T042 [US5] Add `getTemplate(id: number)`, `updateTemplate(id: number, name: string, body: string)`, and `deleteTemplate(id: number)` functions to `frontend-2/app/lib/api.ts`
- [X] T043 [US5] Create `frontend-2/app/components/template-picker-modal.tsx`: split-panel modal; left panel = scrollable list of template names with checkmark on selected; right panel = formatted preview of selected template body (rendered as styled card with section headings, not raw markdown); bottom action bar adapts by context: management mode shows "Set as Default", "Edit" (custom only), "Delete" (custom only) buttons; clicking Edit opens `TemplateEditorModal` in edit mode; Delete shows `ConfirmDeleteDialog`; close button top-right
- [X] T044 [US5] Extend `TemplateEditorModal` in `frontend-2/app/components/template-editor-modal.tsx` to support edit mode: pre-populate name and body fields, call `updateTemplate()` on save
- [X] T045 [US5] Update `/templates` page (`frontend-2/app/(dashboard)/templates/page.tsx`) to open `TemplatePickerModal` when a template row is clicked; show last-edited date/type in table; handle delete confirmation and list refresh
- [X] T046 [US5] E2E test in `tests/e2e/test_summary_templates.py`: open template picker modal → verify preview renders for "General Summary" → edit a custom template body → save → verify update reflected in modal preview and meeting dropdown → delete the custom template → verify it no longer appears; also: verify deleting a custom template that was set as personal default causes next upload to fall back to system default

**Checkpoint**: Full template management working. All 5 user stories independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Design system documentation, edge case hardening, E2E test completeness.

- [X] T047 Update `.interface-design/system.md` to document two new UI patterns: (1) `TemplateDropdown` — inline label + dropdown pattern with confirmation prompt; (2) `TemplatePickerModal` — split-panel left-list + right-preview modal pattern; include spacing and color specs per design system (stone/indigo, rounded-lg, no shadows)
- [X] T048 [P] Add error handling to `backend/app/worker.py::stage_summarize` for the case where the specified `template_id` does not exist or is inaccessible — fall back to system default template and log a warning; do not fail the task
- [X] T049 [P] Add `"Templates"` entry to the dashboard sidebar navigation if not already added in T032 — confirm correct active state highlighting when on `/templates`
- [X] T050 [P] Verify the `TemplateDropdown` dropdown closes correctly on Escape key and outside click; verify re-summarization polling stops when the component unmounts (clean up `setInterval` refs in `frontend-2/app/(dashboard)/meetings/[id]/page.tsx`)
- [X] T051 Run E2E test suite: `cd tests/e2e && uv run pytest test_summary_templates.py -v` — verify all scenarios pass (upload default, change template, set default, create custom, edit, delete, fallback, validation error)
- [X] T052 Run quickstart.md validation: fresh DB reset → seed → upload a meeting → exercise all 5 user stories end to end; confirm no regressions in existing meeting feed, transcript tab, or other features

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — can start independently
- **Phase 4 (US2)**: Depends on Phase 2 — can start independently of US1 (but US1 provides the label US2 extends)
- **Phase 5 (US3)**: Depends on Phase 2 + `getTemplates()` from T025 (US2) — start after T025
- **Phase 6 (US4)**: Depends on Phase 2 — can start after Phase 2 independently
- **Phase 7 (US5)**: Depends on Phase 2; GET/PUT/DELETE endpoints independent; `TemplatePickerModal` reuses `TemplateEditorModal` from US4 (depends on T036)
- **Phase 8 (Polish)**: Depends on all user story phases complete

### User Story Dependencies

- **US1 (P1)**: Phase 2 only — no other story dependencies
- **US2 (P2)**: Phase 2 only — independent of US1 (extends the label it introduced, but doesn't require US1 to be done first)
- **US3 (P3)**: Phase 2 + T025 (getTemplates from US2) — minimal dependency
- **US4 (P4)**: Phase 2 only — independent
- **US5 (P5)**: Phase 2 + T036 (TemplateEditorModal from US4) — edit mode reuses the modal

### Critical Path

```
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009
→ T010 → T011 → T012 → T013
→ T017 → T018 → T019 → T020 → T021     ← US1 complete
→ T022 → T023 → T024 → T025 → T026 → T027 → T028   ← US2 complete
→ T029 → T030 → T031 → T032 → T033     ← US3 complete
→ T034 → T035 → T036 → T037 → T038     ← US4 complete
→ T039 → T040 → T041 → T042 → T043 → T044 → T045 → T046   ← US5 complete
→ T047 → T048 → T049 → T050 → T051 → T052
```

### Parallel Opportunities Within Phases

**Phase 1**: T001, T002, T003 can be written in parallel (all in models.py — coordinate); T007 and T005/T006 can be done in parallel after T001 creates the model.

**Phase 2**: T014, T015, T016 can run in parallel (different files).

**Phase 4 (US2)**: T022 (backend) and T025 (frontend api.ts) can run in parallel; T026 and T027 require T025; T023 and T024 are backend-only and can run in parallel with T025.

**Phase 7 (US5)**: T039, T040, T041 (backend endpoints) can run in parallel; T042 can run in parallel with them.

**Phase 8**: T047, T048, T049, T050 can all run in parallel.

---

## Parallel Example: US2 (Change Template in Summary Tab)

```
# Backend (parallel):
Task T022: GET /templates/ endpoint
Task T023: POST /meetings/{id}/summarize endpoint
Task T024: Extend stage_summarize with template_id param

# Frontend (parallel with backend):
Task T025: getTemplates() + resummarizeMeeting() in api.ts

# Depends on T025:
Task T026: TemplateDropdown component
Task T027: Wire dropdown into meetings/[id]/page.tsx
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Schema + seed
2. Complete Phase 2: Service + ai_agent + router
3. Complete Phase 3 (US1): Auto-summarize with default
4. **STOP and VALIDATE**: Upload a meeting, confirm template label appears, confirm summary quality
5. Deploy/demo: Every user immediately gets templated summaries on upload

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 (US1) → MVP: auto-summarize with default template ✅
3. Phase 4 (US2) → Template switching in summary tab ✅
4. Phase 5 (US3) → Personal default on templates page ✅
5. Phase 6 (US4) → Custom template creation ✅
6. Phase 7 (US5) → Full management + preview ✅
7. Phase 8 → Polish, E2E, design system docs ✅

---

## Notes

- [P] tasks = different files, no conflicting edits — safe to run in parallel
- [Story] label enables per-story traceability and independent demo
- E2E tests are added per user story within their phase for constitution compliance
- Commit after each task or logical group; use phase checkpoints to validate
- `TemplateService.get_active_default()` is the single source of truth for default resolution — ensure it is the only caller path in both upload and re-summarize flows
- Constitution: all template CRUD must go through `TemplateService`; no direct session access in endpoints
