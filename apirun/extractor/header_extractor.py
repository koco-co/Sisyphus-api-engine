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

    def extract(self, header_name: str, data: Any, index: int = 0, default: Any = None) -> Optional[str]:
        """Extract header value from response data.

        Args:
            header_name: Name of header to extract (case-insensitive)
            data: Response data dict with 'headers' key
            index: Ignored (for API consistency)
            default: Default value to return if header not found (default: None)

        Returns:
            Header value or default value if not found
        """
        if not isinstance(data, dict):
            return default

        headers = data.get("headers", {})

        if not isinstance(headers, dict):
            return default

        # Case-insensitive header search
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                return str(value)

        return default
