# GPU Worker: CUDA runtime + ML deps via uv + source code
# Models download at first startup (not baked in)
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies + Python + FFmpeg 6 (Ubuntu 24.04 default)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    software-properties-common \
    && add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Ensure libraries are indexed
RUN ldconfig

# Install uv (pinned version for reproducible builds)
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files (cached layer — rebuilds only when deps change)
COPY pyproject.toml uv.lock ./

# Install all dependencies with cache mount for faster retries
ENV UV_HTTP_TIMEOUT=1200
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Activate venv via PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code (fast layer — rebuilds on every code change)
COPY scripts/ scripts/
COPY src/ src/

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health')" || exit 1

CMD ["python", "-m", "src.main"]
