# Quickstart: Unified Processing Queue

## Prerequisites

- Node.js 20+
- Frontend dev server running: `cd frontend-2 && npm run dev`
- Backend API running at `http://localhost:8000` (or configured via `NEXT_PUBLIC_API_URL`)
- No new environment variables required

## Testing the Feature

### Manual Testing

1. **File Upload → Queue**:
   - Click "Import" button on the dashboard
   - Select an audio file in the upload dialog
   - Watch the upload progress in the dialog (byte progress)
   - After upload completes, close the dialog
   - Verify a processing queue panel appears at the bottom-right
   - Verify it shows the file name and current worker stage
   - Wait for processing to complete — item should show "Done"
   - Click the completed item — should navigate to the meeting detail page

2. **YouTube URL → Queue**:
   - Click "Paste URL" button on the dashboard
   - Paste a valid YouTube URL and click "Process"
   - Dialog closes after submission
   - Verify a processing queue panel appears at the bottom-right
   - Verify it shows the video title/URL and current worker stage
   - Wait for processing to complete

3. **Queue Management**:
   - Submit multiple items (mix of uploads and YouTube URLs)
   - Verify each item tracks independently in the queue
   - Click the collapse button — queue should minimize to a compact pill
   - Click expand — queue should show full item list
   - After all items complete, wait 10 seconds — queue should auto-hide

4. **Import Dialog Verification**:
   - Upload a file and keep the import dialog open
   - After upload completes, verify NO worker stage indicators appear in the dialog
   - The dialog should show "success" for the upload, nothing more

### E2E Tests

```bash
pytest tests/e2e/test_processing_queue.py -v
```

## Architecture Overview

```
Dashboard Page
├── ProcessingQueueProvider (context)
│   ├── ActionBar → opens dialogs
│   ├── MeetingFeed
│   ├── UploadModal → addItem() on upload success
│   ├── YouTubeUrlDialog → addItem() on submission success
│   └── ProcessingQueue (floating panel)
│       └── ProcessingQueueItem (per item)
│           └── ProgressSteps (reused)
```

State flows:
- Upload modal completes upload → calls `addItem(meetingId, fileName, "upload")`
- YouTube dialog gets API response → calls `addItem(meeting.id, title, "youtube")`
- Context provider polls each processing item every 3s via `getMeeting()`
- `getUserStage()` maps backend status to UI stage
- Queue panel re-renders on stage updates
- Auto-hide timer fires 10s after all items reach terminal state
