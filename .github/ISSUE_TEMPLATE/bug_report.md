---
name: Bug report
about: Report a problem with zabt.ai
title: "[Bug] "
labels: bug
assignees: ''
---

## Describe the bug
A clear and concise description of what the bug is.

## To reproduce
Steps to reproduce the behavior:
1. ...
2. ...
3. See error

## Expected behavior
What you expected to happen.

## Logs / screenshots
Relevant logs (`docker compose logs api worker worker-gpu`), stack traces, or screenshots.
Please redact any secrets or personal meeting content.

## Environment
- **Deployment topology:** single-machine / CPU-only / cloud (RunPod split)
- **Transcription backend:** `gpu-local` / `runpod`
- **GPU:** model + VRAM (or "CPU only")
- **`WHISPER_MODEL`:** (e.g. large-v3, base)
- **Storage provider:** minio / s3
- **OS + Docker version:** `docker version`
- **zabt.ai version / commit:** `git rev-parse --short HEAD`

## Additional context
Anything else that might help (custom config, reverse proxy, managed DB, etc.).
