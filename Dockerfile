# ─────────────────────────────────────────────────────────────
#  AroundU Backend — Dockerfile
#  Multi-stage build: keeps the final image lean
# ─────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a prefix so we can
# copy only them to the final stage
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt gunicorn uvloop httptools

# ── Stage 2: runtime ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Labels
LABEL maintainer="AroundU Team"
LABEL description="AroundU – location-based place discovery API"

WORKDIR /app

# Runtime system libs only (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create uploads directory, strip Windows CR if present, make scripts executable
RUN mkdir -p /app/uploads/places && \
    sed -i 's/\r//' /app/start.sh && \
    chmod +x /app/start.sh

# Non-root user for security
RUN adduser --disabled-password appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the API port
EXPOSE 8000

# Health check — hits the /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command (using our robust start script)
CMD ["./start.sh"]

