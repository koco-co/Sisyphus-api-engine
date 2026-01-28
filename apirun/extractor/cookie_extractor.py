"""Cookie Extractor for Sisyphus API Engine.

This module implements extraction from HTTP response cookies.
Following Google Python Style Guide.
"""

from typing import Any, Optional


class CookieExtractor:
    """Extract values from HTTP response cookies.

    Usage:
        extractor = CookieExtractor()
        value = extractor.extract("session_id", response_data)
    """

    def extract(self, cookie_name: str, data: Any, index: int = 0) -> Optional[str]:
        """Extract cookie value from response data.

        Args:
            cookie_name: Name of cookie to extract
            data: Response data dict with 'cookies' key
            index: Ignored (for API consistency)

        Returns:
            Cookie value or None if not found
        """
        if not isinstance(data, dict):
            return None

        cookies = data.get("cookies", {})

        if not isinstance(cookies, dict):
            return None

        return cookies.get(cookie_name)
