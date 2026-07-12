# Research: Whisper-to-Chirp Transcription Migration

**Feature**: 013-whisper-chirp-migration
**Date**: 2026-02-28

## 1. Google Cloud Speech-to-Text V2 SDK (Python)

**Decision**: Use `google-cloud-speech` PyPI package (v2.37+), importing from
`google.cloud.speech_v2`.

**Rationale**: The V2 module (`google.cloud.speech_v2`) provides the `SpeechClient`
and typed request/response objects for Chirp 3. The V1 module
(`google.cloud.speech`) does NOT support Chirp 3.

**Alternatives considered**:
- REST API directly (rejected — SDK handles LRO polling, auth, retries natively)
- V1 SDK with beta features (rejected — V2 is GA and Chirp 3 is V2-only)

**Key imports**:
```python
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions
```

**Client instantiation** (regional endpoint required for Chirp 3):
```python
client = SpeechClient(
    client_options=ClientOptions(
        api_endpoint=f"{REGION}-speech.googleapis.com",
    )
)
```

---

## 2. BatchRecognize API

**Decision**: Use `BatchRecognize` with `InlineOutputConfig` for results returned
directly in the response (no GCS output step needed).

**Rationale**: Inline output avoids a second GCS read step. For files up to 8 hours,
inline results are returned as part of the LRO response.

### RecognitionConfig for Chirp 3

```python
config = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    language_codes=["auto"],  # auto-detect (Chirp 3 only)
    model="chirp_3",
    features=cloud_speech.RecognitionFeatures(
        enable_word_time_offsets=True,
        enable_word_confidence=True,
        diarization_config=cloud_speech.SpeakerDiarizationConfig(),
    ),
)
```

### Dynamic Batching

```python
request = cloud_speech.BatchRecognizeRequest(
    recognizer=f"projects/{PROJECT_ID}/locations/{REGION}/recognizers/_",
    config=config,
    files=[cloud_speech.BatchRecognizeFileMetadata(uri=gcs_uri)],
    recognition_output_config=cloud_speech.RecognitionOutputConfig(
        inline_response_config=cloud_speech.InlineOutputConfig(),
    ),
    processing_strategy=cloud_speech.BatchRecognizeRequest.ProcessingStrategy.DYNAMIC_BATCHING,
)
```

For **standard batch**, omit the `processing_strategy` field entirely.

### LRO Polling

```python
operation = client.batch_recognize(request=request)
response = operation.result(timeout=3600)  # blocks until done
```

### Response Access Pattern

```python
file_result = response.results[gcs_uri]
for result in file_result.transcript.results:
    alt = result.alternatives[0]
    for word in alt.words:
        word.word           # str: the word
        word.start_offset   # timedelta
        word.end_offset     # timedelta
        word.speaker_label  # str: e.g., "1", "2" (V2 uses speaker_label, NOT speaker_tag)
        word.confidence     # float (note: not a true confidence score per docs)
```

---

## 3. Speaker Diarization

**Decision**: Enable diarization by providing an empty `SpeakerDiarizationConfig()`
in the RecognitionFeatures. Do NOT set `min_speaker_count` / `max_speaker_count`
unless the user explicitly provides them — Chirp 3 auto-detects speaker count.

**Rationale**: In V2 with Chirp 3, an empty config is sufficient. The model handles
speaker count automatically. Setting counts constrains the model unnecessarily.

**SPEC CORRECTION NEEDED**: The spec states diarization supports 85+ languages.
Research shows diarization with Chirp 3 only supports **14 languages**. Transcription
supports 100+ languages, but diarization is limited. This does not block the
migration but should be documented as a known limitation.

**V2 vs V1 difference**: V1 used `speaker_tag` (int). V2 uses `speaker_label` (str).
The normalization layer must map `speaker_label` → `"SPEAKER_{label}"` format
to match existing Whisper output convention (`"SPEAKER_00"`, `"SPEAKER_01"`, etc.).

---

## 4. Automatic Language Detection

**Decision**: Use `language_codes=["auto"]` for automatic detection.

**Rationale**: Chirp 3 is the only model that supports true `["auto"]` detection.
Other V2 models require an explicit list of up to 3 BCP-47 codes.

**Detected language in response**: Available via `result.language_code` on each
`SpeechRecognitionResult`.

---

## 5. StreamingRecognize

**Decision**: Use V2 `StreamingRecognize` for Business-tier real-time captions.

**Key constraints**:
- **Max duration**: 5 minutes per stream (must reconnect for longer sessions)
- **Chunk size**: Each request limited to 25 KB
- **First request**: Carries `StreamingRecognitionConfig` (no audio)
- **Subsequent requests**: Carry raw audio bytes only

**Interim vs final results**:
- `result.is_final`: True for settled results
- `result.stability`: Float 0-1 for interim confidence
- Word-level timestamps only available in final results

