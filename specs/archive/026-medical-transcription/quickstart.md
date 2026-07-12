# Quickstart: Transcription Type Selection

## Environment Variables

No new environment variables required in backend or frontend.

GPU worker already has model configuration via existing env vars:
- `WHISPER_MODEL` — WhisperX model name (default: `large-v3`)
- `HF_AUTH_TOKEN` — Hugging Face token for pyannote diarization model

New GPU worker env var (optional, has default):
- `MEDASR_MODEL` — MedASR model name (default: `google/medasr`)

## Docker Build

### Building the base image (rare — only when upgrading CUDA/PyTorch):
```bash
cd zabt-gpu-worker
docker build -f Dockerfile.base -t yourdockerhub/zabt-gpu-base:latest .
docker push yourdockerhub/zabt-gpu-base:latest
```

### Building the worker image (on every code/dependency change):
```bash
cd zabt-gpu-worker
docker build -t zabt-gpu-worker:latest .
```

### Local development with GPU:
```bash
docker compose --profile local up worker-gpu
```

## Testing Scenarios

### Scenario 1: Normal Upload (backward compatibility)
1. Open upload modal
2. Verify selector defaults to "Normal"
3. Upload any audio file
4. Verify transcription uses WhisperX (check meeting detail shows "Normal")
5. Verify transcript quality matches pre-feature behavior

### Scenario 2: Medical Upload
1. Open upload modal
2. Select "Medical" transcription type
3. Upload a medical dictation audio file
4. Verify transcription completes successfully
5. Verify meeting detail shows "Medical" type
6. Verify transcript has accurate medical terminology

### Scenario 3: YouTube URL with Medical Type
1. Click "Paste URL" button
2. Select "Medical" transcription type
3. Paste a YouTube URL
4. Verify meeting is created with `transcription_type: "medical"`
5. Verify transcription processes with MedASR

### Scenario 4: Existing Meetings
1. Open any meeting created before this feature
2. Verify it shows "Normal" transcription type
3. Verify no changes to existing transcript

## Rollback Procedure

1. Revert GPU worker to previous image (without MedASR)
2. Revert backend code changes
3. The `transcription_type` column can remain — it defaults to "normal" and is harmless
4. Frontend selector disappears with code revert
