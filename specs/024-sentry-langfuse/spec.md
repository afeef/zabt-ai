# Feature Specification: Observability Upgrade (Sentry + Langfuse)

**Feature Branch**: `024-sentry-langfuse`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Replace/augment Logfire with Sentry for APM and Langfuse for LLM observability."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Error and Performance Monitoring (Priority: P1)

As the platform owner, I want all application errors, slow requests, and slow database queries to be automatically captured and surfaced in a monitoring dashboard so I can diagnose production issues without reading raw logs.

**Why this priority**: Without error and performance visibility, production debugging is guesswork. This is the foundational observability layer.

**Independent Test**: Deploy with monitoring enabled, trigger an error (e.g., invalid API call), and verify it appears in the monitoring dashboard with full stack trace, request context, and timing breakdown.

**Acceptance Scenarios**:

1. **Given** an unhandled exception occurs in any API endpoint, **When** the error is thrown, **Then** it appears in the monitoring dashboard within 30 seconds with full stack trace, request URL, user context, and environment metadata.
2. **Given** a request takes longer than 1 second, **When** the request completes, **Then** its full timing breakdown (database queries, external calls) is captured in the performance dashboard.
3. **Given** a database query takes longer than 500ms, **When** the query executes, **Then** it is flagged as a slow query in the monitoring dashboard with the full SQL statement.
4. **Given** a Celery task fails, **When** the exception is raised, **Then** the error appears in the monitoring dashboard with task name, arguments, and stack trace.

---

### User Story 2 - LLM Call Tracing (Priority: P1)

As the platform owner, I want full visibility into every LLM call made during summarization — including the prompt sent, completion received, token usage, cost, and latency — so I can monitor AI spend, detect quality issues, and compare model performance.

**Why this priority**: LLM calls are the highest variable cost. Without tracing, cost overruns and quality regressions go undetected.

**Independent Test**: Trigger a meeting summarization, then verify the LLM call trace appears in the LLM dashboard with prompt, completion, token counts, model name, and latency.

**Acceptance Scenarios**:

1. **Given** a meeting is summarized, **When** the LLM call completes, **Then** the full trace (prompt, completion, model, tokens, latency) appears in the LLM observability dashboard.
2. **Given** multiple summarizations occur over a day, **When** the owner checks the dashboard, **Then** aggregate metrics are visible: total token usage, total cost, average latency per model.
3. **Given** the LLM observability service is unreachable, **When** a summarization runs, **Then** the summarization completes normally — tracing failures never block user flows.

---

### User Story 3 - Logfire Cleanup (Priority: P2)

As a developer, I want the existing Logfire instrumentation removed or reduced to structured logging only so that there is a single source of truth for each observability signal — no duplicate traces or conflicting dashboards.

**Why this priority**: Dual instrumentation causes confusion (which dashboard to check?) and wastes resources sending duplicate data. Clean separation matters but isn't blocking.

**Independent Test**: Verify that after cleanup, Logfire no longer sends APM traces or LLM data — only structured log messages (if retained) or nothing (if removed).

**Acceptance Scenarios**:

1. **Given** the migration is complete, **When** a request is processed, **Then** APM traces appear only in the error/performance dashboard (not Logfire).
2. **Given** the migration is complete, **When** an LLM call is made, **Then** LLM traces appear only in the LLM dashboard (not Logfire).

---

### Edge Cases

- What happens when the monitoring service credentials are not configured? Monitoring is silently disabled — no errors, no crashes. The application runs exactly as it did before this feature.
- What happens when the monitoring service is down or rate-limits? Events are dropped silently. No retry queues, no buffering beyond what the SDK provides by default.
- What happens when sensitive data (user emails, meeting content) is sent to monitoring services? Prompt/completion data sent to the LLM dashboard is expected and acceptable. PII in error reports (emails, IPs) should follow the monitoring service's default scrubbing.
- What happens in local development? Monitoring should be disabled by default (empty credentials) so local dev is unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture all unhandled exceptions in API endpoints and background tasks and send them to a monitoring dashboard with full context (stack trace, request details, user ID, environment).
- **FR-002**: System MUST capture request performance traces including timing breakdown for database queries and external HTTP calls.
- **FR-003**: System MUST flag database queries exceeding 500ms as slow queries with the full SQL statement captured.
- **FR-004**: System MUST capture Celery task errors with task name, arguments, and stack trace.
- **FR-005**: System MUST trace every LLM call with: prompt text, completion text, model name, token usage (input/output), estimated cost, and latency.
- **FR-006**: System MUST provide aggregate LLM metrics: total tokens, total cost, and average latency over configurable time periods.
- **FR-007**: All monitoring credentials MUST be configurable via environment variables. Missing credentials MUST silently disable the corresponding monitoring — no errors.
- **FR-008**: Monitoring instrumentation MUST NOT increase request latency by more than 5ms p99.
- **FR-009**: Monitoring failures (network errors, service outages) MUST NOT affect application behavior — all monitoring is best-effort.
- **FR-010**: The previous APM instrumentation MUST be removed or reduced to structured logging only to avoid duplicate signal collection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unhandled exceptions appear in the monitoring dashboard within 60 seconds of occurrence.
- **SC-002**: All database queries exceeding 500ms are automatically flagged in the performance dashboard.
- **SC-003**: Every LLM call is traced with prompt, completion, token usage, cost, and latency — zero calls go untracked.
- **SC-004**: Zero user-facing latency impact — p99 request latency increases by less than 5ms with monitoring enabled.
- **SC-005**: Zero application failures caused by monitoring service outages — the system degrades gracefully.
- **SC-006**: Single source of truth — each observability signal (errors, performance, LLM traces) appears in exactly one dashboard, not duplicated across tools.

## Assumptions

- The platform owner will create accounts on the monitoring services and obtain credentials before deployment.
- Both monitoring services offer free tiers sufficient for the current scale (< 100 meetings/day).
- LLM prompt and completion content is acceptable to send to the LLM observability service (no compliance restrictions on meeting transcript data).
- The existing Logfire token environment variable can be repurposed or removed.
- Monitoring is backend-only — no frontend instrumentation is in scope.
