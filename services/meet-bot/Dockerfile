# ===========================================
# Meet Bot Dockerfile
# ===========================================
# Container for Google Meet recording bot
# Includes: Chrome, Playwright, FFmpeg, PulseAudio, Xvfb

FROM python:3.11-slim-bookworm

# Install system dependencies for browser and recording
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Virtual display
    xvfb \
    # Audio
    pulseaudio \
    # Video recording
    ffmpeg \
    # Browser dependencies (required by Playwright Chromium)
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Utilities
    dbus \
    fonts-liberation \
    fonts-noto-color-emoji \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy source code
COPY src/ ./src/
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create recordings directory
RUN mkdir -p /recordings

# Create assets directory for custom camera
RUN mkdir -p /assets

# Generate a default "robot face" video for the fake camera
# Using Liberation Sans which is definitely installed by fonts-liberation package
# Output to .y4m (YUV4MPEG2) which is required for --use-file-for-fake-video-capture
RUN ffmpeg -f lavfi -i color=c=black:s=1280x720:d=10 \
    -vf "drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf:text='BOT':fontsize=200:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
    -pix_fmt yuv420p /assets/camera_loop.y4m

# Set environment variables
ENV DISPLAY=:99
ENV PULSE_SERVER=unix:/tmp/pulse/native

# Entrypoint script sets up Xvfb and PulseAudio
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["python", "-m", "src.main"]

