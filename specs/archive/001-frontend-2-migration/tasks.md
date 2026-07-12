# Tasks: Frontend-2 Migration

**Input**: Design documents from `/specs/001-frontend-2-migration/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/frontend-api.md ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize `frontend-2` as a runnable Next.js project with all required config files.

- [x] T001 Scaffold `frontend-2/` with project config files: copy `package.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`, `eslint.config.mjs`, `next-env.d.ts`, and `Dockerfile` from `frontend/` into `frontend-2/`
- [x] T002 Run `npm install` inside `frontend-2/` to generate `node_modules` and `package-lock.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared infrastructure that all user stories depend on — app shell, API client, base components, infrastructure config.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 [P] Create `frontend-2/app/globals.css` with Tailwind v4 base directives (`@import "tailwindcss"`) and root CSS variables matching `frontend/app/globals.css`
- [x] T004 [P] Create `frontend-2/app/layout.tsx` as the root HTML layout with Geist font setup, `<html lang="en">`, `<body>` with antialiasing, and app-level metadata (title: "Meetily", description: "AI Meeting Notes")
- [x] T005 [P] Create `frontend-2/app/lib/api.ts` with: Axios base client reading `NEXT_PUBLIC_API_URL` env var (default `http://localhost:8000/api/v1`); auth token helpers `getToken()` / `setToken()` / `clearToken()` using `localStorage`; Axios request interceptor attaching `Authorization: Bearer {token}` header; TypeScript types `Meeting`, `MeetingList`, `User`, `AuthToken`
- [x] T006 [P] Create `frontend-2/app/components/ui/button.tsx` reusable button with `variant` prop (primary/secondary/danger) and `disabled`/`loading` states
- [x] T007 Update `docker-compose.yml` web service: change `context: ./frontend` to `context: ./frontend-2` and confirm `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` is in the `environment` section
- [x] T008 [P] Update `backend/app/main.py` CORS middleware: replace `allow_origins=["*"]` with `allow_origins=["http://localhost:3000"]`

**Checkpoint**: Run `docker-compose up --build web` and confirm the container builds without errors. App does not need to render pages yet.

---

## Phase 3: User Story 1 — Application Runs from frontend-2 (Priority: P1) 🎯 MVP

**Goal**: The application loads in the browser from `frontend-2`, users can register and log in, and the backend connection is verified with no CORS errors.

**Independent Test**: Navigate to `http://localhost:3000` — the app loads. Register a new account at `/register`, log in at `/login`, and be redirected to the home page. Browser network tab shows zero CORS errors.

### Implementation for User Story 1

- [x] T009 [US1] Add `login(email, password)` (calls `POST /login/access-token`) and `register(email, password)` (calls `POST /users/`) functions to `frontend-2/app/lib/api.ts`; on login success call `setToken(access_token)`
- [x] T010 [P] [US1] Create `frontend-2/app/login/page.tsx` with email + password form fields, submit button, error message display on 400 response, and redirect to `/` on success (depends on T009)
- [x] T011 [P] [US1] Create `frontend-2/app/register/page.tsx` with email + password form fields, submit button, error message on duplicate email, and redirect to `/login` on success (depends on T009)
- [x] T012 [US1] Create `frontend-2/app/page.tsx` as the home page: display the app title "Meetily — AI Meeting Notes", a brief description, and placeholder sections for "Upload Meeting" and "AI Style Training" with nav link to `/meetings`

**Checkpoint**: `docker-compose up` → visit `http://localhost:3000` → app loads → register at `/register` → log in at `/login` → land on home page. Zero CORS errors in browser console.

---

## Phase 4: User Story 2 — Meeting Audio Upload Works End-to-End (Priority: P2)

**Goal**: A logged-in user can upload an audio/video file on the home page, see it appear as a real entry in their meetings list, open the meeting to watch status update from "queued" → "processing" → "completed", and read the transcript, summary, and action items.

**Independent Test**: Log in → upload an audio file on the home page → navigate to `/meetings` → meeting appears with status "queued" → open meeting → poll until "completed" → transcript and summary are visible. Delete the meeting and confirm it disappears from the list.

### Implementation for User Story 2

- [x] T013 [US2] Add `uploadMeeting(file)` (calls `POST /upload` with auth), `getMeetings(skip?, limit?)` (calls `GET /meetings/`), `getMeeting(id)` (calls `GET /meetings/{id}`), and `deleteMeeting(id)` (calls `DELETE /meetings/{id}`) to `frontend-2/app/lib/api.ts`
- [x] T014 [P] [US2] Create `frontend-2/app/components/file-upload-zone.tsx`: drag-and-drop + click-to-browse file input accepting `audio/*, video/*`; displays selected filename; passes selected `File` up via `onChange` prop (depends on T013 completing before T017)
- [x] T015 [P] [US2] Create `frontend-2/app/components/ui/status-badge.tsx`: renders a colored pill badge for meeting status values `queued` (gray), `processing` (yellow), `completed` (green), `failed` (red)
- [x] T016 [P] [US2] Create `frontend-2/app/components/meeting-card.tsx`: displays meeting `title`, `created_at` formatted as locale date string, `StatusBadge`, and a "View" link to `/meetings/{id}`; includes a "Delete" button that calls `deleteMeeting(id)` and invokes an `onDelete` callback prop
- [x] T017 [US2] Update `frontend-2/app/page.tsx` home page to include a full audio upload section: render `FileUploadZone`, a "Process Meeting" button using `Button` component, call `uploadMeeting()` on submit, show success alert with meeting ID and redirect option to `/meetings`, show error alert on failure (depends on T013, T014)
- [x] T018 [US2] Create `frontend-2/app/meetings/page.tsx`: fetch `getMeetings()` on mount; render list of `MeetingCard` components; show empty state when no meetings; handle `onDelete` by removing meeting from local state; show loading state while fetching (depends on T013, T015, T016)
- [x] T019 [US2] Create `frontend-2/app/meetings/[id]/page.tsx`: fetch `getMeeting(id)` on mount; poll every 3 seconds while `status` is `queued` or `processing` (switch to 10-second interval after 30 seconds elapsed, stop when `completed` or `failed`); render `StatusBadge`; render transcript, summary, and action items sections when completed; render failure message when failed (depends on T013, T015)

