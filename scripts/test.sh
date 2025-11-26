#!/bin/bash
# Jellyseerr Pi UI Test Launcher (Windowed Mode)
# Use this for testing via SSH or on desktop

# Run in windowed mode (no framebuffer)
# Navigate to project root (one level up from scripts/)
cd "$(dirname "$0")/.."
python3 main.py

# Return exit code
exit $?
