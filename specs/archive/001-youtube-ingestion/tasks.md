# Tasks: YouTube URL Ingestion

**Input**: Design documents from `/specs/001-youtube-ingestion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/youtube-ingest.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Docker, dependencies, and database schema changes shared across all stories

- [X] T001 Add `yt-dlp` to worker dependencies in backend/Dockerfile (worker target stage only, not API stage). Verify ffmpeg is already available in worker image.
- [X] T002 Add 6 new fields to Meeting model in backend/app/models.py: `source_type` (str, default "upload"), `source_url` (Optional[str]), `youtube_title` (Optional[str]), `youtube_duration_seconds` (Optional[int]), `youtube_thumbnail_url` (Optional[str]), `youtube_channel` (Optional[str]). Also add these fields to `MeetingBase` or `MeetingRead` response schema so they appear in API responses.
- [X] T003 Generate Alembic migration for the 6 new Meeting fields: `alembic revision --autogenerate -m "add_youtube_source_fields"` in backend/alembic/versions/. Verify both upgrade() and downgrade() functions are correct per data-model.md.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service + worker task that all stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create backend/app/services/youtube.py with YouTube utility functions: (1) `validate_youtube_url(url: str) -> bool` — regex validation for known YouTube URL formats (watch, youtu.be, live, shorts, embed); (2) `is_playlist_url(url: str) -> bool` — detect playlist URLs; (3) `extract_metadata(url: str) -> dict` — run `yt-dlp --dump-json --no-download` via subprocess, return title, duration, thumbnail, channel; (4) `download_audio(url: str, output_path: str) -> str` — run `yt-dlp -x --audio-format mp3 --audio-quality 0` via subprocess, return path to downloaded file. Handle subprocess errors with descriptive exceptions.
- [X] T005 Add `create_from_youtube(url: str, owner_id: int) -> Meeting` method to MeetingService in backend/app/services/meeting.py. Creates meeting with `source_type="youtube"`, `source_url=url`, `title="YouTube Video"`, `status="queued"`. Also add `count_active_youtube(owner_id: int) -> int` that counts meetings where `source_type="youtube"` and `status in ("queued", "processing")` for concurrency limiting.
- [X] T006 Add `stage_youtube_download` Celery task to backend/app/worker.py. This task: (1) sets sub_status to "downloading_youtube"; (2) calls `extract_metadata()` to get video info; (3) validates duration <= 14400s (4 hours), fails meeting if exceeded; (4) updates meeting title to youtube_title, sets youtube_* metadata fields; (5) calls `download_audio()` to download MP3 to /media/tmp/; (6) uploads audio to object storage using `storage.upload_file()`; (7) sets meeting.file_path to the storage key; (8) returns meeting_id for the next stage in the chain. Handle all yt-dlp failure modes: video unavailable, age-restricted, geo-blocked, no audio, live stream in progress.
- [X] T007 Add `dispatch_youtube_pipeline(meeting_id: int)` function to backend/app/worker.py. Builds Celery chain: `stage_youtube_download.s(meeting_id) | stage_transcribe.s() | stage_summarize.s()` with `link_error=[on_stage_failure.s()]` on each stage. This reuses the existing stage_transcribe and stage_summarize tasks unchanged.

**Checkpoint**: Backend YouTube processing pipeline ready — can process a meeting from URL to transcription+summary

---

## Phase 3: User Story 1 — Paste YouTube URL to Create Meeting (Priority: P1) 🎯 MVP

**Goal**: User clicks "Paste URL", enters a YouTube URL, meeting is created and processed end-to-end

**Independent Test**: Paste a valid YouTube URL → meeting card appears → processing completes → transcript + summary available

### Implementation for User Story 1

- [X] T008 [US1] Add `POST /api/v1/meetings/youtube` endpoint to backend/app/api/v1/endpoints/meetings.py. Request body: `{"url": str}`. Validates URL format using `validate_youtube_url()` and `is_playlist_url()` from youtube service. Checks concurrency limit via `count_active_youtube()` (max 3, return 429 if exceeded). Creates meeting via `create_from_youtube()`. Dispatches `dispatch_youtube_pipeline()`. Returns 201 with MeetingRead. Error responses per contracts/youtube-ingest.md.
- [X] T009 [P] [US1] Create frontend-2/app/lib/youtube-utils.ts with client-side URL validation: `isValidYoutubeUrl(url: string): boolean` (regex matching youtube.com/watch, youtu.be, youtube.com/live, youtube.com/shorts, youtube.com/embed, m.youtube.com) and `isPlaylistUrl(url: string): boolean` (detects /playlist?list= patterns).
- [X] T010 [P] [US1] Add `submitYoutubeUrl(url: string): Promise<Meeting>` function to frontend-2/app/lib/api.ts. POST to `/meetings/youtube` with `{url}` body. Returns Meeting object on success. Throws with error detail on 400/429.
- [X] T011 [US1] Create frontend-2/app/components/youtube-url-dialog.tsx. Uses shadcn/ui Dialog with: (1) text Input for URL; (2) "Process" Button; (3) inline error display below input; (4) client-side validation using youtube-utils before API call; (5) on success: closes dialog, calls `onSuccess(meeting)` callback; (6) on API error: displays error message inline; (7) loading state on Process button during API call. Props: `isOpen: boolean, onOpenChange: (open: boolean) => void, onSuccess: (meeting: Meeting) => void`. Track PostHog events: dialog opened, URL submitted.
- [X] T012 [US1] Add "Paste URL" button to frontend-2/app/components/action-bar.tsx next to the Import button. Uses shadcn/ui Button with Link icon from lucide-react. Clicking opens YouTubeUrlDialog. Pass `onSuccess` callback that dispatches `window.dispatchEvent(new Event("youtube-url-submitted"))` to trigger feed refresh.
- [X] T013 [US1] Update frontend-2/app/(dashboard)/page.tsx to: (1) add `isYoutubeDialogOpen` state; (2) pass `onPasteUrlClick` to ActionBar; (3) render YouTubeUrlDialog; (4) listen for `youtube-url-submitted` custom event to refresh meeting feed (same pattern as upload modal).
- [X] T014 [US1] Add YouTube badge/icon to MeetingFeedCard in frontend-2/app/components/meeting-feed.tsx. When `meeting.source_type === "youtube"`, show a small YouTube icon (use `Youtube` from lucide-react) next to the meeting title or in the metadata line. Use `text-primary` for the icon color.
- [X] T015 [US1] Update frontend-2/app/lib/stage-utils.ts to handle the new `downloading_youtube` sub_status. Map it to a UserStage (e.g., map to `"uploaded"` stage or add a new label "Downloading…" if appropriate). Ensure `isActiveMeeting()` correctly identifies YouTube meetings in processing.

**Checkpoint**: Full end-to-end flow works — paste URL → meeting created → YouTube downloaded → transcribed → summarized → visible in feed with YouTube badge

---

## Phase 4: User Story 2 — URL Validation and Error Handling (Priority: P2)

**Goal**: Invalid URLs show instant client-side errors; server-side failures display on meeting card

**Independent Test**: Submit various invalid URLs → see inline errors. Submit unavailable video → see failure on card.

### Implementation for User Story 2

- [X] T016 [US2] Enhance youtube-url-dialog.tsx validation UX in frontend-2/app/components/youtube-url-dialog.tsx: (1) distinguish playlist error message ("Playlist URLs are not supported. Please paste a single video URL.") from generic invalid URL error ("Please enter a valid YouTube video URL"); (2) clear error on input change; (3) disable Process button when input is empty; (4) handle 429 concurrency limit error with specific message.
- [X] T017 [US2] Enhance `stage_youtube_download` error handling in backend/app/worker.py. Map yt-dlp exit codes and stderr patterns to user-facing error messages: "Video unavailable — it may be private, deleted, or restricted", "Video is age-restricted and cannot be processed", "Video exceeds the maximum duration of 4 hours", "No audio track found in video", "Live streams in progress cannot be processed", "Failed to download audio. Please try again." Use `meeting_service.mark_failed(meeting_id, error_message)` for each case.
- [X] T018 [US2] Ensure the meeting detail page (frontend-2/app/(dashboard)/meetings/[id]/page.tsx) displays the failure reason for failed YouTube meetings. The existing `meeting.sub_status` or error field should already surface in the status badge — verify this works and add the error reason text if not already visible for failed meetings.

**Checkpoint**: All validation and error paths work — invalid URLs caught in dialog, server failures shown on card

---

## Phase 5: User Story 3 — Processing Progress and Status (Priority: P3)

**Goal**: YouTube meetings show processing progress consistent with file uploads

**Independent Test**: Submit YouTube URL → observe status transitions from "Queued" → "Downloading…" → "Transcribing…" → "Completed"

### Implementation for User Story 3

- [X] T019 [US3] Add `downloading_youtube` sub_status publishing in backend/app/worker.py `stage_youtube_download` task. Call `meeting_service.update_sub_status(meeting_id, "downloading_youtube")` at the start of the task, so the frontend can show a "Downloading…" stage. Ensure the existing `stage_transcribe` and `stage_summarize` tasks publish their sub_statuses as before.
- [X] T020 [US3] Update frontend-2/app/lib/stage-utils.ts to add `"downloading_youtube"` to the sub_status → UserStage mapping. Add a `STAGE_LABELS` entry for the downloading stage (e.g., `"Downloading…"`). Update `getStageIndex()` if needed to position the downloading stage before transcribing.
- [X] T021 [US3] Verify the existing meeting feed polling in frontend-2/app/components/meeting-feed.tsx correctly picks up YouTube meetings as active (status "queued" or "processing") and polls for updates. The `isActiveMeeting()` check should already work since YouTube meetings use the same status values — confirm this.

**Checkpoint**: Full progress visibility — YouTube meetings show downloading → transcribing → summarizing → completed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Analytics, E2E test, and final verification

- [X] T022 Add PostHog analytics events in frontend-2/app/components/youtube-url-dialog.tsx: `youtube_dialog_opened` (when dialog opens), `youtube_url_submitted` (when Process clicked with valid URL), `youtube_url_error` (when validation fails, with error type property). Also add `youtube_processing_started` and `youtube_processing_completed`/`youtube_processing_failed` events in backend/app/worker.py stage_youtube_download task.
- [X] T023 Write E2E test in tests/e2e/test_youtube_ingestion.py using Playwright/Python. Test the happy path: navigate to home → click Paste URL → enter YouTube URL → click Process → verify meeting card appears with Processing status and YouTube badge. Also test error path: enter invalid URL → verify inline error message.
- [X] T024 Run quickstart.md verification checklist: (1) rebuild worker image with yt-dlp; (2) run alembic upgrade head; (3) test full flow with a real YouTube URL; (4) verify existing file upload still works; (5) verify all error cases from quickstart.md.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (model + migration must exist before service/worker code)
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
  - US1 (Phase 3) can start immediately after Phase 2
  - US2 (Phase 4) builds on US1 — enhances dialog and worker error handling
  - US3 (Phase 5) builds on US1 — adds progress visibility
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 only — delivers full MVP
- **User Story 2 (P2)**: Depends on US1 (enhances dialog from T011 and worker from T006)
- **User Story 3 (P3)**: Depends on US1 (adds progress to existing flow)

### Within Each User Story

- Backend tasks before frontend tasks (API must exist before UI calls it)
- T009+T010 can run in parallel (different files, no dependencies)
- T011 depends on T009+T010 (dialog uses both youtube-utils and api.ts)
- T012 depends on T011 (ActionBar triggers dialog)
- T013 depends on T012 (page.tsx renders ActionBar + dialog)

### Parallel Opportunities

- T009 and T010 can run in parallel (frontend utility + API function, different files)
- T022 can run in parallel with T023 (analytics + E2E test, different files)
- Within Phase 2: T004 and T005 can start in parallel after Phase 1

---

## Parallel Example: User Story 1

```bash
# After Phase 2 is complete, launch parallel frontend tasks:
Task T009: "Create youtube-utils.ts with URL validation"
Task T010: "Add submitYoutubeUrl() to api.ts"

# Then sequential (depends on T009+T010):
Task T011: "Create youtube-url-dialog.tsx"
Task T012: "Add Paste URL button to action-bar.tsx"
Task T013: "Update page.tsx to wire up dialog"
Task T014: "Add YouTube badge to meeting-feed.tsx"
Task T015: "Update stage-utils.ts for downloading_youtube sub_status"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T015)
4. **STOP and VALIDATE**: Test with a real YouTube URL end-to-end
5. Deploy if ready — core feature works

### Incremental Delivery

1. Setup + Foundational → Backend pipeline ready
2. Add User Story 1 → Full end-to-end flow (MVP!)
3. Add User Story 2 → Polished error handling
4. Add User Story 3 → Progress visibility
5. Polish → Analytics + E2E test + verification

---

## Notes

- yt-dlp is installed in worker Docker image only (not API)
- YouTube meetings start at status "queued" (skip "pending_upload")
- New sub_status "downloading_youtube" added for progress tracking
- Existing transcription pipeline (stage_transcribe, stage_summarize) is reused unchanged
- Max 3 concurrent YouTube ingestions per user (soft limit via DB count)
- All UI components use shadcn/ui per constitution
