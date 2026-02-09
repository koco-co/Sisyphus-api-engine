"""Cookie Extractor for Sisyphus API Engine.

This module implements extraction from HTTP response cookies.
Following Google Python Style Guide.
"""

from typing import Any


class CookieExtractor:
    """Extract values from HTTP response cookies.

    Usage:
        extractor = CookieExtractor()
        value = extractor.extract("session_id", response_data)
    """

    def extract(
        self, cookie_name: str, data: Any, index: int = 0, default: Any = None
    ) -> str | None:
        """Extract cookie value from response data.

        Args:
            cookie_name: Name of cookie to extract
            data: Response data dict with 'cookies' key
            index: Ignored (for API consistency)
            default: Default value to return if cookie not found (default: None)

        Returns:
            Cookie value or default value if not found
        """
        if not isinstance(data, dict):
            return default

        cookies = data.get('cookies', {})

        if not isinstance(cookies, dict):
            return default

        return cookies.get(cookie_name, default)
