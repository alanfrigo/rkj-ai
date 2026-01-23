# ===========================================
# Scheduler Service Dockerfile
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
RUN useradd -m -u 1000 scheduler && chown -R scheduler:scheduler /app
USER scheduler

# Run the scheduler
CMD ["python", "-m", "src.main"]
