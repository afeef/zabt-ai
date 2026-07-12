# zabt-vision-worker

Stateless vision worker for Zabt's visual breakdown feature.

## Local development (RTX 3090)

Prereqs: Python 3.11, ffmpeg, Ollama running with `qwen3-vl:8b-thinking` pulled.

```bash
cd zabt-vision-worker
uv sync --all-extras
uv run uvicorn zabt_vision.server:app --host 0.0.0.0 --port 8003 --reload
```

Run tests:
```bash
uv run pytest                          # unit tests
uv run pytest -m integration           # end-to-end with a real video
```

See `docs/superpowers/specs/2026-04-19-visual-breakdown-design.md` for design.

## CLI

The `zabt-vision` Typer CLI is the primary way to test the worker locally
during Phase 1 calibration. It imports the same `JobInput`, `Settings`,
and `run_pipeline` as the FastAPI server — there is no separate CLI logic.

```bash
# Run the pipeline against a local video without uploading to S3
uv run zabt-vision run path/to/demo.mp4 --no-upload

# Override thresholds for calibration
uv run zabt-vision run path/to/demo.mp4 \
    --fps 2 --phash 8 --ocr 0.3 --min-signals 2 --confidence 0.7

# Provide a transcript for the transcript-hint signal
uv run zabt-vision run path/to/demo.mp4 \
    --transcript path/to/transcript.json --no-upload

# Emit machine-readable JSON for diffing across runs
uv run zabt-vision run path/to/demo.mp4 --no-upload --json > result.json

# Start the FastAPI server via the CLI
uv run zabt-vision serve --reload
```
