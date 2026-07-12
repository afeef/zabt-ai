# Tasks: Whisper-to-Chirp Transcription Migration

**Input**: Design documents from `/specs/013-whisper-chirp-migration/`
**Prerequisites**: spec.md (required)

**Organization**: Tasks follow the user-specified priority order, mapped to spec user
stories (US1–US5). Each phase builds on the previous and can be validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Current Architecture (reference)

```text
backend/app/
├── services/transcription.py   # Hardcoded Whisper — will be refactored
├── services/storage.py         # S3StorageService (MinIO) — will be extended
├── services/base.py            # BaseService (repository pattern)
├── worker.py                   # Celery task — will consume provider interface
├── core/config.py              # Settings — will gain GCS + Chirp config
├── models.py                   # Meeting, TranscriptSegment, UserTier
├── api/v1/endpoints/
│   ├── transcriptions.py       # WebSocket — will consume provider interface
│   └── meetings.py             # REST — no changes
├── cli/transcribe.py           # CLI — will consume provider interface
└── middleware/audit.py         # Audit — will be extended for cost logging
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies, configuration, and project structure for the migration

- [x] T001 [P] Add `google-cloud-speech>=2.0` and `google-cloud-storage` to
  `backend/pyproject.toml` (or `requirements.txt`) as project dependencies
- [x] T002 [P] Add GCS and Chirp configuration fields to
  `backend/app/core/config.py`:
  - `GOOGLE_CLOUD_PROJECT: str`
  - `GCS_AUDIO_BUCKET: str` (for audio staging)
  - `GCS_REGION: str = "us-central1"`
  - `GOOGLE_APPLICATION_CREDENTIALS: str = ""` (path to service account JSON)
  - `TRANSCRIPTION_PROVIDER: str = "whisper"` (feature flag: "whisper" | "chirp")
  - `CHIRP_MODEL: str = "chirp_3"`
  - `CIRCUIT_BREAKER_THRESHOLD: int = 5`
  - `CIRCUIT_BREAKER_COOLDOWN_SECONDS: int = 300`
- [x] T003 [P] Create directory structure for provider abstraction:
  `backend/app/services/transcription/` (new package to replace the single-file
  `backend/app/services/transcription.py`)

---

## Phase 2: Provider Abstraction Interface (Priority #1)

**Purpose**: Define the abstract contract so both Whisper and Chirp can be swapped
without touching consumers. This is the foundation for every subsequent phase.

**Goal**: After this phase, all existing code (worker, CLI, WebSocket) calls the
abstraction — not the concrete Whisper class directly.

- [x] T004 [US1] Define `TranscriptionProvider` Protocol in
  `backend/app/services/transcription/provider.py`:
  - `process_audio(audio_path: str, ...) -> TranscriptionResult`
  - `transcribe_chunk(data: bytes) -> str` (for real-time)
  - `get_provider_name() -> str`
- [x] T005 [P] [US1] Define `TranscriptionResult` dataclass in
  `backend/app/services/transcription/types.py`:
  - `text: str` (full transcript)
  - `language: str`
  - `segments: list[TranscriptSegment]` (not the DB model — a plain dataclass)
  - Each segment: `start: float`, `end: float`, `text: str`,
    `speaker: str | None`, `words: list[WordTimestamp]`
  - `WordTimestamp`: `word: str`, `start: float`, `end: float`,
    `speaker_label: str | None`
  - `provider_name: str`
  - `recognition_method: str` (e.g., "batch_dynamic", "batch_standard", "streaming")
  - `audio_duration_seconds: float`
  - `estimated_cost: float`
- [x] T006 [US1] Wrap existing `TranscriptionService` as `WhisperProvider` in
  `backend/app/services/transcription/whisper_provider.py`:
  - Move all logic from `backend/app/services/transcription.py` into this class
  - Implement `TranscriptionProvider` Protocol
  - Map existing whisperx output dict → `TranscriptionResult` dataclass
  - Set `recognition_method = "local_whisperx"`
  - Compute `audio_duration_seconds` from segment end times
  - Compute `estimated_cost` using `$0.006/min * duration`
- [x] T007 [US1] Create `TranscriptionProviderFactory` in
  `backend/app/services/transcription/factory.py`:
  - Reads `settings.TRANSCRIPTION_PROVIDER` to select active provider
  - Returns `WhisperProvider` when `"whisper"` (default — backward compatible)
  - Returns `ChirpProvider` when `"chirp"` (wired in Phase 4)
  - Accepts optional `user_tier` parameter for routing logic (Phase 6)
- [x] T008 [US1] Create package `__init__.py` at
  `backend/app/services/transcription/__init__.py`:
  - Export `get_provider()` factory function
  - Export `TranscriptionResult`, `TranscriptionProvider` types
- [x] T009 [US1] Update `backend/app/worker.py`:
  - Replace `from app.services.transcription import transcription_service`
    with `from app.services.transcription import get_provider`
  - Call `provider = get_provider()` then `provider.process_audio(...)` instead
    of `transcription_service.process_audio(...)`
  - Map `TranscriptionResult` segments → DB `TranscriptSegment` objects
    (same logic, but reading from the dataclass instead of a raw dict)
- [x] T010 [US1] Update `backend/app/cli/transcribe.py`:
  - Replace `from app.services.transcription import transcription_service`
    with `from app.services.transcription import get_provider`
  - Call `provider = get_provider()` then `provider.process_audio(...)`
  - Update `_print_transcript()` to accept `TranscriptionResult` instead of
    raw dict
  - Update `_print_json()` to serialize `TranscriptionResult` instead of raw dict
- [x] T011 [US1] Update `backend/app/api/v1/endpoints/transcriptions.py`:
  - Replace `from app.services.transcription import transcription_service`
    with `from app.services.transcription import get_provider`
  - Call `provider = get_provider()` then `provider.transcribe_chunk(data)`
- [x] T012 [US1] Delete the old `backend/app/services/transcription.py` single-file
  module (all logic now lives in the `transcription/` package)

**Checkpoint**: All existing functionality works exactly as before. `TRANSCRIPTION_PROVIDER=whisper` (default). No behavioral change — only structural.

---

## Phase 3: GCS Audio Upload Pipeline (Priority #2)

**Purpose**: Chirp 3 BatchRecognize requires audio hosted on GCS. Build the upload
pipeline that stages audio from MinIO → GCS before transcription.

- [x] T013 [US1] Create `GCSStorageService` in
  `backend/app/services/gcs_storage.py`:
  - Initialize `google.cloud.storage.Client` using
    `settings.GOOGLE_APPLICATION_CREDENTIALS`
  - `upload_audio(local_path: str, meeting_id: int) -> str`:
    uploads file to `gs://{GCS_BUCKET}/audio/{meeting_id}/{filename}`,
    returns the `gs://` URI
  - `delete_audio(gcs_uri: str) -> None`: cleanup after transcription
  - `get_gcs_uri(meeting_id: int, filename: str) -> str`: construct URI
