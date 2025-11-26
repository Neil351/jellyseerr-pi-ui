# Quick Start Guide

## First Time Setup

1. **Install dependencies** (one-time setup):
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pygame python3-requests
   ```

2. **Configure Jellyseerr connection**:
   Edit `config.py` and update these lines:
   ```python
   JELLYSEERR_BASE_URL = "http://100.112.21.82:5055"  # Your Jellyseerr server
   JELLYSEERR_API_KEY = ""  # Add API key if needed
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x run.sh test.sh
   ```

4. **Test the connection**:
   ```bash
   ./test.sh
   ```

   If you see "Cannot connect to Jellyseerr", verify:
   - Jellyseerr is running
   - URL is correct in config.py
   - Network connectivity works

## Testing (SSH/Desktop)

Run in windowed mode for testing:
```bash
./test.sh
```

**Keyboard controls for testing:**
- Arrow keys: Navigate
- Enter: Select
- Backspace: Go back
- ESC: Exit
- Type directly when on search screen

## Running on Pi (Fullscreen)

Launch in framebuffer mode:
```bash
./run.sh
```

Or manually:
```bash
SDL_VIDEODRIVER=fbcon python3 main.py
```

## Controller Setup

1. Connect Xbox-compatible controller via USB or Bluetooth
2. Verify controller is detected:
   ```bash
   ls /dev/input/js*
   ```
   You should see `/dev/input/js0` or similar

3. Test controller in pygame:
   ```bash
   python3 -c "import pygame; pygame.init(); pygame.joystick.init(); print(f'Controllers: {pygame.joystick.get_count()}')"
   ```

## First Use

1. Launch the application
2. Main menu appears with options:
   - **Search Movies**: Search for movies
   - **Search TV Shows**: Search for TV shows
   - **Browse Popular**: Browse trending content
   - **Exit**: Close application

3. **To search:**
   - Select "Search Movies" or "Search TV Shows"
   - Use on-screen keyboard to enter search term
   - Navigate to "SEARCH" button and press A

4. **To browse:**
   - Select "Browse Popular"
   - Navigate through list with D-Pad/stick
   - Press A to view details

5. **To request content:**
   - View details of a movie/show
   - Press A to submit request
   - Wait for confirmation message

## Adding to EmulationStation

Add this to your EmulationStation menu:

1. Create launcher script in `/home/pi/RetroPie/roms/ports/`
2. Make it executable
3. Restart EmulationStation

Example launcher script:
```bash
#!/bin/bash
cd /path/to/jellyseer_pi_ui
./run.sh
```

## Troubleshooting

**No image on screen (framebuffer mode)**
- Try switching to a different TTY (Ctrl+Alt+F2)
- Ensure no X server is running
- Check SDL_VIDEODRIVER is set to fbcon

**Controller not working**
- Check `/dev/input/js0` exists
- Try reconnecting controller
- Use keyboard as fallback

**API errors**
- Check logs: `cat /tmp/jellyseerr-ui.log`
- Verify Jellyseerr is accessible
- Test API: `curl http://your-server:5055/api/v1/status`

**Images not loading**
- Normal - first load takes time to download
- Check internet connectivity
- Images are cached after first load

## Tips

- Images load on-demand and are cached
- First time browsing may be slow (downloading posters)
- Use "Search" for specific titles
- Use "Browse Popular" to discover new content
- Press B button to go back at any time
- Press START button to exit from anywhere
