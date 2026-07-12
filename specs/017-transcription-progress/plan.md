# Implementation Plan: Transcription Progress Tracking

**Branch**: `017-transcription-progress` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-transcription-progress/spec.md`

## Summary

Users currently see a green checkmark when a file upload completes, then a generic "Processing…" label on the meetings list — with no visibility into which stage of the transcription pipeline their meeting is in. This feature exposes the backend's existing `sub_status` field to the frontend API, decomposes the monolithic Celery worker into a chain of discrete stage tasks (event-driven), and builds frontend UI to display a stepped progress indicator showing the current processing stage in both the upload modal and meetings list.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5 / Node.js 20 (frontend)
**Primary Dependencies**: FastAPI, Celery (canvas: chain, link_error), SQLModel, Redis; Next.js 16, React 19, Axios
**Storage**: PostgreSQL (via SQLModel), Redis (Celery broker + Pub/Sub), MinIO (S3-compatible)
**Testing**: Playwright/Python for E2E (per constitution); pytest for backend unit tests
**Target Platform**: Linux server (Docker), Web browser (frontend)
**Project Type**: Web application (full-stack)
**Performance Goals**: Stage updates visible to user within 10 seconds of backend transition
**Constraints**: Polling-based (no WebSocket/SSE this iteration); no new dependencies
**Scale/Scope**: Single-user concurrent processing; affects ~8 backend files, ~8 frontend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
| --- | --- | --- | --- |
| Design System | Yes | PASS | New progress indicator component will use `indigo-600` accent, `rounded-lg`, 4px grid, borders only (no shadows). Will document new pattern in system.md. |
| API Contract | Yes | PASS | Contract documented in [contracts/meetings-api.md](contracts/meetings-api.md). Only change: add `sub_status` to `MeetingRead`. |
| Auth/Security | Yes | PASS | All endpoints remain JWT-protected. No new auth flows. |
| Env Config | No | N/A | No new environment variables. |
| Scope Boundary | Yes | PASS | Implementation stays within spec scope: expose sub_status, add polling, build progress UI. No undocumented additions. |
| E2E Testing | Yes | PASS | E2E test planned: `tests/e2e/test_transcription_progress.py` covering upload → stage visibility → completion. |
| Repository Pattern | Yes | PASS | Stage tasks use `MeetingService` for all DB operations. The worker's inline `update_status` closure will be replaced with service method calls. |
| CLI/Typer | No | N/A | No CLI changes. |
| Provider Abstraction | No | N/A | No new providers. Existing `TranscriptionProvider` protocol unchanged. |
| Cost Awareness | No | N/A | No new external API calls. Existing batch processing unchanged. |
| Migration Safety | No | N/A | No provider migration. |

## Project Structure

### Documentation (this feature)

```text
specs/017-transcription-progress/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── meetings-api.md  # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py                          # Add sub_status to MeetingRead
│   ├── worker.py                          # Decompose into stage tasks + chain
│   ├── services/
│   │   └── meeting.py                     # Add update_sub_status() method
│   └── api/v1/endpoints/
│       └── meetings.py                    # No changes (schema change auto-propagates)

frontend-2/
├── app/
│   ├── lib/
│   │   ├── api.ts                         # Add sub_status to Meeting interface
│   │   └── stage-utils.ts                 # NEW: getUserStage() mapping + stage labels
│   ├── components/
│   │   ├── upload-modal.tsx               # Add post-upload polling + stage display
│   │   ├── meeting-feed.tsx               # Add polling for active meetings + stage labels
│   │   ├── meeting-card.tsx               # Show stage label instead of generic "Processing…"
│   │   └── ui/
│   │       ├── status-badge.tsx           # Update to show sub-stage labels
│   │       └── progress-steps.tsx         # NEW: Stepped progress indicator component
│   └── (dashboard)/
│       └── meetings/
│           ├── page.tsx                   # Add polling for active meetings
│           └── [id]/page.tsx              # Show sub-stage in detail view

tests/
└── e2e/
    └── test_transcription_progress.py     # NEW: E2E test
