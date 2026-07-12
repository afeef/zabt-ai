# Tasks: Kong API Gateway

**Input**: Design documents from `/specs/001-kong-api-gateway/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/infra-gateway.md ✓, quickstart.md ✓

**Organization**: Tasks grouped by user story. All changes are YAML/config only — no backend or frontend source code is modified.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Create new directory and file structure required by the gateway

- [X] T001 Create `kong/` directory at repo root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core gateway config and Docker Compose wiring that all user stories depend on

**⚠️ CRITICAL**: All three user stories require Kong to be running. This phase must complete before US1–US3.

- [X] T002 Write `kong/kong.yml` with `api-service` route (`/` → `api:8000`, `strip_path: false`, `preserve_host: false`) and `minio-service` route (`/storage` → `minio:9000`, `strip_path: true`, `preserve_host: true`) — full content per `specs/001-kong-api-gateway/quickstart.md`
- [X] T003 Add `kong` service to `docker-compose.yml` (image `kong:3.6`, env vars `KONG_DATABASE=off`, `KONG_DECLARATIVE_CONFIG=/etc/kong/kong.yml`, `KONG_PROXY_LISTEN=0.0.0.0:8000`, `KONG_ADMIN_LISTEN=127.0.0.1:8001`, volume mount `./kong/kong.yml:/etc/kong/kong.yml:ro`, port `8100:8000`, depends_on api + minio)
- [X] T004 [P] Remove `ports` binding from `api` service in `docker-compose.yml` (comment out or delete `"8000:8000"`)
- [X] T005 [P] Remove `ports` bindings from `minio` service in `docker-compose.yml` (comment out or delete `"9000:9000"` and `"9001:9001"`)

**Checkpoint**: Run `docker compose up -d kong` — confirm Kong starts and `curl http://localhost:8100/api/v1/health` returns a response (not connection refused)

---

## Phase 3: User Story 1 — Single Public Entry Point (Priority: P1) 🎯 MVP

**Goal**: All external API traffic enters through Kong; MinIO has no public port.

**Independent Test**: Point browser at `api.zabt.ai/api/v1/meetings` and get a valid API response. Attempt direct connection to `:9000` from outside the host — expect connection refused.

- [X] T006 [US1] Update `config.yml` Cloudflare tunnel ingress rule for `api.zabt.ai` from `http://localhost:8000` to `http://localhost:8100`
- [ ] T007 [US1] Restart Cloudflare tunnel (`cloudflared service restart` or equivalent) and verify API requests from an external client resolve correctly through `api.zabt.ai`

**Checkpoint**: US1 is independently complete. External API traffic flows through Kong. MinIO port 9000 is not reachable externally (verify with `nc -zv <host-ip> 9000` from an external machine — expect timeout/refused).

---

## Phase 4: User Story 2 — Presigned Upload URLs via Gateway (Priority: P2)

**Goal**: File uploads from remote clients succeed using presigned URLs that reference the gateway hostname, not `localhost:9000`.

**Independent Test**: Upload a meeting file from a browser on a remote machine. Verify the presigned URL in the API response begins with `https://api.zabt.ai/storage/...` and the PUT to that URL stores the file successfully in MinIO.

- [X] T008 [US2] Update `MINIO_PUBLIC_ENDPOINT` env var from `http://localhost:9000` to `https://api.zabt.ai` in `docker-compose.yml` for `api`, `worker`, and `worker-gpu` services
- [ ] T009 [US2] Rebuild and restart the `api` service (`docker compose up -d --build api`) and verify presigned upload URL hostname by calling `POST /api/v1/meetings/upload-url` — the returned URL must start with `https://api.zabt.ai/storage/`

**Checkpoint**: US2 is independently complete. Upload a file end-to-end from a remote client — confirm file appears in MinIO bucket and meeting processing starts successfully.

---

## Phase 5: User Story 3 — Rate Limiting & Declarative Routes (Priority: P3)

**Goal**: Kong returns HTTP 429 after exceeding configured threshold; adding a new route requires only a `kong/kong.yml` edit + `docker compose restart kong`.

**Independent Test**: Send 101+ requests in one minute to any API endpoint — requests beyond threshold return 429 with `Retry-After` header.

- [X] T010 [US3] Add `rate-limiting` plugin to `api-service` routes in `kong/kong.yml` (config: `minute: 100`, `policy: local`, `error_code: 429`) per `specs/001-kong-api-gateway/contracts/infra-gateway.md`
- [ ] T011 [US3] Reload Kong config (`docker compose restart kong`) and validate 429 response using the rate limit test command from `specs/001-kong-api-gateway/quickstart.md` (loop 105 requests, expect 429 after ~100)

**Checkpoint**: US3 is independently complete. Rate limiting is active on all API routes.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T012 Run all 4 validation scenarios from `specs/001-kong-api-gateway/quickstart.md` end-to-end and confirm each passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **blocks all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 only — no dependency on US2 or US3
- **US2 (Phase 4)**: Depends on Phase 2 only — can run in parallel with US1 after Phase 2
- **US3 (Phase 5)**: Depends on Phase 2 only — can run in parallel with US1/US2 after Phase 2
- **Polish (Phase 6)**: Depends on all story phases complete

### Within Foundational Phase

- T002 before T003 (kong service mounts kong.yml)
- T004 and T005 can run in parallel [P] — different services in same file

### Parallel Opportunities

```bash
# Phase 2 — after T002 + T003:
Task T004: Remove api port bindings in docker-compose.yml
Task T005: Remove minio port bindings in docker-compose.yml

# After Phase 2 complete, all user stories can proceed in parallel:
Task T006+T007 (US1): Cloudflare tunnel update
Task T008+T009 (US2): MINIO_PUBLIC_ENDPOINT update
Task T010+T011 (US3): Rate limiting plugin
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Phase 1: Create `kong/` directory
2. Phase 2: Write `kong.yml`, add `kong` service, remove port bindings
3. Phase 3: Update `config.yml`, restart Cloudflare tunnel
4. **STOP and VALIDATE**: External API traffic flows through Kong, MinIO unreachable externally
5. US2 and US3 can be added incrementally without disrupting US1

### Incremental Delivery

1. Complete Phase 1 + Phase 2 → Kong running, internal services hidden
2. Complete US1 → External traffic consolidated through gateway (MVP)
3. Complete US2 → File uploads work from remote clients
4. Complete US3 → Rate limiting active, declarative routing established
5. Each story is independently testable and does not break previous stories

---

## Notes

- Zero backend/frontend source code changes required — all work is YAML config
- `preserve_host: true` on the MinIO route is critical — do not remove (S3 HMAC signature will fail)
- `MINIO_PUBLIC_ENDPOINT` change requires `api` service restart to take effect
- After `kong/kong.yml` changes: `docker compose restart kong` (no other service restarts needed)
- Reverting US1 requires only changing `config.yml` back to `localhost:8000` and restarting the tunnel
