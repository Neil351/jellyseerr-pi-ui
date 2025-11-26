"""
Jellyseerr API wrapper for making requests to the Jellyseerr server
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from typing import Dict, List, Optional, Callable, Any
import re
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
import time
import config

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2):
    """
    Decorator to retry functions on RequestException with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise

                    wait_time = backoff_factor ** attempt
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


def validate_search_query(query: str) -> str:
    """
    Validate and sanitize search query input.

    Args:
        query: Search query string

    Returns:
        Sanitized query string

    Raises:
        ValueError: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    # Length limit to prevent DoS
    if len(query) > 200:
        raise ValueError("Query exceeds maximum length of 200 characters")

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\"\';&|`$]', '', query)

    return sanitized.strip()


def validate_media_id(media_id: int) -> int:
    """
    Validate media ID parameter.

    Args:
        media_id: Media ID to validate

    Returns:
        Validated media ID

    Raises:
        ValueError: If media_id is invalid
    """
    if not isinstance(media_id, int) or media_id <= 0:
        raise ValueError(f"Invalid media_id: {media_id}")

    return media_id


def validate_media_type(media_type: str) -> str:
    """
    Validate media type parameter.

    Args:
        media_type: Media type to validate

    Returns:
        Validated media type

    Raises:
        ValueError: If media_type is invalid
    """
    valid_types = ['movie', 'tv']
    if media_type not in valid_types:
        raise ValueError(f"Invalid media_type: {media_type}. Must be one of {valid_types}")

    return media_type


def validate_page_number(page: int) -> int:
    """
    Validate page number parameter.

    Args:
        page: Page number to validate

    Returns:
        Validated page number

    Raises:
        ValueError: If page is invalid
    """
    if not isinstance(page, int) or page < 1 or page > 1000:
        raise ValueError(f"Invalid page number: {page}. Must be between 1 and 1000")

    return page


def validate_media_item(item: Dict) -> bool:
    """
    Validate that a media item has required fields.

    Args:
        item: Media item dictionary from API

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(item, dict):
        return False

    required_fields = ['id', 'mediaType']
    return all(field in item for field in required_fields)


def validate_api_response(data: Any, expected_type: type = dict) -> bool:
    """
    Validate API response structure.

    Args:
        data: Response data to validate
        expected_type: Expected type of the response

    Returns:
        True if valid, False otherwise
    """
    return isinstance(data, expected_type)


