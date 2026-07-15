# ==============================================================================
# Smart HRMS — Production Dockerfile
# Multi-stage build for minimal production image size.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder — install dependencies
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Set build arguments
ARG APP_DIR=/app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment in the builder stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all requirements files (production.txt references base.txt via -r)
COPY requirements/ /tmp/requirements/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements/production.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime — lean production image
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# Metadata
LABEL maintainer="Smart HRMS Team <dev@smarthrms.com>"
LABEL version="1.0.0"
LABEL description="Smart HRMS — Production Flask Application"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_ENV=production \
    APP_DIR=/app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root application user
RUN groupadd -r hrms && useradd -r -g hrms -d /app -s /sbin/nologin hrms

# Set working directory
WORKDIR $APP_DIR

# Copy application source code
COPY --chown=hrms:hrms . .

# Create runtime directories with correct permissions
RUN mkdir -p /app/logs /app/instance/uploads /app/instance/sessions && \
    chown -R hrms:hrms /app/logs /app/instance

# Switch to non-root user
USER hrms

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command — Gunicorn WSGI server
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 4 --worker-class sync --worker-connections 1000 --timeout 120 --keepalive 5 --max-requests 1000 --max-requests-jitter 100 --preload --access-logfile /app/logs/gunicorn_access.log --error-logfile /app/logs/gunicorn_error.log --log-level warning run:app"]
