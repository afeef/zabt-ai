# Lean local-dev image for the zabt-vision-worker FastAPI server.
# Plan 4 will produce a separate GPU-enabled image (transformers + Qwen3-VL)
# for RunPod. This image is CPU-only and pulls only the [scene] extra so
# iteration stays fast — no torch, no easyocr.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv for dep management (matches the project's tooling)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Cached dep install — copy lockfile + manifest first for layer reuse
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --extra scene --frozen --no-install-project --no-dev

# Now copy the source (changes invalidate only this layer)
COPY zabt_vision ./zabt_vision

# Install the package itself (editable not needed — image is rebuilt on change)
RUN uv sync --extra scene --frozen --no-dev

ENV OCR_USE_GPU=false \
    PYTHONUNBUFFERED=1

EXPOSE 8003

CMD ["uv", "run", "--no-sync", "uvicorn", "zabt_vision.server:app", \
     "--host", "0.0.0.0", "--port", "8003"]
