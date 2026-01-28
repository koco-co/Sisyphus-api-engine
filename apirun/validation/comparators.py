"""Validation Comparators for Sisyphus API Engine.

This module implements all comparison operators for assertions.
Following Google Python Style Guide.
"""

import re
from typing import Any
from jsonpath import jsonpath


class ComparatorError(Exception):
    """Exception raised for comparator errors."""

    pass


class Comparators:
    """Collection of comparison functions."""

    @staticmethod
    def eq(actual: Any, expected: Any) -> bool:
        """Check if actual equals expected.

        Args:
            actual: Actual value
            expected: Expected value

        Returns:
            True if equal, False otherwise
        """
        return actual == expected

    @staticmethod
    def ne(actual: Any, expected: Any) -> bool:
        """Check if actual not equals expected.

        Args:
            actual: Actual value
            expected: Expected value

        Returns:
            True if not equal, False otherwise
        """
        return actual != expected

    @staticmethod
    def gt(actual: Any, expected: Any) -> bool:
        """Check if actual greater than expected.

        Args:
            actual: Actual value (must be comparable)
            expected: Expected value (must be comparable)

        Returns:
            True if actual > expected, False otherwise

        Raises:
            ComparatorError: If values cannot be compared
        """
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError) as e:
            raise ComparatorError(f"Cannot compare values: {e}")

    @staticmethod
    def lt(actual: Any, expected: Any) -> bool:
        """Check if actual less than expected.

        Args:
            actual: Actual value (must be comparable)
            expected: Expected value (must be comparable)

        Returns:
            True if actual < expected, False otherwise

        Raises:
            ComparatorError: If values cannot be compared
        """
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError) as e:
            raise ComparatorError(f"Cannot compare values: {e}")

    @staticmethod
    def ge(actual: Any, expected: Any) -> bool:
        """Check if actual greater than or equal to expected.

        Args:
            actual: Actual value (must be comparable)
            expected: Expected value (must be comparable)

        Returns:
            True if actual >= expected, False otherwise

        Raises:
            ComparatorError: If values cannot be compared
        """
        try:
            return float(actual) >= float(expected)
        except (ValueError, TypeError) as e:
            raise ComparatorError(f"Cannot compare values: {e}")

    @staticmethod
    def le(actual: Any, expected: Any) -> bool:
        """Check if actual less than or equal to expected.

        Args:
            actual: Actual value (must be comparable)
            expected: Expected value (must be comparable)

        Returns:
            True if actual <= expected, False otherwise

        Raises:
            ComparatorError: If values cannot be compared
        """
        try:
            return float(actual) <= float(expected)
        except (ValueError, TypeError) as e:
            raise ComparatorError(f"Cannot compare values: {e}")

    @staticmethod
    def contains(actual: Any, expected: Any) -> bool:
        """Check if actual contains expected.

        For strings: checks if expected is substring of actual
        For lists/dicts: checks if expected is in actual

        Args:
            actual: Actual value
            expected: Expected value to check for

        Returns:
            True if actual contains expected, False otherwise
        """
        if isinstance(actual, str):
            return expected in actual
        if isinstance(actual, (list, tuple)):
            return expected in actual
        if isinstance(actual, dict):
            return expected in actual.keys()
        return False

    @staticmethod
    def not_contains(actual: Any, expected: Any) -> bool:
        """Check if actual does not contain expected.

        Args:
            actual: Actual value
            expected: Expected value to check for

        Returns:
            True if actual does not contain expected, False otherwise
        """
        return not Comparators.contains(actual, expected)

    @staticmethod
    def regex(actual: Any, expected: Any) -> bool:
        """Check if actual matches regex pattern.

        Args:
            actual: Actual value (string)
            expected: Regex pattern

        Returns:
            True if actual matches pattern, False otherwise

        Raises:
            ComparatorError: If pattern is invalid
        """
        if not isinstance(actual, str):
            return False

        try:
            return bool(re.search(expected, actual))
        except re.error as e:
            raise ComparatorError(f"Invalid regex pattern: {e}")

    @staticmethod
    def type(actual: Any, expected: Any) -> bool:
        """Check if actual is of expected type.

        Args:
            actual: Actual value
            expected: Expected type name (str, int, float, bool, list, dict, null)

        Returns:
            True if actual is of expected type, False otherwise
        """
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "null": type(None),
        }

        expected_type = type_map.get(expected)
        if expected_type is None:
            return False

        return isinstance(actual, expected_type)

    @staticmethod
    def in_list(actual: Any, expected: Any) -> bool:
        """Check if actual is in expected list.

        Args:
            actual: Actual value
            expected: List of values

        Returns:
            True if actual is in expected list, False otherwise
        """
        if not isinstance(expected, (list, tuple)):
            return False
        return actual in expected

    @staticmethod
    def not_in_list(actual: Any, expected: Any) -> bool:
        """Check if actual is not in expected list.

        Args:
            actual: Actual value
            expected: List of values

        Returns:
            True if actual is not in expected list, False otherwise
        """
        return not Comparators.in_list(actual, expected)

    @staticmethod
    def length_eq(actual: Any, expected: Any) -> bool:
        """Check if length of actual equals expected.

        Args:
            actual: Actual value (string, list, dict, etc.)
            expected: Expected length

        Returns:
            True if lengths are equal, False otherwise
        """
        try:
            return len(actual) == int(expected)
        except TypeError:
            return False

    @staticmethod
    def length_gt(actual: Any, expected: Any) -> bool:
        """Check if length of actual greater than expected.

        Args:
            actual: Actual value (string, list, dict, etc.)
            expected: Expected length

        Returns:
            True if length > expected, False otherwise
        """
        try:
            return len(actual) > int(expected)
        except TypeError:
            return False

    @staticmethod
    def length_lt(actual: Any, expected: Any) -> bool:
        """Check if length of actual less than expected.

        Args:
            actual: Actual value (string, list, dict, etc.)
            expected: Expected length

        Returns:
            True if length < expected, False otherwise
        """
        try:
            return len(actual) < int(expected)
        except TypeError:
            return False

    @staticmethod
    def is_empty(actual: Any, expected: Any = None) -> bool:
        """Check if actual is empty.

        Args:
            actual: Actual value
            expected: Ignored (for API consistency)

        Returns:
            True if actual is empty, False otherwise
        """
        if actual is None:
            return True
        if isinstance(actual, (str, list, dict, tuple)):
            return len(actual) == 0
        return False

    @staticmethod
    def is_null(actual: Any, expected: Any = None) -> bool:
        """Check if actual is None.

        Args:
            actual: Actual value
            expected: Ignored (for API consistency)

        Returns:
            True if actual is None, False otherwise
        """
        return actual is None

    @staticmethod
    def status_code(actual: Any, expected: Any) -> bool:
        """Check if HTTP status code matches expected.

        Special comparator for HTTP status codes.

        Args:
            actual: Actual status code
            expected: Expected status code or range (e.g., "2xx", "404")

        Returns:
            True if status code matches, False otherwise
        """
        try:
            actual_code = int(actual)
            expected_str = str(expected).lower()

            # Check for range pattern (e.g., "2xx", "4xx")
            if "xx" in expected_str:
                prefix = expected_str.replace("xx", "")
                expected_prefix = str(actual_code)[0]
                return prefix == expected_prefix

            # Direct comparison
            return actual_code == int(expected)

        except (ValueError, TypeError):
            return False

    @staticmethod
    def exists(actual: Any, expected: Any = None) -> bool:
        """Check if actual exists (not None and not empty).

        Args:
            actual: Actual value
            expected: Ignored (for API consistency)

        Returns:
            True if actual exists, False otherwise
        """
        if actual is None:
            return False
        if isinstance(actual, (str, list, dict, tuple)):
            return len(actual) > 0
        return True

    @staticmethod
    def between(actual: Any, expected: Any) -> bool:
        """Check if actual is between expected values (inclusive).

        Args:
            actual: Actual value
            expected: List or tuple [min, max]

        Returns:
            True if actual is between min and max, False otherwise

        Raises:
            ComparatorError: If expected is not a valid range
        """
        if not isinstance(expected, (list, tuple)) or len(expected) != 2:
            raise ComparatorError("between comparator requires [min, max] format")

        try:
            actual_val = float(actual)
            min_val = float(expected[0])
            max_val = float(expected[1])
            return min_val <= actual_val <= max_val
        except (ValueError, TypeError) as e:
            raise ComparatorError(f"Cannot compare values: {e}")


# Get comparator function by name
def get_comparator(name: str):
    """Get comparator function by name.

    Args:
        name: Comparator name

    Returns:
        Comparator function

    Raises:
        ComparatorError: If comparator not found
    """
    comparator_func = getattr(Comparators, name, None)
    if comparator_func is None:
        raise ComparatorError(f"Unknown comparator: {name}")
    return comparator_func
