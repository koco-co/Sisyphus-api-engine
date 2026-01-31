"""JSONPath Extractor for Sisyphus API Engine.

This module implements variable extraction using JSONPath with function support.
Following Google Python Style Guide.
"""

from typing import Any
from apirun.utils.enhanced_jsonpath import extract_value


class JSONPathExtractor:
    """Extract values from data using JSONPath expressions.

    Supports:
    - Root node: $
    - Child node: $.key
    - Nested node: $.parent.child
    - Wildcard: $.*
    - Array index: $.array[0]
    - Array slice: $.array[0:2]
    - Recursive search: $..key
    - Filter expressions: $.array[?(@.key > 10)]

    Enhanced Functions:
    - length(), size(), count(): Get array length
    - sum(): Sum of numeric values
    - avg(): Average of numeric values
    - min(), max(): Min/Max values
    - first(), last(): First/Last elements
    - keys(), values(): Object keys/values
    - reverse(), sort(), unique(): Array operations
    - flatten(): Flatten nested arrays
    - upper(), lower(), trim(): String operations
    - split(delimiter), join(delimiter): String operations
    - contains(value), starts_with(value), ends_with(value): Checks
    - matches(pattern): Regex match
    """

    def extract(self, path: str, data: Any, index: int = 0) -> Any:
        """Extract value from data using JSONPath.

        Args:
            path: JSONPath expression (may include function calls)
            data: Data to extract from
            index: Index to return if multiple matches (default: 0)

        Returns:
            Extracted value

        Raises:
            ValueError: If path is invalid or no match found

        Examples:
            >>> extractor = JSONPathExtractor()
            >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
            >>> extractor.extract("$.users", data)
            [{"name": "Alice"}, {"name": "Bob"}]
            >>> extractor.extract("$.users.length()", data)
            2
            >>> extractor.extract("$.users[0].name", data)
            "Alice"
        """
        try:
            return extract_value(path, data, index)
        except Exception as e:
            raise ValueError(f"JSONPath extraction failed: {e}")
