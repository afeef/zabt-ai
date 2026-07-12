# Feature Specification: Migrate Auth to Supabase Cloud & Repurpose Backend

**Feature Branch**: `001-migrate-supabase`  
**Created**: 2026-02-21  
**Status**: Draft  
**Input**: User description: "Migrate the project authentication from Logto to the Supabase Cloud Service. The local docker-compose will no longer run auth services. Furthermore, alter the FastAPI backend architecture so it is solely responsible for AI-related transcription and summarization tasks. The backend should secure its endpoints by verifying the Supabase JWT tokens passed from the frontend."

## Clarifications

### Session 2026-02-21
- Q: Does the Supabase migration imply complete removal of all legacy Logto code and dependencies? → A: Yes, the logto implementation needs to be completely removed from the project and project needs to be cleaned of it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authentication via Hosted Supabase (Priority: P1)

Users can register, log in, and manage their authentication session directly utilizing the cloud-hosted Supabase services rather than a local Logto environment.

**Why this priority**: Ensures robust authentication availability, removing local deployment dependencies and providing a scalable auth solution.

**Independent Test**: Can be tested by configuring the frontend to point to a live Supabase project and successfully registering a new user and logging in.

**Acceptance Scenarios**:

1. **Given** a new user on the registration page, **When** they submit their details, **Then** the user is created in the hosted Supabase project and a session is returned.
2. **Given** a user is logged out, **When** they submit valid credentials, **Then** they are logged into the application.

---

### User Story 2 - Delegated AI Processing via Secure Backend (Priority: P1)

Authenticated users can execute AI-related transcription and summarization tasks through a specialized FastAPI backend that securely validates their identity using Supabase JWT tokens.

**Why this priority**: Restricting the backend solely to AI tasks optimizes the architecture by decoupling authentication flow control from heavy AI processing.

**Independent Test**: Can be tested by sending API requests (both with and without a valid Supabase JWT) to the backend's AI endpoints and observing the correct authorization behavior.

**Acceptance Scenarios**:

1. **Given** an unauthenticated client, **When** they request a transcription or summarization task, **Then** the backend rejects the request with an unauthorized error.
2. **Given** an authenticated user's frontend client, **When** it sends an AI processing request with a valid Supabase JWT, **Then** the backend successfully verifies the token against the Supabase project configuration and executes the task.

---

### User Story 3 - Streamlined Local Development (Priority: P2)

Developers can run the application locally without deploying authentication services, reducing resource consumption.

**Why this priority**: Improves developer experience by decreasing local system load and startup time.

**Independent Test**: Can be tested by running the local startup scripts or `docker-compose up` and verifying auth containers are not spawned.

**Acceptance Scenarios**:

1. **Given** a developer starting the local environment, **When** they run `docker-compose up`, **Then** the environment starts successfully without Logto or other auth-specific containers.

### Edge Cases

- How does the system handle temporary outages of the Supabase Cloud Service when the backend attempts to verify a JWT or fetch JWKS?
- What occurs if a token expires precisely during a long-running AI transcription task?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to a Supabase project hosted on `supabase.com` for all user authentication and registration flows.
- **FR-002**: Local `docker-compose.yml` MUST NOT deploy Logto or any local authentication infrastructure components.
- **FR-003**: Next.js frontend MUST explicitly direct user login and signup flows to Supabase instead of the legacy auth provider.
- **FR-004**: FastAPI backend MUST NOT implement user registration or login API routes natively.
- **FR-005**: FastAPI backend MUST be exclusively dedicated to AI-related capabilities, specifically transcription and summarization tasks.
- **FR-006**: FastAPI backend MUST validate the authenticity and integrity of incoming requests by verifying the Supabase JWT against the Supabase project's secret/JWKS.
- **FR-007**: All Logto-related SDKs, dependencies, environment variables, UI components, and API routes MUST be completely removed from the frontend and backend codebases.

### Key Entities

- **Supabase User**: Represents the authenticated identity managed in the cloud.
- **AI Task (Transcription/Summarization)**: Represents the core workload processed by the FastAPI backend, tied to the authenticated user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application successfully authenticates users via hosted Supabase with 100% feature parity to the previous local Logto implementation.
- **SC-002**: Local development memory and CPU usage decreases demonstrably due to the removal of Logto and associated database containers.
- **SC-003**: Backend AI endpoints accurately reject 100% of requests lacking a valid Supabase JWT and successfully authorize requests bearing valid ones.
- **SC-004**: The FastAPI backend contains zero native authentication registration or session-creation routes.
