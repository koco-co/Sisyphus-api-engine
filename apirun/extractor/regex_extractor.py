"""Regex Extractor for Sisyphus API Engine.

This module implements variable extraction using regular expressions.
Following Google Python Style Guide.
"""

import re
from typing import Any, Optional


class RegexExtractor:
    """Extract values from strings using regular expressions.

    Supports:
    - Named groups: (?P<name>pattern)
    - Numbered groups: (pattern)
    - Multiple match modes
    """

    def extract(self, pattern: str, data: Any, index: int = 0) -> Optional[str]:
        """Extract value from data using regex.

        Args:
            pattern: Regular expression pattern
            data: Data to extract from (will be converted to string)
            index: Group index to return (0 for full match, 1+ for groups)

        Returns:
            Extracted string value or None if no match

        Raises:
            ValueError: If pattern is invalid
        """
        if not isinstance(data, str):
            data = str(data)

        try:
            match = re.search(pattern, data)

            if not match:
                return None

            if index == 0:
                return match.group(0)
            elif index <= len(match.groups()):
                return match.group(index)
            else:
                return None

        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
