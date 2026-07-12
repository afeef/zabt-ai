# Quickstart: GPU Worker Extraction

## Environment Variables

### Main Worker (zabt-ai)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRANSCRIPTION_PROVIDER` | Yes | `runpod` | Provider: `runpod` or `gpu-local` |
| `RUNPOD_API_KEY` | If runpod | — | RunPod API key |
| `RUNPOD_ENDPOINT_ID` | If runpod | — | RunPod endpoint ID |
| `RUNPOD_POLL_INTERVAL` | No | `5` | Poll interval in seconds |
| `RUNPOD_TIMEOUT` | No | `1800` | Job timeout in seconds |
| `GPU_SERVICE_URL` | If gpu-local | — | Local GPU service URL (e.g., `http://gpu-worker:8001`) |

### GPU Service (zabt-gpu-worker)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODE` | Yes | `runpod` | Entry point: `runpod` or `local` |
| `WHISPER_MODEL` | No | `large-v3` | WhisperX model name |
| `DIARIZATION_MODEL` | No | `pyannote/speaker-diarization-3.1` | Diarization model |
| `HF_AUTH_TOKEN` | Yes | — | Hugging Face token (for pyannote) |
| `SENTRY_DSN` | No | — | Sentry DSN for error tracking |
| `SENTRY_ENVIRONMENT` | No | `production` | Sentry environment tag |
| `PORT` | No | `8001` | HTTP port (local mode only) |

## Local Development

```bash
# 1. Start GPU service in local mode
cd zabt-gpu-worker
docker build -t zabt-gpu-worker .
docker run --gpus all -e MODE=local -e HF_AUTH_TOKEN=hf_xxx -p 8001:8001 zabt-gpu-worker

# 2. Configure main worker
export TRANSCRIPTION_PROVIDER=gpu-local
export GPU_SERVICE_URL=http://localhost:8001

# 3. Start main worker
cd zabt-ai/backend
celery -A app.worker.celery_app worker --loglevel=info
```

## RunPod Deployment

```bash
# 1. Build and push GPU image
cd zabt-gpu-worker
docker build -t your-registry/zabt-gpu-worker:latest .
docker push your-registry/zabt-gpu-worker:latest

# 2. Create RunPod serverless endpoint pointing to the image
# Set env vars: MODE=runpod, HF_AUTH_TOKEN, SENTRY_DSN

# 3. Configure main worker
export TRANSCRIPTION_PROVIDER=runpod
export RUNPOD_API_KEY=rp_xxx
export RUNPOD_ENDPOINT_ID=abc123
```

## Rollback

If the GPU service has issues, temporarily revert by:
1. Restoring `whisper_provider.py` and `pipeline.py` from git history
2. Re-adding the `ml` dependency group to `pyproject.toml`
3. Setting `TRANSCRIPTION_PROVIDER=local`
4. Rebuilding with the worker-base Dockerfile
