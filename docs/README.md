# Jellyseerr Pi UI

A controller-friendly interface for Jellyseerr designed for Raspberry Pi 4 running in framebuffer mode.

## Features

- Full controller support (Xbox layout)
- Search movies and TV shows with on-screen keyboard
- Browse popular content
- View media details with poster art
- Request content directly from your controller
- Clean, TV-friendly interface

## Requirements

### System
- Raspberry Pi 4 (32-bit armhf, Debian Buster)
- Python 3.x
- pygame library
- requests library

### Jellyseerr
- Running Jellyseerr instance (configured in `config.py`)
- Network connectivity to Jellyseerr server

## Installation

1. Install required packages:
```bash
sudo apt-get update
sudo apt-get install python3-pygame python3-requests
```

2. Clone or download this project to your Pi

3. Edit `config.py` and set your Jellyseerr server details:
```python
JELLYSEERR_BASE_URL = "http://your-server-ip:5055"
```

4. If your Jellyseerr requires an API key, add it to `config.py`:
```python
JELLYSEERR_API_KEY = "your-api-key-here"
```

## Usage

### Running from SSH (Testing)
```bash
python3 main.py
```
This will run in windowed mode. You can use keyboard for testing:
- Arrow keys: Navigate
- Enter/Space: Select
- Backspace: Go back
- ESC: Exit

### Running in Framebuffer Mode (on Pi)
```bash
SDL_VIDEODRIVER=fbcon python3 main.py
```

### Adding to EmulationStation
Create a new system in EmulationStation that launches the script.

## Controller Layout (Xbox)

- **D-Pad / Left Analog Stick**: Navigate menus and on-screen keyboard
- **A Button**: Select / Confirm
- **B Button**: Back / Cancel
- **START Button**: Exit application

## On-Screen Keyboard

When searching, use the controller to navigate the on-screen keyboard:
- Use D-Pad or analog stick to highlight characters
- Press A to select a character
- Navigate to "DEL" to delete last character
- Navigate to "SEARCH" to submit search
- Navigate to "CANCEL" or press B to go back

## File Structure

```
jellyseer_pi_ui/
├── main.py              # Entry point
├── jellyseerr_api.py    # API wrapper for Jellyseerr
├── ui.py                # Pygame UI implementation
├── config.py            # Configuration settings
└── README.md            # This file
```

## Configuration

Edit `config.py` to customize:
- Jellyseerr server URL and API key
- Screen resolution (default: 1920x1080)
- Controller button mappings
- Colors and fonts
- Navigation timing

## Troubleshooting

### "Cannot connect to Jellyseerr"
- Check that Jellyseerr is running
- Verify the URL in `config.py`
- Test connectivity: `curl http://your-server:5055/api/v1/status`

### No controller detected
- The application will fall back to keyboard controls
- Check controller is connected: `ls /dev/input/js*`
- Verify pygame can see controller: `python3 -c "import pygame; pygame.init(); pygame.joystick.init(); print(pygame.joystick.get_count())"`

### Images not loading
- pygame supports most image formats natively
- If images fail to load, check network connectivity
- Check logs at `/tmp/jellyseerr-ui.log`

### Screen too small / text too large
- Edit `config.py` and adjust font sizes
- Adjust `SCREEN_WIDTH` and `SCREEN_HEIGHT` for your display

## Logs

Application logs are written to `/tmp/jellyseerr-ui.log`

View logs:
```bash
tail -f /tmp/jellyseerr-ui.log
```

## API Key Setup

To get your Jellyseerr API key:

1. Open Jellyseerr web interface
2. Go to Settings → General
3. Copy your API Key
4. Add it to `config.py`:
```python
JELLYSEERR_API_KEY = "your-api-key-here"
```

Note: Some Jellyseerr setups may not require an API key for local network access.

## Known Limitations

- Images are cached in memory (may use significant RAM for many posters)
- No authentication UI (assumes open access or pre-configured API key)
- Limited to 10 visible items per list
- Search results limited to first page

## Future Enhancements

Potential improvements:
- Persistent disk cache for images
- Multiple pages of search results
- User authentication UI
- Request status checking
- Season/episode selection for TV shows
- Watchlist integration

## License

This project is provided as-is for personal use.
