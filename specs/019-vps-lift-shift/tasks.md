# Tasks: Lift-and-Shift Backend to Contabo VPS

**Input**: Design documents from `/specs/019-vps-lift-shift/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: No automated tests — this is an infrastructure migration validated manually via quickstart.md scenarios.

**Organization**: Tasks are grouped by user story to enable independent validation of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare docker-compose.yml changes and VPS environment

- [x] T001 Add Qdrant service with persistent volume and health check to `docker-compose.yml`
- [x] T002 Add `restart: unless-stopped` to all services in `docker-compose.yml`
- [x] T003 Verify `docker compose up` still works locally after docker-compose.yml changes (no regressions)

---

## Phase 2: Foundational (VPS Provisioning)

**Purpose**: VPS must be accessible and secured before any services can be deployed

**Note**: These tasks are manual/scripted on the VPS, not code changes.

- [x] T004 SSH into Contabo VPS and install Docker Engine + Docker Compose plugin
- [x] T005 Configure UFW firewall: deny all incoming, allow SSH + HTTP (80) + HTTPS (443)
- [x] T006 ~~Install cloudflared~~ — replaced with Cloudflare DNS A record (proxied) pointing to VPS IP
- [x] T007 ~~Copy tunnel credentials~~ — N/A, using DNS instead of tunnel
- [x] T008 ~~Install cloudflared systemd service~~ — N/A, using DNS instead of tunnel
- [x] T009 Verify Cloudflare DNS routes traffic to VPS: `curl https://api.zabt.ai/api/v1/health`

**Checkpoint**: VPS is secured and tunnel is live. No Docker services running yet.

---

## Phase 3: User Story 1 - Backend Accessible from Internet (Priority: P1) MVP

**Goal**: FastAPI backend running on VPS, accessible via Cloudflare tunnel through Kong gateway.

**Independent Test**: Open `https://api.zabt.ai/api/v1/health` in browser and get a response.

### Implementation for User Story 1

- [x] T010 [US1] Clone repository to `/opt/zabt` on VPS
- [x] T011 [US1] Create `.env` file on VPS with production environment variables
- [x] T012 [US1] Build and start all services on VPS: `docker compose up -d`
- [x] T013 [US1] Migrate database from local to VPS via pg_dump/psql
- [x] T014 [US1] Verify Kong gateway responds via Cloudflare: `curl https://api.zabt.ai/api/v1/health`
- [x] T015 [US1] Update Vercel frontend environment variable `NEXT_PUBLIC_API_URL` if backend URL changed
- [x] T016 [US1] Verify frontend login works via Vercel hitting VPS backend

**Checkpoint**: Users can log in and browse the dashboard via the Vercel frontend connected to the VPS backend.

---

## Phase 4: User Story 2 - File Upload and Storage on VPS (Priority: P1)

**Goal**: Audio file uploads go to MinIO on VPS and meeting records are created in PostgreSQL on VPS.

**Independent Test**: Upload a 50 MB audio file through the frontend and verify it appears in MinIO and the database.

### Implementation for User Story 2

- [x] T017 [US2] Verify MinIO is running and accessible on VPS
- [x] T018 [US2] Verify MinIO bucket `zabt-media` exists (minio-init created it)
- [x] T019 [US2] Upload a test audio file through the frontend and confirm meeting record is created
- [x] T020 [US2] Verify uploaded file exists in MinIO on VPS

**Checkpoint**: File uploads work end-to-end. Meeting records are created in the VPS database.

---

## Phase 5: User Story 3 - End-to-End Transcription Pipeline on VPS (Priority: P1)

**Goal**: Full pipeline (download → transcribe → diarize → summarize → notify) runs on VPS using CPU worker.

**Independent Test**: Upload a short audio file (~2-5 min), wait for pipeline to complete, verify transcript + summary + email.

### Implementation for User Story 3

- [x] T021 [US3] Start CPU worker on VPS: `COMPOSE_PROFILES=cpu docker compose up -d worker`
- [x] T022 [US3] Verify worker connects to Redis and is ready
- [x] T023 [US3] Upload audio file and monitor pipeline progress
- [x] T024 [US3] Verify transcription completes on CPU
- [x] T025 [US3] Verify summary is generated and meeting status shows "completed" in dashboard
- [x] T026 [US3] Verify summary email is received via Resend

**Checkpoint**: Full transcription pipeline works end-to-end on VPS using CPU. Email notification received.

---

## Phase 6: User Story 4 - Qdrant Vector Database Available (Priority: P2)

