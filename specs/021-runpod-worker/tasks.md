# Tasks: Transcription Worker Provider Switch (RunPod / Local)

**Input**: Design documents from `/specs/021-runpod-worker/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested — no test tasks included.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add `runpod` dependency and configuration settings shared by all stories

- [x] T001 Add `runpod` package to core dependencies in `backend/pyproject.toml`
- [x] T002 Add `TRANSCRIPTION_PROVIDER`, `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`, `RUNPOD_POLL_INTERVAL`, and `RUNPOD_TIMEOUT` settings to `backend/app/core/config.py`
- [x] T003 [P] Add `TRANSCRIPTION_PROVIDER` and `RUNPOD_*` environment variables to `docker-compose.yml` for both `worker` and `worker-gpu` services
- [x] T004 [P] Add `TRANSCRIPTION_PROVIDER` and `RUNPOD_*` entries to `.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update the factory to dispatch by provider — MUST complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Update `backend/app/services/transcription/factory.py` to read `TRANSCRIPTION_PROVIDER` from settings and dispatch to either WhisperProvider (`local`) or RunPodProvider (`runpod`). Add startup validation: if `TRANSCRIPTION_PROVIDER=runpod` and `RUNPOD_API_KEY` or `RUNPOD_ENDPOINT_ID` are empty, raise a clear error. Keep lazy-loading pattern for both providers.

**Checkpoint**: Factory dispatches by env var — provider implementations can now be built independently

---

## Phase 3: User Story 1 — RunPod Transcription on VPS (Priority: P1) 🎯 MVP

**Goal**: Worker delegates transcription to RunPod Serverless when `TRANSCRIPTION_PROVIDER=runpod`

**Independent Test**: Set `TRANSCRIPTION_PROVIDER=runpod` with valid credentials, upload a meeting, verify transcript segments and summary are stored in DB.

### Implementation for User Story 1

- [x] T006 [US1] Create `backend/app/services/transcription/runpod_provider.py` with `RunPodProvider` class implementing `TranscriptionProvider` Protocol:
  - `__init__`: initialize `runpod` SDK with `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` from settings
  - `get_provider_name()`: return `"runpod_whisper"`
  - `transcribe_chunk()`: raise `NotImplementedError` (real-time WebSocket not supported via RunPod)

- [x] T007 [US1] Implement `RunPodProvider.process_audio()` in `backend/app/services/transcription/runpod_provider.py`:
  - Generate a presigned download URL for the audio file using storage provider (`storage.get_presigned_download_url()`)
  - Call `on_status_change("transcribing")` callback
  - Submit async job to RunPod via `endpoint.run({"audio_url": presigned_url, "language": config.language, "min_speakers": config.min_speakers, "max_speakers": config.max_speakers})`
  - Poll for completion with `RUNPOD_POLL_INTERVAL` interval and `RUNPOD_TIMEOUT` timeout
  - Call `on_status_change("diarizing")` when status transitions (or after a reasonable delay to keep progress UI moving)
  - On completion, parse the RunPod response JSON into `TranscriptionResult`
  - On failure/timeout, raise descriptive exception

- [x] T008 [US1] Implement `RunPodProvider._parse_response()` helper in `backend/app/services/transcription/runpod_provider.py`:
  - Map RunPod output JSON to `TranscriptionResult` dataclass
  - Map each segment to `ResultSegment` with `start`, `end`, `text`, `speaker`
  - Map each word to `WordTimestamp` with `word`, `start`, `end`, `speaker_label`
  - Set `provider_name="runpod_whisper"`, `recognition_method="runpod_whisperx"`
  - Handle partial results gracefully (missing diarization → `SPEAKER_UNKNOWN`)

- [x] T009 [US1] Update `backend/app/services/transcription/factory.py` to import and return `RunPodProvider` when `TRANSCRIPTION_PROVIDER=runpod` (complete the dispatch logic stub from T005)

- [x] T010 [US1] Modify `stage_transcribe` in `backend/app/worker.py` to pass the audio `file_path` (S3 key) to `RunPodProvider.process_audio()` so the provider can generate its own presigned URL. Update the `process_audio` signature call: the provider needs access to the meeting's `file_path` from storage to generate the presigned URL. Add `file_path` to the provider invocation context or have the worker generate the presigned URL and pass it alongside `audio_path`.

**Checkpoint**: Upload a meeting with `TRANSCRIPTION_PROVIDER=runpod` → worker sends to RunPod → polls → stores segments → summarizes locally

---

## Phase 4: User Story 2 — Local GPU Transcription Unchanged (Priority: P2)

**Goal**: Local development with `TRANSCRIPTION_PROVIDER=local` works identically to current behavior

**Independent Test**: Start with `COMPOSE_PROFILES=local` and no `TRANSCRIPTION_PROVIDER` set. Upload a meeting. GPU worker transcribes locally as before.

### Implementation for User Story 2

- [x] T011 [US2] Verify `backend/app/services/transcription/factory.py` returns `WhisperProvider` when `TRANSCRIPTION_PROVIDER` is `local` or unset — this should already work from T005, verify with a manual read-through and ensure no RunPod imports are triggered in local mode

- [x] T012 [US2] Verify `backend/app/worker.py` requires no changes — `stage_transcribe` calls `get_provider()` which returns WhisperProvider in local mode, and the rest of the pipeline (download, transcribe, summarize) is unchanged

