"""
Configuration settings for Jellyseerr Pi UI
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Jellyseerr API Settings
JELLYSEERR_BASE_URL = os.getenv("JELLYSEERR_BASE_URL", "http://localhost:5055")
JELLYSEERR_API_URL = f"{JELLYSEERR_BASE_URL}/api/v1"
JELLYSEERR_API_KEY = os.getenv("JELLYSEERR_API_KEY", "")

# Display Settings
SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", "1920"))
SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", "1080"))
FPS = int(os.getenv("FPS", "60"))

# Colors (RGB)
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PRIMARY = (100, 200, 255)
COLOR_SELECTED = (255, 200, 0)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (150, 150, 150)
COLOR_SUCCESS = (100, 255, 100)
COLOR_ERROR = (255, 100, 100)

# Font Sizes (readable from TV distance)
FONT_SIZE_TITLE = 72
FONT_SIZE_MENU = 56
FONT_SIZE_NORMAL = 42
FONT_SIZE_SMALL = 32

# Controller Settings
CONTROLLER_DEADZONE = 0.35  # Increased to prevent stick drift triggering navigation

# Controller profiles for different controller types
CONTROLLER_PROFILES = {
    'xbox': {
        'name': 'Xbox Controller',
        'A': 0,      # Select/Confirm
        'B': 1,      # Back/Cancel
        'X': 2,
        'Y': 3,
        'START': 7   # Exit application
    },
    'playstation': {
        'name': 'PlayStation Controller',
        'A': 1,      # Cross (✕)
        'B': 2,      # Circle (○)
        'X': 0,      # Square (□)
        'Y': 3,      # Triangle (△)
        'START': 9   # Options button
    },
    'switch': {
        'name': 'Nintendo Switch Pro Controller',
        'A': 1,      # B button (Nintendo layout)
        'B': 0,      # A button (Nintendo layout)
        'X': 3,      # Y button (Nintendo layout)
        'Y': 2,      # X button (Nintendo layout)
        'START': 10  # + button
    },
    'generic': {
        'name': 'Generic Controller',
        'A': 0,
        'B': 1,
        'X': 2,
        'Y': 3,
        'START': 7
    }
}

# Auto-detect controller profile based on name
def detect_controller_profile(controller_name: str) -> str:
    """
    Detect controller type from joystick name.

    Args:
        controller_name: Name of the joystick/controller

    Returns:
        Profile name ('xbox', 'playstation', 'switch', or 'generic')
    """
    name_lower = controller_name.lower()

    if 'xbox' in name_lower or 'x-box' in name_lower:
        return 'xbox'
    elif 'playstation' in name_lower or 'ps4' in name_lower or 'ps5' in name_lower or 'dualshock' in name_lower or 'dualsense' in name_lower:
        return 'playstation'
    elif 'nintendo' in name_lower or 'switch' in name_lower or 'pro controller' in name_lower:
        return 'switch'
    else:
        return 'generic'

# Default to Xbox layout for backward compatibility
CONTROLLER_PROFILE = os.getenv("CONTROLLER_PROFILE", "xbox")
BUTTON_A = CONTROLLER_PROFILES[CONTROLLER_PROFILE]['A']
BUTTON_B = CONTROLLER_PROFILES[CONTROLLER_PROFILE]['B']
BUTTON_X = CONTROLLER_PROFILES[CONTROLLER_PROFILE]['X']
BUTTON_Y = CONTROLLER_PROFILES[CONTROLLER_PROFILE]['Y']
BUTTON_START = CONTROLLER_PROFILES[CONTROLLER_PROFILE]['START']

# Navigation timing (prevent too-fast inputs)
NAV_DELAY = 0.15  # seconds between navigation inputs (reduced for better responsiveness)

# API Settings
API_TIMEOUT = 10  # seconds
REQUEST_TIMEOUT = 5  # seconds

# Logging
LOG_FILE = os.getenv("LOG_FILE", "/tmp/jellyseerr-ui.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Image cache
IMAGE_CACHE_DIR = "/tmp/jellyseerr_cache"
IMAGE_SIZE = (300, 450)  # Poster size
MAX_IMAGE_CACHE_SIZE = 50  # Maximum number of cached images
MAX_IMAGE_DOWNLOAD_SIZE = 5 * 1024 * 1024  # 5MB max per image

# UI Display Constants
MAX_VISIBLE_LIST_ITEMS = 10  # Maximum items shown in lists
MAX_BROWSE_ITEMS_PER_TYPE = 10  # Max movies/TV shows in browse
MAX_TITLE_CHARS = 40  # Title truncation length
MAX_WRAPPED_TEXT_LINES = 8  # Max lines for wrapped text
POSTER_PREVIEW_WIDTH = 200  # Width of poster preview


def validate_config():
    """
    Validate configuration values for sanity.

    Raises:
        ValueError: If configuration values are invalid
    """
    errors = []

    # Validate URL format
    if not JELLYSEERR_BASE_URL.startswith(('http://', 'https://')):
        errors.append("JELLYSEERR_BASE_URL must start with http:// or https://")

    # Validate screen dimensions
    if SCREEN_WIDTH <= 0 or SCREEN_HEIGHT <= 0:
        errors.append(f"Screen dimensions must be positive (got {SCREEN_WIDTH}x{SCREEN_HEIGHT})")

    if SCREEN_WIDTH > 7680 or SCREEN_HEIGHT > 4320:  # 8K max
        errors.append(f"Screen dimensions unreasonably large ({SCREEN_WIDTH}x{SCREEN_HEIGHT})")

    # Validate FPS
    if not 1 <= FPS <= 120:
        errors.append(f"FPS must be between 1 and 120 (got {FPS})")

    # Validate controller deadzone
    if not 0 < CONTROLLER_DEADZONE < 1:
        errors.append(f"CONTROLLER_DEADZONE must be between 0 and 1 (got {CONTROLLER_DEADZONE})")

    # Validate timeouts
    if API_TIMEOUT <= 0 or REQUEST_TIMEOUT <= 0:
        errors.append("Timeout values must be positive")

    if API_TIMEOUT > 300 or REQUEST_TIMEOUT > 60:
        errors.append("Timeout values unreasonably large")

    # Validate navigation delay
    if NAV_DELAY < 0 or NAV_DELAY > 2:
        errors.append(f"NAV_DELAY should be between 0 and 2 seconds (got {NAV_DELAY})")

    # Validate image size
    if IMAGE_SIZE[0] <= 0 or IMAGE_SIZE[1] <= 0:
        errors.append(f"IMAGE_SIZE dimensions must be positive (got {IMAGE_SIZE})")

    # Validate cache settings
    if MAX_IMAGE_CACHE_SIZE < 1 or MAX_IMAGE_CACHE_SIZE > 1000:
        errors.append(f"MAX_IMAGE_CACHE_SIZE should be between 1 and 1000 (got {MAX_IMAGE_CACHE_SIZE})")

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


# Validate configuration on import
try:
    validate_config()
except ValueError as e:
    print(f"WARNING: {e}")
    print("Using potentially invalid configuration values.")