**Goal**: Qdrant is running, healthy, and persisting data on the VPS.

**Independent Test**: Check Qdrant health endpoint returns OK.

### Implementation for User Story 4

- [x] T027 [US4] Verify Qdrant container is running on VPS
- [x] T028 [US4] Verify Qdrant health endpoint
- [x] T029 [US4] Verify Qdrant volume persistence

**Checkpoint**: Qdrant is running and healthy, ready for future AI Chat feature.

---

## Phase 7: User Story 5 - VPS Security and Stability (Priority: P2)

**Goal**: Firewall blocks all non-essential ports, Docker services auto-restart on crash/reboot.

**Independent Test**: Port scan VPS from external machine; restart a container and verify auto-recovery.

### Implementation for User Story 5

- [x] T030 [US5] Run external port scan against VPS public IP and verify only SSH + HTTP/HTTPS open
- [x] T031 [US5] Kill a Docker container and verify it auto-restarts
- [x] T032 [US5] Reboot VPS and verify all Docker services come back up automatically

**Checkpoint**: VPS is secured and resilient. No internal ports exposed.

---

## Phase 8: User Story 6 - Local Development Mode (Priority: P1)

**Goal**: `docker compose up` still works locally after all changes, GPU worker available via `--profile gpu`.

**Independent Test**: Run `docker compose up` on local machine and verify API responds.

### Implementation for User Story 6

- [x] T033 [US6] Run `docker compose up` locally and verify all services start without errors
- [x] T034 [US6] Verify local API responds
- [x] T035 [US6] Verify `docker compose --profile gpu up` starts GPU worker locally

**Checkpoint**: Local development is unaffected by VPS migration changes.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and cleanup

- [x] T036 [P] Update `README.md` with VPS deployment info and link to quickstart
- [x] T037 [P] Verify `.env.example` is complete with all required variables
- [x] T038 Run full quickstart.md validation scenario end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — code changes to docker-compose.yml
- **Foundational (Phase 2)**: No dependency on Phase 1 code changes — VPS provisioning is independent
- **US1 (Phase 3)**: Depends on Phase 1 (docker-compose changes) + Phase 2 (VPS ready)
- **US2 (Phase 4)**: Depends on US1 (services running on VPS)
- **US3 (Phase 5)**: Depends on US2 (files uploadable) + worker started
- **US4 (Phase 6)**: Depends on Phase 1 (Qdrant in docker-compose) + US1 (stack running)
- **US5 (Phase 7)**: Depends on Phase 2 (firewall) + US1 (services running)
- **US6 (Phase 8)**: Depends on Phase 1 (docker-compose changes) — can run in parallel with VPS tasks
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Backend Accessible)**: Requires VPS provisioned + docker-compose changes
- **US2 (File Upload)**: Requires US1 complete (services running)
- **US3 (Transcription Pipeline)**: Requires US2 complete (files uploadable)
- **US4 (Qdrant)**: Can start after US1 (independent of US2/US3)
- **US5 (Security)**: Can start after VPS provisioning (independent of US2/US3/US4)
- **US6 (Local Dev)**: Can start after Phase 1 (independent of all VPS tasks)

### Parallel Opportunities

- Phase 1 (code changes) and Phase 2 (VPS provisioning) can run in parallel
- US4 (Qdrant), US5 (Security), US6 (Local Dev) can all run in parallel after their dependencies are met
- T036 and T037 (documentation) can run in parallel

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1: docker-compose.yml changes
2. Complete Phase 2: VPS provisioning
3. Complete Phase 3: US1 — Backend accessible via Cloudflare tunnel
4. **STOP and VALIDATE**: Can users log in and see dashboard?
5. If yes: proceed to US2 → US3

### Incremental Delivery

1. Phase 1 + Phase 2 → VPS ready
2. US1 → Backend live → Validate login/dashboard
3. US2 → File uploads work → Validate upload
4. US3 → Full pipeline on CPU → Validate transcription + email
5. US4 + US5 + US6 → Qdrant ready, security hardened, local dev verified
6. Polish → Documentation updated

---

## Notes

- This is primarily an infrastructure migration — most tasks are manual VPS operations, not code changes
- The only code changes are in `docker-compose.yml` (Phase 1: add Qdrant, add restart policies)
- CPU transcription is slow (~20-60 min for 30 min audio) — use a short test file (2-5 min) for validation
- Commit docker-compose.yml changes after Phase 1, push to VPS via git pull
