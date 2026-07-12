# Implementation Plan: Owner Notifications via Telegram Bot

**Branch**: `023-telegram-notifications` | **Date**: 2026-03-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-telegram-notifications/spec.md`

## Summary

Add a backend notification system that sends real-time Telegram messages to the platform owner when key events occur (user login, upload, transcription, summary, PDF export). Uses a `NotificationProvider` protocol for extensibility, with Telegram as the first concrete implementation. Notifications are dispatched as fire-and-forget HTTP calls — no new database tables, no Celery tasks, no frontend changes.

## Technical Context

**Language/Version**: Python 3.11 (backend only — no frontend changes)
**Primary Dependencies**: FastAPI, Celery, httpx (new — async HTTP client for Telegram Bot API), pydantic-settings
**Storage**: N/A — no new tables or schema changes
**Testing**: pytest
**Target Platform**: Linux server (Docker)
**Project Type**: Web service (backend addition)
**Performance Goals**: Notification delivered within 5 seconds of event; zero impact on request latency
**Constraints**: Notifications must never block or fail the triggering request/task; best-effort delivery
**Scale/Scope**: ~6 event types, 1 provider (Telegram), 1 recipient (owner)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes |
| API Contract | No | N/A | No new endpoints — notifications fire from existing code paths |
| Auth/Security | Yes | PASS | Bot token stored in env var; no user-facing auth changes |
| Env Config | Yes | PASS | `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` documented in quickstart.md |
| Scope Boundary | Yes | PASS | Backend-only; 6 event hooks + 1 provider + 1 protocol |
| E2E Testing | No | N/A | No user-facing flow — owner receives Telegram messages; tested via unit/integration tests |
| Repository Pattern | No | N/A | No data access — no database tables involved |
| CLI/Typer | No | N/A | No CLI component |
| Provider Abstraction | Yes | PASS | `NotificationProvider` Protocol defined; Telegram is concrete implementation |
| Cost Awareness | Yes | PASS | Telegram Bot API is free; no paid API calls |
| Migration Safety | No | N/A | No provider replacement — this is a new capability |
| DB Migration | No | N/A | No schema changes |
| shadcn/ui Components | No | N/A | No frontend changes |

## Project Structure

### Documentation (this feature)

```text
specs/023-telegram-notifications/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py              # Add TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
│   ├── services/
│   │   └── notifications/
│   │       ├── __init__.py        # Public API: notify()
│   │       ├── provider.py        # NotificationProvider Protocol + NotificationEvent dataclass
│   │       └── telegram.py        # TelegramProvider implementation
│   ├── api/
│   │   └── deps.py                # Hook: login event (new/returning user)
│   │   └── v1/endpoints/
│   │       └── meetings.py        # Hook: upload confirmed, PDF exported
│   └── worker.py                  # Hook: transcription completed, summary generated
```

**Structure Decision**: Backend-only. New `notifications/` service module follows the existing pattern established by `transcription/` (Protocol + concrete provider + factory). Event hooks are added inline at existing code locations — same pattern as `analytics.capture()` calls.

## Complexity Tracking

> No constitution violations. All gates pass.