**Checkpoint**: Local mode is a no-op verification — existing behavior preserved

---

## Phase 5: User Story 3 — RunPod Serverless Endpoint (Priority: P3)

**Goal**: Standalone RunPod handler that runs Whisper large-v3 + pyannote and returns Zabt-compatible JSON

**Independent Test**: Deploy handler to RunPod, call directly with an audio URL, verify JSON response matches `TranscriptionResult` format.

### Implementation for User Story 3

- [x] T013 [P] [US3] Create `runpod/` directory at repository root

- [x] T014 [US3] Create `runpod/handler.py` — RunPod Serverless handler:
  - Load WhisperX model and pyannote DiarizationPipeline globally (warm between jobs)
  - Handler receives `{"audio_url": str, "language": str|null, "min_speakers": int, "max_speakers": int}`
  - Download audio from URL to temp file
  - Run WhisperX transcribe → align → diarize (same 3-stage pipeline as WhisperProvider)
  - Return JSON matching `TranscriptionResult` format: `{"text", "language", "segments": [{"start", "end", "text", "speaker", "words": [...]}], "audio_duration_seconds", "provider_name", "recognition_method", "estimated_cost"}`
  - Report progress via `runpod.serverless.progress_update()`
  - Clean up temp file in finally block

- [x] T015 [US3] Create `runpod/Dockerfile` — GPU image for RunPod deployment:
  - Base: `nvidia/cuda:12.1.0-runtime-ubuntu22.04` with Python 3.11
  - Install WhisperX, pyannote-audio, runpod, ffmpeg
  - Copy `handler.py`
  - Set `CMD ["python", "handler.py"]`

- [x] T016 [P] [US3] Create `runpod/README.md` with build, push, and RunPod dashboard deployment instructions

**Checkpoint**: Handler deployed to RunPod, callable with audio URL, returns correct JSON format

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, configuration, and cleanup

- [x] T017 [P] Update `README.md` to document `TRANSCRIPTION_PROVIDER` toggle, RunPod setup, and deployment scenarios
- [x] T018 [P] Add `runpod/` to `.dockerignore` in `backend/` to prevent it from being included in backend Docker builds (N/A — backend build context is `./backend`, `runpod/` is at repo root)
- [ ] T019 Validate end-to-end: deploy to VPS with `TRANSCRIPTION_PROVIDER=runpod`, upload meeting, verify full pipeline (download → RunPod transcribe → summarize → email)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001, T002 from Setup
- **US1 (Phase 3)**: Depends on T005 from Foundational
- **US2 (Phase 4)**: Depends on T005 from Foundational — verification only
- **US3 (Phase 5)**: No dependencies on other phases — standalone handler, can run in parallel with US1
- **Polish (Phase 6)**: Depends on US1 and US3 completion

### User Story Dependencies

- **US1 (RunPod provider)**: Depends on Foundational (factory dispatch) — core MVP
- **US2 (Local unchanged)**: Depends on Foundational — verification only, no new code
- **US3 (RunPod handler)**: Independent — can start after Setup (needs no backend changes)

### Within Each User Story

- US1: T006 (class skeleton) → T007 (process_audio) → T008 (parse response) → T009 (factory wiring) → T010 (worker integration)
- US2: T011 → T012 (both verification tasks)
- US3: T013 (directory) → T014 (handler) → T015 (Dockerfile) → T016 (README, parallel with T015)

### Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- US1 and US3 can proceed in parallel (independent codebases)
- T013 and T016 can run in parallel with other US3 tasks
- T017 and T018 can run in parallel (different files)

---

## Parallel Example: Phase 1

```bash
# After T001 and T002 complete, these can run in parallel:
Task T003: "Add env vars to docker-compose.yml"
Task T004: "Add env vars to .env.example"
```

## Parallel Example: US1 + US3

```bash
# After Foundational (T005) completes, these can run in parallel:
# Team A: US1 — RunPod provider in backend
Task T006: "Create RunPodProvider class"
Task T007: "Implement process_audio"
...

# Team B: US3 — RunPod handler (standalone)
Task T013: "Create runpod/ directory"
Task T014: "Create handler.py"
Task T015: "Create Dockerfile"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005)
3. Complete Phase 3: US1 — RunPod Provider (T006-T010)
4. **STOP and VALIDATE**: Test with a real RunPod endpoint
5. Deploy to VPS with `TRANSCRIPTION_PROVIDER=runpod`

### Incremental Delivery

1. Setup + Foundational → Configuration ready
2. US1 (RunPod Provider) → VPS can transcribe via RunPod (MVP!)
3. US2 (Local verification) → Confirm no regression
4. US3 (RunPod handler) → Self-hosted RunPod endpoint
5. Polish → Documentation and E2E validation

---

## Notes

- The RunPod handler (US3) is a separate deployable — it can be built and tested independently of the backend
- `worker.py` should need minimal changes — the factory pattern handles provider dispatch
- The `runpod` Python SDK is lightweight (~2MB) and doesn't require ML dependencies
- For US1 T010: the key design decision is how `RunPodProvider.process_audio()` gets the S3 file key to generate a presigned URL. Options: (a) the worker passes the presigned URL as a parameter, (b) the provider receives the file_path and generates its own URL. Option (a) is simpler — generate the presigned URL in the worker before calling `process_audio()` and pass it via config or a new parameter.
