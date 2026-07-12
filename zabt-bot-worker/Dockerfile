# Bot Worker: headless browser + audio capture
# Ubuntu 24.04 base for PPA access (ffmpeg8) and Chromium compatibility
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System deps: Python, Xvfb, PulseAudio, D-Bus + ffmpeg 8 from PPA
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    software-properties-common \
    && add-apt-repository ppa:ubuntuhandbook1/ffmpeg7 -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    xvfb \
    pulseaudio \
    dbus \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

WORKDIR /app

# Install Python deps
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Install Playwright Chromium + ALL its system dependencies (handles libcups, libnss3, etc.)
RUN uv run playwright install --with-deps chromium

# Copy source
COPY src/ src/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8002

CMD ["/entrypoint.sh"]
