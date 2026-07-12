---
description: "Task list for 007-transcript-viewer — Media Transcription Viewer"
---

# Tasks: Media Transcription Viewer

**Input**: Design documents from `/specs/007-transcript-viewer/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅
**Branch**: `007-transcript-viewer`
**Tech**: TypeScript 5 / Next.js 16 App Router, Python 3.11 / FastAPI, Supabase, Playwright, `react-virtuoso`
**Tests**: Playwright E2E tests are REQUIRED per constitution (Principle VI).

---

## Phase 1: Setup (Data Contracts & Mocking)

**Purpose**: Project initialization, type definitions, and unblocking the UI with mocked data without requiring the full FastAPI backend to be wired.

- [x] T001 Create Playwright E2E test file skeleton `tests/e2e/test_transcript_viewer.py` with standard login and basic navigation shell.
- [x] T002 [P] Define `TranscriptSegment` and `TranscriptWord` TypeScript interfaces in `frontend-2/app/lib/api.ts` based on `contracts/api.md`.
- [x] T003 Expand the existing `Meeting` type in `frontend-2/app/lib/api.ts` to include the `speakers` and `segments` fields.
- [x] T004 Implement a mock meeting JSON payload in `tests/e2e/mocks/transcript_mock.json` containing a 35-minute multi-speaker payload to test virtualization and paywalls.
- [x] T004b [P] Expand `transcript_mock.json` with an unknown speaker chunk (`SPEAKER_UNKNOWN`) to validate fallback UI gracefully.
- [x] T005 Create `frontend-2/app/components/transcript-viewer.tsx` (stub).
- [x] T006 Create `frontend-2/app/components/sticky-media-player.tsx` (stub).
- [x] T007 Create `frontend-2/app/components/paywall-modal.tsx` (stub).

**Checkpoint**: Core files exist, types are strictly defined, and mocked data is ready for the UI.

---

## Phase 2: Foundational (Static UI Implementation)

**Purpose**: Build out the visual components before introducing the complex 60fps synchronization logic.

- [x] T011 Install `react-virtuoso` dependency in `frontend-2`.
- [x] T012 Build `transcript-viewer.tsx` utilizing `Virtuoso` to render the rows. Each row must display the speaker avatar, name, starting timestamp, and text block.
- [x] T012b [P] Add error handling in `transcript-viewer.tsx` to explicitly handle and safely default `TranscriptWord` parsing errors without crashing the `Virtuoso` list.

**Checkpoint**: The transcript UI renders large mocked payloads efficiently without scrolling lag.

---

## Phase 3: User Story 2 — Metadata & Speaker Identification (Priority: P2)

**Goal**: A metadata header and a "Speakers" section showing talk time percentages.

### Implementation

- [x] T008 [US2] Update `frontend-2/app/meetings/[id]/page.tsx` to include "Summary" and "Transcript" tab navigation.
- [x] T009 [P] [US2] Implement the metadata header in `page.tsx` displaying Participants, Duration, and Keywords.
- [x] T010 [P] [US2] Implement the "Speakers" breakdown UI section, rendering the talk-time percentages from the payload.

---

## Phase 4: User Story 1 — Transcript Navigation & Playback (Priority: P1)

**Goal**: A persistent media player with a vertical transcript log that highlights current playback position and allows seeking by clicking timestamps.

### E2E Test

- [x] T013 [US1] Write E2E test `test_transcript_sync_flow` in `test_transcript_viewer.py` — Load mock meeting, assert the player exists, click a timestamp in the transcript, assert the audio `currentTime` changes, and assert the correct word receives the highlight class.

### Implementation

- [x] T014 [US1] Build `sticky-media-player.tsx` interfacing with an HTML5 `<audio>` ref. Expose play/pause, 10-second rewind, and playback rate buttons.
- [x] T015 [US1] Implement a segmented CSS/SVG progress bar in `sticky-media-player.tsx` that maps speaker `['SPEAKER_00', 'SPEAKER_01']` arrays to mapped color blocks on the timeline.
- [x] T016 [US1] Implement the core synchronization engine (Zustand store or React Context): Use `requestAnimationFrame` attached to the audio `timeupdate` to precisely track `currentTime` and compute the `activeWordIndex`.
- [x] T017 [US1] Apply the active highlight CSS class to the specific `TranscriptWord` span inside `transcript-viewer.tsx` matching the `activeWordIndex`.
- [x] T018 [US1] Bind `onClick` on transcript timestamps to trigger an imperative `seekTo(time)` function on the media player.

**Checkpoint**: The player syncs highlights flawlessly at 60fps and bi-directional seeking works.

---

## Phase 5: User Story 3 — Paywall for Long Media (Priority: P3)

**Goal**: Block free-tier users with a blurred overlay modal if the media exceeds 30 minutes.

### E2E Test

- [x] T019 [P] [US3] Write E2E test `test_30_min_paywall` in `test_transcript_viewer.py` — Load the 35-minute mock payload, attempt to scroll past 30 minutes, and assert the overlay modal appears and prevents further reading.

### Implementation

- [x] T020 [US3] Build `paywall-modal.tsx` as an absolute positioned overlay containing a lock icon, descriptive text, and an "Upgrade" button.
- [x] T021 [US3] Integrate the paywall logic into `transcript-viewer.tsx` — if `user.tier === 'free'` and the rendered segment extends past 1800 seconds, apply `blur-sm` to those elements and render the `<PaywallModal />` over them, explicitly disabling scroll on the `Virtuoso` list.

---

## Final Phase: Polish & Validation

**Purpose**: Edge case handling and compliance.

- [x] T022 Handle edge case in `transcript-viewer.tsx` — Render fallback UI generic avatars for `SPEAKER_UNKNOWN` strings gracefully (validated via mock from T004b).
- [x] T023 Run `/interface-design:audit` — Ensure the sticky media player and tabs comply with `.interface-design/system.md` (e.g., `rounded-lg`, `bg-white`, `border-stone-200`).
- [x] T024 Execute full E2E test locally (`pytest tests/e2e/test_transcript_viewer.py` using Chromium) with mocked interceptions to confirm the UI interactions pass.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Begins immediately.
- **Phase 2 (Static UI)**: Requires Phase 1 mocks and component stubs.
- **Phase 3 (US2)**: Can run concurrently with Phase 2/4.
- **Phase 4 (US1)**: Must have the static UI (Phase 2) to attach refs and state to.
- **Phase 5 (US3)**: Attaches to Phase 4.
- **Polish (Final)**: Validates the completed feature.

### Parallel Opportunities
Tasks marked with `[P]` can be executed simultaneously:
- T002 (Data Models) and T004 (Mock Data) can run in parallel with UI setup.
- T009 (Metadata UI) and T010 (Speaker Summary UI) can be implemented independently of the main List virtualization (T011/T012).
