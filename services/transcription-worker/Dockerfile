# ===========================================
# Transcription Worker Dockerfile
# ===========================================

FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

# Run the worker
CMD ["python", "-m", "src.main"]
