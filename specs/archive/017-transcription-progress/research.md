# Research: 017 — Transcription Progress Tracking

**Date**: 2026-03-03
**Feature**: [spec.md](spec.md)

## Research Topics

### 1. Event-Driven Pipeline Architecture with Celery

**Decision**: Decompose the monolithic `process_meeting` Celery task into discrete stage tasks, chained via Celery canvas primitives (`chain`, `link`, `link_error`). Each stage task fires a status event before starting and after completing, then triggers the next stage.

**Rationale**:
- The user explicitly requested an event-driven architecture where each stage is a separate task triggered by events
- Celery's built-in canvas primitives (`chain`, `signature.apply_async(link=...)`) provide exactly this: each task completes → triggers the next task in the chain
- This gives per-stage visibility in Celery's task monitor (Flower), individual retry capability, and clean separation of concerns
- Each task opens its own DB session (no long-lived session across the entire pipeline)
- Tasks can be manually re-triggered if stuck at any stage

**Alternatives considered**:
- **Redis Pub/Sub custom event bus**: Rejected — reinvents what Celery canvas already provides; adds complexity without Celery's built-in retry, monitoring, and result tracking
- **Celery Signals (`task_prerun`, `task_postrun`)**: Considered as a complement — useful for logging/notification but not for controlling pipeline flow; signals are fire-and-forget and cannot chain tasks
- **WebSockets / SSE for real-time push**: Deferred — polling is sufficient for this iteration per spec assumptions; adding SSE would require a new endpoint, connection management, and frontend EventSource handling — too much scope

### 2. Pipeline Stage Decomposition

**Decision**: Split into 5 Celery tasks matching the user-visible stages, plus entry/exit orchestration:

| Task Name | Responsibility | Triggers |
| --- | --- | --- |
| `stage_download` | Download audio from MinIO, validate, extract audio track | Chained from `initiate_processing` |
| `stage_transcribe` | Run transcription provider (Whisper or Chirp) | Chained from `stage_download` |
| `stage_align` | Run word-level alignment (Whisper only; no-op for Chirp) | Chained from `stage_transcribe` |
| `stage_diarize` | Run speaker diarization + parse segments into DB | Chained from `stage_align` |
| `stage_summarize` | Run AI agent summarization + finalize | Chained from `stage_diarize` |

Each task receives `meeting_id` and returns `meeting_id` (pass-through for chain compatibility). Each task updates `meeting.sub_status` at entry and `meeting.status` on completion/failure.

**Rationale**:
- Maps 1:1 to the 5 user-visible stages in the spec (Uploaded → Transcribing → Aligning → Diarizing → Done)
- The download stage absorbs the internal validating/extracting substages since they are fast and always sequential
- The summarize stage absorbs cleaning_up since it is a quick tail operation
- Each task is independently retryable and debuggable

**Alternatives considered**:
- **One task per internal sub-stage (12+ tasks)**: Rejected — too granular; many sub-stages take <1 second; the overhead of Celery task dispatch (Redis round-trip) would add latency without user value
- **Keep monolithic task + just expose sub_status**: Rejected — user explicitly requested event-driven architecture with separate tasks for traceability and debuggability

### 3. Provider Pipeline Adaptation