```

**Structure Decision**: Web application (Option 2). The existing `backend/` and `frontend-2/` structure is preserved. Changes are modifications to existing files plus 2 new frontend utility/component files and 1 new E2E test.

## Implementation Approach

### Backend: Event-Driven Pipeline Decomposition

The monolithic `process_meeting` Celery task is decomposed into 3 chained tasks:

```
initiate_processing()
    → stage_download.s(meeting_id)
    | stage_transcribe.s()
    | stage_summarize.s()
    (linked via Celery chain)
    (each has link_error → on_stage_failure)
```

**Task details**:

1. **`stage_download(meeting_id) → meeting_id`**
   - Sets `sub_status = "downloading"` at entry
   - Downloads audio from MinIO presigned URL
   - Validates duration, extracts audio from video if needed
   - Sets `sub_status` through `validating`, `extracting_audio`
   - Returns `meeting_id`

2. **`stage_transcribe(meeting_id) → meeting_id`**
   - Sets `sub_status = "transcribing"` at entry
   - Calls `provider.process_audio()` with `on_status_change` callback
   - Callback updates `sub_status` as provider progresses (transcribing → aligning → diarizing)
   - Saves transcript segments to DB
   - Updates user minutes usage
   - Returns `meeting_id`

3. **`stage_summarize(meeting_id) → meeting_id`**
   - Sets `sub_status = "summarizing"` at entry
   - Runs AI agent for summary + action items
   - Sets `status = "completed"`, clears `sub_status`
   - Writes final `summary_text` and `action_items_text`

4. **`on_stage_failure(request, exc, traceback)`** (error callback)
   - Sets `meeting.status = "failed"`
   - Sets `meeting.summary_text = f"[Error: {str(exc)}]"`
   - Linked to each task via `link_error`

**Event emission**: Each task calls `meeting_service.update_sub_status(meeting_id, sub_status)` which:
1. Updates PostgreSQL (existing pattern)
2. Publishes to Redis Pub/Sub `meeting:{meeting_id}:status` (fire-and-forget, for future SSE)

### Backend: API Schema Change

Single change to `MeetingRead` in `models.py`:
```python
class MeetingRead(MeetingBase):
    # ... existing fields ...
    sub_status: Optional[str] = None  # NEW
```

The `sub_status` field is already on the `Meeting` table model — adding it to the response schema is all that's needed.

### Frontend: Stage Utilities

New `stage-utils.ts` module:
- `getUserStage(meeting)` — maps `status` + `sub_status` → `UserStage` enum
- `STAGE_ORDER` — array defining the visual order: `["uploaded", "transcribing", "aligning", "diarizing", "done"]`
- `STAGE_LABELS` — display labels: `{ uploaded: "Uploaded", transcribing: "Transcribing…", ... }`
- `getStageIndex(stage)` — returns position in the pipeline for progress indicator

### Frontend: Progress Steps Component

New `progress-steps.tsx` component showing a horizontal stepped progress indicator:
- 5 steps: Uploaded → Transcribing → Aligning → Diarizing → Done
- Each step: circle indicator + label
- States: completed (indigo-600 fill), active (indigo-600 ring + pulse), pending (stone-200)
- Connecting lines between steps: completed (indigo-600), pending (stone-200)
- Design system compliant: `rounded-full` for circles, 4px grid spacing, no shadows

### Frontend: Polling

- **Upload modal**: After `status: "success"`, stores the `meeting_id` and starts polling `getMeeting(id)` every 3 seconds. Shows `ProgressSteps` below the upload item. Stops on `completed` or `failed`.
- **Meetings list + home feed**: `useEffect` checks if any meeting has active status → starts polling `getMeetings()` every 5 seconds. Stops when no active meetings remain.
- **Meeting detail**: Existing polling enhanced to read `sub_status` and show `ProgressSteps`.

### Frontend: Status Badge Update

`StatusBadge` component updated:
- When `status === "processing"` and `sub_status` is available: show the specific stage label (e.g., "Transcribing…") with amber styling
- When `status === "processing"` and `sub_status` is null: fall back to "Processing…"

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| (none) | — | — |
