# Feature Specification: Frontend-2 Migration

**Feature Branch**: `001-frontend-2-migration`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "I created this project which basically is a AI meeting notes taker, transcriber and summarizer with an old 'frontend' folder. I now have created a new 'frontend-2' and want to switch from 'frontend' to 'frontend-2' with the same backend. I also want to make required changes in the backend as well."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application Runs from frontend-2 (Priority: P1)

A developer or user launches the AI meeting notes application and all functionality works through the `frontend-2` codebase instead of the old `frontend` folder. The application entry point — whether via Docker Compose or running locally — now serves `frontend-2`.

**Why this priority**: This is the core migration goal. Without pointing the infrastructure to `frontend-2`, nothing else in this feature delivers value.

**Independent Test**: Can be fully tested by running the application stack and verifying the UI loads from the `frontend-2` source directory, and all existing features (audio upload, meeting list, style upload) remain accessible.

**Acceptance Scenarios**:

1. **Given** the developer runs `docker-compose up`, **When** the web service starts, **Then** it builds and serves the `frontend-2` application on port 3000.
2. **Given** the developer runs the frontend locally from `frontend-2`, **When** they start the dev server, **Then** the application loads in the browser and connects to the backend successfully.
3. **Given** the user visits the running application, **When** they interact with any feature (upload a meeting, view meetings, upload a style), **Then** all API calls to the backend succeed without errors.

---

### User Story 2 - Meeting Audio Upload Works End-to-End (Priority: P2)

A user uploads an audio or video file through `frontend-2`, and the backend receives, stores, and queues it for processing — same behavior as the old frontend.

**Why this priority**: The core product value — transcribing and summarizing meetings — begins with a successful file upload. If this breaks during migration, the product is non-functional.

**Independent Test**: Can be fully tested by uploading an audio file via the `frontend-2` UI and confirming the backend creates a meeting record with status "queued."

**Acceptance Scenarios**:

1. **Given** a user selects an audio or video file in `frontend-2`, **When** they click "Process Meeting," **Then** the file is uploaded to the backend and a success confirmation is displayed.
2. **Given** the backend receives an upload, **When** it processes the request, **Then** a meeting record is created in the database with the correct filename and status "queued."
3. **Given** an unsupported file type is selected, **When** the user attempts to upload, **Then** a clear error message is shown without crashing the application.

---

### User Story 3 - AI Style Upload Works End-to-End (Priority: P3)

A user uploads PDF examples of their preferred note-taking style through `frontend-2`, and the backend stores them for few-shot AI learning — same behavior as the old frontend.

**Why this priority**: This feature extends the product's AI personalization capability. It is secondary to the core upload flow but must continue to work after migration.

**Independent Test**: Can be fully tested by uploading a PDF through the style upload section in `frontend-2` and confirming the backend stores and returns it via the styles list.

**Acceptance Scenarios**:

1. **Given** a user selects a PDF file in the style upload area of `frontend-2`, **When** they submit it, **Then** the file is sent to the backend and a success notification is shown.
2. **Given** the backend receives a style upload, **When** it processes the request, **Then** the PDF is stored and retrievable via the styles list endpoint.

---

### Edge Cases

- What happens when `frontend-2` is missing required environment variables (e.g., `NEXT_PUBLIC_API_URL`)? The app should fall back to the default backend URL (`http://localhost:8000/api/v1`) rather than breaking silently.
- What if the `frontend-2` directory does not yet contain a valid project structure (missing `package.json`, `app/` directory)? The Docker build should fail early with a clear error.
- How does the system handle CORS if the frontend origin changes? The backend must allow requests from the new frontend's origin without errors.
- What happens if both `frontend` and `frontend-2` are run simultaneously by accident? Only one service should be active on port 3000 at a time; conflicting port bindings should surface a clear startup error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `docker-compose.yml` web service MUST be updated to build and serve from the `./frontend-2` directory instead of `./frontend`.
- **FR-002**: The `frontend-2` directory MUST contain a complete, runnable application with all pages and features equivalent to those in `frontend`: audio/video file upload, meeting list display, and AI style PDF upload.
- **FR-003**: The `frontend-2` application MUST connect to the backend API using the URL provided by the `NEXT_PUBLIC_API_URL` environment variable, defaulting to `http://localhost:8000/api/v1` when not set.
- **FR-004**: The `frontend-2` Dockerfile MUST be present and correctly configured to build and run the application in both development and production modes.
- **FR-005**: The `frontend-2` application MUST preserve all existing API integrations without regression: meeting audio upload (`POST /upload`), style PDF upload (`POST /styles/upload`), and style list retrieval (`GET /styles/`).
- **FR-006**: The backend CORS configuration MUST explicitly allow requests from the `frontend-2` application's origin (at minimum `http://localhost:3000` for development).
- **FR-007**: The old `frontend` directory MUST remain in the repository but MUST NOT be referenced by any active infrastructure configuration (Docker Compose, CI/CD scripts) after migration.
- **FR-008**: The backend `docker-compose.yml` environment configuration for the web service MUST pass the correct `NEXT_PUBLIC_API_URL` value so `frontend-2` connects to the API service.

### Key Entities

- **Meeting**: Represents a recorded meeting submitted for transcription and summarization; has an ID, title (filename), processing status, owner reference, and creation timestamp.
- **Style**: Represents a user-uploaded PDF example used for AI few-shot note-taking style learning; stored as a file and retrievable by name.
- **Web Service**: The containerized frontend service in the application stack; migrated from `./frontend` to `./frontend-2` as its build source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full application stack starts without errors when running `docker-compose up`, with the web service sourced exclusively from `frontend-2`.
- **SC-002**: All existing user-facing features (audio upload, meeting list display, style PDF upload) are functional through `frontend-2` with no regression in behavior compared to `frontend`.
- **SC-003**: An audio or video file upload initiated from `frontend-2` produces a new meeting record with status "queued" in the backend within 5 seconds for files up to 50MB.
- **SC-004**: A style PDF upload initiated from `frontend-2` results in the file being retrievable via the styles list endpoint within 3 seconds.
- **SC-005**: No references to `./frontend` remain in active infrastructure files (Docker Compose, deployment scripts) after migration is complete.
- **SC-006**: All API requests from `frontend-2` to the backend succeed without CORS errors in both local development and Docker Compose environments.

## Assumptions

- The `frontend-2` application will use the same technology stack as `frontend` (Next.js, TypeScript, Tailwind CSS) since reusing the same backend API contract is the stated goal.
- The backend API contract (endpoints, request/response shapes) does not change — this migration is a frontend and infrastructure swap only.
- The backend's current wildcard CORS (`allow_origins=["*"]`) is acceptable as a starting point but should be tightened to explicit origins as part of the backend changes requested by the user.
- The `media` volume mount and upload directory remain unchanged between old and new frontend.
- The user intends to keep the `frontend` directory as an archive for reference, not delete it.
- The `frontend-2` directory currently exists but does not yet contain a runnable application — scaffolding it is in scope for this feature.
