"""Header Extractor for Sisyphus API Engine.

This module implements extraction from HTTP response headers.
Following Google Python Style Guide.
"""

from typing import Any, Optional


class HeaderExtractor:
    """Extract values from HTTP response headers.

    Usage:
        extractor = HeaderExtractor()
        value = extractor.extract("Content-Type", response_data)
    """

    def extract(self, header_name: str, data: Any, index: int = 0) -> Optional[str]:
        """Extract header value from response data.

        Args:
            header_name: Name of header to extract (case-insensitive)
            data: Response data dict with 'headers' key
            index: Ignored (for API consistency)

        Returns:
            Header value or None if not found
        """
        if not isinstance(data, dict):
            return None

        headers = data.get("headers", {})

        if not isinstance(headers, dict):
            return None

        # Case-insensitive header search
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                return str(value)

        return None
