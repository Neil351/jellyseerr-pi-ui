"""
Pygame UI for Jellyseerr - Controller-friendly interface
"""
import pygame
import logging
import time
import os
import threading
from typing import Optional, List, Dict, Tuple
from collections import OrderedDict
import config
from jellyseerr_api import JellyseerrAPI

logger = logging.getLogger(__name__)

# Check PIL availability at import time
try:
    from PIL import Image
    PIL_AVAILABLE = True
    logger.info("PIL/Pillow is available for image processing")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available - some images may not load correctly")
    logger.warning("Install with: pip install Pillow")


def load_font_safely(size: int, font_name: Optional[str] = None) -> pygame.font.Font:
    """
    Load pygame font with fallback support.

    Args:
        size: Font size in pixels
        font_name: Optional font file path

    Returns:
        pygame.font.Font object

    Raises:
        RuntimeError: If no fonts can be loaded
    """
    try:
        if font_name:
            # Try to load specific font file
            return pygame.font.Font(font_name, size)
        else:
            # Try default system font
            return pygame.font.Font(None, size)
    except (pygame.error, IOError, OSError) as e:
        logger.warning(f"Failed to load font (size={size}, name={font_name}): {e}")
        try:
            # Fallback to pygame default font
            logger.info("Falling back to pygame default font")
            return pygame.font.Font(pygame.font.get_default_font(), size)
        except Exception as e:
            # Last resort: try SysFont
            logger.warning(f"Default font failed, trying SysFont: {e}")
            try:
                return pygame.font.SysFont('arial,helvetica,sans-serif', size)
            except Exception as e:
                raise RuntimeError(f"Could not load any font: {e}")


