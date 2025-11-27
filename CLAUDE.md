# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Controller-friendly Jellyseerr interface for Raspberry Pi 4 targeting TV couch navigation. Built with pygame for framebuffer rendering (no X server required) and optimized for Xbox-style controller input.

## Development Commands

**Testing mode (windowed, keyboard fallback):**
```bash
python3 main.py
# or
./scripts/test.sh
```

**Production mode (framebuffer, fullscreen on Pi):**
```bash
SDL_VIDEODRIVER=fbcon python3 main.py
# or
./scripts/run.sh
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Setup environment:**
```bash
cp .env.example .env
# Edit .env with your Jellyseerr URL and API key
```

**View logs:**
```bash
tail -f /tmp/jellyseerr-ui.log
```

## Architecture

### Core Components

1. **main.py** - Entry point: logging setup, API connection test, UI initialization
2. **jellyseerr_api.py** - API wrapper: HTTP client with retry logic, rate limiting (30 req/min), input validation
3. **ui.py** - Main UI class: pygame event loop, screen state machine, rendering, controller input
4. **config.py** - Centralized configuration: loads from .env, validates config values, controller profiles

### Screen State Machine

The UI operates as a state machine with screens: `main_menu`, `keyboard` (on-screen input), `search_results`, `browse`, `media_detail`. Navigation uses `screen_stack` for back button functionality.

### Input System

Three parallel input systems:
- **Controller buttons** - `pygame.JOYBUTTONDOWN` events for A/B/START
- **D-pad** - `pygame.JOYHATMOTION` events for directional navigation
- **Analog stick** - Polled via `joystick.get_axis()` with 0.3 deadzone

Keyboard fallback enabled for testing. Navigation uses `NAV_DELAY` (0.2s) to prevent double-inputs.

### Controller Auto-detection

Controller profiles auto-detected by name (ui.py:234-258) with support for Xbox, PlayStation, Switch, and generic controllers. Button mappings dynamically updated based on detected profile.

### Image Loading

- On-demand loading when content selected
- In-memory LRU cache (50 items max, ~27MB)
- Tries pygame native loading, falls back to PIL if available
- TMDB poster URLs via `get_poster_url()` with configurable size
- Placeholder surface for missing images

### Non-blocking API Calls

Search and browse operations run in background threads (threading.Thread, daemon=True) to prevent UI freezing. Results update UI state via thread-safe assignment.

### Security Features

- Environment variable configuration via .env
- Input validation and sanitization (jellyseerr_api.py:46-128)
- Rate limiting (30 requests/60 seconds)
- Retry logic with exponential backoff (max 3 retries)
- Image download size limits (5MB max)
- Log file path validation to prevent directory traversal

## Configuration

Edit `.env` file before first run:
- `JELLYSEERR_BASE_URL` - Your Jellyseerr server (required)
- `JELLYSEERR_API_KEY` - Optional, leave empty if not required
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS` - Display settings (optional)

Controller button mappings assume Xbox layout by default but auto-detect based on controller name.

## Common Development Patterns

**Adding a new screen:**
1. Add screen name to state handling in `ui.py:handle_select()`/`handle_back()`
2. Create `draw_screenname()` method
3. Add case to `draw()` method
4. Handle input in `handle_select()` with screen-specific logic

**Modifying controller mappings:**
Edit `CONTROLLER_PROFILES` in `config.py` or set `CONTROLLER_PROFILE` env var.

**Adjusting for different screen sizes:**
Modify `SCREEN_WIDTH`, `SCREEN_HEIGHT`, font sizes in `.env` or `config.py`.

**Image caching changes:**
All image loading goes through `ui.py:load_image()` method (lines 169-221).

**API error handling:**
All API methods return `None` on failure and log errors. UI shows messages via `show_message()` with color-coded feedback (green=success, red=error).

## Known Limitations

- Images cached in RAM only (no disk persistence)
- Search/browse limited to first page of results (no pagination)
- No authentication UI (API key must be pre-configured in .env)
- 10 visible items max per list (hardcoded)
- No request status checking after submission

## Documentation

Complete documentation in `docs/` directory:
- `QUICKSTART.md` - Setup and first-time use
- `DEVELOPMENT.md` - Detailed architecture (contains comprehensive implementation details)
- `SECURITY_FIXES.md` - Security improvements
- `FIXES_COMPLETED.md` - Complete changelog
