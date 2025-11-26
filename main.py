#!/usr/bin/env python3
"""
Jellyseerr Pi UI - Controller-friendly interface for Raspberry Pi
Entry point for the application
"""
import sys
import logging
import os
import config
from jellyseerr_api import JellyseerrAPI
from ui import JellyseerrUI


def setup_logging():
    """Setup logging configuration with security checks"""
    # Validate log level
    log_level_str = config.LOG_LEVEL.upper()
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

    if log_level_str not in valid_log_levels:
        print(f"Warning: Invalid log level '{config.LOG_LEVEL}', using INFO")
        log_level_str = 'INFO'

    log_level = getattr(logging, log_level_str)

    # Sanitize and validate log file path to prevent directory traversal
    log_file = os.path.abspath(config.LOG_FILE)

    # Define allowed log directories
    allowed_log_dirs = [
        '/tmp',
        '/var/log',
        os.path.expanduser('~/.local/share/jellyseerr-ui'),
        os.path.abspath('.')  # Current directory
    ]

    # Check if log file is in an allowed directory
    if not any(log_file.startswith(allowed_dir) for allowed_dir in allowed_log_dirs):
        print(f"Warning: Log file {log_file} not in allowed directory, using /tmp")
        log_file = "/tmp/jellyseerr-ui.log"

    # Create log directory safely (fixes TOCTOU race condition)
    log_dir = os.path.dirname(log_file)
    if log_dir:
        try:
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
        except Exception as e:
            # If we can't create directory, fall back to current directory
            print(f"Warning: Could not create log directory {log_dir}: {e}")
            log_file = "jellyseerr-ui.log"

    # Update config with validated path
    config.LOG_FILE = log_file

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Jellyseerr Pi UI starting...")
    return logger


def main():
    """Main entry point"""
    logger = setup_logging()

    try:
        # Initialize API
        logger.info("Initializing Jellyseerr API...")
        api = JellyseerrAPI()

        # Test connection
        logger.info("Testing connection to Jellyseerr...")
        if not api.test_connection():
            logger.error("Failed to connect to Jellyseerr. Check your network and config.")
            print("ERROR: Cannot connect to Jellyseerr at {}".format(config.JELLYSEERR_BASE_URL))
            print("Please check your network connection and config.py settings.")
            return 1

        logger.info("Connection successful! Starting UI...")

        # Initialize and run UI
        ui = JellyseerrUI(api)
        ui.run()

        logger.info("Application exiting normally")
        return 0

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
