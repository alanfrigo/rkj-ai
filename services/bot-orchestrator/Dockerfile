# ===========================================
# Bot Orchestrator Dockerfile
# ===========================================

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 orchestrator && chown -R orchestrator:orchestrator /app

# Note: Running as root to access Docker socket
# USER orchestrator

# Healthcheck - verify process can connect to Redis
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import redis; r = redis.from_url('redis://redis:6379'); r.ping()" || exit 1

# Run the orchestrator
CMD ["python", "-m", "src.main"]
