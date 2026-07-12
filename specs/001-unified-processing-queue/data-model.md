# Data Model: Unified Processing Queue

This feature is frontend-only with session-only state. No database entities or backend changes.

## Frontend State Entities

### QueueItem

Represents a single meeting being processed by the backend worker.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (UUID, generated on creation) |
| meetingId | number | Backend meeting ID, used for polling and navigation |
| displayName | string | File name (uploads) or YouTube video title/URL (YouTube) |
| sourceType | "upload" \| "youtube" | Distinguishes the ingestion source |
| stage | UserStage | Current worker pipeline stage from `getUserStage()` |
| status | "processing" \| "done" \| "failed" | Terminal state indicator |
| errorMessage | string \| null | Failure reason from backend (when status = "failed") |
| addedAt | number | Timestamp (Date.now()) when item was added to queue |

### QueueState

Top-level state for the processing queue context.

| Field | Type | Description |
|-------|------|-------------|
| items | QueueItem[] | All queue items (active + completed) for this session |
| isCollapsed | boolean | Whether the queue panel is minimized |
| isVisible | boolean | Whether the queue panel is shown (auto-hides after completion) |

### State Transitions

```
QueueItem lifecycle:
  [addItem] → status: "processing", stage: "uploaded"
     ↓ (polling)
  stage updates: "transcribing" → "aligning" → "diarizing" → "summarizing"
     ↓
  status: "done", stage: "done"
     OR
  status: "failed", stage: "failed", errorMessage: <detail>

QueueState visibility:
  [addItem] → isVisible: true (auto-show when first item added)
  [all items terminal] → start 10s timer
  [10s elapsed] → isVisible: false
  [new addItem during timer] → cancel timer, isVisible: true
  [user collapse] → isCollapsed: true (panel stays visible but minimized)
  [user expand] → isCollapsed: false
```

### Context Actions (Reducer)

| Action | Payload | Effect |
|--------|---------|--------|
| ADD_ITEM | { meetingId, displayName, sourceType } | Creates QueueItem, sets isVisible: true |
| UPDATE_STAGE | { meetingId, stage, status?, errorMessage? } | Updates item's stage/status |
| SET_COLLAPSED | { collapsed: boolean } | Toggles isCollapsed |
| SET_VISIBLE | { visible: boolean } | Controls auto-hide |
| CLEAR | — | Removes all items (used on explicit dismiss) |
