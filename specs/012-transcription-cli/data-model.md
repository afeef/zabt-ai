# Data Model: Transcription CLI

**Branch**: `012-transcription-cli` | **Date**: 2026-02-26

> This feature does not introduce new database tables. The CLI operates entirely on
> local files and in-memory data structures. This document describes the data shapes
> returned by the shared services and consumed by the CLI for output formatting.

## Entities (In-Memory Only)

### Transcript Segment

Returned by `TranscriptionService.process_audio()` inside the `result["segments"]` list.

| Field | Type | Description |
|-------|------|-------------|
| text | str | The spoken text content of this segment |
| speaker | str | Speaker label (e.g., "SPEAKER_00", "SPEAKER_UNKNOWN" if diarization skipped) |
| start | float | Segment start time in seconds |
| end | float | Segment end time in seconds |
| words | List[dict] | Word-level timestamps — each dict has `word`, `start`, `end` keys |

**Full return shape** of `process_audio()`:

```python
{
    "segments": [
        {
            "text": "Hello, let's start the meeting.",
            "speaker": "SPEAKER_00",
            "start": 0.0,
            "end": 2.5,
            "words": [
                {"word": "Hello,", "start": 0.0, "end": 0.3},
                {"word": "let's", "start": 0.4, "end": 0.6},
                ...
            ]
        },
        ...
    ],
    "language": "en"
}
```

### Meeting Minutes (Summarization Output)

Returned by `meeting_agent.run_sync()` as `result.data` — a `MeetingMinutes` Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| summary | str | Concise meeting summary |
| key_decisions | List[str] | Key decisions made during the meeting |
| action_items | List[ActionItem] | Extracted action items |
| sentiment | str | Overall sentiment: "Positive", "Neutral", or "Negative" |

### Action Item (Nested in Meeting Minutes)

| Field | Type | Description |
|-------|------|-------------|
| description | str | What needs to be done |
| owner | Optional[str] | Person responsible (may be None) |
| due_date | Optional[str] | Target date (may be None) |

## State Transitions

No persistent state. The CLI processes a file and exits. No status lifecycle.

## Relationships

- A single audio file produces zero or more **Transcript Segments**
- The concatenated segment text is fed to the agent, producing one **Meeting Minutes** (optional)
- **Action Items** are nested within **Meeting Minutes**