**Decision**: The existing `TranscriptionProvider.process_audio()` method bundles transcribe + align + diarize into one call. Rather than refactoring the provider protocol (which would break the Chirp provider's BatchRecognize flow), we will:

1. **For WhisperProvider**: Keep `process_audio()` but use the existing `on_status_change` callback to emit fine-grained sub-status updates. The `stage_transcribe` task calls the provider and the callback updates `meeting.sub_status` as transcribing → aligning → diarizing within the provider.
2. **For ChirpProvider**: Same approach — the provider internally handles all its stages and fires callbacks.
3. The separate `stage_align` and `stage_diarize` Celery tasks become **pass-through/status-update** tasks when the provider handles alignment and diarization internally. They serve as status checkpoints rather than performing the actual work.

**Updated approach**: Actually, since the providers bundle transcribe+align+diarize, the cleanest split is:

| Task Name | What it does |
| --- | --- |
| `stage_download` | Download from MinIO, validate duration, extract audio if video |
| `stage_transcribe` | Runs the FULL provider pipeline (transcribe + align + diarize), saves segments. The `on_status_change` callback updates `sub_status` for granular tracking |
| `stage_summarize` | Runs AI agent for summary + action items, marks complete |

The user-visible progress indicator still shows 5 stages (Uploaded, Transcribing, Aligning, Diarizing, Done) based on the `sub_status` value, even though Celery has 3 tasks. This decouples the user-facing stages from the task boundaries.

**Rationale**: Splitting the provider pipeline across Celery tasks would require passing large intermediate data (transcription results, alignment data) between tasks via Redis — expensive and fragile. The provider protocol is designed as a single `process_audio()` call that handles cleanup internally. The `on_status_change` callback already gives us granular sub-status updates within the task.

### 4. Status Event Emission Pattern

**Decision**: Use a `emit_stage_event(meeting_id, sub_status, message)` helper function that:
1. Updates `meeting.sub_status` in PostgreSQL (existing pattern)
2. Publishes to a Redis Pub/Sub channel `meeting:{meeting_id}:status` (new — enables future SSE/WebSocket push)
3. Returns immediately (non-blocking)

For this iteration, the Redis Pub/Sub publish is fire-and-forget with no subscribers — it lays the groundwork for future SSE without adding complexity now. The frontend continues to poll.

**Rationale**: Dual-write (DB + Redis Pub/Sub) is cheap (one extra Redis command per stage transition, ~0.1ms). It separates the "state persistence" concern (PostgreSQL) from the "event notification" concern (Redis Pub/Sub), enabling future real-time push without modifying the pipeline tasks.

**Alternatives considered**:
- **PostgreSQL LISTEN/NOTIFY**: Rejected — requires persistent DB connection in the API process; doesn't integrate naturally with the existing Redis infrastructure
- **Celery task state updates (`self.update_state()`)**: Rejected — Celery's custom state is stored in the result backend and requires polling the result backend, which is less natural than polling the meetings API

### 5. Frontend Polling Strategy

**Decision**: Add polling to the meetings list page and the upload modal for in-progress meetings:

- **Meetings list / home feed**: Poll `GET /meetings/?skip=0&limit=20` every 5 seconds while any meeting in the list has `status` in `["pending_upload", "queued", "processing"]`. Stop polling when no meetings are active.
- **Upload modal**: After upload success, poll `GET /meetings/{id}` every 3 seconds for that specific meeting until it reaches `completed` or `failed`.
- **Meeting detail page**: Keep existing polling logic (3s → 10s adaptive), but display `sub_status` instead of generic "Processing…"

**Rationale**: Polling the list endpoint is simple and keeps the UI consistent. The 5-second interval balances responsiveness with server load. Per-meeting polling in the upload modal gives faster feedback for the active upload session.

**Alternatives considered**:
- **SSE (Server-Sent Events)**: Better UX (instant updates) but requires new infrastructure (SSE endpoint, connection management, reconnection logic). Deferred to a future iteration.
- **Polling individual meetings**: More efficient per-request but requires tracking which meetings are active and making N requests. The list endpoint is already optimized and returns all meetings in one call.

### 6. `sub_status` Exposure in API Response

**Decision**: Add `sub_status: Optional[str]` to the `MeetingRead` response schema. No new endpoint needed — the existing `GET /meetings/` and `GET /meetings/{id}` endpoints will return `sub_status` alongside `status`.

**Rationale**: Minimal backend change (one field added to the Pydantic response model). The frontend maps `sub_status` to user-visible stage labels client-side, keeping the backend stage names internal.

### 7. `summary_text` Dual-Purpose Abuse

**Decision**: Stop using `summary_text` for progress messages. The `sub_status` field becomes the sole source of processing stage information. During processing, `summary_text` remains `None` until the summarization stage writes the actual summary.

**Rationale**: The current pattern of writing `[System: Transcribing Audio]` into `summary_text` and then overwriting it with the real summary is fragile and confusing. With `sub_status` exposed, there is no need for this workaround. The frontend will read `sub_status` for stage display and `summary_text` only for the actual meeting summary.
