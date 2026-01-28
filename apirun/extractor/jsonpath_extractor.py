"""JSONPath Extractor for Sisyphus API Engine.

This module implements variable extraction using JSONPath.
Following Google Python Style Guide.
"""

from typing import Any
from jsonpath import jsonpath


class JsonPathExtractor:
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
    """

    def extract(self, path: str, data: Any, index: int = 0) -> Any:
        """Extract value from data using JSONPath.

        Args:
            path: JSONPath expression
            data: Data to extract from
            index: Index to return if multiple matches (default: 0)

        Returns:
            Extracted value

        Raises:
            ValueError: If path is invalid or no match found
        """
        try:
            result = jsonpath(data, path)

            if result is False:
                raise ValueError(f"Invalid JSONPath expression: {path}")

            if len(result) == 0:
                raise ValueError(f"No value found at path: {path}")

            if index >= len(result):
                raise ValueError(
                    f"Index {index} out of range (found {len(result)} matches)"
                )

            return result[index]

        except Exception as e:
            raise ValueError(f"JSONPath extraction failed: {e}")
