#!/bin/bash
# Jellyseerr Pi UI Test Launcher (Headless Mode)
# Use this for testing over SSH without X11 forwarding

# Navigate to project root (one level up from scripts/)
cd "$(dirname "$0")/.."

# Use SDL dummy video driver (no display output, but runs without errors)
export SDL_VIDEODRIVER=dummy
export SDL_AUDIODRIVER=dummy

echo "Running in headless mode (no display output)..."
echo "This is useful for testing API/logic but you won't see the UI."
echo ""

python3 main.py

# Return exit code
exit $?
