# GPU Service API Contract

Both RunPod and local HTTP server expose the same logical contract.

## POST /run — Submit Transcription Job

**Request body:**
```json
{
  "input": {
    "audio_url": "https://s3.example.com/audio.wav?presigned...",
    "language": "en",
    "min_speakers": 1,
    "max_speakers": 10
  }
}
```

**Response (202 Accepted):**
```json
{
  "id": "job-abc123",
  "status": "QUEUED"
}
```

## GET /status/{job_id} — Poll Job Status

**Response (in progress):**
```json
{
  "id": "job-abc123",
  "status": "IN_PROGRESS"
}
```

**Response (completed):**
```json
{
  "id": "job-abc123",
  "status": "COMPLETED",
  "output": {
    "text": "[SPEAKER_00] Hello everyone...\n[SPEAKER_01] Thanks for joining...",
    "language": "en",
    "segments": [
      {
        "start": 0.0,
        "end": 3.5,
        "text": "Hello everyone, welcome to the meeting.",
        "speaker": "SPEAKER_00",
        "words": [
          {"word": "Hello", "start": 0.0, "end": 0.4, "speaker_label": "SPEAKER_00", "confidence": 0.95}
        ]
      }
    ],
    "provider_name": "whisperx-local",
    "audio_duration_seconds": 1823.4,
    "estimated_cost": 0.084
  }
}
```

**Response (failed):**
```json
{
  "id": "job-abc123",
  "status": "FAILED",
  "error": "Audio file could not be downloaded: 403 Forbidden"
}
```

## RunPod Mapping

The RunPod SDK maps to this contract as follows:

| Local HTTP | RunPod SDK |
|------------|-----------|
| `POST /run` | `endpoint.run(input)` → returns `run_request` with `.job_id` |
| `GET /status/{id}` | `endpoint.status(job_id)` → returns status object |
| `status: COMPLETED` | `status == "COMPLETED"` |
| `output` field | `run_request.output` |

The unified `GpuTranscriptionClient` abstracts these differences internally.
