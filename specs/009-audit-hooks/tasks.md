# Tasks: BaseService Audit Hooks

**Input**: Design documents from `/specs/009-audit-hooks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Initialize feature branch `009-audit-hooks` (Completed via script)
- [x] T002 Verify backend environment and dependencies for SQLModel support

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Implement `on_before_action` and `on_after_action` stubs in `backend/app/services/base.py`
- [x] T004 Integrate `on_before_action` and `on_after_action` into `save` method of `backend/app/services/base.py`
- [x] T005 Integrate hooks into `get` and `get_all` methods of `backend/app/services/base.py`
- [x] T006 Integrate hooks into `delete` method of `backend/app/services/base.py`

## Phase 3: User Story 1 - Global Database Auditing (Priority: P1) 🎯 MVP

**Goal**: Catch all database operations in a central location.

**Independent Test**: Verify by printing/logging inside the base hooks and running any existing service test.

### Implementation for User Story 1

- [x] T007 [US1] Add basic logging to `on_before_action` in `backend/app/services/base.py` for demonstration
- [x] T008 [US1] Add basic logging to `on_after_action` in `backend/app/services/base.py` for demonstration

## Phase 4: User Story 2 - Model-Specific Audit Customization (Priority: P2)

**Goal**: Allow local services to customize auditing.

**Independent Test**: Override hooks in `MeetingService` and verify specialized output.

### Implementation for User Story 2

- [x] T009 [US2] [P] Override `on_before_action` in `backend/app/services/meeting.py`
- [x] T010 [US2] [P] Override `on_after_action` in `backend/app/services/meeting.py`

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T011 [P] Verify `StyleService` (backend/app/services/styles.py) continues to function with default hooks
- [x] T012 Code cleanup and docstring updates in `backend/app/services/base.py`

## Dependencies & Execution Order

- **Phase 1 & 2**: MUST be completed first.
- **US1**: Primary goal, should be implemented before US2.
- **US2**: Can be implemented in parallel with other story overrides if needed.

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 2 (Foundational Hooks).
2. Complete US1 (Basic Logging).
3. Validate global triggers.
