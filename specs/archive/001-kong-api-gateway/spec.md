# Feature Specification: Kong API Gateway

**Feature Branch**: `001-kong-api-gateway`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "I have exposed the backend api on the internet using cloudflare tunnel. However, my minio is using localhost url for upload. I don't want to expose that too on the internet. I am looking for a central way of exposing the backend to the cloudflare tunnels preferebly using an api gateway like kong."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Single Public Entry Point via API Gateway (Priority: P1)

All external traffic (from the Cloudflare tunnel and internet-facing clients) reaches the system through a single gateway. The gateway forwards requests to the backend API. MinIO remains internal and is never directly reachable from outside.

**Why this priority**: This is the core ask — consolidate external exposure into one controlled entry point so that only the API is publicly routable and internal services (MinIO, Redis, database) are unreachable from the internet.

**Independent Test**: Point the Cloudflare tunnel at the gateway's public port → verify that `/api/*` requests are proxied correctly to the backend and return valid responses. Then attempt to reach the MinIO endpoint (port 9000) directly from outside the network and confirm the connection is refused.

**Acceptance Scenarios**:

1. **Given** the Cloudflare tunnel is pointed at the gateway, **When** a client sends an API request (e.g., `GET /api/v1/meetings`), **Then** the gateway forwards it to the backend and the response is returned correctly.
2. **Given** MinIO is not routed through the gateway, **When** an external actor attempts to reach MinIO's port directly, **Then** the connection is refused or unreachable from the internet.
3. **Given** the gateway is the only public-facing service, **When** the backend is restarted, **Then** the gateway retries or surfaces an error without exposing MinIO or other internal services.

---

### User Story 2 — Presigned Upload URLs Remain Functional Without Exposing MinIO (Priority: P2)

The file upload flow currently uses presigned MinIO URLs that point to `localhost`. After this change, presigned URLs must resolve correctly for remote clients — routed through the gateway — without making MinIO's port publicly accessible.

**Why this priority**: Without solving this, the upload feature breaks entirely once MinIO's localhost URL is no longer reachable by external clients.

**Independent Test**: Upload a meeting file from a browser on a remote machine (not localhost) → verify the file reaches MinIO storage and the meeting is created successfully.

**Acceptance Scenarios**:

1. **Given** a user requests a file upload, **When** the backend generates a presigned URL, **Then** the URL points to the gateway's public hostname (not `localhost:9000`).
2. **Given** a presigned upload URL pointing to the gateway, **When** the client PUTs a file to it, **Then** the gateway proxies the request to internal MinIO and the file is stored successfully.
3. **Given** a large file upload (e.g., 500 MB audio), **When** streamed through the gateway, **Then** the upload completes without timeout or data corruption.

---

### User Story 3 — Rate Limiting and Declarative Route Management (Priority: P3)

The gateway enforces basic rate limiting on public-facing routes to prevent abuse, and routes are defined declaratively so future services can be added without touching the Cloudflare tunnel configuration.

**Why this priority**: Foundational operational concern; the system should not be trivially overloaded once publicly exposed. Lower priority than the routing fundamentals.

**Independent Test**: Send more than the allowed number of requests per minute to an API endpoint → verify the gateway returns a 429 response for excess requests.

**Acceptance Scenarios**:

1. **Given** a configured rate limit, **When** a client exceeds the limit, **Then** the gateway returns HTTP 429 with a `Retry-After` hint.
2. **Given** a new internal service needs to be exposed, **When** a route entry is added to the gateway configuration file, **Then** the new route is live after a gateway reload — no Cloudflare tunnel reconfiguration required.

---

### Edge Cases

- What happens if the gateway is down when a request arrives at the Cloudflare tunnel entry point?
- What happens if MinIO is restarted mid-upload while the request is proxied through the gateway?
- How does the gateway handle requests to undefined routes (no matching upstream)?
- What happens if a presigned URL expires before the client finishes uploading?
- How are CORS headers preserved when the gateway sits between the browser and the API?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All public API traffic MUST enter the system through the API gateway; no other service port shall be reachable from the internet.
- **FR-002**: The gateway MUST proxy requests to the backend API service without altering request or response payloads.
- **FR-003**: The gateway MUST proxy MinIO presigned upload and download requests so that clients use the gateway's public hostname instead of `localhost:9000`.
- **FR-004**: The Cloudflare tunnel MUST point exclusively to the gateway's public port; tunnel configuration must NOT require changes when internal services are updated or rerouted.
- **FR-005**: MinIO MUST generate presigned URLs that reference the gateway's public hostname, not `localhost` or any internal address.
- **FR-006**: The gateway MUST support rate limiting per IP on public routes with a configurable threshold.
- **FR-007**: Internal services (MinIO, Redis, database) MUST NOT be bound to any publicly routable network interface.
- **FR-008**: The gateway configuration MUST be declarative and version-controlled so routes can be reviewed and updated without manual UI steps.
- **FR-009**: The gateway MUST pass standard HTTP headers (including `Authorization`, `Content-Type`, `X-Forwarded-For`) to upstream services unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of external API requests reach the backend exclusively through the gateway — confirmed by an external network scan finding no directly reachable backend or MinIO ports.
- **SC-002**: File uploads from remote clients (not localhost) succeed end-to-end with no changes required to the client-side upload flow.
- **SC-003**: MinIO port is unreachable from outside the host network, verified by an external port probe returning connection refused or timeout.
- **SC-004**: Adding or removing a gateway route requires only a configuration file change and gateway reload — no Cloudflare tunnel or host firewall changes needed.
- **SC-005**: Rate limiting activates within 1 request of the configured threshold with no false positives under normal load.
- **SC-006**: Gateway adds no more than 20 ms of additional latency on API responses measured under typical load.

## Assumptions

- The deployment runs on a single host using Docker Compose; the API gateway is added as a new service in the same Compose stack.
- Cloudflare tunnel is already operational and will be reconfigured to point to the gateway rather than directly to the API container.
- MinIO's public endpoint environment variable can be updated to the gateway's public hostname to fix presigned URL generation — no backend code changes required.
- The backend and MinIO services will remain on an internal Docker network with no ports bound to the host's public interface.
- No authentication or authorization logic is added at the gateway layer in this iteration — authentication remains in the backend.
- The gateway is responsible for SSL termination when traffic arrives from Cloudflare (Cloudflare handles TLS to the tunnel; the tunnel connects to the gateway over HTTP internally).
