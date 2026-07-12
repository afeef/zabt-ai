# Quickstart: Transcription CLI

**Branch**: `012-transcription-cli` | **Date**: 2026-02-26

## Prerequisites

- Python 3.11+
- `uv` package manager installed
- FFmpeg installed on the system (`sudo apt install ffmpeg` or `brew install ffmpeg`)
- CUDA-capable GPU (optional; CPU fallback is automatic)

## Environment Variables

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `WHISPER_MODEL` | No | `base.en` | Whisper model size (tiny, base, small, medium, large) |
| `TRANSCRIPTION_DEVICE` | No | `auto` | Force device: `cpu`, `cuda`, or `auto` (auto-detect) |
| `HF_AUTH_TOKEN` | For diarization | `""` (empty) | Hugging Face token for Pyannote speaker diarization. If empty, diarization is skipped and all segments are labeled "SPEAKER_UNKNOWN" |
| `OPENAI_BASE_URL` | For summarization | `http://host.docker.internal:1234/v1` | LLM API base URL (e.g., LM Studio local server) |
| `OPENAI_API_KEY` | For summarization | `lm-studio` | LLM API key |
| `OPENAI_MODEL` | For summarization | `llama-3-8b` | LLM model name |

**Note**: Database, MinIO, and Redis environment variables are NOT required for the CLI.
The CLI operates entirely on local files.

## Installation

From the backend directory:

```bash
cd backend
uv sync
```

This installs all dependencies including the new `typer` package and registers
the `zabt` console script.

## Usage

### Basic Transcription (US1)

```bash
# Using the registered console script
cd backend
uv run zabt transcribe path/to/meeting.mp3

# Or using python -m
uv run python -m app.cli transcribe path/to/meeting.mp3
```

**Output** (human-readable, default):

```
Transcription Results
=====================

[00:00.0 - 00:02.5] SPEAKER_00
  Hello, let's start the meeting.

[00:02.8 - 00:05.1] SPEAKER_01
  Sure, I have the quarterly numbers ready.

...

Language: en
Segments: 42
Duration: 5m 12s
```

### With AI Summarization (US2)

```bash
uv run zabt transcribe path/to/meeting.mp3 --summarize
```

**Additional output** after transcript:

```
Meeting Summary
===============

Summary: The team discussed Q4 results and planning for next quarter...

Key Decisions:
  1. Increase marketing budget by 15%
  2. Hire two additional engineers

Action Items:
  - Review budget proposal (Owner: Sarah, Due: 2026-03-01)
  - Post engineering job listings (Owner: Mike, Due: 2026-02-28)

Sentiment: Positive
```

### JSON Output (US3)

```bash
uv run zabt transcribe path/to/meeting.mp3 --json
uv run zabt transcribe path/to/meeting.mp3 --summarize --json
```

JSON output can be piped to other tools:

```bash
uv run zabt transcribe meeting.mp3 --json | jq '.segments[].speaker' | sort -u
```

### Styles Directory (Optional)

If you have style example PDFs for the summarization agent, place them in:

```
/media/styles/
```

The CLI reads PDFs from this directory and passes them as few-shot examples
to the summarization agent (same behavior as the Celery worker).

## Supported File Formats

Any format supported by FFmpeg:
- Audio: WAV, MP3, FLAC, OGG, M4A, AAC
- Video: MP4, MKV, AVI, MOV, WebM (audio track extracted automatically)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError` | Check the file path exists and is accessible |
| "HF_AUTH_TOKEN not set" warning | Set `HF_AUTH_TOKEN` env var for speaker diarization, or ignore if speaker labels are not needed |
| CUDA out of memory | Set `TRANSCRIPTION_DEVICE=cpu` or use a smaller `WHISPER_MODEL` |
| Summarization fails | Ensure the LLM service is running at `OPENAI_BASE_URL` |
| "No module named 'app'" | Run from the `backend/` directory: `cd backend && uv run zabt ...` |
