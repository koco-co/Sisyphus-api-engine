"""Regex Extractor for Sisyphus API Engine.

This module implements variable extraction using regular expressions.
Following Google Python Style Guide.
"""

import re
import json
from typing import Any, Optional


class RegexExtractor:
    """Extract values from strings using regular expressions.

    Supports:
    - Named groups: (?P<name>pattern)
    - Numbered groups: (pattern)
    - Multiple match modes
    """

    def extract(self, pattern: str, data: Any, index: int = 0, default: Any = None) -> Optional[str]:
        """Extract value from data using regex.

        Args:
            pattern: Regular expression pattern
            data: Data to extract from (will be converted to string)
            index: Group index to return (0 for full match, 1+ for groups)
            default: Default value to return if extraction fails (default: None)

        Returns:
            Extracted string value or default value if no match

        Raises:
            ValueError: If pattern is invalid
        """
        # Convert data to string for regex matching
        # For dict/list, use json.dumps() to preserve JSON formatting (double quotes)
        # For other types, use str()
        if not isinstance(data, str):
            if isinstance(data, (dict, list)):
                # Use json.dumps for proper JSON formatting (double quotes)
                data = json.dumps(data, ensure_ascii=False)
            else:
                data = str(data)

        try:
            match = re.search(pattern, data)

            if not match:
                return default

            if index == 0:
                return match.group(0)
            elif 0 < index <= len(match.groups()):
                return match.group(index)
            else:
                # Index out of range - return default
                return default

        except re.error as e:
            raise ValueError(
                f"无效的正则表达式 '{pattern}': {e}。\n"
                f"请检查正则表达式语法，建议使用在线工具验证。"
            )
