# UI Contracts: Unified Processing Queue

## ProcessingQueueContext

### Provider API

```typescript
interface ProcessingQueueContextValue {
  items: QueueItem[];
  isCollapsed: boolean;
  isVisible: boolean;
  addItem: (meetingId: number, displayName: string, sourceType: "upload" | "youtube") => void;
  setCollapsed: (collapsed: boolean) => void;
  clearQueue: () => void;
}
```

**Usage**: Wrap the dashboard page content with `<ProcessingQueueProvider>`. Components call `useProcessingQueue()` to access the context.

**Consumers**:
- `upload-modal.tsx` — calls `addItem(meetingId, fileName, "upload")` after successful upload
- `youtube-url-dialog.tsx` — calls `addItem(meeting.id, meeting.youtube_title || url, "youtube")` after successful submission
- `processing-queue.tsx` — reads `items`, `isCollapsed`, `isVisible` for rendering
- `processing-queue-item.tsx` — reads individual item data

### Polling Contract

The context provider manages all queue polling internally:
- For each item where `status === "processing"`: poll `getMeeting(meetingId)` every 3 seconds
- Map response through `getUserStage()` to update item stage
- Stop polling when stage reaches `"done"` or `"failed"`
- After all items reach terminal state, start 10-second auto-hide timer

## ProcessingQueue Component

### Props

```typescript
interface ProcessingQueueProps {
  // No props — reads entirely from context
}
```

### Rendering Contract

- **Hidden**: When `isVisible === false` OR `items.length === 0`, render nothing
- **Collapsed**: When `isCollapsed === true`, render compact pill showing count of active items and expand button
- **Expanded**: Render full panel with:
  - Header: "Processing" title + collapse button + item count
  - Item list: Scrollable, max-height constrained
  - Each item: ProcessingQueueItem component

### Visual Contract

- Position: `fixed bottom-4 right-4` (viewport-anchored)
- Width: `w-80` (320px)
- Max height: `max-h-96` (384px) with overflow-y-auto for item list
- Z-index: `z-50` (above page content, below modals)
- Surface: `bg-white border border-stone-200 rounded-lg`
- No shadows (design system: borders only)

## ProcessingQueueItem Component

### Props

```typescript
interface ProcessingQueueItemProps {
  item: QueueItem;
}
```

### Rendering Contract

- **Processing state**: Show file/video name, current stage label from `STAGE_LABELS`, ProgressSteps component, pulsing indicator
- **Done state**: Show file/video name, green checkmark, "Done" label, clickable (navigates to `/meetings/{meetingId}`)
- **Failed state**: Show file/video name, red X icon, error message text, non-clickable
- Source indicator: Small upload or YouTube icon next to the display name

## Upload Modal Modifications

### Removed

- `pollTimers` ref and all per-item polling logic (lines ~65–109 of current upload-modal.tsx)
- `processingStage` field from `UploadItem` interface
- `ProgressSteps` rendering after upload success
- `STAGE_LABELS` subtitle display for post-upload stages

### Retained

- File selection, presigned URL upload, byte progress tracking
- Upload cancellation via AbortController
- "Cancel all" functionality
- Upload success/error status display
- Quota footer ("3 of 3 imports left")

### Added

- After successful upload: call `addItem(meetingId, file.name, "upload")` from processing queue context
- Import `useProcessingQueue` hook

## YouTube URL Dialog Modifications

### Retained (no changes except one addition)

- URL input, client-side validation, API submission
- Error handling, loading state
- PostHog analytics events

### Added

- After successful submission: call `addItem(meeting.id, meeting.youtube_title || url, "youtube")` from processing queue context
- Import `useProcessingQueue` hook
