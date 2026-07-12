# Quickstart: Transcription Worker Provider Switch

## Environment Variables

### New Variables

| Variable | Required When | Default | Description |
|----------|--------------|---------|-------------|
| `TRANSCRIPTION_PROVIDER` | Always | `local` | Transcription backend: `local` (WhisperX on worker) or `runpod` (RunPod Serverless) |
| `RUNPOD_API_KEY` | `TRANSCRIPTION_PROVIDER=runpod` | — | RunPod API key from dashboard |
| `RUNPOD_ENDPOINT_ID` | `TRANSCRIPTION_PROVIDER=runpod` | — | RunPod Serverless endpoint ID |
| `RUNPOD_POLL_INTERVAL` | Optional | `5` | Seconds between status polls |
| `RUNPOD_TIMEOUT` | Optional | `1800` | Maximum seconds to wait for RunPod job completion |

### Existing Variables (unchanged)

| Variable | Used By | Notes |
|----------|---------|-------|
| `WHISPER_MODEL` | Local provider only | Model size for local WhisperX (e.g., `large-v3`) |
| `HF_AUTH_TOKEN` | Local provider only | HuggingFace token for pyannote diarization |
| `DIARIZATION_MODEL` | Local provider only | pyannote model name |
| `TRANSCRIPTION_DEVICE` | Local provider only | `auto`, `cuda`, or `cpu` |

## Configuration Scenarios

### Local Development (GPU)

```env
# .env
TRANSCRIPTION_PROVIDER=local  # or omit — local is the default
```

```bash
COMPOSE_PROFILES=local docker compose up -d
```

Worker-gpu runs WhisperX + pyannote locally with CUDA. No RunPod credentials needed.

### VPS Deployment (no GPU)

```env
# .env
TRANSCRIPTION_PROVIDER=runpod
RUNPOD_API_KEY=rp_xxxxxxxxxxxxxxxx
RUNPOD_ENDPOINT_ID=abc123def456
```

```bash
COMPOSE_PROFILES=vps docker compose up -d
```

Worker delegates transcription to RunPod Serverless. No local ML models needed.

## RunPod Endpoint Setup

1. Build and push the handler image from `runpod/`:
   ```bash
   cd runpod
   docker build -t your-registry/zabt-runpod-whisper:latest .
   docker push your-registry/zabt-runpod-whisper:latest
   ```

2. Create a Serverless endpoint on RunPod dashboard:
   - Image: `your-registry/zabt-runpod-whisper:latest`
   - GPU: A40 or better (24GB+ VRAM for large-v3 + pyannote)
   - Min workers: 0 (scale to zero when idle)
   - Max workers: 1-3 (based on expected concurrency)
   - Idle timeout: 5 minutes

3. Copy the endpoint ID and your API key to `.env`.
