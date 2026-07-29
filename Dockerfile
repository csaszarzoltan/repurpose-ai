FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for layer caching
COPY pyproject.toml ./

# Install Python dependencies with uv (list all deps from pyproject.toml so the
# fallback still works when editable install fails in Docker build context)
RUN uv pip install --system --no-cache -e ".[dev]" 2>/dev/null || \
    uv pip install --system --no-cache \
        fastapi uvicorn\[standard\] pydantic httpx \
        PyJWT python-multipart openai anthropic tiktoken

# Copy application code (src/app → /app/app so `app.main:app` resolves)
COPY src/app/ app/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn (shell form allows PORT env var expansion)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
