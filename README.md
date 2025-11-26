# Jellyseerr Pi UI

Controller-friendly Jellyseerr interface for Raspberry Pi 4, designed for couch navigation on TVs.

## Quick Start

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
nano .env  # Add your Jellyseerr URL and API key
```

**3. Run application:**
```bash
# Testing mode (windowed)
python3 main.py

# Production mode (Pi framebuffer)
SDL_VIDEODRIVER=fbcon python3 main.py
```

## Features

- **Controller Support**: Auto-detects Xbox, PlayStation, Switch, and generic controllers
- **Non-blocking UI**: Background API calls prevent UI freezing
- **Smart Caching**: LRU image cache with 50 item limit (~27MB max)
- **Secure**: Environment variable configuration, input validation, HTTPS enforcement
- **Reliable**: Retry logic with exponential backoff, rate limiting (30 req/min)

## Requirements

- Raspberry Pi 4 (or any Linux system)
- Python 3.6+
- pygame 1.9.4+
- Jellyseerr server instance

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Detailed setup instructions
- **[Development Guide](docs/DEVELOPMENT.md)** - Architecture and development patterns
- **[Security Fixes](docs/SECURITY_FIXES.md)** - Security improvements applied
- **[Complete Changelog](docs/FIXES_COMPLETED.md)** - All 30 fixes (94% technical debt reduction)

## Project Status

**Production Ready** - All critical and high severity issues resolved.

- ✅ 8/8 Critical severity fixes
- ✅ 10/10 High severity fixes
- ✅ 12/14 Medium severity fixes
- **94% technical debt reduction** (30/32 issues fixed)

## License

This project is provided as-is for personal use.

## Support

For issues or questions, see the development documentation in `docs/DEVELOPMENT.md`.
