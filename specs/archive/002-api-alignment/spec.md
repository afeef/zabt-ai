# Feature Specification: Backend API Alignment for Frontend-2

**Feature Branch**: `002-api-alignment`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "Also make sure you analyze the existing apis written and see how many apis are needed to be created, updated or deleted according to the new frontend design"

## Current API Inventory

> *This section documents the current state of the backend as a reference baseline. It is not part of the standard spec template but is included here as essential context for what must change.*

| Status | Endpoint | Purpose | Issue |
|--------|----------|---------|-------|
| EXISTS | `POST /login/access-token` | User login, returns JWT token | JWT secret is hardcoded (security risk) |
| EXISTS | `POST /users/` | Register new user account | Functional |
| EXISTS | `GET /users/me` | Get current logged-in user's profile | Functional |
| EXISTS | `POST /upload` | Upload audio/video file for transcription | Auth is disabled; background task is never triggered |
| EXISTS | `POST /styles/upload` | Upload PDF style examples for AI training | Functional |
| EXISTS | `GET /styles/` | List uploaded style examples | Functional |
| **MISSING** | `GET /meetings/` | List all meetings for the current user | Old frontend shows a hardcoded mock list |
| **MISSING** | `GET /meetings/{id}` | View a single meeting's transcript, summary, and action items | No way to read AI results after processing |
| **MISSING** | `DELETE /meetings/{id}` | Remove a meeting and its associated files | No cleanup capability |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Real Meeting History (Priority: P1)

A user logs in and sees their actual past meetings displayed in the application — not placeholder data. Each meeting shows its title, date, duration, and current processing status (queued, processing, completed, or failed).

**Why this priority**: The old frontend renders a hardcoded mock list. Without a real meetings list endpoint, users can upload meetings but have no way to track or revisit them. This is the most fundamental gap between the current backend and a functional frontend.

**Independent Test**: Can be fully tested by uploading a meeting, then loading the meetings list view — the newly uploaded meeting must appear with its real title and status.

**Acceptance Scenarios**:

1. **Given** a logged-in user with no meetings, **When** they view the meetings list, **Then** an empty state is shown (not a mock list).
2. **Given** a logged-in user who has uploaded meetings, **When** they view the meetings list, **Then** all their meetings appear with correct title, date, and processing status.
3. **Given** a meeting that is still being processed, **When** the user views the list, **Then** the meeting shows a "processing" status and refreshing the page updates it when complete.
4. **Given** a user who is not logged in, **When** they attempt to access the meetings list, **Then** they are redirected to login rather than seeing an error.

---

### User Story 2 - Read Meeting Results (Priority: P1)

A user selects a completed meeting and views its AI-generated output: the full transcript, a written summary, and a list of action items with owners.

**Why this priority**: This is the core value of the product. Without the ability to retrieve and display AI output, the entire transcription and summarization pipeline produces results that are stored but never surfaced to the user.

**Independent Test**: Can be fully tested by uploading a meeting, waiting for it to complete processing, then clicking into it — the transcript, summary, and action items must all be displayed correctly.

**Acceptance Scenarios**:

1. **Given** a completed meeting, **When** the user opens it, **Then** the full transcript text, summary, key decisions, and action items (with owners and due dates where extracted) are all displayed.
2. **Given** a meeting that failed processing, **When** the user opens it, **Then** a clear failure message is shown along with whatever partial data was saved (e.g., transcript may exist even if summarization failed).
3. **Given** a meeting still being processed, **When** the user opens it, **Then** a processing indicator is shown and the results area displays "not yet available."

---

### User Story 3 - Secure Upload with Real Processing (Priority: P2)

A logged-in user uploads an audio or video file and the system automatically begins transcribing and summarizing it in the background. The upload is tied to the user's account, not a hardcoded placeholder owner.

**Why this priority**: The current upload endpoint saves the file and creates a database record but never triggers the AI processing pipeline, and it assigns all meetings to a hardcoded user ID of 1. This must be fixed before the new frontend goes live.

**Independent Test**: Can be fully tested by a logged-in user uploading an audio file and then polling the meeting detail — it must eventually transition from "queued" → "processing" → "completed" with real AI-generated output.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they upload an audio file, **Then** the meeting is created under their account (not a hardcoded owner) and processing begins automatically.
2. **Given** a meeting has been uploaded, **When** sufficient time passes for processing, **Then** the meeting status changes from "queued" to "processing" and eventually to "completed" or "failed."
3. **Given** a user who is not logged in attempts to upload a file, **When** the request reaches the backend, **Then** it is rejected with an authentication error.

---

### User Story 4 - Delete a Meeting (Priority: P3)

A user removes a meeting they no longer need. The meeting record and its associated uploaded file are permanently deleted from the system.

**Why this priority**: Basic data management. Users will accumulate meetings over time and need the ability to clean up their history. This is essential for a production-ready product but is not blocking core functionality.

**Independent Test**: Can be fully tested by uploading a meeting, then deleting it, and confirming it no longer appears in the meetings list.

**Acceptance Scenarios**:

