# ============================================================
# Care AI Engine - Production Dockerfile
# Multi-stage build for minimal image size
#
# Build fixes:
#   - setuptools<72 pinned (openai-whisper needs pkg_resources)
#   - --no-build-isolation for whisper to find pkg_resources
#   - CPU-only PyTorch installed first for layer caching
# ============================================================

# --- Stage 1: Build ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Layer 1: CPU-only PyTorch (cached — rarely changes)
RUN pip install --no-cache-dir \
    torch --extra-index-url https://download.pytorch.org/whl/cpu

# Layer 2: Pin setuptools<72 (openai-whisper uses pkg_resources)
RUN pip install --no-cache-dir "setuptools<72" wheel

# Layer 3: App requirements (only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# --- Stage 2: Production ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system careai \
    && adduser --system --ingroup careai careai

# Copy installed packages from builder (default location, not --prefix)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

# Create data directories with correct ownership
RUN mkdir -p logs \
    && chown -R careai:careai /app

# Create whisper cache dir (model downloads to persistent volume on first use)
RUN mkdir -p /app/app/data/whisper && chown -R careai:careai /app/app/data

# NOTE: Whisper model is NOT pre-downloaded into the image (saves ~150MB-3GB).
# It downloads on first request to /app/app/data/whisper (mounted volume).
# To change model size, set WHISPER_MODEL_SIZE env var (tiny/base/small/medium/large-v3)
# and the new model will download on next restart.

# Switch to non-root user
USER careai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ping || exit 1

# Expose port
EXPOSE 8000

# Run with uvicorn (production settings)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--log-level", "info"]
