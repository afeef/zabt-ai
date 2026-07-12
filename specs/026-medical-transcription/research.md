# Research: Transcription Type Selection (Normal + Medical)

## Decision 1: Medical ASR Model

**Decision**: Google MedASR (`google/medasr`) — open-source Conformer model, 105M parameters

**Rationale**:
- 5x better WER than Whisper on medical audio (4.6% vs 25.3% on radiology dictation)
- Open-source (Apache 2.0), available on Hugging Face
- Small model (105M params) — fits alongside WhisperX on a single RTX 3090 (24GB VRAM)
- Purpose-built for medical dictation and conversation
- No cloud API dependency — fully self-hosted on existing RunPod infrastructure

**Alternatives considered**:
- Deepgram Nova-3 Medical: Cloud API, good accuracy, but adds per-minute cost and external dependency
- Google Cloud Speech Medical: Cloud API, requires GCS staging, expensive ($0.016/min), rejected complexity
- Whisper fine-tuned (medical): Requires medical training data (HIPAA-protected), impractical
- AWS Transcribe Medical: Cloud API, English-only, mid-range pricing, adds AWS dependency

## Decision 2: MedASR Integration Approach

**Decision**: Add MedASR as a second model in the GPU worker pipeline, routing based on `transcription_type` job input field

**Rationale**:
- MedASR uses NeMo/Conformer architecture — inference via `nemo.collections.asr`
- Same pipeline structure: transcribe → align → diarize
- Diarization still uses pyannote (MedASR doesn't include diarization)
- Alignment step may differ — MedASR outputs word-level timestamps natively (CTC-based), may not need WhisperX alignment
- Output normalized to same JSON schema as WhisperX

**Alternatives considered**:
- Separate RunPod endpoint for medical: Adds operational complexity, duplicates infrastructure
- Separate Docker image: Increases build/maintenance burden for minimal benefit

## Decision 3: Frontend Selector Pattern

**Decision**: shadcn/ui RadioGroup with two options (Normal / Medical) in the upload modal and YouTube URL dialog

**Rationale**:
- Only two options — RadioGroup is more appropriate than Select/Dropdown
- Visible without interaction (no click to see options)
- Defaults to "Normal" — existing users see no friction
- shadcn/ui compliant per constitution

## Decision 4: Database Schema

**Decision**: Add `transcription_type` VARCHAR column to `meeting` table with default `"general"`

**Rationale**:
- Simple string enum rather than foreign key to a models table
- Only two values now; easily extensible if more models added later
- Default ensures backward compatibility for existing records
- Alembic migration with server_default for zero-downtime deployment

## Decision 5: Docker Build Strategy

**Decision**: Multi-stage build with base image on Docker Hub, uv/pyproject.toml for dependency management

**Rationale**:
- CUDA + PyTorch download is ~5GB and takes 60+ minutes — caching in a base image eliminates re-downloading on every code change
- `Dockerfile.base`: FROM nvidia/cuda:12.8.1 → install Python 3.11, uv, PyTorch. Build once, push to Docker Hub.
- `Dockerfile`: FROM base image → copy pyproject.toml/uv.lock → `uv sync` for ML deps → COPY source → download models
- Source-only changes rebuild in seconds; dependency changes rebuild in 2-5 minutes
- uv/pyproject.toml gives reproducible builds with lockfile

**Alternatives considered**:
- Single Dockerfile with layer caching: Fragile across CI/CD; doesn't help with RunPod's builder
- Raw pip install: No lockfile, non-reproducible builds

## Decision 6: Enum Naming

**Decision**: Use `"general"` (not `"normal"`) for the default transcription type

**Rationale**:
- "General purpose" is more descriptive than "normal"
- Avoids implying medical is "abnormal"
- `TranscriptionType.GENERAL` and `TranscriptionType.MEDICAL` are clear, professional enum values
