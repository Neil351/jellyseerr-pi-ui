#!/bin/bash
# EmulationStation launcher for Jellyseerr Pi UI
# This script kills EmulationStation, runs the app, then restarts ES

# Navigate to project root
cd "$(dirname "$0")/.."

# Kill EmulationStation to free the framebuffer
killall emulationstation

# Wait longer for ES to fully exit and release framebuffer
sleep 3

# Double-check ES is gone
while pgrep emulationstation > /dev/null; do
    echo "Waiting for EmulationStation to exit..."
    sleep 1
done

# Set SDL to use framebuffer
export SDL_VIDEODRIVER=fbcon
export SDL_NOMOUSE=1

# Run Jellyseerr UI
python3 main.py

# When app exits, restart EmulationStation
emulationstation