```python
streaming_config = cloud_speech.StreamingRecognitionConfig(
    config=recognition_config,
    streaming_features=cloud_speech.StreamingRecognitionFeatures(
        interim_results=True,
    ),
)
```

---

## 6. Pricing (Corrected)

**SPEC CORRECTION NEEDED**: The spec states Dynamic Batch costs $0.003/min.
Current published pricing is **$0.004/min**.

| Method | Rate/min | Notes |
|--------|----------|-------|
| Dynamic Batching | $0.004 | 75% discount; results within 24 hours |
| Standard Batch | $0.016 | Near-instant results |
| Streaming | $0.016 | Same as standard |
| Free tier | $0.00 | 60 minutes/month (ongoing) |

**Billing granularity**: Per **15-second** increment, rounded up.
**SPEC CORRECTION NEEDED**: The spec states "V2 API rounds to 1-second increments."
This is incorrect — billing is per 15-second increment.

**Cost comparison** (corrected):

| Provider | Method | Rate/min | 1-hour cost |
|----------|--------|----------|-------------|
| Whisper (current) | API | $0.006 | $0.36 |
| Chirp 3 | Dynamic Batch | $0.004 | $0.24 |
| Chirp 3 | Standard | $0.016 | $0.96 |

**Savings**: Dynamic Batch is ~33% cheaper than Whisper (not 50% as spec states).
Standard Batch is ~2.7x more expensive than Whisper.

---

## 7. Constraints and Limits

| Constraint | Value |
|-----------|-------|
| Max audio (Batch) | 8 hours per file, 15 files per request |
| Max audio (Streaming) | 5 minutes per stream |
| Max audio (Sync Recognize) | 1 minute or 10 MB |
| Batch requests/min | 150 per region |
| Streaming sessions | 300 concurrent per region |
| Supported formats | WAV, FLAC, MP3, OGG_OPUS, WEBM_OPUS, MP4_AAC, M4A_AAC, MOV_AAC, AMR |
| Auto decoding | Yes (`AutoDetectDecodingConfig`) |
| Chirp 3 regions (GA) | `us`, `eu`, `us-central1` |
| Diarization languages | 14 (not 85+) |

---

## 8. Existing Backend Architecture

**Decision**: Extend existing architecture patterns (singleton services, Celery worker,
BaseService repository pattern). Introduce provider abstraction as a new package.

### Current Transcription Flow
```
MinIO webhook → process_meeting (Celery) → TranscriptionService.process_audio()
  → Stage 1: whisper.load_model().transcribe()
  → Stage 2: whisperx.align()
  → Stage 3: whisperx.DiarizationPipeline()
→ Store TranscriptSegments → AI summarization
```

### Key Architecture Facts
- **Services**: Module-level singletons (no DI container)
- **Config**: `pydantic-settings` BaseSettings, env vars from `.env`
- **Task queue**: Celery with Redis broker
- **DB**: PostgreSQL 16 via SQLModel (sync engine)
- **Storage**: MinIO via boto3 (`S3StorageService`)
- **Auth**: Supabase JWT (JWKS + HS256 fallback), JIT user provisioning
- **CLI**: Typer, registered as `zabt` command
- **Tests**: pytest + pytest-asyncio, test fixtures in `conftest.py`
- **Docker**: NVIDIA CUDA base image, uv package manager

### Current Dependencies (transcription-related)
- `openai-whisper>=20250625`
- `whisperx>=3.8.1`
- `pyannote-audio>=4.0.4`
- `torch` (implicit, via whisperx)

### Tier Model (existing but unenforced)
- `UserTier`: FREE, PRO, ENTERPRISE
- `minutes_used_this_month`: Field exists on User, never incremented
- `Subscription` model exists with Stripe fields (mocked)

---

## 9. GCS Integration Pattern

**Decision**: Use `google-cloud-storage` SDK with Application Default Credentials.
Create a `GCSStorageService` in `backend/app/services/gcs_storage.py`.

**Rationale**: Consistent with existing `S3StorageService` pattern. ADC avoids
hardcoding service account keys.

**Lifecycle policy**: Set 7-day auto-delete on the GCS bucket for cost + privacy.
Audio files are only needed for the duration of the batch transcription job.

**Auth for local dev**: `gcloud auth application-default login`
**Auth for production**: `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to
service account JSON, or Workload Identity on GKE/Cloud Run.

---

## 10. Spec Corrections Summary

| Item | Spec States | Research Finds | Impact |
|------|-------------|----------------|--------|
| Dynamic Batch cost | $0.003/min | $0.004/min | Cost savings = 33%, not 50% |
| Billing granularity | 1-second | 15-second | Minor cost increase for short files |
| Diarization languages | 85+ | 14 | Diarization unavailable for most languages |
| Speaker field name | `speaker_tag` | `speaker_label` (str) | Code must use correct field |
| Standard Batch cost | $0.006/min (Chirp) | $0.016/min | Standard is 2.7x more than Whisper |
