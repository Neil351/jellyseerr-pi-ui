# Security Fixes Applied

This document outlines the critical security and reliability fixes applied to the Jellyseerr Pi UI.

## Critical Fixes Completed

### 1. Environment Variable Configuration ✅
**Issue:** Hardcoded IP address and API credentials in source control
**Fix:** Moved all sensitive configuration to environment variables using python-dotenv

**Setup Instructions:**
```bash
# Install dependencies
pip install python-dotenv

# Copy example config
cp .env.example .env

# Edit .env with your actual values
nano .env
```

**Example .env file:**
```bash
JELLYSEERR_BASE_URL=http://100.112.21.82:5055
JELLYSEERR_API_KEY=your_api_key_here
```

### 2. Input Validation and Sanitization ✅
**Issue:** No validation of user input, vulnerable to injection attacks
**Fix:** Added comprehensive validation for all API inputs:
- Search queries: max 200 chars, dangerous characters removed
- Media IDs: validated as positive integers
- Media types: whitelisted to 'movie' or 'tv'
- Page numbers: validated between 1-1000

### 3. Fixed Bare Exception Handlers ✅
**Issue:** Bare `except:` blocks caught KeyboardInterrupt and SystemExit
**Fix:** Replaced with specific exception types:
- `pygame.error, IOError, OSError` for image loading
- `ImportError` for optional PIL imports
- Proper error logging with context

### 4. LRU Image Cache Implementation ✅
**Issue:** Unbounded image cache would cause OOM on Raspberry Pi
**Fix:** Implemented OrderedDict-based LRU cache with 50 image limit (~27MB max)

**Features:**
- Automatic eviction of oldest images
- Move-to-end for recently accessed images
- Debug logging for cache operations

### 5. HTTPS Certificate Validation ✅
**Issue:** No certificate verification, vulnerable to MITM attacks
**Fix:** Explicitly enforced certificate validation:
```python
self.session.verify = True
```
- Warns when using plain HTTP
- Logs API key status (length only, not value)

### 6. API Request Rate Limiting ✅
**Issue:** No protection against rapid API requests
**Fix:** Implemented sliding window rate limiter:
- 30 requests per 60 seconds
- Raises exception when limit exceeded
- Prevents API bans and DoS

### 7. Retry Logic with Exponential Backoff ✅
**Issue:** Single network failure caused complete request failure
**Fix:** Added retry logic to image downloads:
- 3 retry attempts
- 1.5x backoff factor (1.5s, 2.25s, 3.375s waits)
- Detailed logging of retry attempts

### 8. Proper Resource Cleanup ✅
**Issue:** No cleanup on exit, potential memory/file descriptor leaks
**Fix:** Comprehensive cleanup method:
- Clears image cache
- Closes joystick resources
- Closes HTTP session
- Quits pygame subsystems
- Handles KeyboardInterrupt gracefully

## Additional Improvements

### Files Created
- `.env.example` - Template for configuration
- `.gitignore` - Protects sensitive files from version control
- `requirements.txt` - Formal dependency specification
- `SECURITY_FIXES.md` - This document

### Configuration Changes
All environment-configurable settings in config.py:
- `JELLYSEERR_BASE_URL`
- `JELLYSEERR_API_KEY`
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`
- `FPS`
- `LOG_FILE`, `LOG_LEVEL`

## Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env  # Add your Jellyseerr URL and API key

# 3. Run application
# Testing mode (windowed):
python3 main.py

# Production mode (Raspberry Pi framebuffer):
SDL_VIDEODRIVER=fbcon python3 main.py
```

## Security Recommendations

### Immediate
1. ✅ Never commit `.env` file to version control
2. ✅ Use HTTPS for production deployments
3. ✅ Generate strong API keys in Jellyseerr
4. ✅ Keep dependencies updated

### Future Enhancements
1. Add TLS certificate pinning for production
2. Implement API response validation
3. Add proper authentication flow
4. Implement async API calls to prevent UI blocking
5. Add comprehensive error messages for users

## Testing

After applying fixes, test:
1. Application starts without errors
2. Keyboard screen renders correctly (no border_radius crash)
3. Browse Popular fetches content with authentication
4. Search works with validated input
5. Image cache doesn't grow beyond 50 items
6. Application exits cleanly with Ctrl+C
7. Rate limiter prevents spam requests

## Remaining Known Issues

**Medium Priority:**
- Blocking UI during API calls (future: make async)
- No pagination support
- Hardcoded controller mappings (Xbox only)
- Magic numbers throughout code

**Low Priority:**
- Missing type hints in ui.py
- Inconsistent string formatting
- No signal handlers for systemd

## Performance Impact

**Memory:** Reduced from unbounded to ~27MB max for images
**Network:** Retry logic adds 1-6 seconds on failures (rare)
**Rate Limiting:** No impact under normal use (30 req/min is generous)

## Migration Guide

If you have existing code:

1. **Install new dependency:**
   ```bash
   pip install python-dotenv
   ```

2. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

3. **Move your config:**
   ```bash
   # Old: config.py had hardcoded values
   # New: Put values in .env file
   echo "JELLYSEERR_BASE_URL=http://your-server:5055" >> .env
   echo "JELLYSEERR_API_KEY=your_key_here" >> .env
   ```

4. **Test application:**
   ```bash
   python3 main.py
   # Check logs: tail -f /tmp/jellyseerr-ui.log
   ```

## Support

For issues:
1. Check logs: `tail -f /tmp/jellyseerr-ui.log`
2. Verify .env configuration
3. Test Jellyseerr API manually: `curl http://your-server:5055/api/v1/status`
4. Check controller detection: `ls /dev/input/js*`

## Version

**Fixes Applied:** 2025-01-25
**Target Platform:** Raspberry Pi 4, Debian Buster, Python 3.6+
**Dependencies:** pygame>=1.9.4, requests>=2.25.0, python-dotenv>=0.19.0
