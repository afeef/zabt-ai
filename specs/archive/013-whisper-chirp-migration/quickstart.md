# Quickstart: Whisper-to-Chirp Transcription Migration

**Feature**: 013-whisper-chirp-migration
**Date**: 2026-02-28

## Prerequisites

- Google Cloud project with billing enabled
- Google Cloud Speech-to-Text API enabled
- Google Cloud Storage bucket for audio staging
- Service account with required permissions

## 1. Google Cloud Setup

### Create GCS Bucket (audio staging)

```bash
gcloud storage buckets create gs://zabt-audio-staging \
  --location=us-central1 \
  --uniform-bucket-level-access

# Set 7-day lifecycle policy for auto-cleanup
cat > /tmp/lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 7}
    }
  ]
}
EOF
gcloud storage buckets update gs://zabt-audio-staging \
  --lifecycle-file=/tmp/lifecycle.json
```

### Create Service Account

```bash
gcloud iam service-accounts create zabt-transcription \
  --display-name="Zabt Transcription Service"

# Grant required roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:zabt-transcription@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/speech.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:zabt-transcription@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Download key (for local dev / Docker)
gcloud iam service-accounts keys create /path/to/zabt-sa-key.json \
  --iam-account=zabt-transcription@$PROJECT_ID.iam.gserviceaccount.com
```

### Local Development (ADC)

```bash
gcloud auth application-default login
# OR
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/zabt-sa-key.json
```

## 2. Environment Variables

### New Variables (add to `.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | — | GCP project ID |
| `GCS_AUDIO_BUCKET` | Yes | — | GCS bucket for audio staging (e.g., `zabt-audio-staging`) |
| `GCS_REGION` | No | `us-central1` | GCS/Speech API region |
| `GOOGLE_APPLICATION_CREDENTIALS` | Prod only | — | Path to service account JSON key |
| `TRANSCRIPTION_PROVIDER` | No | `whisper` | Active provider: `whisper` or `chirp` |
| `CHIRP_MODEL` | No | `chirp_3` | Chirp model identifier |
| `DIARIZATION_MIN_SPEAKERS` | No | `1` | Min speakers for diarization |
| `DIARIZATION_MAX_SPEAKERS` | No | `10` | Max speakers for diarization |
| `CIRCUIT_BREAKER_THRESHOLD` | No | `5` | Consecutive failures before fallback |
| `CIRCUIT_BREAKER_COOLDOWN_SECONDS` | No | `300` | Seconds to stay in fallback mode |

### Existing Variables (unchanged)

| Variable | Description |
|----------|-------------|
| `WHISPER_MODEL` | Whisper model size (used by WhisperProvider fallback) |
| `TRANSCRIPTION_DEVICE` | `auto` / `cuda` / `cpu` |
| `HF_AUTH_TOKEN` | Hugging Face token for pyannote diarization |
| `MINIO_ENDPOINT` | MinIO S3 endpoint |

### Example `.env` Addition

```env
# Google Cloud (Chirp 3 migration)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GCS_AUDIO_BUCKET=zabt-audio-staging
GCS_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/zabt-sa-key.json
TRANSCRIPTION_PROVIDER=whisper
```

## 3. Install Dependencies

```bash
cd backend
uv add google-cloud-speech google-cloud-storage
uv sync
```

## 4. Docker Compose Updates

Add these environment variables to the `api` and `worker` services in
`docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GCS_AUDIO_BUCKET=${GCS_AUDIO_BUCKET}
      - GCS_REGION=${GCS_REGION:-us-central1}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-key.json
      - TRANSCRIPTION_PROVIDER=${TRANSCRIPTION_PROVIDER:-whisper}
    volumes:
      - ./zabt-sa-key.json:/app/gcp-key.json:ro

  worker:
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GCS_AUDIO_BUCKET=${GCS_AUDIO_BUCKET}
      - GCS_REGION=${GCS_REGION:-us-central1}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-key.json
      - TRANSCRIPTION_PROVIDER=${TRANSCRIPTION_PROVIDER:-whisper}
    volumes:
      - ./zabt-sa-key.json:/app/gcp-key.json:ro
```

## 5. Feature Flag (Migration Control)

### Default (no change)
```env
TRANSCRIPTION_PROVIDER=whisper
```
All transcription uses existing Whisper pipeline. Zero risk.

### Activate Chirp 3
```env
TRANSCRIPTION_PROVIDER=chirp
```
All transcription routes through ChirpProvider (with circuit breaker fallback
to Whisper on failures).

### Rollback
Set `TRANSCRIPTION_PROVIDER=whisper` and restart services. Instant rollback,
no code changes required.

## 6. Verify Setup

```bash
# Test GCS access
python -c "
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('zabt-audio-staging')
print(f'Bucket exists: {bucket.exists()}')
"

# Test Speech API access
python -c "
from google.cloud.speech_v2 import SpeechClient
from google.api_core.client_options import ClientOptions
client = SpeechClient(
    client_options=ClientOptions(api_endpoint='us-central1-speech.googleapis.com')
)
print('Speech client initialized successfully')
"

# Test health endpoint (after deployment)
curl http://localhost:8000/api/v1/health/transcription
```

## 7. Cost Reference

| Tier | Method | Rate/min | 1-hour cost |
|------|--------|----------|-------------|
| Starter (FREE) | Dynamic Batch | $0.004 | $0.24 |
| Pro (PRO) | Standard Batch | $0.016 | $0.96 |
| Business (ENTERPRISE) | Streaming | $0.016 | $0.96 |
| Whisper (fallback) | Local WhisperX | $0.006 | $0.36 |
| Google Free Tier | Any | $0.00 | First 60 min/month |