1. **Given** a user owns a meeting, **When** they delete it, **Then** the meeting is removed from their list and the associated file is deleted from storage.
2. **Given** a user attempts to delete a meeting they do not own, **When** the delete request is made, **Then** it is rejected with a permissions error.
3. **Given** a deleted meeting's ID, **When** the user tries to access it directly, **Then** a "not found" response is returned.

---

### User Story 5 - Register and Log In (Priority: P2)

A new user creates an account with their email and password, then logs in to access their personalized meeting history and uploads.

**Why this priority**: The old frontend had no login UI — all operations used a hardcoded user. The new frontend requires real user sessions. Without working registration and login, no other user-scoped feature works.

**Independent Test**: Can be fully tested by creating a new account, logging in, and confirming that the meetings list shows only that user's meetings — not another user's.

**Acceptance Scenarios**:

1. **Given** a new visitor, **When** they register with a valid email and password, **Then** their account is created and they can immediately log in.
2. **Given** a registered user, **When** they log in with correct credentials, **Then** they receive a session token and are redirected to their dashboard.
3. **Given** a registered user, **When** they log in with incorrect credentials, **Then** a clear error message is shown and access is denied.
4. **Given** a valid session, **When** the user navigates between pages, **Then** their session persists without requiring re-login.

---

### Edge Cases

- What happens if a user uploads a file, loses their session, and logs back in? Their meeting must still appear in their history and be associated with their account.
- What if a meeting's audio file is deleted from disk manually but the database record still exists? The system should handle this gracefully when the user tries to view or process that meeting.
- What if two users upload files with the same filename at the same time? The system must store them without collision (files should not overwrite each other).
- What if a meeting is still processing when the user tries to delete it? The system must either cancel processing and delete, or reject the deletion with a clear explanation.
- What if the AI processing service is unavailable when a meeting is uploaded? The meeting should stay in "queued" status and be retried rather than immediately failing.

## Requirements *(mandatory)*

### Functional Requirements

#### APIs to Create (New)

- **FR-001**: The backend MUST provide a way to retrieve a list of all meetings belonging to the currently authenticated user, including each meeting's title, status, creation date, and duration.
- **FR-002**: The backend MUST provide a way to retrieve a single meeting's full details, including its transcript, AI-generated summary, key decisions, action items, and processing status.
- **FR-003**: The backend MUST provide a way to permanently delete a meeting owned by the authenticated user, including removal of the associated file from storage.

#### APIs to Update (Existing — Broken or Incomplete)

- **FR-004**: The meeting upload endpoint MUST authenticate the requesting user and associate the uploaded meeting with that user's account instead of a hardcoded placeholder owner.
- **FR-005**: The meeting upload endpoint MUST trigger the background AI processing task automatically after the file is saved and the meeting record is created.
- **FR-006**: The backend's security configuration MUST store the JWT signing secret in an environment variable rather than as a hardcoded value in source code.
- **FR-007**: The backend MUST prevent one user from accessing, modifying, or deleting meetings that belong to another user.

#### APIs to Remove (Cleanup)

- **FR-008**: No existing endpoints are candidates for removal at this stage. The login, user registration, user profile, upload, and styles endpoints are all either needed or being improved.

### Key Entities

- **User**: An authenticated account holder; has an email, display name, account tier (free/pro/enterprise), active status, and a collection of meetings. Owns all meetings they upload.
- **Meeting**: A recorded meeting submitted for AI processing; has a title, owner, file reference, processing status, and the AI-generated outputs (transcript, summary, key decisions, action items). Status progresses through: queued → processing → completed (or failed).
- **Style Example**: A PDF document uploaded by the user to teach the AI their preferred note-taking format; stored as a file and applied globally during meeting summarization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A logged-in user can view their complete, real meeting history (not mocked data) within 2 seconds of loading the meetings page.
- **SC-002**: A logged-in user can open any completed meeting and view its transcript, summary, and action items within 2 seconds.
- **SC-003**: After uploading an audio file, the meeting transitions from "queued" to "processing" automatically without any manual intervention — no endpoint calls, scripts, or admin actions required.
- **SC-004**: 100% of meetings are associated with the uploading user's account; zero meetings are assigned to placeholder or hardcoded identities.
- **SC-005**: A user can delete any of their own meetings successfully; attempting to delete another user's meeting returns an error 100% of the time.
- **SC-006**: The application passes a basic security review with no hardcoded credentials or secrets present in source code.
- **SC-007**: All 3 missing endpoints (list meetings, get meeting detail, delete meeting) are implemented, documented in the API schema, and return consistent, well-formed responses.

## Assumptions

- The new `frontend-2` application will require all 6 existing endpoints plus the 3 new ones identified here — no existing endpoints will become obsolete during the migration.
- User authentication will use the existing JWT/OAuth2 flow (login with email and password) — no SSO or social login is required for this phase.
- Meeting ownership is tied to the user who uploads the file; there is no sharing or team access model in this phase.
- The AI processing pipeline (transcription → summarization) will continue to use the existing background worker; the only change is ensuring it is triggered automatically on upload.
- File collision prevention (two users uploading files with the same name) will be handled by prefixing stored filenames with a unique identifier, keeping the original filename visible in the UI.
- The styles endpoint naming inconsistency (`POST /styles/upload` vs `GET /styles/`) is acceptable for this phase and will not be refactored unless it causes integration issues with `frontend-2`.
