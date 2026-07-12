# Feature Specification: Monitoring and Observability

**Feature Branch**: `001-observability`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "As a user i want to add monitoring and observability in the application so that I can view the api, worker and llm traces, metrics and logs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - API & Worker Traces (Priority: P1)

As a developer, I want to view distributed traces for every API request and background worker task so that I can identify bottlenecks, diagnose failures, and understand end-to-end request flows through the system.

**Why this priority**: The API and worker are the core of the application. Without visibility into request traces and task durations, diagnosing production issues is guesswork. This is the highest-value observability signal.

**Independent Test**: Can be fully tested by making an API request and triggering a file processing job, then verifying both appear as structured traces with duration, status, and error information in the observability dashboard.

**Acceptance Scenarios**:

1. **Given** a user uploads a meeting file, **When** the backend processes the request, **Then** a trace is recorded showing the full API request lifecycle including duration and status code.
2. **Given** a background task runs (transcription or summarization), **When** the task completes or fails, **Then** a trace is recorded showing task name, duration, and outcome.
3. **Given** an API request fails with an error, **When** the trace is viewed, **Then** the error message and stack trace are captured and visible.
4. **Given** a slow database query occurs, **When** the trace is viewed, **Then** the query and its duration appear as a child span within the parent request trace.

---

### User Story 2 - LLM Call Traces (Priority: P2)

As a developer, I want to see detailed traces of every LLM call made during meeting summarization so that I can monitor prompt quality, token usage, latency, and cost per operation.

**Why this priority**: LLM calls are the most expensive and variable part of the pipeline. Visibility into prompt/completion content, token counts, and per-call costs enables cost control and quality monitoring.

**Independent Test**: Can be fully tested by triggering a meeting summarization and verifying the LLM call appears with prompt, completion, token count, model name, latency, and estimated cost.

**Acceptance Scenarios**:

1. **Given** a meeting summary is generated, **When** the LLM trace is viewed, **Then** it shows the model used, prompt content, completion content, token counts (input/output), and latency.
2. **Given** multiple summarizations occur, **When** viewing aggregate LLM metrics, **Then** total token usage and estimated cost are visible over a time period.
3. **Given** an LLM call fails or times out, **When** the trace is viewed, **Then** the error reason is captured alongside the prompt that caused it.
4. **Given** different summary templates are used, **When** viewing traces, **Then** each trace is tagged with the template name for comparison.

---

### User Story 3 - Structured Logs (Priority: P3)

As a developer, I want structured logs from the API and worker to be centrally collected and searchable so that I can investigate specific events without SSH-ing into the server.

**Why this priority**: Logs provide context that traces alone don't capture. Centralized, searchable logs reduce debugging time for production incidents.

**Independent Test**: Can be fully tested by triggering a specific operation and searching for its log output by meeting ID or user ID in the log viewer.

**Acceptance Scenarios**:

1. **Given** any API request is processed, **When** logs are searched by request ID, **Then** all log lines for that request are returned in order.
2. **Given** a worker task runs, **When** logs are searched by meeting ID, **Then** all log output from that task is returned including any warnings or errors.
3. **Given** an unhandled exception occurs, **When** logs are viewed, **Then** the full stack trace is captured as a structured log entry with severity level "error".

---

### Edge Cases

- What happens when the observability service is unreachable — does it crash the application or fail silently?
- How are traces handled when a worker task is retried after failure?
- What happens if trace context is lost between the API request and the async worker task?
- How is sensitive data (prompts containing meeting content) handled in LLM traces?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST capture a trace for every inbound API request, including HTTP method, path, status code, and duration.
- **FR-002**: The system MUST capture a trace for every background worker task, including task name, duration, and success/failure outcome.
- **FR-003**: The system MUST capture a trace for every LLM call, including model name, token counts (input and output), latency, and estimated cost — visible within the same unified observability platform as API and worker traces.
- **FR-004**: The system MUST link worker task traces to the originating API request, and LLM call traces to their parent worker task, so the full end-to-end flow is visible in a single trace view.
- **FR-005**: The system MUST capture and surface application errors and exceptions with stack traces in both traces and logs.
- **FR-006**: The system MUST capture database query spans as child spans within their parent request trace.
- **FR-007**: LLM traces MUST be tagged with the summary template identifier used for the call.
- **FR-008**: All observability instrumentation MUST fail silently — errors in tracing must never crash or degrade the application.
- **FR-009**: The system MUST collect structured logs from the API and worker that are searchable by meeting ID, user ID, and request ID.
- **FR-010**: LLM traces MUST include token and cost metrics that can be aggregated over a time period.

### Key Entities

- **Trace**: A record of a single operation (API request, worker task, or LLM call) with start time, duration, status, and nested child spans.
- **Span**: A single unit of work within a trace (e.g., a database query, an HTTP call) with its own duration and metadata.
- **Log Entry**: A structured log line with timestamp, severity level, correlation IDs (request ID, meeting ID, user ID), and message.
- **LLM Trace**: A specialised trace for AI calls capturing prompt, completion, model, token counts, and cost.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every API request and worker task produces a visible trace within 5 seconds of completion.
- **SC-002**: 100% of LLM summarization calls produce a trace capturing model, token usage, and latency.
- **SC-003**: Engineers can locate the root cause of a production error within 5 minutes using traces and logs alone, without requiring direct server access.
- **SC-004**: Instrumentation overhead adds less than 5% to API response time under normal load.
- **SC-005**: LLM cost per meeting summarization is visible and aggregatable within the same unified dashboard as API and worker traces.
- **SC-006**: Zero application crashes or errors occur as a result of observability instrumentation failures.

## Clarifications

### Session 2026-03-05

- Q: What does "unified observability" mean — single platform or two correlated platforms? → A: Single platform (Logfire only) — API, worker, and LLM traces all in Logfire via its pydantic-ai integration.

## Assumptions

- **Logfire (by Pydantic) is the single unified observability platform** for API traces, worker task traces, and LLM call traces. Langfuse is not used.
- LLM call traces are captured via Logfire's native pydantic-ai instrumentation, appearing as child spans within the parent worker task trace.
- The application backend runs locally, exposed via Cloudflare tunnel — observability data is sent to Logfire Cloud.
- Sensitive prompt content in LLM traces is acceptable since Logfire is used only by the development team.
- Frontend observability is out of scope (covered by PostHog analytics).
- Data retention follows Logfire's free tier default settings.
- A single developer is the primary consumer of observability data.
