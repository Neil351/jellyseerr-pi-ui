#!/bin/bash
# EmulationStation launcher for Jellyseerr Pi UI
# This script kills EmulationStation, runs the app, then restarts ES

# Navigate to project root
cd "$(dirname "$0")/.."

# Kill EmulationStation to free the framebuffer
killall emulationstation

# Wait for ES to fully exit
sleep 1

# Set SDL to use framebuffer
export SDL_VIDEODRIVER=fbcon
export SDL_NOMOUSE=1

# Run Jellyseerr UI
python3 main.py

# When app exits, restart EmulationStation
emulationstation
