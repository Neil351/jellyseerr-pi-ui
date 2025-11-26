# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Controller-friendly Jellyseerr interface designed for Raspberry Pi 4 running in framebuffer mode (no X server). Built with pygame for rendering and controller input, targeting TV couch navigation with Xbox-style controllers.

## Running the Application

**Testing mode (windowed, keyboard fallback):**
```bash
python3 main.py
# or
./test.sh
```

**Production mode (framebuffer, fullscreen on Pi):**
```bash
SDL_VIDEODRIVER=fbcon python3 main.py
# or
./run.sh
```

**View logs:**
```bash
tail -f /tmp/jellyseerr-ui.log
```

**Test Jellyseerr connectivity:**
```bash
curl http://100.112.21.82:5055/api/v1/status
```

**Test controller detection:**
```bash
ls /dev/input/js*
python3 -c "import pygame; pygame.init(); pygame.joystick.init(); print(f'Controllers: {pygame.joystick.get_count()}')"
```

## Architecture

### Application Flow
1. `main.py` - Entry point: initializes logging, tests API connection, creates UI instance
2. `jellyseerr_api.py` - API wrapper: handles all HTTP requests to Jellyseerr server
3. `ui.py` - Main UI class: pygame event loop, screen state machine, rendering
4. `config.py` - Centralized configuration: URLs, colors, fonts, controller mappings

### Screen State Machine (ui.py)
The UI operates as a state machine with the following screens:
- `main_menu` - Four options: Search Movies, Search TV Shows, Browse Popular, Exit
- `keyboard` - On-screen keyboard for text input (4x10 grid with special keys)
- `search_results` - List view with poster preview
- `browse` - Popular content list with poster preview
- `media_detail` - Full details with poster, overview, and request button

Navigation handled by `screen_stack` for back button functionality.

### Input Handling Architecture
Three parallel input systems:
1. **Controller buttons** (`pygame.JOYBUTTONDOWN`) - A/B/START buttons
2. **D-pad** (`pygame.JOYHATMOTION`) - Hat switch for navigation
3. **Analog stick** (polled via `joystick.get_axis()`) - Continuous movement with deadzone

Keyboard fallback available for SSH testing. `NAV_DELAY` prevents double-inputs.

### Image Loading Strategy
- Images loaded on-demand when content is selected
- In-memory cache (`image_cache` dict) keyed by URL
- Tries pygame native loading first, falls back to PIL if available
- Placeholder surface generated at init for missing images
- TMDB poster URLs constructed via `get_poster_url()` with configurable size

### Configuration Requirements
`config.py` must be edited before first run:
- `JELLYSEERR_BASE_URL` - Your Jellyseerr server (default: `http://100.112.21.82:5055`)
- `JELLYSEERR_API_KEY` - Optional, empty string if not required
- Controller button mappings assume Xbox layout (A=0, B=1, START=7)

### Display Mode Detection
`ui.py` checks `SDL_VIDEODRIVER` environment variable:
- `fbcon` → Fullscreen framebuffer mode (Pi production)
- Not set → Windowed mode (testing/development)

### API Error Handling
All API methods return `None` on failure and log errors. UI shows error messages via `show_message()` with color-coded feedback (success=green, error=red).

Connection test runs on startup - application exits with error if Jellyseerr unreachable.

### Keyboard Screen (On-Screen Input)
4-row grid layout with 2D navigation:
- Rows 0-2: Letters and numbers
- Row 3: Space, DEL, SEARCH, CANCEL
- Navigation via `keyboard_row`/`keyboard_col` indices
- Selection handled by `handle_keyboard_select()`

When adding features to keyboard: ensure both D-pad and analog stick work for 2D navigation.

## Dependencies

Required Python packages:
```bash
sudo apt-get install python3-pygame python3-requests
```

Target platform: Raspberry Pi 4, 32-bit armhf, Debian Buster.

## Common Development Patterns

**Adding new screen:**
1. Add screen name to state machine logic in `handle_select()`/`handle_back()`
2. Create `draw_screenname()` method
3. Add case to `draw()` method
4. Handle input in `handle_select()` with screen-specific logic

**Modifying controller mappings:**
Edit button constants in `config.py` - values are pygame button indices.

**Adjusting UI for different screen sizes:**
Modify `SCREEN_WIDTH`, `SCREEN_HEIGHT`, and font sizes in `config.py`.

**Image caching changes:**
All image loading goes through `load_image()` method - modify here for disk caching or async loading.

## Known Limitations

- Images cached in RAM only (no disk persistence)
- Search/browse limited to first page of results (no pagination)
- No authentication UI (API key must be pre-configured)
- 10 visible items max per list (hardcoded in draw methods)
- No request status checking after submission
