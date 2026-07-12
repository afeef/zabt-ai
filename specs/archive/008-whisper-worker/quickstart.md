# Quickstart: WhisperX Backend & MinIO Local Environment

This guide covers setting up the new background transcription queue and local object storage.

## 1. Environment Configuration

You must add the following variables to your backend `.env` file to support the Celery worker and MinIO S3-compatibility layer:

```dotenv
# MinIO Local Storage Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=zabt-media
MINIO_SECURE=false # Set to true in production with valid TLS

# WhisperX Machine Learning Configuration
WHISPER_MODEL=base.en  # Use 'large-v3' for production accuracy
TRANSCRIPTION_DEVICE=auto  # Set to 'cuda' or 'cpu' explicitly if needed

# IMPORTANT: Required for Speaker Diarization
# You MUST accept the Pyannote terms of service on HuggingFace:
# 1. https://huggingface.co/pyannote/segmentation-3.0
# 2. https://huggingface.co/pyannote/speaker-diarization-3.1
HF_AUTH_TOKEN=your_huggingface_read_token_here
```

## 2. Running Local MinIO

If you are not using AWS S3 locally, start the MinIO container to simulate it:
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```
After booting, navigate to `http://localhost:9001` and create a bucket named `zabt-media`.

## 3. Starting the Celery Worker

The FastAPI server (`npm run dev` or `fastapi run`) handles serving the Presigned URLs to the UI. However, the background transcription requires the Celery daemon to be active:

```bash
cd backend
# Depending on your environment (ensure Redis is running on localhost:6379)
celery -A app.worker.celery_app worker --loglevel=info
```

## 4. Hardware Fallback Note
If you see the log:
`[WhisperX] CUDA not detected. Falling back to int8 CPU processing. This will be slow.`
Your system does not have the PyTorch CUDA libraries installed, or no GPU is physically present. The transcription will succeed but may take 5-10x longer than realtime.
