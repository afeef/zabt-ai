# Research: Unified Processing Queue

## R1: React State Management Pattern for Queue

**Decision**: React Context with `useReducer` for queue state management.

**Rationale**: The queue state needs to be shared between the dashboard page, upload modal, YouTube dialog, and the queue panel component. React Context avoids prop drilling while keeping the state local to the dashboard (no global store needed). `useReducer` provides predictable state transitions for queue operations (add item, update stage, remove item, set collapsed).

**Alternatives considered**:
- **Zustand/Jotai**: Overkill for session-only state scoped to one page. Adds a dependency.
- **Lifting state to page.tsx**: Would require passing callbacks through multiple component layers. Context is cleaner.
- **Custom event system**: Already used for `youtube-url-submitted`; works for fire-and-forget signals but poor for shared mutable state that needs reactive rendering.

## R2: Polling Strategy for Queue Items

**Decision**: Per-item polling using `setInterval` at 3-second intervals, managed within the context provider via a `useEffect` hook. Reuses the existing `getMeeting(id)` API and `getUserStage()` mapping.

**Rationale**: The upload modal already uses this exact pattern (per-item 3s polling via `getMeeting`). Moving the polling into the context provider centralizes it. The meeting feed's 5-second full-list polling continues independently (it serves a different purpose: updating the feed list, not tracking individual item stages).

**Alternatives considered**:
- **WebSocket/SSE for real-time updates**: Would require backend changes (out of scope) and adds infrastructure complexity.
- **Single poll for all queue items**: Would require a batch endpoint or fetching all meetings. Per-item polling with `getMeeting(id)` is simpler and already proven.
- **Consolidating feed + queue polling**: The feed polls the full meeting list; the queue polls individual meetings by ID. Different granularity — keeping them separate avoids coupling.

## R3: Queue Panel UI Pattern

**Decision**: Fixed-position floating panel at the bottom-right of the viewport, built with shadcn/ui Card + Collapsible components. Animated expand/collapse.

**Rationale**: Fixed positioning keeps the queue visible regardless of scroll position (FR-012). Bottom-right is the standard position for notification/progress panels (like browser download managers). shadcn/ui Collapsible provides accessible expand/collapse with keyboard support.

**Alternatives considered**:
- **Toast notifications**: Too transient; users need persistent progress visibility.
- **Sidebar panel**: Would compete with the existing sidebar and reduce meeting feed width.
- **Bottom bar (full width)**: Takes too much screen real estate for a small list of items.

## R4: Upload Modal Refactoring Scope

**Decision**: Remove the `pollTimers` mechanism, `processingStage` state tracking, and `ProgressSteps` rendering from upload-modal.tsx. After a successful upload, the modal marks the item as "success" (upload done) and the context provider's `addItem()` is called to hand off to the queue. The modal retains all upload byte progress, cancellation, and file selection logic.

**Rationale**: Clean separation — the modal owns the upload lifecycle, the queue owns the worker lifecycle. The modal's existing `meetingId` from the upload response is what the queue needs to start polling.

**Alternatives considered**:
- **Keep polling in modal AND queue**: Duplicates work and creates potential state conflicts.
- **Remove modal entirely**: Too aggressive — users still need byte-level upload progress and cancellation during the transfer phase.

## R5: Queue Item Lifecycle

**Decision**: Queue items follow this lifecycle: `processing` → `done` | `failed`. Items are added when:
- File upload: After `uploadFile()` succeeds and `meetingId` is available (upload-modal calls `addItem`)
- YouTube: After `submitYoutubeUrl()` succeeds and returns a meeting object (youtube-dialog calls `addItem`)

Items are never removed programmatically — they remain visible until the auto-hide timer fires (10 seconds after all items reach terminal state). On next session, the queue starts empty.

**Rationale**: Simple lifecycle. No intermediate "uploading" state in the queue since uploads stay in the modal. The 10-second persistence after completion lets users see final status and click through to meetings.
