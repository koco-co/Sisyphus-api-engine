"""Validation Comparators for Sisyphus API Engine.

This module implements all comparison operators for assertions.
Following Google Python Style Guide.
"""

import re
from typing import Any


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
            raise ComparatorError(f'Cannot compare values: {e}')

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
            raise ComparatorError(f'Cannot compare values: {e}')

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
            raise ComparatorError(f'Cannot compare values: {e}')

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
            raise ComparatorError(f'Cannot compare values: {e}')

    @staticmethod
    def contains(actual: Any, expected: Any) -> bool:
        """Check if actual contains expected.

        For strings: checks if expected is substring of actual
        For lists/tuples: checks if expected is in actual (handles None values)
        For dicts: checks if expected is in actual keys

        Args:
            actual: Actual value
            expected: Expected value to check for

        Returns:
            True if actual contains expected, False otherwise
        """
        # Handle None case
        if actual is None:
            return expected is None

        if isinstance(actual, str):
            # For strings, expected must also be a string
            if expected is None:
                return False
            return str(expected) in actual

        if isinstance(actual, (list, tuple)):
            # For lists/tuples, check each element
            # Handle case where expected might be None
            for item in actual:
                if item == expected:
                    return True
            return False

        if isinstance(actual, dict):
            # For dicts, check if expected is a key
            if expected is None:
                return False
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
            actual: Actual value (will be converted to string)
            expected: Regex pattern

        Returns:
            True if actual matches pattern, False otherwise

        Raises:
            ComparatorError: If pattern is invalid
        """
        # Convert actual to string for matching
        actual_str = str(actual) if actual is not None else ''

        try:
            # Check if pattern expects full match (^...$)
            # If so, use fullmatch for better accuracy
            if (
                isinstance(expected, str)
                and expected.startswith('^')
                and expected.endswith('$')
            ):
                return bool(re.fullmatch(expected, actual_str))
            else:
                # Use search for partial matching
                return bool(re.search(expected, actual_str))
        except re.error as e:
            raise ComparatorError(f'Invalid regex pattern: {e}')

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
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'null': type(None),
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
        """Check if actual is empty or not empty based on expected.

        Args:
            actual: Actual value
            expected: True to check if empty, False to check if not empty

        Returns:
            True if actual matches expected emptiness, False otherwise
        """
        is_actually_empty = False
        if actual is None:
            is_actually_empty = True
        elif isinstance(actual, (str, list, dict, tuple)):
            is_actually_empty = len(actual) == 0

        # If expected is True, check if actually empty
        # If expected is False, check if not empty
        if expected is True:
            return is_actually_empty
        elif expected is False:
            return not is_actually_empty
        else:
            # Backward compatibility: if expected is None, return emptiness status
            return is_actually_empty

    @staticmethod
    def is_null(actual: Any, expected: Any = None) -> bool:
        """Check if actual is None or not None based on expected.

        Args:
            actual: Actual value
            expected: True to check if null, False to check if not null

        Returns:
            True if actual matches expected nullness, False otherwise
        """
        is_actually_null = actual is None

        # If expected is True, check if actually null
        # If expected is False, check if not null
        if expected is True:
            return is_actually_null
        elif expected is False:
            return not is_actually_null
        else:
            # Backward compatibility: if expected is None, return null status
            return is_actually_null

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
            if 'xx' in expected_str:
                prefix = expected_str.replace('xx', '')
                expected_prefix = str(actual_code)[0]
                return prefix == expected_prefix

            # Direct comparison
            return actual_code == int(expected)

        except (ValueError, TypeError):
            return False

    @staticmethod
    def exists(actual: Any, expected: Any = None) -> bool:
        """Check if actual exists or not exists based on expected.

        Args:
            actual: Actual value
            expected: True to check if exists, False to check if not exists

        Returns:
            True if actual matches expected existence, False otherwise
        """
        actually_exists = False
        if actual is None:
            actually_exists = False
        elif isinstance(actual, (str, list, dict, tuple)):
            actually_exists = len(actual) > 0
        else:
            actually_exists = True

        # If expected is True, check if actually exists
        # If expected is False, check if not exists
        if expected is True:
            return actually_exists
        elif expected is False:
            return not actually_exists
        else:
            # Backward compatibility: if expected is None, return existence status
            return actually_exists

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
            raise ComparatorError('between comparator requires [min, max] format')

        try:
            actual_val = float(actual)
            min_val = float(expected[0])
            max_val = float(expected[1])
            return min_val <= actual_val <= max_val
        except (ValueError, TypeError) as e:
            raise ComparatorError(f'Cannot compare values: {e}')

    @staticmethod
    def starts_with(actual: Any, expected: Any) -> bool:
        """Check if actual string starts with expected prefix.

        Args:
            actual: Actual value (will be converted to string)
            expected: Expected prefix

        Returns:
            True if actual starts with expected, False otherwise
        """
        if actual is None:
            return expected is None or expected == ''
        actual_str = str(actual)
        expected_str = str(expected) if expected is not None else ''
        return actual_str.startswith(expected_str)

    @staticmethod
    def ends_with(actual: Any, expected: Any) -> bool:
        """Check if actual string ends with expected suffix.

        Args:
            actual: Actual value (will be converted to string)
            expected: Expected suffix

        Returns:
            True if actual ends with expected, False otherwise
        """
        if actual is None:
            return expected is None or expected == ''
        actual_str = str(actual)
        expected_str = str(expected) if expected is not None else ''
        return actual_str.endswith(expected_str)


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
    # 别名映射，支持多种命名方式
    aliases = {
        # 比较验证器别名
        'gte': 'ge',
        'lte': 'le',
        # 字符串验证器别名
        'startswith': 'starts_with',
        'endswith': 'ends_with',
        # 列表验证器别名
        'in': 'in_list',
        'not_in': 'not_in_list',
        # 长度验证器别名
        'len_eq': 'length_eq',
        'len_gt': 'length_gt',
        'len_lt': 'length_lt',
        'length_eq': 'length_eq',
        'length_gt': 'length_gt',
        'length_lt': 'length_lt',
        # 状态验证器别名
        'is_empty': 'is_empty',
        'is_null': 'is_null',
        'not_empty': 'not_empty',
    }

    # 查找别名对应的标准名称
    standard_name = aliases.get(name, name)

    comparator_func = getattr(Comparators, standard_name, None)
    if comparator_func is None:
        raise ComparatorError(f'Unknown comparator: {name}')
    return comparator_func
