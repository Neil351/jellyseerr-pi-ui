#!/bin/bash
# Jellyseerr Pi UI Launcher Script

# Set SDL to use framebuffer (comment out for testing in SSH)
export SDL_VIDEODRIVER=fbcon

# Disable mouse cursor
export SDL_NOMOUSE=1

# Run the application
cd "$(dirname "$0")"
python3 main.py

# Return exit code
exit $?
