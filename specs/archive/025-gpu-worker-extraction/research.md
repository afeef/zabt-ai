# Research: GPU Worker Extraction

## R1: Dual-Mode Entry Point Strategy

**Decision**: Single Docker image with entrypoint switching via `MODE` env var.
**Rationale**: `MODE=runpod` starts the RunPod handler; `MODE=local` starts a FastAPI HTTP server. Both call the same `run_pipeline()` function. This eliminates image divergence and ensures identical behavior.
**Alternatives considered**:
- Separate Dockerfiles per mode — rejected (code duplication, test divergence)
- CMD override at runtime — rejected (less explicit than env var)

## R2: Model Baking Strategy

**Decision**: Run `download_models.py` during Docker build to download and cache WhisperX + pyannote models into the image layer.
**Rationale**: Eliminates cold-start model downloads. RunPod workers start with models already in memory (just GPU load). Image is ~10 GB but builds once and caches.
**Alternatives considered**:
- Volume-mount models — rejected (adds deployment complexity, version drift risk)
- Download on first request — rejected (30-60s cold start per container, unacceptable)

## R3: Local HTTP Server API Design

**Decision**: FastAPI server that mirrors RunPod's `/run` and `/status/{job_id}` pattern.
**Rationale**: The main worker's `gpu_client.py` uses the same submit/poll code path regardless of backend. Local server uses in-memory job tracking (dict of job_id → status/result).
**Alternatives considered**:
- Synchronous endpoint (POST → wait → response) — rejected (doesn't match RunPod's async pattern, would need two code paths in client)
- gRPC — rejected (overkill for single-consumer service)

## R4: Unified Client Architecture

**Decision**: Single `GpuTranscriptionClient` class with `backend` config (`runpod` or `local`). For RunPod, uses RunPod SDK. For local, uses httpx HTTP calls. Both expose `submit_job()` → `poll_status()` → `get_result()`.
**Rationale**: Implements `TranscriptionProvider` protocol. Factory function selects based on `TRANSCRIPTION_PROVIDER` env var (values: `runpod` or `gpu-local`).
**Alternatives considered**:
- Keep separate RunPodProvider and LocalGpuProvider — rejected (duplicates poll logic, doesn't achieve unified protocol goal)

## R5: Sentry in Ephemeral Containers

**Decision**: `sentry_sdk.init()` at handler/server startup. `sentry_sdk.flush(timeout=5)` before handler return. Environment tag differentiates RunPod vs local.
**Rationale**: RunPod serverless containers are ephemeral — events must be flushed before the process exits. 5-second flush timeout balances reliability vs latency.
**Alternatives considered**:
- Skip Sentry in RunPod — rejected (most failure-prone environment, needs monitoring most)

## R6: Removing ML Dependencies from Main Worker

**Decision**: Remove the `ml` dependency group from `backend/pyproject.toml`. Delete `whisper_provider.py`, `pipeline.py`, and `Dockerfile.worker-base`. The worker Dockerfile becomes a single lightweight target.
**Rationale**: The main worker on VPS uses `TRANSCRIPTION_PROVIDER=runpod` — it never runs local transcription. All GPU code moves to the new repo. The `runpod_provider.py` is replaced by the unified `gpu_client.py`.
**Alternatives considered**:
- Keep WhisperProvider as fallback — initially keep the code but remove from deps; can re-add if needed. Migration safety gate satisfied by validating GPU service before removing old code.