**Checkpoint**: Full upload → poll → view results flow works end-to-end. Delete a meeting from the list and confirm it disappears without a page reload.

---

## Phase 5: User Story 3 — AI Style Upload Works End-to-End (Priority: P3)

**Goal**: A user can upload a PDF example of their preferred note-taking style and see it listed as an active style example on the home page.

**Independent Test**: On the home page, upload a PDF file via the style upload section → success notification appears → the filename appears in the "Current Styles" list below the upload form.

### Implementation for User Story 3

- [x] T020 [US3] Add `uploadStyle(file)` (calls `POST /styles/upload`) and `getStyles()` (calls `GET /styles/`) to `frontend-2/app/lib/api.ts`
- [x] T021 [US3] Add style upload section to `frontend-2/app/page.tsx` below the audio upload section: PDF-only file input, "Upload Style" button calling `uploadStyle()`, success/error notifications, and a list of filenames fetched from `getStyles()` on page load (depends on T020, T017)

**Checkpoint**: Upload a PDF → filename appears in styles list on the same page → backend stores it (verify with `GET /styles/`).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Auth protection, global error handling, and end-to-end validation.

- [x] T022 [P] Add auth guard to `frontend-2/app/meetings/page.tsx` and `frontend-2/app/meetings/[id]/page.tsx`: check `getToken()` on mount; redirect to `/login` if token is absent
- [x] T023 Add 401 response interceptor to the Axios client in `frontend-2/app/lib/api.ts`: call `clearToken()` and redirect to `/login` using `window.location.href` on any 401 response
- [x] T024 Run end-to-end verification from `quickstart.md`: `docker-compose up --build` → register → login → upload meeting → view meetings list → open meeting detail → delete meeting → confirm no `./frontend` references in `docker-compose.yml`
- [x] T025 [P] Add `frontend-2/` to `.gitignore` exclusions for `node_modules/`, `.next/`, and `.env.local`; add `frontend-2/.env.local` example to repository documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **Phase 3 (US1 P1)**: Depends on Phase 2 — implements core app shell and auth
- **Phase 4 (US2 P2)**: Depends on Phase 2; builds on Phase 3's auth and home page
- **Phase 5 (US3 P3)**: Depends on Phase 2; extends Phase 4's home page
- **Phase 6 (Polish)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only — independently testable
- **US2 (P2)**: Depends on Phase 2; integrates with US1's home page (T012 → T017)
- **US3 (P3)**: Depends on Phase 2; extends US2's home page (T017 → T021)

### Within Each Phase — Parallel Opportunities

**Phase 2**: T003, T004, T005, T006, T008 can all run in parallel (different files). T007 (docker-compose) also independent.

**Phase 3**: T009 first → then T010 and T011 in parallel (different files). T012 independently after T009.

**Phase 4**: T013 first → then T014, T015, T016 in parallel (different files) → then T017, T018, T019 sequentially (each depends on earlier tasks).

**Phase 5**: T020 first → then T021 (depends on T020 and T017).

**Phase 6**: T022, T025 in parallel; T023 and T024 sequential.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# All 5 of these can run simultaneously (different files):
Task T003: Create frontend-2/app/globals.css
Task T004: Create frontend-2/app/layout.tsx
Task T005: Create frontend-2/app/lib/api.ts
Task T006: Create frontend-2/app/components/ui/button.tsx
Task T008: Update backend/app/main.py CORS
# T007 (docker-compose.yml) can also run in parallel
```

## Parallel Example: Phase 4 (US2 Components)

```bash
# After T013 completes, these 3 run simultaneously (different files):
Task T014: Create frontend-2/app/components/file-upload-zone.tsx
Task T015: Create frontend-2/app/components/ui/status-badge.tsx
Task T016: Create frontend-2/app/components/meeting-card.tsx
```

---

## Implementation Strategy

### MVP First (US1 Only — ~10 tasks)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T008)
3. Complete Phase 3: User Story 1 (T009–T012)
4. **STOP and VALIDATE**: App loads at `localhost:3000`, register + login works, CORS is clean
5. Deploy or demo

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (app shell builds)
2. Phase 3 (US1) → Auth and app entry point ✓
3. Phase 4 (US2) → Full meeting upload + view results flow ✓
4. Phase 5 (US3) → Style upload ✓
5. Phase 6 → Polish and hardening ✓

---

## Notes

- **No tests** are included — the feature spec does not request TDD. Verification is done via the quickstart.md steps.
- [P] tasks operate on different files — safe to run in parallel.
- The `frontend/` directory is **never modified** in any task — it is preserved as-is.
- Auth token storage (`localStorage`) is intentional for this MVP. A future feature can upgrade to `httpOnly` cookies.
- Commit after each phase checkpoint (6 natural commit points).
