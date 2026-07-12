# Data Model: Owner Notifications via Telegram Bot

## Overview

This feature introduces **no database tables or schema changes**. All data structures are in-memory Python dataclasses used for event dispatch.

## Entities

### NotificationEvent (dataclass — not persisted)

Represents a single event to be dispatched to notification providers.

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | `str` | Event identifier (e.g., `"new_user"`, `"upload_started"`, `"transcription_completed"`) |
| `emoji` | `str` | Display emoji for the event type (e.g., `"🆕"`, `"📤"`, `"✅"`) |
| `label` | `str` | Human-readable event label (e.g., `"New User"`, `"Upload Started"`) |
| `user_email` | `str` | Email of the user who triggered the event (Supabase ID as fallback) |
| `meeting_title` | `str \| None` | Meeting title, if applicable to the event |
| `extra` | `dict[str, str]` | Optional additional context (e.g., `{"duration": "5 min"}`, `{"pdf_type": "summary"}`) |
| `timestamp` | `datetime` | UTC timestamp of the event |

### NotificationProvider (Protocol — not persisted)

Abstract interface for notification delivery channels.

| Method | Signature | Description |
|--------|-----------|-------------|
| `send` | `(event: NotificationEvent) -> None` | Deliver a notification event to the channel. Must not raise exceptions. |

### Event Type Registry

| Event Type | Emoji | Label | Triggered From | Meeting Context |
|------------|-------|-------|----------------|-----------------|
| `new_user` | 🆕 | New User | `deps.py` — JIT provisioning (user created) | No |
| `user_login` | 👤 | User Login | `deps.py` — JIT provisioning (user exists) | No |
| `upload_started` | 📤 | Upload Started | `meetings.py` — confirm upload / webhook | Yes |
| `transcription_completed` | 🎙️ | Transcription Done | `worker.py` — `stage_transcribe` | Yes |
| `summary_generated` | 📝 | Summary Generated | `worker.py` — `stage_summarize` | Yes |
| `pdf_exported` | 📄 | PDF Downloaded | `meetings.py` — export endpoint | Yes |
