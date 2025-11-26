#!/bin/bash
# Jellyseerr Pi UI Launcher Script

# Set SDL to use framebuffer
export SDL_VIDEODRIVER=fbcon

# Disable mouse cursor
export SDL_NOMOUSE=1

# Navigate to project root (one level up from scripts/)
cd "$(dirname "$0")/.."

# Run the application
python3 main.py

# Return exit code
exit $?
