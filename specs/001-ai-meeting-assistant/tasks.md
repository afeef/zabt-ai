---
description: "Task list for AI Meeting Assistant implementation"
---

# Tasks: Enterprise AI Meeting Assistant

**Input**: Design documents from `/specs/001-ai-meeting-assistant/`
**Prerequisites**: plan.md (completed), spec.md (completed), data-model.md, contracts/api.yaml

**Tests**: Tests are INCLUDED as per project constitution (TDD lifecycle).
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Ensure exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure (Using Existing Codebase)

- [x] T001 Verify project structure (backend/app, frontend/app)
- [x] T002 Verify FastAPI (Poetry) in backend/
- [x] T003 Verify Next.js (shadcn/ui) in frontend/
- [x] T004 Update Docker Compose (Add Logto Service, Postgres, Redis, Backend, Frontend, Celery) in docker-compose.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Install dependencies: `logto` (backend), `@logto/react` (frontend)
- [x] T006 Update SQLModel + Alembic migrations in backend/app/db/
- [x] T007 Configure Logto (OIDC) environment variables in backend/app/core/config.py
- [x] T008 [P] Implement Auth Middleware (Logto JWT verify) in backend/app/core/security.py
- [x] T009 [P] Setup Celery worker + Redis connection in backend/app/worker.py
- [x] T010 [P] Setup Local File Storage service (Encrypted) in backend/app/services/storage.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-time Transcription (Priority: P1) 🎯 MVP

**Goal**: Live audio streaming -> Text via WebSocket + Whisper
**Independent Test**: Connect to WS, stream binary audio, receive text transcript.

### Tests for User Story 1 (TDD) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Create Contract Test for Meeting creation in backend/tests/contract/test_meetings.py
- [x] T011 [P] [US1] Create Integration Test for WebSocket audio stream in backend/tests/integration/test_websocket.py

### Implementation for User Story 1

- [x] T012 [P] [US1] Create Meeting model in backend/app/models/meeting.py
- [x] T013 [P] [US1] Create TranscriptSegment model in backend/app/models/meeting.py
- [x] T014 [US1] Implement MeetingService (CRUD) in backend/app/services/meeting.py
- [x] T015 [US1] Implement WhisperService (Streaming inference) in backend/app/services/transcription.py
- [x] T016 [US1] Implement WebSocket endpoint for audio streaming in backend/app/api/v1/endpoints/transcriptions.py
- [x] T017 [US1] Frontend: Implement Meeting Recorder component in frontend/app/components/meeting-recorder.tsx
- [x] T018 [US1] Frontend: Implement Real-time Transcript view in frontend/app/components/transcription-view.tsx


**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Compliance & Archives (Priority: P1)

**Goal**: Secure storage, encryption, RBAC, and data export (GDPR).
**Independent Test**: Verify encrypted files on disk, check RBAC failure for unauthorized user.

### Tests for User Story 4 (TDD) ⚠️

- [ ] T019 [P] [US4] Create Test for Data Export (GDPR) in backend/tests/integration/test_compliance.py

### Implementation for User Story 4

- [ ] T020 [P] [US4] Implement EncryptionService (AES-256 for files) in backend/app/services/encryption.py
- [ ] T021 [US4] Implement RBAC permission checks in API (backend/app/api/deps.py)
- [x] T033 [US4] Implement Encryption at Rest/Transit in backend/app/services/security.py
- [x] T034 [US4] Implement Audit Logging Middleware in backend/app/middleware/audit.py
- [ ] T035 [US4] Implement RBAC (Role Based Access Control) in backend/app/core/security.py

**Checkpoint**: Compliance features active.

---

## Phase 5: User Story 2 - Upload Recording (Priority: P2)

**Goal**: Process offline files via Celery.
**Independent Test**: Upload file -> Celery Task -> Transcript generated.

### Tests for User Story 2 (TDD) ⚠️

- [x] T024 [P] [US2] Create Test for File Upload endpoint in backend/tests/integration/test_uploads.py

### Implementation for User Story 2

- [x] T025 [P] [US2] Implement Celery Task for Audio Processing in backend/app/worker.py
- [x] T026 [US2] Implement Upload endpoint using Celery task in backend/app/api/v1/endpoints/meetings.py
- [x] T027 [US2] Frontend: Create Upload Dashboard component in frontend/app/components/upload-dashboard.tsx

**Checkpoint**: Offline uploads functional.

---

## Phase 6: User Story 3 - Custom Note Styles (Priority: P2)

**Goal**: Few-shot prompting for generated notes.
**Independent Test**: Upload style PDF -> Generate notes -> Verify format match.

### Tests for User Story 3 (TDD) ⚠️

- [x] T028 [P] [US3] Create Test for Style Profile creation in backend/tests/integration/test_styles.py

### Implementation for User Story 3

- [x] T029 [P] [US3] Create StyleProfile model in backend/app/models/style.py
- [x] T030 [US3] Implement StyleService (PDF parsing) in backend/app/services/styles.py
- [x] T031 [US3] Implement LLM Note Generation (Pydantic-AI) using StyleProfile in backend/app/services/llm.py
- [x] T032 [US3] Frontend: Create Style configuration page in frontend/app/dashboard/styles/page.tsx

### Implementation for User Story 5

- [x] T038 [US5] Create Subscription model in backend/app/models/subscription.py
- [x] T039 [US5] Implement StripeService (Mock) in backend/app/services/stripe.py
- [x] T040 [US5] Implement Webhook handler for Stripe events in backend/app/api/v1/endpoints/billing.py
- [x] T041 [US5] Frontend: Create Pricing Page component in frontend/app/pricing/page.tsx

**Checkpoint**: Custom styling functional.

---

## Phase 7: User Story 5 - Subscription Management (Priority: P3)

**Goal**: Quota management and rate limiting.
**Independent Test**: Simulate quota exceeded -> Verify API rejection.

### Implementation for User Story 5

- [ ] T033 [P] [US5] Implement UsageQuota tracking in User model (via Logto sync/webhooks) in backend/app/models/user.py
- [ ] T034 [US5] Implement RateLimiting/Quota checks dependency in backend/app/api/deps.py
- [x] T035 [US5] Frontend: Create Subscription/Usage page in frontend/app/dashboard/subscription/page.tsx

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in docs/
- [ ] T037 E2E Testing with Playwright
- [ ] T038 Performance optimization for WebSocket audio buffer
- [ ] T039 Security hardening (ensure TLS 1.3 enforcement)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1.
- **User Stories (Phase 3-7)**: Depend on Phase 2.
  - Phase 3 (US1) & Phase 4 (US4) are P1 priority.
  - Phase 5 (US2) & Phase 6 (US3) are P2 priority.
  - Phase 7 (US5) is P3 priority.

### Implementation Strategy

1. **MVP First**: Complete Phase 1 -> Phase 2 -> Phase 3 (US1: Real-time).
   - *Result*: Functional real-time transcription app.
2. **Compliance**: Add Phase 4 (US4: Compliance) immediately after to ensure security.
3. **Enhancement**: Add Phase 5 (Uploads) & Phase 6 (Styles).
4. **Monetization**: Add Phase 7 (Subscriptions) last.
