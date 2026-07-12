# Data Model: 017 — Transcription Progress Tracking

**Date**: 2026-03-03
**Feature**: [spec.md](spec.md)

## Entity Changes

### Meeting (existing — modified)

No new columns. The existing `sub_status` field is already stored in PostgreSQL but not exposed in the API response schema.

**Changes**:
1. **`MeetingRead` response schema**: Add `sub_status: Optional[str] = None` field to expose the processing stage to the frontend.
2. **`summary_text` usage**: Stop writing `[System: ...]` progress messages to `summary_text` during processing. Leave it as `None` until the summarization stage produces the actual summary.

**Existing fields used by this feature**:

| Field | Type | Purpose in this feature |
| --- | --- | --- |
| `status` | `str` | High-level state: `pending_upload`, `queued`, `processing`, `completed`, `failed` |
| `sub_status` | `Optional[str]` | Granular processing stage: `downloading`, `validating`, `extracting_audio`, `uploading`, `transcribing`, `aligning`, `diarizing`, `parsing`, `cleaning_up`, `summarizing` |
| `summary_text` | `Optional[str]` | **No longer used for progress messages**. Only holds the final AI-generated summary after processing completes. |

### State Machine

```
                    ┌──────────────┐
                    │pending_upload│
                    └──────┬───────┘
                           │ (MinIO webhook)
                    ┌──────▼───────┐
                    │   queued     │
                    └──────┬───────┘
                           │ (Celery picks up → stage_download)
                    ┌──────▼───────┐
                    │  processing  │ sub_status: downloading
                    │              │ sub_status: validating
                    │              │ sub_status: extracting_audio
                    │              │ sub_status: transcribing
                    │              │ sub_status: aligning
                    │              │ sub_status: diarizing
                    │              │ sub_status: parsing
                    │              │ sub_status: summarizing
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
         ┌──────▼───────┐     ┌───────▼──────┐
         │  completed   │     │   failed     │
         └──────────────┘     └──────────────┘
```

### User-Visible Stage Mapping (frontend concern)

The frontend maps `status` + `sub_status` to 5 user-visible stages:

| User Stage | Condition |
| --- | --- |
| Uploaded | `status` in `[pending_upload, queued]` OR `sub_status` in `[downloading, validating, extracting_audio]` |
| Transcribing | `sub_status` in `[uploading, transcribing]` |
| Aligning | `sub_status == "aligning"` |
| Diarizing | `sub_status` in `[diarizing, parsing]` |
| Done | `status == "completed"` OR `sub_status` in `[cleaning_up, summarizing]` |

## No New Tables

This feature does not require new database tables. The existing `meeting` table already stores all necessary state via `status` and `sub_status` columns.
