# ═══════════════════════════════════════════════════════════════════════════
# Kaio Portfolio - Production Container (Multi-Stage Build)
# FastAPI + ML Projects (Credit Risk + Doc QA) - Dark Theme Portfolio
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ═══════════════════════════════════════════════════════════════════════════
# Stage 1: Install Python dependencies
# ═══════════════════════════════════════════════════════════════════════════
FROM base as dependencies

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Production image
# ═══════════════════════════════════════════════════════════════════════════
FROM base as production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY data/ data/

# Copy .env file (will be overridden by environment variables in production)
# COPY .env .env

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Run application with production settings
# Use 4 workers for better performance (adjust based on CPU cores)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