class JellyseerrUI:
    """Main UI controller"""

    def __init__(self, api: JellyseerrAPI):
        self.api = api
        self.running = True
        self.clock = pygame.time.Clock()

        # Initialize pygame
        pygame.init()
        pygame.joystick.init()

        # Setup display (framebuffer mode on Pi, windowed for testing)
        if os.environ.get('SDL_VIDEODRIVER') == 'fbcon':
            # Running on Pi framebuffer
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                pygame.FULLSCREEN
            )
        else:
            # Testing mode - windowed
            self.screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            )

        pygame.display.set_caption("Jellyseerr")
        pygame.mouse.set_visible(False)

        # Setup fonts with fallback support
        try:
            self.font_title = load_font_safely(config.FONT_SIZE_TITLE)
            self.font_menu = load_font_safely(config.FONT_SIZE_MENU)
            self.font_normal = load_font_safely(config.FONT_SIZE_NORMAL)
            self.font_small = load_font_safely(config.FONT_SIZE_SMALL)
            logger.info("Fonts loaded successfully")
        except RuntimeError as e:
            logger.error(f"Critical error loading fonts: {e}")
            raise

        # Controller setup
        self.joystick = None
        self.setup_controller()

        # Navigation timing (thread-safe)
        self.last_nav_time = 0
        self._nav_lock = threading.Lock()

        # Current screen state
        self.current_screen = "main_menu"
        self.screen_stack = []  # For back navigation

        # UI state
        self.menu_items = []
        self.selected_index = 0
        self.message = None
        self.message_color = config.COLOR_TEXT
        self.message_time = 0

        # Scheduled actions (non-blocking)
        self.scheduled_back_time = None

        # Search state
        self.search_query = ""
        self.search_results = []

        # On-screen keyboard state
        self.keyboard_layout = [
            ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            ['k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
            ['u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4'],
            ['5', '6', '7', '8', '9', '0', ' ', 'DEL', 'SEARCH', 'CANCEL']
        ]
        self.keyboard_row = 0
        self.keyboard_col = 0

        # Browse state
        self.browse_results = []
        self.browse_page = 1
        self.browse_type = None  # 'movie' or 'tv'

        # Selected media
        self.selected_media = None

        # Image cache with LRU eviction
        self.image_cache = OrderedDict()
        self.max_cache_size = config.MAX_IMAGE_CACHE_SIZE
        self.placeholder_image = self.create_placeholder_image()

        logger.info("UI initialized")

    def create_placeholder_image(self):
        """Create a placeholder image for missing posters with safe dimensions"""
        # Validate IMAGE_SIZE to prevent division by zero
        width, height = config.IMAGE_SIZE
        if width <= 0 or height <= 0:
            logger.error(f"Invalid IMAGE_SIZE: {config.IMAGE_SIZE}, using fallback (300, 450)")
            width, height = 300, 450

        surf = pygame.Surface((width, height))
        surf.fill((60, 60, 80))
        # Draw "No Image" text
        text = self.font_small.render("No Image", True, config.COLOR_TEXT_DIM)
        text_rect = text.get_rect(center=(width // 2, height // 2))
        surf.blit(text, text_rect)
        return surf

    def load_image(self, url: str) -> pygame.Surface:
        """Load image from URL with LRU caching"""
        if not url:
            return self.placeholder_image

        # Check cache
        if url in self.image_cache:
            # Move to end (most recently used)
            self.image_cache.move_to_end(url)
            return self.image_cache[url]

        # Download and load image
        try:
            image_data = self.api.download_image(url)
            if image_data:
                import io

                # Try to load with pygame directly first
                try:
                    pygame_image = pygame.image.load(io.BytesIO(image_data))
                    # Scale to target size
                    pygame_image = pygame.transform.scale(pygame_image, config.IMAGE_SIZE)

                    # Add to cache with LRU eviction
                    self._add_to_cache(url, pygame_image)
                    return pygame_image
                except (pygame.error, IOError, OSError) as e:
                    # Fallback to PIL if available
                    if PIL_AVAILABLE:
                        logger.debug(f"Pygame image load failed, trying PIL: {e}")
                        try:
                            pil_image = Image.open(io.BytesIO(image_data))
                            pil_image = pil_image.resize(config.IMAGE_SIZE)

                            # Convert to pygame surface
                            mode = pil_image.mode
                            size = pil_image.size
                            data = pil_image.tobytes()

                            pygame_image = pygame.image.fromstring(data, size, mode)

                            # Add to cache with LRU eviction
                            self._add_to_cache(url, pygame_image)
                            return pygame_image
                        except (IOError, OSError, ValueError) as e:
                            logger.warning(f"PIL image loading failed for {url}: {e}")
                    else:
                        logger.debug(f"PIL not available, cannot retry image load for {url}")
        except Exception as e:
            logger.warning(f"Failed to load image from {url}: {e}")

        # Return placeholder on failure
        return self.placeholder_image

    def _add_to_cache(self, url: str, image: pygame.Surface):
        """Add image to cache with LRU eviction"""
        # Evict oldest item if cache is full
        if len(self.image_cache) >= self.max_cache_size:
            oldest_url = next(iter(self.image_cache))
            logger.debug(f"Cache full, evicting oldest image: {oldest_url}")
            self.image_cache.popitem(last=False)

        # Add new image
        self.image_cache[url] = image

    def setup_controller(self):
        """Initialize game controller with auto-detection"""
        num_joysticks = pygame.joystick.get_count()
        if num_joysticks > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            controller_name = self.joystick.get_name()

            # Auto-detect controller profile
            detected_profile = config.detect_controller_profile(controller_name)
            profile_info = config.CONTROLLER_PROFILES[detected_profile]

            logger.info(f"Controller detected: {controller_name}")
            logger.info(f"Using profile: {profile_info['name']} ({detected_profile})")

            # Update button mappings dynamically
            config.BUTTON_A = profile_info['A']
            config.BUTTON_B = profile_info['B']
            config.BUTTON_X = profile_info['X']
            config.BUTTON_Y = profile_info['Y']
            config.BUTTON_START = profile_info['START']

            logger.info(f"Button mappings: A={config.BUTTON_A}, B={config.BUTTON_B}, START={config.BUTTON_START}")
        else:
            logger.warning("No controller detected - keyboard fallback enabled")

    def show_message(self, message: str, color=None, duration: float = 3.0):
        """Display a temporary message"""
        self.message = message
        self.message_color = color or config.COLOR_TEXT
        self.message_time = time.time() + duration
        logger.info(f"Message: {message}")

    def can_navigate(self) -> bool:
        """Check if enough time has passed for navigation (thread-safe)"""
        with self._nav_lock:
            current_time = time.time()
            if current_time - self.last_nav_time > config.NAV_DELAY:
                self.last_nav_time = current_time
                return True
            return False

    def handle_input(self):
        """Handle controller and keyboard input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Button presses
            elif event.type == pygame.JOYBUTTONDOWN:
                self.handle_button_press(event.button)

            # D-pad (hat) navigation
            elif event.type == pygame.JOYHATMOTION:
                if self.can_navigate():
                    self.handle_dpad_motion(event.value)

            # Keyboard fallback for testing
            elif event.type == pygame.KEYDOWN:
                self.handle_keyboard(event.key)

        # Handle analog stick for navigation
        if self.joystick:
            self.handle_analog_navigation()

    def handle_dpad_motion(self, value: Tuple[int, int]):
        """Handle D-pad (hat) motion"""
        x, y = value

        if self.current_screen == "keyboard":
            # 2D navigation on keyboard
            if y == 1:  # Up
                self.keyboard_row = max(0, self.keyboard_row - 1)
            elif y == -1:  # Down
                self.keyboard_row = min(len(self.keyboard_layout) - 1, self.keyboard_row + 1)

            if x == -1:  # Left
                self.keyboard_col = max(0, self.keyboard_col - 1)
            elif x == 1:  # Right
                max_col = len(self.keyboard_layout[self.keyboard_row]) - 1
                self.keyboard_col = min(max_col, self.keyboard_col + 1)
        else:
            # Vertical navigation
            if y == 1:  # Up
                self.navigate(-1)
            elif y == -1:  # Down
                self.navigate(1)

    def handle_button_press(self, button: int):
        """Handle controller button press"""
        if button == config.BUTTON_START:
            # Exit application
            self.running = False

        elif button == config.BUTTON_A:
            # Confirm/Select
            self.handle_select()

        elif button == config.BUTTON_B:
            # Back/Cancel
            self.handle_back()

    def handle_keyboard(self, key: int):
        """Keyboard fallback for testing"""
        # Handle text input on keyboard screen
        if self.current_screen == "keyboard":
            # Arrow keys navigate the on-screen keyboard
            if key == pygame.K_UP:
                if self.can_navigate():
                    self.keyboard_row = max(0, self.keyboard_row - 1)
            elif key == pygame.K_DOWN:
                if self.can_navigate():
                    self.keyboard_row = min(len(self.keyboard_layout) - 1, self.keyboard_row + 1)
            elif key == pygame.K_LEFT:
                if self.can_navigate():
                    self.keyboard_col = max(0, self.keyboard_col - 1)
            elif key == pygame.K_RIGHT:
                if self.can_navigate():
                    max_col = len(self.keyboard_layout[self.keyboard_row]) - 1
                    self.keyboard_col = min(max_col, self.keyboard_col + 1)
            elif key == pygame.K_RETURN:
                # Submit search or select key
                self.handle_keyboard_select()
            elif key == pygame.K_ESCAPE:
                # Cancel search
                self.handle_back()
            elif key == pygame.K_BACKSPACE:
                # Delete character
                self.search_query = self.search_query[:-1]
            elif key == pygame.K_SPACE:
                self.search_query += " "
            elif pygame.K_a <= key <= pygame.K_z:
                # Add letter
                char = chr(key)
                self.search_query += char
            elif pygame.K_0 <= key <= pygame.K_9:
                # Add number
                char = chr(key)
                self.search_query += char
            return

        # Normal navigation
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            self.handle_select()
        elif key == pygame.K_BACKSPACE:
            self.handle_back()
        elif key == pygame.K_UP:
            if self.can_navigate():
                self.navigate(-1)
        elif key == pygame.K_DOWN:
            if self.can_navigate():
                self.navigate(1)

    def handle_analog_navigation(self):
        """Handle analog stick navigation"""
        if not self.joystick or not self.can_navigate():
            return

        # Get axes
        y_axis = self.joystick.get_axis(1)
        x_axis = self.joystick.get_axis(0)

        # Keyboard screen uses 2D navigation
        if self.current_screen == "keyboard":
            if abs(y_axis) > config.CONTROLLER_DEADZONE:
                if y_axis < 0:  # Up
                    self.keyboard_row = max(0, self.keyboard_row - 1)
                else:  # Down
                    self.keyboard_row = min(len(self.keyboard_layout) - 1, self.keyboard_row + 1)

            if abs(x_axis) > config.CONTROLLER_DEADZONE:
                if x_axis < 0:  # Left
                    self.keyboard_col = max(0, self.keyboard_col - 1)
                else:  # Right
                    max_col = len(self.keyboard_layout[self.keyboard_row]) - 1
                    self.keyboard_col = min(max_col, self.keyboard_col + 1)
        else:
            # Normal vertical navigation
            if abs(y_axis) > config.CONTROLLER_DEADZONE:
                if y_axis < 0:  # Up
                    self.navigate(-1)
                else:  # Down
                    self.navigate(1)

    def navigate(self, direction: int):
        """Navigate menu items with safe boundary checking"""
        # Determine which list to use based on current screen
        if self.current_screen == "main_menu":
            items = self.menu_items
        elif self.current_screen == "search_results":
            items = self.search_results
        elif self.current_screen == "browse":
            items = self.browse_results
        else:
            # For other screens (keyboard, media_detail), no list navigation
            return

        if not items:
            self.selected_index = 0
            return

        # Clamp direction to -1, 0, or 1
        direction = max(-1, min(1, direction))

        new_index = self.selected_index + direction

        # Wrap around with explicit bounds checking
        if new_index < 0:
            new_index = len(items) - 1
        elif new_index >= len(items):
            new_index = 0

        self.selected_index = new_index

    def handle_select(self):
        """Handle selection action"""
        if self.current_screen == "main_menu":
            self.handle_main_menu_select()
        elif self.current_screen == "search_results":
            self.handle_search_result_select()
        elif self.current_screen == "browse":
            self.handle_browse_select()
        elif self.current_screen == "media_detail":
            self.handle_media_detail_select()
        elif self.current_screen == "keyboard":
            self.handle_keyboard_select()

    def handle_back(self):
        """Handle back action"""
        if self.screen_stack:
            self.current_screen = self.screen_stack.pop()
            self.selected_index = 0
        else:
            # Go to main menu or exit
            if self.current_screen != "main_menu":
                self.current_screen = "main_menu"
                self.selected_index = 0

    def handle_main_menu_select(self):
        """Handle main menu selection"""
        if self.selected_index == 0:  # Search Movies
            self.screen_stack.append(self.current_screen)
            self.current_screen = "keyboard"
            self.browse_type = "movie"
            self.search_query = ""
        elif self.selected_index == 1:  # Search TV Shows
            self.screen_stack.append(self.current_screen)
            self.current_screen = "keyboard"
            self.browse_type = "tv"
            self.search_query = ""
        elif self.selected_index == 2:  # Browse Popular
            self.screen_stack.append(self.current_screen)
            self.current_screen = "browse"
            self.load_popular_content()
        elif self.selected_index == 3:  # Exit
            self.running = False

    def handle_search_result_select(self):
        """Handle search result selection"""
        if 0 <= self.selected_index < len(self.search_results):
            self.selected_media = self.search_results[self.selected_index]
            self.screen_stack.append(self.current_screen)
            self.current_screen = "media_detail"

    def handle_browse_select(self):
        """Handle browse selection"""
        if 0 <= self.selected_index < len(self.browse_results):
            self.selected_media = self.browse_results[self.selected_index]
            self.screen_stack.append(self.current_screen)
            self.current_screen = "media_detail"

    def handle_media_detail_select(self):
        """Handle media detail action - request content"""
        if self.selected_media:
            media_type = self.selected_media.get('mediaType', 'movie')
            media_id = self.selected_media.get('id')

            if self.api.request_media(media_id, media_type):
                self.show_message("Request submitted successfully!", config.COLOR_SUCCESS)
                # Schedule non-blocking back navigation after 1.5 seconds
                self.scheduled_back_time = time.time() + 1.5
            else:
                self.show_message("Failed to submit request", config.COLOR_ERROR)

    def handle_keyboard_select(self):
        """Handle on-screen keyboard selection"""
        if self.keyboard_row >= len(self.keyboard_layout):
            return

        row = self.keyboard_layout[self.keyboard_row]
        if self.keyboard_col >= len(row):
            return

        key = row[self.keyboard_col]

        if key == 'SEARCH':
            # Submit search
            if self.search_query.strip():
                self.perform_search(self.search_query)
        elif key == 'CANCEL':
            # Cancel and go back
            self.handle_back()
        elif key == 'DEL':
            # Delete last character
            self.search_query = self.search_query[:-1]
        elif key == ' ':
            # Add space
            self.search_query += ' '
        else:
            # Add character
            self.search_query += key

    def load_popular_content(self):
        """Load popular movies and TV shows (non-blocking)"""
        self.show_message("Loading popular content...", config.COLOR_PRIMARY)

        def load_in_background():
            """Background thread for API calls"""
            try:
                # Get popular movies and TV shows
                movies = self.api.get_popular_movies(page=1)
                tv_shows = self.api.get_popular_tv(page=1)

                # Update results (thread-safe assignment)
                results = []
                if movies:
                    results.extend(movies[:config.MAX_BROWSE_ITEMS_PER_TYPE])
                if tv_shows:
                    results.extend(tv_shows[:config.MAX_BROWSE_ITEMS_PER_TYPE])

                self.browse_results = results

                # Update UI state
                if self.browse_results:
                    self.message = None
                    self.selected_index = 0
                else:
                    self.show_message("No content found", config.COLOR_ERROR)

                logger.info(f"Loaded {len(self.browse_results)} popular items")
            except Exception as e:
                logger.error(f"Error loading popular content: {e}")
                self.show_message("Error loading content", config.COLOR_ERROR)

        # Start background thread
        thread = threading.Thread(target=load_in_background, daemon=True, name="LoadPopularContent")
        thread.start()
        logger.debug("Started background thread for popular content")

    def perform_search(self, query: str):
        """Perform search based on browse type (non-blocking)"""
        self.show_message(f"Searching for '{query}'...", config.COLOR_PRIMARY)

        def search_in_background():
            """Background thread for search API call"""
            try:
                # Perform search based on type
                if self.browse_type == "movie":
                    results = self.api.search_movies(query)
                else:
                    results = self.api.search_tv(query)

                # Update UI state (thread-safe)
                if results:
                    self.search_results = results
                    self.current_screen = "search_results"
                    self.selected_index = 0
                    self.message = None
                    logger.info(f"Found {len(results)} results for '{query}'")
                else:
                    self.show_message("No results found", config.COLOR_ERROR)
            except Exception as e:
                logger.error(f"Error performing search: {e}")
                self.show_message("Search error", config.COLOR_ERROR)

        # Start background thread
        thread = threading.Thread(target=search_in_background, daemon=True, name="PerformSearch")
        thread.start()
        logger.debug(f"Started background thread for search: '{query}'")

    def draw(self):
        """Main draw function"""
        self.screen.fill(config.COLOR_BACKGROUND)

        if self.current_screen == "main_menu":
            self.draw_main_menu()
        elif self.current_screen == "search_results":
            self.draw_search_results()
        elif self.current_screen == "browse":
            self.draw_browse()
        elif self.current_screen == "media_detail":
            self.draw_media_detail()
        elif self.current_screen == "keyboard":
            self.draw_keyboard()

        # Draw message if active
        if self.message and time.time() < self.message_time:
            self.draw_centered_message(self.message, self.message_color)

        pygame.display.flip()

    def draw_main_menu(self):
        """Draw main menu"""
        # Title
        title = self.font_title.render("JELLYSEERR", True, config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Menu items
        self.menu_items = [
            "Search Movies",
            "Search TV Shows",
            "Browse Popular",
            "Exit"
        ]

        y_start = 400
        y_spacing = 100

        for i, item in enumerate(self.menu_items):
            color = config.COLOR_SELECTED if i == self.selected_index else config.COLOR_TEXT
            text = self.font_menu.render(item, True, color)
            text_rect = text.get_rect(center=(config.SCREEN_WIDTH // 2, y_start + i * y_spacing))

            # Draw selection indicator
            if i == self.selected_index:
                indicator = self.font_menu.render(">", True, config.COLOR_SELECTED)
                indicator_rect = indicator.get_rect(right=text_rect.left - 20, centery=text_rect.centery)
                self.screen.blit(indicator, indicator_rect)

            self.screen.blit(text, text_rect)

        # Controls hint
        hint = self.font_small.render("A: Select  |  B: Back  |  START: Exit", True, config.COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def draw_search_results(self):
        """Draw search results"""
        # Title
        title_text = f"Search Results ({len(self.search_results)})"
        title = self.font_title.render(title_text, True, config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        if not self.search_results:
            return

        # Show selected item with poster on left side
        selected_item = self.search_results[self.selected_index] if self.selected_index < len(self.search_results) else None

        if selected_item:
            # Draw poster
            poster_path = selected_item.get('posterPath')
            if poster_path:
                poster_url = self.api.get_poster_url(poster_path)
                poster_image = self.load_image(poster_url)
            else:
                poster_image = self.placeholder_image

            poster_x = 100
            poster_y = 200
            self.screen.blit(poster_image, (poster_x, poster_y))

        # Results list on right side
        list_x = 500
        y_start = 200
        y_spacing = 70
        visible_items = 10

        scroll_offset = max(0, self.selected_index - visible_items // 2)

        for i in range(scroll_offset, min(scroll_offset + visible_items, len(self.search_results))):
            item = self.search_results[i]
            display_index = i - scroll_offset

            color = config.COLOR_SELECTED if i == self.selected_index else config.COLOR_TEXT
            title_text = item.get('title') or item.get('name', 'Unknown')
            year = item.get('releaseDate', '')[:4] if item.get('releaseDate') else ''

            # Truncate long titles
            max_chars = 40
            if len(title_text) > max_chars:
                title_text = title_text[:max_chars - 3] + "..."

            text_str = f"{title_text} ({year})" if year else title_text
            text = self.font_normal.render(text_str, True, color)
            text_rect = text.get_rect(left=list_x, top=y_start + display_index * y_spacing)

            # Selection indicator
            if i == self.selected_index:
                indicator = self.font_normal.render(">", True, config.COLOR_SELECTED)
                indicator_rect = indicator.get_rect(right=text_rect.left - 20, centery=text_rect.centery)
                self.screen.blit(indicator, indicator_rect)

            self.screen.blit(text, text_rect)

        # Controls hint
        hint = self.font_small.render("A: View Details  |  B: Back", True, config.COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def draw_browse(self):
        """Draw browse popular content"""
        # Title
        title = self.font_title.render("Popular Content", True, config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        if not self.browse_results:
            return

        # Show selected item with poster on left side
        selected_item = self.browse_results[self.selected_index] if self.selected_index < len(self.browse_results) else None

        if selected_item:
            # Draw poster
            poster_path = selected_item.get('posterPath')
            if poster_path:
                poster_url = self.api.get_poster_url(poster_path)
                poster_image = self.load_image(poster_url)
            else:
                poster_image = self.placeholder_image

            poster_x = 100
            poster_y = 200
            self.screen.blit(poster_image, (poster_x, poster_y))

        # Results list on right side
        list_x = 500
        y_start = 200
        y_spacing = 70
        visible_items = 10

        scroll_offset = max(0, self.selected_index - visible_items // 2)

        for i in range(scroll_offset, min(scroll_offset + visible_items, len(self.browse_results))):
            item = self.browse_results[i]
            display_index = i - scroll_offset

            color = config.COLOR_SELECTED if i == self.selected_index else config.COLOR_TEXT
            title_text = item.get('title') or item.get('name', 'Unknown')
            media_type = item.get('mediaType', 'unknown').upper()

            # Truncate long titles
            max_chars = 40
            if len(title_text) > max_chars:
                title_text = title_text[:max_chars - 3] + "..."

            text_str = f"[{media_type}] {title_text}"
            text = self.font_normal.render(text_str, True, color)
            text_rect = text.get_rect(left=list_x, top=y_start + display_index * y_spacing)

            if i == self.selected_index:
                indicator = self.font_normal.render(">", True, config.COLOR_SELECTED)
                indicator_rect = indicator.get_rect(right=text_rect.left - 20, centery=text_rect.centery)
                self.screen.blit(indicator, indicator_rect)

            self.screen.blit(text, text_rect)

        # Controls hint
        hint = self.font_small.render("A: View Details  |  B: Back", True, config.COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def draw_media_detail(self):
        """Draw media detail screen"""
        if not self.selected_media:
            return

        # Draw poster on left
        poster_path = self.selected_media.get('posterPath')
        if poster_path:
            poster_url = self.api.get_poster_url(poster_path)
            poster_image = self.load_image(poster_url)
        else:
            poster_image = self.placeholder_image

        poster_x = 100
        poster_y = 150
        self.screen.blit(poster_image, (poster_x, poster_y))

        # Details on right
        detail_x = 500
        y_pos = 150

        # Title
        title = self.selected_media.get('title') or self.selected_media.get('name', 'Unknown')
        # Wrap title if too long
        max_title_width = config.SCREEN_WIDTH - detail_x - 100
        title_surf = self.font_title.render(title, True, config.COLOR_PRIMARY)
        if title_surf.get_width() > max_title_width:
            # Use smaller font for long titles
            title_surf = self.font_menu.render(title, True, config.COLOR_PRIMARY)

        self.screen.blit(title_surf, (detail_x, y_pos))
        y_pos += 100

        # Details
        details = [
            f"Type: {self.selected_media.get('mediaType', 'unknown').upper()}",
            f"Release: {self.selected_media.get('releaseDate', 'Unknown')[:10]}",
            f"Rating: {self.selected_media.get('voteAverage', 'N/A')}/10"
        ]

        for detail in details:
            detail_surf = self.font_normal.render(detail, True, config.COLOR_TEXT)
            self.screen.blit(detail_surf, (detail_x, y_pos))
            y_pos += 60

        # Overview
        y_pos += 20
        overview = self.selected_media.get('overview', 'No description available.')
        self.draw_wrapped_text(overview, detail_x, y_pos, config.SCREEN_WIDTH - detail_x - 100, config.COLOR_TEXT_DIM)

        # Action prompt
        y_pos = config.SCREEN_HEIGHT - 150
        prompt = self.font_menu.render("Press A to Request This Content", True, config.COLOR_SUCCESS)
        prompt_rect = prompt.get_rect(center=(config.SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(prompt, prompt_rect)

        # Controls hint
        hint = self.font_small.render("B: Back to Browse", True, config.COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def draw_keyboard(self):
        """Draw on-screen keyboard for search"""
        # Title
        title_text = f"Search {self.browse_type.upper()}S"
        title = self.font_title.render(title_text, True, config.COLOR_PRIMARY)
        title_rect = title.get_rect(center=(config.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        # Current query
        query_text = f"{self.search_query}_"
        query = self.font_menu.render(query_text, True, config.COLOR_TEXT)
        query_rect = query.get_rect(center=(config.SCREEN_WIDTH // 2, 200))
        self.screen.blit(query, query_rect)

        # Keyboard grid
        key_width = 140
        key_height = 100
        key_spacing = 20
        start_x = 200
        start_y = 350

        for row_idx, row in enumerate(self.keyboard_layout):
            # Center each row
            row_width = len(row) * (key_width + key_spacing) - key_spacing
            row_start_x = (config.SCREEN_WIDTH - row_width) // 2

            for col_idx, key in enumerate(row):
                x = row_start_x + col_idx * (key_width + key_spacing)
                y = start_y + row_idx * (key_height + key_spacing)

                # Determine if this key is selected
                is_selected = (row_idx == self.keyboard_row and col_idx == self.keyboard_col)

                # Draw key background
                key_color = config.COLOR_SELECTED if is_selected else (60, 60, 80)
                pygame.draw.rect(self.screen, key_color, (x, y, key_width, key_height))

                # Draw key border
                border_color = config.COLOR_PRIMARY if is_selected else (100, 100, 120)
                pygame.draw.rect(self.screen, border_color, (x, y, key_width, key_height), 3)

                # Draw key label
                # Use smaller font for special keys
                if len(key) > 1:
                    key_surf = self.font_small.render(key, True, config.COLOR_TEXT)
                else:
                    key_surf = self.font_menu.render(key.upper(), True, config.COLOR_TEXT)

                key_rect = key_surf.get_rect(center=(x + key_width // 2, y + key_height // 2))
                self.screen.blit(key_surf, key_rect)

        # Instructions
        hint = self.font_small.render("A: Select  |  B: Back  |  D-Pad/Stick: Navigate", True, config.COLOR_TEXT_DIM)
        hint_rect = hint.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def draw_centered_message(self, message: str, color):
        """Draw a centered message overlay"""
        # Semi-transparent background
        overlay = pygame.Surface((config.SCREEN_WIDTH, 150))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, config.SCREEN_HEIGHT // 2 - 75))

        # Message text
        text = self.font_menu.render(message, True, color)
        text_rect = text.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def draw_wrapped_text(self, text: str, x: int, y: int, max_width: int, color):
        """Draw text with word wrapping"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            test_surf = self.font_small.render(test_line, True, color)

            if test_surf.get_width() > max_width:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        # Draw lines
        for i, line in enumerate(lines[:8]):  # Limit to 8 lines
            line_surf = self.font_small.render(line, True, color)
            self.screen.blit(line_surf, (x, y + i * 40))

    def cleanup(self):
        """Clean up resources before exit"""
        try:
            logger.info("Starting cleanup")

            # Clear image cache
            if hasattr(self, 'image_cache'):
                self.image_cache.clear()
                logger.debug("Image cache cleared")

            # Close joystick
            if hasattr(self, 'joystick') and self.joystick:
                try:
                    self.joystick.quit()
                    logger.debug("Joystick closed")
                except:
                    pass

            # Close HTTP session
            if hasattr(self, 'api') and hasattr(self.api, 'session'):
                try:
                    self.api.session.close()
                    logger.debug("HTTP session closed")
                except:
                    pass

            # Quit pygame subsystems
            try:
                pygame.joystick.quit()
                pygame.quit()
                logger.debug("Pygame subsystems quit")
            except:
                pass

            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Main game loop with FPS monitoring"""
        logger.info(f"Starting main loop (target FPS: {config.FPS})")

        frame_times = []
        frame_count = 0

        try:
            while self.running:
                frame_start = time.time()

                self.handle_input()

                # Check for scheduled actions (non-blocking)
                if self.scheduled_back_time and time.time() >= self.scheduled_back_time:
                    self.scheduled_back_time = None
                    self.handle_back()

                self.draw()
                self.clock.tick(config.FPS)

                # Monitor FPS every 100 frames
                frame_count += 1
                frame_time = time.time() - frame_start
                frame_times.append(frame_time)

                if frame_count >= 100:
                    avg_frame_time = sum(frame_times) / len(frame_times)
                    actual_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0

                    if actual_fps < config.FPS * 0.75:  # 75% threshold
                        logger.warning(f"Low FPS detected: {actual_fps:.1f} (target: {config.FPS})")

                    frame_times.clear()
                    frame_count = 0
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.exception(f"Unexpected error in main loop: {e}")
        finally:
            logger.info("Exiting application")
            self.cleanup()