- [x] T014 [P] [US1] Add GCS bucket lifecycle configuration note to
  `specs/013-whisper-chirp-migration/quickstart.md`:
  - Document required GCS bucket creation
  - Document service account permissions (roles/speech.client,
    roles/storage.objectAdmin)
  - Document all new environment variables from T002

**Checkpoint**: GCS upload/delete works independently. Can be tested by uploading a
sample file and verifying the `gs://` URI is accessible.

---

## Phase 4: ChirpProvider Implementation (Priority #3 + #4)

**Purpose**: Implement the Chirp 3 provider — batch recognition with diarization,
word-level timestamps, and automatic language detection. This phase also covers
response normalization (Priority #4) since parsing is internal to the provider.

- [x] T015 [US1] [US3] [US4] Create `ChirpProvider` in
  `backend/app/services/transcription/chirp_provider.py`:
  - Implement `TranscriptionProvider` Protocol
  - Initialize `google.cloud.speech_v2.SpeechClient`
  - Implement `process_audio(audio_path, ...)`:
    1. Upload audio to GCS via `GCSStorageService` (from Phase 3)
    2. Build `RecognitionConfig` with:
       - `model = "chirp_3"`
       - `language_codes = ["auto"]` (automatic detection)
       - `features.enable_word_time_offsets = True`
       - `features.enable_word_confidence = True`
       - `features.diarization_config.min_speaker_count` (configurable)
       - `features.diarization_config.max_speaker_count` (configurable)
    3. Call `BatchRecognize` with the GCS URI
    4. Poll `operation.result()` for completion
    5. Parse response → `TranscriptionResult` (T016)
    6. Cleanup: delete audio from GCS
  - Set `provider_name = "chirp_3"`
- [x] T016 [US1] [US3] [US4] Implement response normalization in
  `ChirpProvider._parse_response()` (inside `chirp_provider.py`):
  - Map `SpeechRecognitionResult` → `TranscriptionResult` dataclass
  - Extract `word.word`, `word.start_offset`, `word.end_offset` for each word
  - Extract `word.speaker_label` for diarization labels → map to
    `"SPEAKER_{label}"` format (matching existing Whisper output convention)
  - Group words into segments by speaker turn and silence gaps
  - Build `text` field as concatenation of all segments
  - Extract `result.language_code` for the `language` field
  - Compute `audio_duration_seconds` from final word's `end_offset`
  - Set `recognition_method` based on batch type (populated in Phase 6)
- [x] T017 [US3] Add diarization configuration to `backend/app/core/config.py`:
  - `DIARIZATION_MIN_SPEAKERS: int = 1`
  - `DIARIZATION_MAX_SPEAKERS: int = 10`
- [x] T017b [US1] Add audio duration validation to
  `backend/app/services/transcription/chirp_provider.py`:
  - Before submitting to BatchRecognize, check audio duration against
    max limit (8 hours for batch)
  - If duration exceeds limit, raise a `ValueError` with a user-friendly
    message: "Audio file exceeds maximum duration of {limit}. Please
    upload a shorter file."
  - Also validate in `WhisperProvider` for consistency
  - FR-011 coverage
- [x] T018 [US1] Register `ChirpProvider` in the factory
  `backend/app/services/transcription/factory.py`:
  - When `settings.TRANSCRIPTION_PROVIDER == "chirp"`, return `ChirpProvider()`

**Checkpoint**: Setting `TRANSCRIPTION_PROVIDER=chirp` and uploading a file produces
a transcript with speaker diarization, word timestamps, and auto-detected language.
The output `TranscriptionResult` is structurally identical to what `WhisperProvider`
produces. The frontend sees no difference.

---

## Phase 5: Dynamic Batch vs Standard Routing (Priority #5)

**Purpose**: Route Starter-tier (FREE) users to Dynamic Batch ($0.004/min) and
Pro-tier users to Standard Batch ($0.016/min).

- [x] T019 [US1] [US2] Add `use_dynamic_batching: bool` parameter to
  `ChirpProvider.process_audio()`:
  - When `True`: set `processing_strategy.dynamic_batching_config` on the
    `BatchRecognizeRequest` (Dynamic Batch — cheapest path)
  - When `False`: use default `BatchRecognize` without dynamic batching flag
    (Standard Batch — faster)
- [x] T020 [US1] [US2] Update `TranscriptionProviderFactory.get_provider()` in
  `backend/app/services/transcription/factory.py`:
  - Accept `user_tier: UserTier` parameter
  - When tier is `FREE`: pass `use_dynamic_batching=True` to ChirpProvider
  - When tier is `PRO` or `ENTERPRISE`: pass `use_dynamic_batching=False`
  - Set `recognition_method` accordingly:
    `"batch_dynamic"` for FREE, `"batch_standard"` for PRO/ENTERPRISE
- [x] T021 [US1] [US2] Update `backend/app/worker.py` to pass user tier:
  - Look up `Meeting.owner` → `User.tier` before calling `get_provider()`
  - Pass `user_tier=user.tier` to the factory
- [x] T022 [US1] [US2] Add cost estimation logic to `ChirpProvider`:
  - Dynamic Batch: `$0.004/min * duration_minutes`
  - Standard Batch: `$0.016/min * duration_minutes`
    (using Google's published $0.96/hr rate)
  - Store in `TranscriptionResult.estimated_cost`

**Checkpoint**: A FREE-tier user's transcription logs `recognition_method=batch_dynamic`
with the lower cost estimate. A PRO-tier user's logs `recognition_method=batch_standard`
with the higher cost. Both produce identical output quality.

---

## Phase 6: Cost Logging and Tracking (Priority #6)

**Purpose**: Add structured logging for every transcription request to enable cost
monitoring, billing reconciliation, and usage analytics.

- [x] T026 [P] [US1] Create `TranscriptionCostLogger` in
  `backend/app/services/transcription/cost_logger.py`:
  - `log_transcription(result: TranscriptionResult, user_id: int, meeting_id: int)`:
    emits a structured JSON log entry with:
    - `timestamp` (ISO 8601)
    - `user_id`
    - `meeting_id`
    - `provider_name` (e.g., "chirp_3", "whisper")
    - `recognition_method` (e.g., "batch_dynamic", "batch_standard", "streaming")
    - `audio_duration_seconds`
    - `estimated_cost`
    - `user_tier`
  - Use Python `logging` module with JSON formatter (compatible with existing
    Docker stdout capture)
- [x] T027 [US1] Integrate cost logger into `backend/app/worker.py`:
  - After successful transcription, call
    `cost_logger.log_transcription(result, user_id, meeting_id)`
- [x] T028 [P] [US1] Integrate cost logger into
  `backend/app/api/v1/endpoints/transcriptions.py`:
  - Log each chunk transcription with estimated cost
- [x] T029 [US1] Update `User.minutes_used_this_month` in
  `backend/app/worker.py` after successful transcription:
  - Increment by `ceil(result.audio_duration_seconds / 60)`
  - This enables future quota enforcement (not enforced in this migration)

**Checkpoint**: Every batch transcription emits a structured JSON log line. The
`minutes_used_this_month` field is updated on the User record.

---

## Phase 7: Circuit Breaker / Fallback Logic (Priority #7)

**Purpose**: If Chirp 3 fails 5 consecutive times, auto-fallback to Whisper for
5 minutes. Includes retry with exponential backoff on transient errors.

- [x] T030 [US5] Create `CircuitBreaker` in
  `backend/app/services/transcription/circuit_breaker.py`:
  - State: `CLOSED` (normal), `OPEN` (fallback active)
  - Track `consecutive_failures: int` and `opened_at: datetime | None`
  - `record_success()`: reset counter to 0, set state to CLOSED
  - `record_failure()`: increment counter; if >= threshold, set state to OPEN
    and record `opened_at`
  - `should_fallback() -> bool`: return True if OPEN and cooldown not expired;
    if cooldown expired, transition back to CLOSED
  - Use `settings.CIRCUIT_BREAKER_THRESHOLD` and
    `settings.CIRCUIT_BREAKER_COOLDOWN_SECONDS`
  - Thread-safe (use `threading.Lock`)
- [x] T031 [US5] Add retry with exponential backoff to `ChirpProvider`:
  - Catch `google.api_core.exceptions.ServiceUnavailable` and
    `google.api_core.exceptions.DeadlineExceeded`
  - Retry up to 3 times with backoff: 1s, 2s, 4s
  - Only count toward circuit breaker after all retries are exhausted
- [x] T032 [US5] Integrate circuit breaker into
  `backend/app/services/transcription/factory.py`:
  - Maintain a module-level `CircuitBreaker` instance
  - In `get_provider()`: if `should_fallback()` returns True, return
    `WhisperProvider` regardless of `settings.TRANSCRIPTION_PROVIDER`
  - After each transcription in worker/CLI: call `record_success()` or
    `record_failure()` on the circuit breaker
- [x] T033 [US5] Update `backend/app/worker.py` to report success/failure:
  - On successful transcription: `circuit_breaker.record_success()`
  - On Chirp-specific exception: `circuit_breaker.record_failure()`
  - Log when fallback activates: `"CIRCUIT_BREAKER: Chirp failed {n} times,
    falling back to Whisper for {cooldown}s"`

**Checkpoint**: Simulating 5 consecutive Chirp failures causes the system to
transparently route to Whisper. After 5 minutes, the next request retries Chirp.
The user never sees a provider switch — only internal logs reflect it.

---

## Phase 8: Integration Tests (Priority #8)

**Purpose**: Validate the full migration end-to-end with real and mocked providers.

- [x] T034 [P] [US1] Unit test: `WhisperProvider` implements `TranscriptionProvider`
  Protocol — `backend/tests/unit/test_whisper_provider.py`
  - Verify `process_audio()` returns a valid `TranscriptionResult`
  - Verify `estimated_cost` calculation at $0.006/min
- [x] T035 [P] [US1] Unit test: `ChirpProvider` implements `TranscriptionProvider`
  Protocol — `backend/tests/unit/test_chirp_provider.py`
  - Mock `SpeechClient` and `GCSStorageService`
  - Verify `process_audio()` returns a valid `TranscriptionResult`
  - Verify response normalization: word timestamps, speaker labels, language
  - Verify `estimated_cost` calculation for dynamic and standard batch
- [x] T036 [P] [US5] Unit test: `CircuitBreaker` —
  `backend/tests/unit/test_circuit_breaker.py`
  - Verify state transitions: CLOSED → OPEN after threshold failures
  - Verify cooldown: OPEN → CLOSED after cooldown expires
  - Verify `record_success()` resets counter
  - Verify thread safety under concurrent access
- [x] T037 [P] [US1] [US2] Unit test: `TranscriptionProviderFactory` —
  `backend/tests/unit/test_provider_factory.py`
  - Verify returns `WhisperProvider` when `TRANSCRIPTION_PROVIDER=whisper`
  - Verify returns `ChirpProvider` when `TRANSCRIPTION_PROVIDER=chirp`
  - Verify tier-based routing: FREE → dynamic batch, PRO → standard batch
  - Verify circuit breaker override returns Whisper when breaker is OPEN
- [x] T038 [US1] Integration test: full pipeline with Chirp —
  `backend/tests/integration/test_chirp_pipeline.py`
  - Upload a sample audio file → trigger `process_meeting` Celery task
  - Verify `TranscriptSegment` records are created with speaker labels
    and word timestamps
  - Verify `Meeting.transcript_text` is populated
  - Verify cost log entry is emitted
  - Can use a short (<30s) sample audio file for CI speed
- [x] T039 [US5] Integration test: circuit breaker fallback —
  `backend/tests/integration/test_circuit_breaker_fallback.py`
  - Mock `ChirpProvider` to raise 5 consecutive exceptions
  - Verify 6th request routes to `WhisperProvider`
  - Advance time past cooldown, verify next request retries Chirp

**Checkpoint**: All unit and integration tests pass. CI pipeline green.

---

## Phase 9: Feature Flag and Phased Rollout Config (Priority #9)

**Purpose**: Enable gradual migration from Whisper to Chirp via configuration,
without code deploys.

- [x] T040 [P] [US5] Document feature flag usage in
  `specs/013-whisper-chirp-migration/quickstart.md`:
  - `TRANSCRIPTION_PROVIDER=whisper` (default — no change, safe)
  - `TRANSCRIPTION_PROVIDER=chirp` (activate Chirp 3)
  - Rollback: set back to `whisper` and restart
  - Document circuit breaker env vars and their defaults
- [x] T041 [US5] Add provider health check endpoint at
  `backend/app/api/v1/endpoints/health.py` (new or extend existing):
  - `GET /api/v1/health/transcription`:
    returns `{ provider: str, circuit_breaker_state: str,
    consecutive_failures: int, fallback_active: bool }`
  - Protected by admin auth or internal-only access
- [x] T042 [US1] Update `CLAUDE.md` with new technologies and configuration:
  - Add `google-cloud-speech`, `google-cloud-storage` to Active Technologies
  - Add GCS config env vars to Commands section
  - Document the provider abstraction pattern in Code Style section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Abstraction)**: Depends on Phase 1 (T003 directory structure)
  — BLOCKS all subsequent phases
- **Phase 3 (GCS Upload)**: Depends on Phase 1 (T001 dependencies, T002 config)
  — can run in parallel with Phase 2 after T001/T002
- **Phase 4 (ChirpProvider)**: Depends on Phase 2 (interface) + Phase 3 (GCS)
- **Phase 5 (Tier Routing)**: Depends on Phase 4
- **Phase 6 (Cost Logging)**: Depends on Phase 2 (TranscriptionResult type);
  can run in parallel with Phases 4-5
- **Phase 7 (Circuit Breaker)**: Depends on Phase 2 (factory); can run in
  parallel with Phases 4-5
- **Phase 8 (Tests)**: Depends on Phases 2-7 being complete
- **Phase 9 (Rollout)**: Depends on Phase 7 (circuit breaker); can run in
  parallel with Phase 8

### Parallel Opportunities

```text
After Phase 1 completes:
├── Phase 2 (Abstraction)     ─────────────────┐
└── Phase 3 (GCS Upload)      ────────┐        │
                                      ▼        ▼
                               Phase 4 (Chirp) ─────────┐
                                      │                  │
                                      ▼                  │
                               Phase 5 (Routing)         │
                                                         │
After Phase 2 completes:                                 │
├── Phase 6 (Cost Logging)    ◄──────────────────────────┘
└── Phase 7 (Circuit Breaker) ◄──────────────────────────┘

After Phases 2-7 complete:
├── Phase 8 (Tests)
└── Phase 9 (Rollout)         (parallel with Phase 8)
```

### Within Each Phase

- Models/types before services
- Services before consumers (worker, CLI, endpoints)
- Core implementation before integration
- Config before implementation

---

## Implementation Strategy

### MVP First (Phases 1-4)

1. Complete Phase 1: Setup (dependencies + config)
2. Complete Phase 2: Provider Abstraction (structural refactor, zero behavior change)
3. Complete Phase 3: GCS Upload Pipeline
4. Complete Phase 4: ChirpProvider + Response Normalization
5. **STOP and VALIDATE**: Set `TRANSCRIPTION_PROVIDER=chirp`, transcribe a sample
   file, verify output matches Whisper format

### Incremental Delivery

5. Add Phase 5: Tier Routing → verify FREE vs PRO cost logs differ
6. Add Phase 6: Cost Logging → verify JSON log lines in stdout
7. Add Phase 7: Circuit Breaker → verify fallback after simulated failures
8. Add Phase 8: Tests → CI green
9. Add Phase 9: Rollout docs + health endpoint

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- `TRANSCRIPTION_PROVIDER=whisper` remains the default throughout — no risk to
  production until explicitly switched
- The `WhisperProvider` is never deleted — it remains as the permanent fallback
  behind the same `TranscriptionProvider` interface (Constitution Principle XI)
- All external API access goes through abstract interfaces (Constitution Principle IX)
- Default to batch/async processing (Constitution Principle X); streaming is out of
  scope for this migration and will be specified as a separate feature
- Tier mapping: `FREE` → Starter (dynamic batch), `PRO` → Pro (standard batch)
