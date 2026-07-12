# Tasks: Email Notifications

**Input**: Design documents from `/specs/001-email-notifications/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story. US1 (summary email) is the MVP and can be validated independently before US2 (failure email).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the `resend` dependency and wire environment configuration — required before any email code can be written or run.

- [X] T001 Add `resend>=2.0.0` to `[tool.uv.dependencies]` in `backend/pyproject.toml`
- [X] T002 Add `RESEND_API_KEY: str = ""`, `RESEND_FROM_EMAIL: str = "no-reply@zabt.ai"`, and `APP_URL: str = "https://zabt.ai"` to the `Settings` class in `backend/app/core/config.py`
- [X] T003 [P] Add `RESEND_API_KEY=`, `RESEND_FROM_EMAIL=no-reply@zabt.ai`, and `APP_URL=https://zabt.ai` placeholders under a `# --- Email (Resend) ---` section in `.env`
- [X] T004 [P] Add `- RESEND_API_KEY=${RESEND_API_KEY:-}`, `- RESEND_FROM_EMAIL=${RESEND_FROM_EMAIL:-no-reply@zabt.ai}`, and `- APP_URL=${APP_URL:-https://zabt.ai}` to the `environment:` section of the `api`, `worker`, and `worker-gpu` services in `docker-compose.yml`

**Checkpoint**: Dependency installed and env vars wired — ready to implement the email service

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `EmailProvider` Protocol + `ResendEmailProvider` implementation must exist before either user story can call it. This phase produces the shared `email_service` singleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `backend/app/services/email.py` with the `EmailProvider` Protocol (`send_summary_email`, `send_failure_email`), the `ResendEmailProvider` concrete class (fail-silent, idempotency keys `meeting-{id}-summary` / `meeting-{id}-failure`, logfire logging), and the `email_service` singleton initialized from `settings`

**Checkpoint**: `email_service` is importable and no-ops silently when `RESEND_API_KEY` is empty — user story wiring can now begin

---

## Phase 3: User Story 1 — Meeting Summary Delivered by Email (Priority: P1) 🎯 MVP

**Goal**: When `stage_summarize` completes successfully, the meeting owner receives a summary email with the meeting title, summary text, and a deep-link back to the meeting.

**Independent Test**: Process a real meeting end-to-end → verify summary email arrives in the inbox within 2 minutes with the correct title and summary (Scenario 1 from quickstart.md).

### Implementation for User Story 1

- [X] T006 [US1] Wire `email_service.send_summary_email()` into `stage_summarize` in `backend/app/worker.py`: after `meeting_service.mark_completed(...)`, look up `User` via `Session(engine)` using `meeting.owner_id`, call `email_service.send_summary_email(user.email, meeting)` if `user and user.email`, wrapped in `try/except Exception` with `logfire.exception()`

**Checkpoint**: US1 fully functional — deploy and validate summary emails before continuing to US2

---

## Phase 4: User Story 2 — Processing Failure Notification (Priority: P2)

**Goal**: When `on_stage_failure` fires, the meeting owner receives a failure email identifying the meeting and linking to it for retry.

**Independent Test**: Upload a corrupt/empty audio file to force a pipeline failure → verify failure notification email arrives in the inbox within 2 minutes (Scenario 2 from quickstart.md).

### Implementation for User Story 2

- [X] T007 [US2] Wire `email_service.send_failure_email()` into `on_stage_failure` in `backend/app/worker.py`: after `meeting_service.mark_failed(meeting_id, str(exc))`, look up `Meeting` via `meeting_service.get(Meeting, meeting_id)`, look up `User` via `Session(engine)` using `failed_meeting.owner_id`, call `email_service.send_failure_email(user.email, failed_meeting, str(exc))` if user email present, wrapped in `try/except Exception` with `logfire.exception()`

**Checkpoint**: Both US1 and US2 are functional — all email scenarios can be validated

---

## Phase 5: Polish & Validation

**Purpose**: Manual end-to-end validation of all 4 quickstart.md scenarios.

- [ ] T008 Run all 4 validation scenarios from `specs/001-email-notifications/quickstart.md`: (1) summary email on completion, (2) failure email on pipeline failure, (3) no email and no crash when `RESEND_API_KEY` is empty, (4) no duplicate email on reprocessing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately; T003 and T004 are parallel
- **Foundational (Phase 2)**: Depends on T001 + T002 — BLOCKS both user stories
- **US1 (Phase 3)**: Depends on T005 — can start after Foundational
- **US2 (Phase 4)**: Depends on T005 — can start after Foundational (independent of US1)
- **Polish (Phase 5)**: Depends on T006 + T007

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 — independently completable and testable
- **US2 (P2)**: No dependency on US1 — independently completable; both wire into different locations in `worker.py`

### Parallel Opportunities

- T003 and T004 (`.env` and `docker-compose.yml`) can run in parallel — different files
- T006 (US1) and T007 (US2) touch different functions in `worker.py` and can be reviewed in parallel, but must be applied sequentially to avoid edit conflicts

---

## Parallel Example: Setup Phase

```bash
# T003 and T004 can run at the same time (different files):
Task: "Add email env vars to .env"
Task: "Add email env vars to docker-compose.yml (api, worker, worker-gpu)"
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005)
3. Complete Phase 3: US1 (T006)
4. **STOP and VALIDATE**: Process a meeting → verify summary email arrives
5. Merge or demo if ready

### Full Value (Both Stories)

1. Complete Setup + Foundational (T001–T005)
2. Complete US1 (T006) → validate Scenario 1
3. Complete US2 (T007) → validate Scenario 2
4. Run all 4 validation scenarios (T008)

---

## Notes

- No new database tables, no new API endpoints, no frontend changes
- `RESEND_API_KEY` absent = no-op mode (fail-silent by design — never crashes the app)
- Idempotency is handled by Resend's `idempotency_key` option — no DB deduplication needed
- All email calls are fire-and-forget wrapped in `try/except Exception` + `logfire.exception()`
- `email_service` is a module-level singleton; import it inside the calling function to avoid circular imports
- Commit after T005 (new file) and again after T006 (US1 complete) to create a clean rollback point before US2
