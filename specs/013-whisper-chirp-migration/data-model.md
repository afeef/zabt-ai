# Data Model: Whisper-to-Chirp Transcription Migration

**Feature**: 013-whisper-chirp-migration
**Date**: 2026-02-28

## Existing Models (NO CHANGES — per FR-014)

These models are NOT modified by this migration. The ingestion layer adapts to
populate them from the new provider's response format.

### Meeting

| Field | Type | Notes |
|-------|------|-------|
| id | int (PK) | Auto-increment |
| owner_id | int (FK → User) | |
| title | str | |
| description | str? | |
| file_path | str? | MinIO S3 object key |
| duration_seconds | int? | |
| created_at | datetime | |
| status | str | pending_upload / queued / processing / completed / failed |
| sub_status | str? | downloading / transcribing / aligning / diarizing / summarizing |
| transcript_text | str? | Full text with speaker labels |
| summary_text | str? | AI-generated summary |
| action_items_text | str? | AI-generated action items |

### TranscriptSegment

| Field | Type | Notes |
|-------|------|-------|
| id | int (PK) | Auto-increment |
| meeting_id | int (FK → Meeting) | |
| start_time | float | Seconds from audio start |
| end_time | float | Seconds from audio start |
| text | str | Segment text |
| speaker | str? | e.g., "SPEAKER_00" |
| words | List[dict] (JSONB) | Word-level timestamps |

### User (tier-relevant fields)

| Field | Type | Notes |
|-------|------|-------|
| tier | UserTier enum | FREE / PRO / ENTERPRISE |
| minutes_used_this_month | int | Updated after each transcription (this migration) |

---

## New Domain Types (NOT database models — in-memory dataclasses)

These are transport types used between the provider abstraction layer and consumers
(worker, CLI, endpoints). They are NOT persisted — the existing DB models above
handle persistence.

### TranscriptionResult

| Field | Type | Notes |
|-------|------|-------|
| text | str | Full transcript text |
| language | str | Detected language code (e.g., "en-US") |
| segments | list[ResultSegment] | Ordered segments |
| provider_name | str | "whisper" or "chirp_3" |
| recognition_method | str | "local_whisperx" / "batch_dynamic" / "batch_standard" / "streaming" |
| audio_duration_seconds | float | Total audio length |
| estimated_cost | float | USD estimated cost |

### ResultSegment

| Field | Type | Notes |
|-------|------|-------|
| start | float | Seconds from audio start |
| end | float | Seconds from audio start |
| text | str | Segment text |
| speaker | str? | e.g., "SPEAKER_00", "SPEAKER_01" |
| words | list[WordTimestamp] | Word-level detail |

### WordTimestamp

| Field | Type | Notes |
|-------|------|-------|
| word | str | The word |
| start | float | Start time in seconds |
| end | float | End time in seconds |
| speaker_label | str? | Speaker ID (from provider) |
| confidence | float? | Word confidence (Chirp 3 caveat: not true confidence) |

### TranscriptionConfig

| Field | Type | Notes |
|-------|------|-------|
| language | str? | Override language (None = auto-detect) |
| min_speakers | int | Default 1 |
| max_speakers | int | Default 10 |
| use_dynamic_batching | bool | Default True (Starter tier) |

### CircuitBreakerState

| Field | Type | Notes |
|-------|------|-------|
| state | enum | CLOSED (normal) / OPEN (fallback active) |
| consecutive_failures | int | Reset to 0 on success |
| opened_at | datetime? | When breaker tripped |
| threshold | int | From config (default 5) |
| cooldown_seconds | int | From config (default 300) |

---

## State Transitions

### Meeting Status (unchanged)

```
pending_upload → queued → processing → completed
                                     → failed
```

### Meeting Sub-Status (unchanged)

```
downloading → transcribing → aligning → diarizing → summarizing
```

Note: With Chirp 3, the "aligning" and "diarizing" sub-statuses are handled
internally by the provider (Chirp 3 returns aligned + diarized results in one
call). The sub-status will transition directly from "transcribing" to
"summarizing" when using ChirpProvider.

### Circuit Breaker State

```
CLOSED ──(failure #N reaches threshold)──→ OPEN
OPEN ──(cooldown expires)──→ CLOSED
OPEN ──(request arrives during cooldown)──→ route to fallback (stay OPEN)
CLOSED ──(success)──→ CLOSED (reset counter)
```

---

## Entity Relationships

```
User (1) ──→ (N) Meeting
Meeting (1) ──→ (N) TranscriptSegment

TranscriptionProvider.process_audio() ──→ TranscriptionResult
  ├── WhisperProvider (whisperx pipeline → TranscriptionResult)
  └── ChirpProvider (GCS upload → BatchRecognize → TranscriptionResult)

TranscriptionResult ──(mapped by worker)──→ TranscriptSegment[] + Meeting.transcript_text

TranscriptionProviderFactory
  ├── reads: settings.TRANSCRIPTION_PROVIDER
  ├── reads: User.tier
  ├── reads: CircuitBreakerState
  └── returns: TranscriptionProvider instance
```
