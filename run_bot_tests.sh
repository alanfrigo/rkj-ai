#!/bin/bash
# Script to run bot tests using Docker (replicating production-like environment)

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

echo "🐳 Preparing to run Meet Bot in Docker..."

# Load environment variables from .env
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
else
    echo "⚠️  .env file not found. Using defaults."
fi

# Ensure critical variables are set for testing
: "${MEETING_URL:=https://meet.google.com/ifg-obfv-cdh}"
: "${BOT_DISPLAY_NAME:=Test Bot}"
: "${MEETING_ID:=$(uuidgen)}" # Generate valid UUID
: "${USER_ID:=test-user}"
: "${DRY_RUN:=true}" # Skip database writes

# Build the image first to ensure it's up to date
echo "🏗️  Building meet-bot image..."
docker-compose -f infrastructure/docker/docker-compose.yml build meet-bot || exit 1

# Prepare recordings directory
mkdir -p "$ROOT_DIR/recordings"

# HOST_DOCKER_INTERNAL handling
# On Linux, host.docker.internal doesn't exist by default, we might need --add-host.
# On Mac/Windows it exists.
# We'll assume Mac since user is on Mac.

# Adjust REDIS_URL for Docker if it points to localhost
# If REDIS_URL is localhost, we change it to host.docker.internal so container can reach host's redis.
if [[ "$REDIS_URL" == *"localhost"* ]]; then
    echo "🔄 Adjusting REDIS_URL from localhost to host.docker.internal for container access..."
    DOCKER_REDIS_URL="${REDIS_URL/localhost/host.docker.internal}"
else
    DOCKER_REDIS_URL="$REDIS_URL"
fi

# Run the container
echo "🚀 Starting Meet Bot container..."
echo "   Meeting: $MEETING_URL"

# Remove existing container if it exists
docker rm -f meet-bot-test >/dev/null 2>&1 || true

docker run --rm \
    --name meet-bot-test \
    --init \
    --env-file "$ROOT_DIR/.env" \
    -e MEETING_URL="$MEETING_URL" \
    -e MEETING_ID="$MEETING_ID" \
    -e USER_ID="$USER_ID" \
    -e BOT_DISPLAY_NAME="$BOT_DISPLAY_NAME" \
    -e REDIS_URL="$DOCKER_REDIS_URL" \
    -e DRY_RUN="$DRY_RUN" \
    -v "$ROOT_DIR/recordings:/recordings" \
    --shm-size=2g \
    --add-host=host.docker.internal:host-gateway \
    docker-meet-bot:latest
