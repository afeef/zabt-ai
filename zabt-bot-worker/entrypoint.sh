#!/bin/bash
set -e

# Start D-Bus (PulseAudio dependency)
dbus-daemon --system --fork 2>/dev/null || true

# Start PulseAudio daemon (persistent, no idle exit)
pulseaudio --start --exit-idle-time=-1 2>/dev/null || true

# Start default Xvfb display (session.py creates per-meeting displays)
Xvfb :99 -screen 0 1280x720x24 -ac &
export DISPLAY=:99

echo "System services started (D-Bus, PulseAudio, Xvfb :99)"

# Start the FastAPI server
exec uv run uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8002}
