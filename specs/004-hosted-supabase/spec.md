# Feature Specification: Use Hosted Supabase

**Feature Branch**: `004-hosted-supabase`  
**Created**: 2026-02-21  
**Status**: Draft  
**Input**: User description: "Use the hosted supabase.com for authentication and authorization flows to build the app quickly instead of building all components locally in docker compose"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authentication via Hosted Supabase (Priority: P1)

Users can register, log in, and manage their authentications directly utilizing the cloud-hosted Supabase services rather than a local Docker environment.

**Why this priority**: Shifting from local authentication orchestration to the cloud ensures immediate infrastructure availability and reduces local development dependencies, prioritizing speed to market.

**Independent Test**: Can be tested by configuring the frontend and backend to point to a live Supabase project URL and keys, then successfully registering a new user and logging in.

**Acceptance Scenarios**:

1. **Given** a developer environment, **When** the environment variables are updated to hosted Supabase credentials, **Then** the application connects to the cloud Supabase instance instead of localhost.
2. **Given** a new user on the registration page, **When** they submit their details, **Then** the user is created in the hosted Supabase project and a session is returned.
3. **Given** an authenticated user, **When** they make requests to the backend API, **Then** the backend successfully verifies their JWT against the hosted Supabase project's JWT secret or JWKS.

---

### Edge Cases

- What happens if the hosted Supabase environment experiences an outage or elevated latency compared to localhost?
- How are development, staging, and production environments separated within the hosted Supabase ecosystem?
- How does the system handle database synchronization if the backend PostgreSQL remains local while Auth is hosted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to a Supabase project hosted on `supabase.com` for all authentication and authorization flows.
- **FR-002**: Local `docker-compose.yml` MUST NOT deploy Supabase infrastructure components (GoTrue, PostgREST, Realtime, Studio, Meta, Kong) to reduce local resource consumption.
- **FR-003**: System environment variables MUST be updated to support distinct hosted Supabase URLs, Anon Keys, and Service Role Keys.
- **FR-004**: Backend JWT verification MUST validate tokens against the hosted Supabase project secret.
- **FR-005**: Social Login and Enterprise SSO redirects MUST point to the configured hosted Supabase Auth URLs instead of the local gateway.
- **FR-006**: System MUST manage the connection between the hosted Supabase Auth users and the local or managed application database [NEEDS CLARIFICATION: Is the PostgreSQL database also moving to hosted Supabase, or remaining local while only Auth moves explicitly?].

### Key Entities

- **Hosted Supabase Project**: The cloud-based Supabase instance (providing GoTrue auth handling and API keys).
- **Environment Configuration**: Key-value mappings directing frontend and backend clients to the cloud platform instead of localhost.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application successfully authenticates users via hosted Supabase with 100% feature parity to the local implementation.
- **SC-002**: Local development memory and CPU usage decreases demonstrably (by stopping the 6+ Supabase local containers).
- **SC-003**: `docker-compose up` startup time decreases by at least 15 seconds.
- **SC-004**: API route latency for login and JWT validation remains within acceptable bounds (< 200ms increase over local).
