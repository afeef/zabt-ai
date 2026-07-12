# Tasks: Owner Notifications via Telegram Bot

**Input**: Design documents from `/specs/023-telegram-notifications/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add httpx dependency and Telegram config to settings

- [x] T001 Add `httpx` to project dependencies in `backend/pyproject.toml`
- [x] T002 Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` settings with empty string defaults in `backend/app/core/config.py`

---

## Phase 2: Foundational (Provider Abstraction)

**Purpose**: Create the notification provider protocol and event dataclass — MUST complete before event hooks

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `NotificationEvent` dataclass and `NotificationProvider` Protocol in `backend/app/services/notifications/provider.py`
- [x] T004 Create `TelegramProvider` implementation using `httpx.Client` sync POST to `https://api.telegram.org/bot<token>/sendMessage` with MarkdownV2 formatting in `backend/app/services/notifications/telegram.py`
- [x] T005 Create module public API — `notify(event_type, user_email, meeting_title, extra)` function that instantiates provider (if configured) and calls `send()` with error swallowing in `backend/app/services/notifications/__init__.py`

**Checkpoint**: `notify()` can be called from anywhere; silently no-ops when Telegram is unconfigured

---

## Phase 3: User Story 1 — Core Event Notifications (Priority: P1) 🎯 MVP

**Goal**: Owner receives a Telegram message for each of the 6 tracked events

**Independent Test**: Trigger each event (login, upload, transcribe, summarize, export) and verify Telegram message arrives with correct details

### Implementation for User Story 1

- [x] T006 [P] [US1] Add login notification hook in `backend/app/api/deps.py` — call `notify()` after JIT provisioning with `"new_user"` (user created) or `"user_login"` (user exists), passing `user.email`
- [x] T007 [P] [US1] Add upload-started notification hook in `backend/app/api/v1/endpoints/meetings.py` — call `notify()` in `confirm_upload()` and MinIO webhook handler, passing user email and meeting title
- [x] T008 [P] [US1] Add transcription-completed notification hook in `backend/app/worker.py` — call `notify()` at end of `stage_transcribe()`, passing user email, meeting title, and audio duration in extra
- [x] T009 [P] [US1] Add summary-generated notification hook in `backend/app/worker.py` — call `notify()` at end of `stage_summarize()`, passing user email and meeting title
- [x] T010 [P] [US1] Add PDF-exported notification hook in `backend/app/api/v1/endpoints/meetings.py` — call `notify()` in export endpoint, passing user email, meeting title, and PDF type in extra

**Checkpoint**: All 6 event types send Telegram messages. Feature is fully functional.

---

## Phase 4: User Story 2 — Provider Extensibility (Priority: P2)

**Goal**: Architecture supports adding new channels without modifying event-firing code

**Independent Test**: Verify that `notify()` call sites have no Telegram-specific imports; confirm adding a mock provider requires zero changes to event hooks

- [x] T011 [US2] Review and verify provider abstraction — ensure `notify()` in `__init__.py` uses only the `NotificationProvider` protocol, no Telegram-specific code leaks into the public API or call sites

**Checkpoint**: Adding a future provider (e.g., Slack) only requires a new file in `notifications/` and a config toggle

---

## Phase 5: User Story 3 — Non-blocking Delivery (Priority: P1)

**Goal**: Notifications never block or break user-facing flows

**Independent Test**: Set invalid `TELEGRAM_BOT_TOKEN`, trigger all events, verify zero errors and normal flow completion

- [x] T012 [US3] Verify error handling in `TelegramProvider.send()` — ensure all exceptions from `httpx.Client.post()` are caught and logged as warnings, never raised. Verify timeout is set (5 seconds max).
- [x] T013 [US3] Verify graceful degradation in `notify()` — ensure missing `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` causes silent skip with no log noise (only a startup-time info log is acceptable)

**Checkpoint**: Feature degrades gracefully under all failure conditions

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and deployment

- [x] T014 Add `.env.example` entries for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `backend/.env.example` (if file exists) or document in quickstart.md
- [x] T015 Verify docker-compose passes `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars to api and worker services in `docker-compose.yml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — all 5 hook tasks (T006-T010) can run in parallel
- **User Story 2 (Phase 4)**: Can run after Phase 2 — independent review task
- **User Story 3 (Phase 5)**: Can run after Phase 2 — independent verification tasks
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within Each User Story

- US1: All hook tasks (T006-T010) touch different files — fully parallelizable
- US2: Single review task — no internal dependencies
- US3: Two verification tasks — can run sequentially

### Parallel Opportunities

```text
After Phase 2 completes:
  ├── T006 [US1] deps.py login hook
  ├── T007 [US1] meetings.py upload hook
  ├── T008 [US1] worker.py transcription hook
  ├── T009 [US1] worker.py summary hook
  ├── T010 [US1] meetings.py export hook
  ├── T011 [US2] provider abstraction review
  └── T012-T013 [US3] error handling verification
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T005)
3. Complete Phase 3: User Story 1 (T006-T010) — all parallelizable
4. **STOP and VALIDATE**: Create Telegram bot, set env vars, trigger events
5. Deploy to VPS

### Incremental Delivery

1. Setup + Foundational → `notify()` API ready
2. Add US1 event hooks → Test with real Telegram bot → Deploy (MVP!)
3. Verify US2 (extensibility) + US3 (error handling) → Confidence in production readiness

---

## Notes

- Total tasks: 15
- US1: 5 tasks (all parallelizable) | US2: 1 task | US3: 2 tasks
- Setup: 2 tasks | Foundational: 3 tasks | Polish: 2 tasks
- All US1 tasks touch different files — maximum parallelism
- No database migrations needed
- No frontend changes needed
- Suggested MVP: Phase 1 + Phase 2 + Phase 3 (US1) = 10 tasks
