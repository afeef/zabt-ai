# Research: Owner Notifications via Telegram Bot

## Decision 1: HTTP Client for Telegram Bot API

**Decision**: Use `httpx` for async HTTP calls to the Telegram Bot API.

**Rationale**: httpx is already the standard async HTTP client in the Python ecosystem, supports both sync and async modes, and has zero configuration overhead for simple POST requests. The Telegram Bot API `sendMessage` endpoint is a single HTTP POST — no SDK needed.

**Alternatives considered**:
- `python-telegram-bot` library: Full-featured but heavy dependency for a single `sendMessage` call. Pulls in ~10 transitive dependencies. Overkill.
- `requests`: Sync-only. Would block the event loop or Celery worker thread during the API call.
- `aiohttp`: Viable but httpx has a cleaner API and is more commonly used in FastAPI projects.
- Raw `urllib`: No connection pooling, no async support, verbose error handling.

## Decision 2: Dispatch Mechanism

**Decision**: Fire-and-forget using `httpx.AsyncClient` in an async context (FastAPI endpoints) and `httpx.Client` (sync) in Celery tasks. No Celery task for notification dispatch.

**Rationale**: Notifications are best-effort with no delivery guarantees (per spec). Adding a Celery task for each notification would add unnecessary complexity (task serialization, result backend, retry logic) for something that should be a ~50ms HTTP call. The analytics module (`analytics.capture()`) uses the same fire-and-forget pattern successfully.

**Alternatives considered**:
- Celery task per notification: Guarantees delivery via retries, but over-engineered for best-effort notifications. Adds task queue overhead for a free API with no rate concerns.
- Background thread: Viable but adds thread management complexity. httpx handles this cleanly.

## Decision 3: Message Format

**Decision**: Plain text with emoji prefixes and markdown formatting (Telegram's MarkdownV2 parse mode).

**Rationale**: Simple, readable on mobile, no HTML complexity. Each event type gets a distinct emoji for visual scanning.

**Message template**:
```
🆕 *New User*
📧 user@example.com
🕐 2026-03-14 15:30 UTC
```
```
📤 *Upload Started*
📧 user@example.com
📝 Meeting Title
🕐 2026-03-14 15:30 UTC
```

**Alternatives considered**:
- HTML parse mode: More formatting options but harder to read on mobile and more escaping required.
- Inline keyboard buttons: Adds interactivity (e.g., "View Meeting") but requires webhook setup for bot commands — out of scope per spec.

## Decision 4: Provider Abstraction Shape

**Decision**: `NotificationProvider` Protocol with a single `send(event: NotificationEvent) -> None` method. Module-level `notify()` function as the public API (same pattern as `analytics.capture()`).

**Rationale**: Matches existing patterns in the codebase:
- `analytics.capture(user_id, event, properties)` — module-level function, fire-and-forget
- `EmailProvider` Protocol — `send_summary_email(to, meeting)`
- `TranscriptionProvider` Protocol — `process_audio(path, config)`

The `notify()` function handles provider initialization, graceful degradation (skip if unconfigured), and error swallowing — callers never need to check configuration or handle exceptions.

**Alternatives considered**:
- Dependency injection via FastAPI Depends: Would only work in endpoint context, not in Celery tasks. The module-level singleton pattern works everywhere.
- Event bus / pub-sub: Over-engineered for 6 event types with 1 subscriber. Would require event registration, handler management, and adds indirection without benefit at this scale.

## Decision 5: New vs Existing Dependency

**Decision**: Use `httpx` (add as new dependency).

**Rationale**: The project doesn't currently use httpx, but it's the recommended async HTTP client for FastAPI projects and has no heavy transitive dependencies. The alternative — using `requests` (already installed) — would work in Celery tasks but would block in async FastAPI endpoints.

**Note**: Since all notification hooks in FastAPI endpoints run in sync context (via `Depends`), and Celery tasks are also sync, we can use `httpx.Client` (sync) everywhere. No need for async client.
