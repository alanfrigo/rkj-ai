#!/bin/bash
# ===========================================
# Meet Bot Entrypoint Script
# ===========================================
# Sets up virtual display and audio before running the bot

set -e

echo "🚀 Starting Meet Bot..."

# Start D-Bus
echo "📡 Starting D-Bus..."
mkdir -p /run/dbus
dbus-daemon --system --fork 2>/dev/null || true

# Start PulseAudio with virtual sink for audio capture
# Start PulseAudio with virtual sink for audio capture
# Unset PULSE_SERVER to prevent "refusing to start" error due to existing env var
unset PULSE_SERVER

echo "🔊 Starting PulseAudio..."
pulseaudio --start --exit-idle-time=-1
sleep 1

# Check if PulseAudio is running
if ! pulseaudio --check; then
    echo "❌ PulseAudio failed to start"
    exit 1
fi

# Create virtual sink for capturing system audio
echo "🎛️ Loading virtual audio drivers..."
pactl load-module module-null-sink sink_name=virtual_speaker sink_properties=device.description=VirtualSpeaker
pactl set-default-sink virtual_speaker

# Start Xvfb (virtual display)
echo "🖥️ Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Check if Xvfb is running
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "❌ Failed to start Xvfb"
    exit 1
fi

echo "✅ Virtual display ready at :99"

# Export display
export DISPLAY=:99

# Trap to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    kill $XVFB_PID 2>/dev/null || true
    pulseaudio --kill 2>/dev/null || true
}
trap cleanup EXIT

# Run the actual command
echo "🤖 Starting bot process..."
exec "$@"
