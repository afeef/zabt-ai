# Implementation Plan: Whisper-to-Chirp Transcription Migration

**Branch**: `013-whisper-chirp-migration` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-whisper-chirp-migration/spec.md`

## Summary

Migrate the transcription backend from OpenAI Whisper (local WhisperX pipeline) to
Google Cloud Speech-to-Text V2 API using the Chirp 3 model. The migration introduces
a provider abstraction layer (Constitution Principle IX) enabling both providers to
coexist behind a shared `TranscriptionProvider` Protocol. The Whisper implementation
is retained as a permanent fallback (Constitution Principle XI) with a circuit breaker
for automatic failover. Subscription tier determines the recognition method:
Dynamic Batch (Starter), Standard Batch (Pro), or Streaming (Business) — defaulting
to the cheapest path (Constitution Principle X).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, SQLModel, Celery (Redis broker), google-cloud-speech (V2),
google-cloud-storage, pydantic-settings, openai-whisper (fallback), whisperx (fallback)
**Storage**: PostgreSQL (via SQLModel, unchanged), MinIO (audio uploads, unchanged),
Google Cloud Storage (new — audio staging for Chirp 3 BatchRecognize)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Docker, NVIDIA CUDA optional for Whisper fallback)
**Project Type**: Web service (backend API + Celery worker + CLI)
**Performance Goals**: Batch transcription for files up to 4 hours; streaming for
sessions up to 5 minutes (V2 API limit)
**Constraints**: Chirp 3 GA in `us`, `eu`, `us-central1` only; diarization limited
to 14 languages; billing per 15-second increment; Dynamic Batch may take up to 24 hours
**Scale/Scope**: Same user scale as existing system; migration is backend-only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Applies? | Status | Notes |
|------|----------|--------|-------|
| Design System | No | N/A | No UI changes — backend-only migration |
| API Contract | Yes | PASS | Health check endpoint documented in `contracts/health-transcription.md`. Existing endpoints unchanged (FR-006). |
| Auth/Security | Yes | PASS | GCS service account credentials via env vars. No hardcoded secrets. Documented in `quickstart.md`. |
| Env Config | Yes | PASS | 10 new env vars documented in `quickstart.md` (GOOGLE_CLOUD_PROJECT, GCS_AUDIO_BUCKET, etc.) |
| Scope Boundary | Yes | PASS | Implementation limited to transcription provider swap. No frontend, DB schema, or summarization changes. |
| E2E Testing | No | N/A | No user-facing UI flow changes. Backend integration tests cover the migration. |
| Repository Pattern | Yes | PASS | Worker still uses session-based DB access via existing pattern. No new direct session use. |
| CLI/Typer | Yes | PASS | Existing CLI (`app/cli/transcribe.py`) updated to use provider abstraction. Remains Typer-based. |
| Provider Abstraction | Yes | PASS | `TranscriptionProvider` Protocol defined in `backend/app/services/transcription/provider.py`. Factory pattern in `factory.py`. No direct SDK imports in consumer code. |
| Cost Awareness | Yes | PASS | Default: Dynamic Batch ($0.004/min). Standard/Streaming only for PRO/ENTERPRISE. Documented in `quickstart.md` cost reference and spec FR-003. |
| Migration Safety | Yes | PASS | WhisperProvider retained permanently. Feature flag `TRANSCRIPTION_PROVIDER`. Circuit breaker for auto-fallback. Validation criteria in `research.md` section 10. |

## Project Structure

### Documentation (this feature)

```text
specs/013-whisper-chirp-migration/
├── plan.md                # This file
├── spec.md                # Feature specification
├── research.md            # Phase 0: Google V2 API research + spec corrections
├── data-model.md          # Phase 1: Domain types (no DB changes)
├── quickstart.md          # Phase 1: Environment setup guide
├── contracts/
│   └── health-transcription.md  # New health check endpoint
├── checklists/
│   └── requirements.md    # Spec quality checklist
└── tasks.md               # Phase 2: Task list (from /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── services/
│   │   ├── transcription/              # NEW: Provider abstraction package
│   │   │   ├── __init__.py             # Exports get_provider(), types
│   │   │   ├── provider.py             # TranscriptionProvider Protocol
│   │   │   ├── types.py                # TranscriptionResult, ResultSegment, WordTimestamp
│   │   │   ├── whisper_provider.py     # WhisperProvider (moved from transcription.py)
│   │   │   ├── chirp_provider.py       # ChirpProvider (new)
│   │   │   ├── factory.py              # TranscriptionProviderFactory
│   │   │   ├── circuit_breaker.py      # CircuitBreaker state machine
│   │   │   └── cost_logger.py          # Structured cost logging
│   │   ├── gcs_storage.py              # NEW: GCS upload/delete service
│   │   ├── storage.py                  # UNCHANGED: MinIO S3 service
│   │   └── ...                         # Other services unchanged
│   ├── core/
│   │   └── config.py                   # MODIFIED: New GCS + Chirp settings
│   ├── worker.py                       # MODIFIED: Uses provider abstraction
│   ├── cli/
│   │   └── transcribe.py              # MODIFIED: Uses provider abstraction
│   ├── api/v1/endpoints/
│   │   ├── transcriptions.py          # MODIFIED: Uses provider abstraction
│   │   └── health.py                  # NEW: Provider health check
│   └── models.py                      # UNCHANGED (FR-014)
└── tests/
    ├── unit/
    │   ├── test_whisper_provider.py     # NEW
    │   ├── test_chirp_provider.py       # NEW
    │   ├── test_circuit_breaker.py      # NEW
    │   └── test_provider_factory.py     # NEW
    └── integration/
        ├── test_chirp_pipeline.py       # NEW
        └── test_circuit_breaker_fallback.py  # NEW
```

**Structure Decision**: Web application pattern (backend/ only). Frontend unchanged.
New code organized as a `transcription/` package within existing `services/` directory.
Old `transcription.py` replaced by the package.

## Research Findings (Key Corrections)

Research revealed several discrepancies between spec assumptions and actual API behavior.
These are documented in detail in [research.md](research.md) section 10.

| Item | Spec Assumption | Actual (Researched) | Action |
|------|----------------|---------------------|--------|
| Dynamic Batch cost | $0.003/min | $0.004/min | Update cost estimates; savings = 33%, not 50% |
| Billing granularity | 1-second increments | 15-second increments | Minor impact; update cost calculation logic |
| Diarization languages | 85+ | 14 | Document as known limitation; does not block |
| Speaker field (V2) | `speaker_tag` (int) | `speaker_label` (str) | Normalization layer maps to `SPEAKER_{label}` |
| Standard Batch cost | ~$0.006/min | $0.016/min | Pro tier costs more than Whisper per-minute |
| Streaming max duration | Unlimited | 5 minutes per stream | Must reconnect for longer sessions |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Standard Batch costs more than Whisper | Pro users pay $0.016/min vs $0.006/min Whisper | Justified by faster turnaround + native diarization + language detection. Platform charges Pro users $0.96/hr, covering the $0.016/min cost. The value proposition is speed and features, not per-minute savings. |
| GCS as second storage layer | Audio must be in GCS for BatchRecognize | Using MinIO as source and direct-streaming to Chirp was considered but BatchRecognize requires `gs://` URIs for files >1 min. GCS staging with 7-day lifecycle policy minimizes cost and privacy risk. |
