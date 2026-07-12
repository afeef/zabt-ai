# ============================================================
# TARGET: api — Lightweight FastAPI image (~850 MB)
# Build: docker build --target api -t zabt-api:latest .
# ============================================================
FROM python:3.11-slim AS api

# System dependencies: PostgreSQL runtime + WeasyPrint (Pango/HarfBuzz) + Noto fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libharfbuzz0b \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up virtual environment
ENV UV_PROJECT_ENVIRONMENT=/opt/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/.venv/bin:$PATH"

# Copy only dependency files first (layer cache)
COPY pyproject.toml uv.lock ./

# Install core dependencies only (no ML, no dev)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .

# Install the project itself (fast — code only)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# ============================================================
# TARGET: worker — Lightweight Celery worker (same base as api)
# Build: docker build --target worker -t zabt-worker:latest .
# ============================================================
FROM api AS worker

CMD ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info"]
