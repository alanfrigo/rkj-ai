# ===========================================
# Bot Orchestrator Dockerfile
# ===========================================

FROM python:3.11-slim

WORKDIR /app

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

# Run the orchestrator
CMD ["python", "-m", "src.main"]
