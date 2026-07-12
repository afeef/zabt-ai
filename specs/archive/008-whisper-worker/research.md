# Research: WhisperX Backend Implementation

## Technology Stack

- **WhisperX**: Next-generation transcription model with word-level alignment and diarization.
- **PyTorch**: Deep learning framework required for WhisperX.
- **Celery**: Distributed task queue for handling long-running transcription jobs.
- **Redis**: Message broker and result backend for Celery.
- **FFmpeg**: Required for audio processing and alignment.

## WhisperX Setup

To use WhisperX effectively, the following system dependencies are required:
- `ffmpeg` (system package)
- `torch`, `torchaudio` (python packages)
- `whisperx` (python package)

### Model Selection
- **Whisper**: The implementation will rely on the standard `openai-whisper` package instead of `faster-whisper`.
- **Alignment Models**: Requires Wav2Vec2 alignment models (handled automatically by WhisperX).
- **Diarization**: Uses `pyannote-audio`.

### Docker & GPU Infrastructure
The services will be fully containerized. A `docker-compose.yml` will be used to orchestrate:
- FastAPI Web Server
- Celery Worker (requires `deploy.resources.reservations.devices` configured for GPU passthrough to allow CUDA acceleration inside the container).
- Redis
- MinIO

## Technical Challenges

### 1. GPU vs CPU Fallback
Implementation will use `torch.cuda.is_available()` to determine the device.
```python
device = "cuda" if torch.cuda.is_available() else "cpu"
batch_size = 16 if device == "cuda" else 1 # reduce batch size for CPU
compute_type = "float16" if device == "cuda" else "int8"
```

### 2. Large File Processing
WhisperX processes audio in batches. For CPU fallback, the `batch_size` must be significantly reduced to avoid OOM or excessive latency.

### 3. Progressive Updates
The worker will update the database at key transition points:
- `status: processing` -> `sub_status: transcribing`
- `sub_status: aligning`
- `sub_status: diarizing`
- `status: completed`

## Extensibility
The implementation will use a `TRANSCRIPTION_LANGUAGE` setting that defaults to `en`. Transcription and alignment models will be loaded dynamically based on this setting.

## Storage (MinIO / S3)
To ensure the backend does not rely on ephemeral local disks (which fail in clustered or containerized deployments), media file storage will use the **S3 Protocol**.
- **Local Development**: Docker Compose will run a `minio/minio` container.
- **Production**: AWS S3 buckets will be provisioned.
- **Backend Service**: `boto3` or `aiobotocore` will be used to stream file uploads into the storage bucket and generate internal paths (e.g., `s3://zabt-media/meetings/{id}.mp3`) which the Celery worker can download for transcription.