class JellyseerrAPI:
    """Wrapper for Jellyseerr API"""

    def __init__(self):
        self.base_url = config.JELLYSEERR_BASE_URL
        self.api_url = config.JELLYSEERR_API_URL
        self.api_key = config.JELLYSEERR_API_KEY
        self.session = requests.Session()

        # Enforce HTTPS certificate validation
        self.session.verify = True

        # Configure connection pooling and retry strategy
        retry_strategy = Retry(
            total=0,  # We handle retries manually
            backoff_factor=0,
            status_forcelist=[],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,       # Max connections per pool
            pool_block=False       # Don't block when pool is full
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.debug("Configured HTTP connection pool (10 pools, 20 max connections)")

        # Rate limiting (30 requests per minute)
        self.request_times = deque(maxlen=100)
        self.rate_limit_window = timedelta(seconds=60)
        self.max_requests_per_window = 30

        # Set up headers
        if self.api_key:
            self.session.headers.update({'X-Api-Key': self.api_key})
            logger.info(f"API key configured (length: {len(self.api_key)})")
        else:
            logger.info("No API key configured")

        # Warn if using plain HTTP
        if self.base_url.startswith('http://'):
            logger.warning("Using plain HTTP connection - API key will be transmitted in cleartext!")

    def _check_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        now = datetime.now()

        # Remove old requests outside window
        while self.request_times and (now - self.request_times[0]) > self.rate_limit_window:
            self.request_times.popleft()

        if len(self.request_times) >= self.max_requests_per_window:
            raise Exception("Rate limit exceeded. Please wait before making more requests.")

        self.request_times.append(now)

    def _make_request_with_retry(self, method: str, url: str, max_retries: int = 3, **kwargs):
        """
        Make HTTP request with retry logic and exponential backoff.

        Args:
            method: HTTP method ('get' or 'post')
            url: URL to request
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            RequestException: If all retries fail
        """
        backoff_factor = 1.5

        for attempt in range(max_retries):
            try:
                if method.lower() == 'get':
                    response = self.session.get(url, **kwargs)
                elif method.lower() == 'post':
                    response = self.session.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 401:
                    logger.error("Authentication failed - check API key in config.py")
                    return None

                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise  # Last attempt, re-raise exception
                wait_time = backoff_factor ** attempt
                logger.warning(f"Request attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)

        return None

    def test_connection(self) -> bool:
        """Test connectivity to Jellyseerr server"""
        try:
            response = self.session.get(
                f"{self.api_url}/status",
                timeout=config.API_TIMEOUT
            )
            if response.status_code == 200:
                logger.info("Successfully connected to Jellyseerr")
                return True
            elif response.status_code == 401:
                logger.error("Jellyseerr authentication failed - check API key in config.py")
                return False
            else:
                logger.warning(f"Jellyseerr returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Jellyseerr: {e}")
            return False

    def search_movies(self, query: str, page: int = 1) -> Optional[List[Dict]]:
        """Search for movies with retry logic"""
        try:
            # Check rate limit
            self._check_rate_limit()

            # Validate and sanitize inputs
            query = validate_search_query(query)
            page = validate_page_number(page)

            # Make request with retry
            response = self._make_request_with_retry(
                'get',
                f"{self.api_url}/search",
                params={'query': query, 'page': page},
                timeout=config.REQUEST_TIMEOUT
            )

            if not response:
                return None

            data = response.json()

            # Validate response structure
            if not validate_api_response(data, dict):
                logger.error("Invalid response format: expected dict")
                return None

            results_raw = data.get('results', [])
            if not validate_api_response(results_raw, list):
                logger.error("Invalid results format: expected list")
                return None

            # Filter to only movies and validate each item
            results = [item for item in results_raw
                      if validate_media_item(item) and item.get('mediaType') == 'movie']
            logger.info(f"Found {len(results)} valid movies for query: {query}")
            return results
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching movies: {e}")
            return None

    def search_tv(self, query: str, page: int = 1) -> Optional[List[Dict]]:
        """Search for TV shows with retry logic"""
        try:
            # Check rate limit
            self._check_rate_limit()

            # Validate and sanitize inputs
            query = validate_search_query(query)
            page = validate_page_number(page)

            # Make request with retry
            response = self._make_request_with_retry(
                'get',
                f"{self.api_url}/search",
                params={'query': query, 'page': page},
                timeout=config.REQUEST_TIMEOUT
            )

            if not response:
                return None

            data = response.json()

            # Validate response structure
            if not validate_api_response(data, dict):
                logger.error("Invalid response format: expected dict")
                return None

            results_raw = data.get('results', [])
            if not validate_api_response(results_raw, list):
                logger.error("Invalid results format: expected list")
                return None

            # Filter to only TV shows and validate each item
            results = [item for item in results_raw
                      if validate_media_item(item) and item.get('mediaType') == 'tv']
            logger.info(f"Found {len(results)} valid TV shows for query: {query}")
            return results
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching TV shows: {e}")
            return None

    def get_popular_movies(self, page: int = 1) -> Optional[List[Dict]]:
        """Get popular movies with retry logic"""
        try:
            # Check rate limit
            self._check_rate_limit()

            # Make request with retry
            response = self._make_request_with_retry(
                'get',
                f"{self.api_url}/discover/movies",
                params={'page': page, 'sortBy': 'popularity.desc'},
                timeout=config.REQUEST_TIMEOUT
            )

            if not response:
                return None

            data = response.json()

            # Validate response structure
            if not validate_api_response(data, dict):
                logger.error("Invalid response format: expected dict")
                return None

            results = data.get('results', [])
            if not validate_api_response(results, list):
                logger.error("Invalid results format: expected list")
                return None

            # Validate each item
            valid_results = [item for item in results if validate_media_item(item)]
            logger.info(f"Retrieved {len(valid_results)} valid popular movies")
            return valid_results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting popular movies: {e}")
            return None

    def get_popular_tv(self, page: int = 1) -> Optional[List[Dict]]:
        """Get popular TV shows with retry logic"""
        try:
            # Check rate limit
            self._check_rate_limit()

            # Make request with retry
            response = self._make_request_with_retry(
                'get',
                f"{self.api_url}/discover/tv",
                params={'page': page, 'sortBy': 'popularity.desc'},
                timeout=config.REQUEST_TIMEOUT
            )

            if not response:
                return None

            data = response.json()

            # Validate response structure
            if not validate_api_response(data, dict):
                logger.error("Invalid response format: expected dict")
                return None

            results = data.get('results', [])
            if not validate_api_response(results, list):
                logger.error("Invalid results format: expected list")
                return None

            # Validate each item
            valid_results = [item for item in results if validate_media_item(item)]
            logger.info(f"Retrieved {len(valid_results)} valid popular TV shows")
            return valid_results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting popular TV shows: {e}")
            return None

    def request_media(self, media_id: int, media_type: str) -> bool:
        """Request media (movie or TV show) with retry logic"""
        try:
            # Check rate limit
            self._check_rate_limit()

            # Validate inputs
            media_id = validate_media_id(media_id)
            media_type = validate_media_type(media_type)

            endpoint = f"{self.api_url}/request"
            payload = {
                'mediaId': media_id,
                'mediaType': media_type
            }

            # Make request with retry
            response = self._make_request_with_retry(
                'post',
                endpoint,
                json=payload,
                timeout=config.REQUEST_TIMEOUT
            )

            if not response:
                return False

            # Verify the request was actually created
            try:
                response_data = response.json()
                # Check if response contains request ID (indicates success)
                if isinstance(response_data, dict) and 'id' in response_data:
                    request_id = response_data['id']
                    logger.info(f"Successfully requested {media_type} with ID: {media_id} (Request ID: {request_id})")
                    return True
                else:
                    logger.warning(f"Request submitted but no confirmation received for {media_type} ID: {media_id}")
                    return True  # Still return True as request was accepted
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not parse request response: {e}")
                return True  # HTTP success, assume request went through
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error requesting media: {e}")
            return False

    def get_poster_url(self, poster_path: str, size: str = "w500") -> Optional[str]:
        """
        Get full URL for a poster image with validation.

        Args:
            poster_path: TMDB poster path (should start with /)
            size: Image size (w92, w154, w185, w342, w500, w780, original)

        Returns:
            Full URL or None if invalid
        """
        if not poster_path:
            return None

        # Validate poster_path format (should start with /)
        if not isinstance(poster_path, str) or not poster_path.startswith('/'):
            logger.warning(f"Invalid poster_path format: {poster_path}")
            return None

        # Prevent directory traversal
        if '..' in poster_path or '//' in poster_path:
            logger.warning(f"Potentially malicious poster_path: {poster_path}")
            return None

        # Validate size parameter
        valid_sizes = ['w92', 'w154', 'w185', 'w342', 'w500', 'w780', 'original']
        if size not in valid_sizes:
            logger.warning(f"Invalid image size: {size}, using w500")
            size = 'w500'

        # Jellyseerr uses TMDB image paths
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"

    def download_image(self, url: str) -> Optional[bytes]:
        """Download image data with retry logic and size limits"""
        max_retries = 3
        backoff_factor = 1.5

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=config.REQUEST_TIMEOUT, stream=True)
                response.raise_for_status()

                # Check content length before downloading
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > config.MAX_IMAGE_DOWNLOAD_SIZE:
                    logger.error(f"Image too large: {content_length} bytes (max {config.MAX_IMAGE_DOWNLOAD_SIZE})")
                    return None

                # Download with size limit
                chunks = []
                total_size = 0

                for chunk in response.iter_content(chunk_size=8192):
                    total_size += len(chunk)
                    if total_size > config.MAX_IMAGE_DOWNLOAD_SIZE:
                        logger.error(f"Image exceeded size limit during download: {total_size} bytes")
                        return None
                    chunks.append(chunk)

                return b''.join(chunks)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error downloading image after {max_retries} attempts: {e}")
                    return None

                wait_time = backoff_factor ** attempt
                logger.debug(f"Image download attempt {attempt + 1} failed, retrying in {wait_time}s")
                time.sleep(wait_time)

        return None
