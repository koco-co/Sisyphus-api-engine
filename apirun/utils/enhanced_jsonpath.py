"""Enhanced JSONPath Processor with Function Support.

This module extends JSONPath with function call support.
Following Google Python Style Guide.
"""

import re
from typing import Any, List
from jsonpath import jsonpath as base_jsonpath


class EnhancedJSONPath:
    """Enhanced JSONPath processor with function support.

    Supports standard JSONPath plus function calls:
    - length(), size(), count(): Get array length
    - sum(): Sum of numeric values
    - avg(): Average of numeric values
    - min(): Minimum value
    - max(): Maximum value
    - first(): First element
    - last(): Last element
    - keys(): Get object keys
    - values(): Get object values
    - reverse(): Reverse array
    - sort(): Sort array
    - unique(): Get unique values
    - flatten(): Flatten nested arrays
    - upper(): Convert string to uppercase
    - lower(): Convert string to lowercase
    - trim(): Trim whitespace
    - split(delimiter): Split string
    - join(delimiter): Join array to string
    - contains(value): Check if contains value
    - starts_with(value): Check if starts with value
    - ends_with(value): Check if ends with value
    - matches(pattern): Check if matches regex pattern
    """

    # Function definitions
    FUNCTIONS = {
        # Array/Object functions
        "length": lambda data: len(data) if isinstance(data, (list, str, dict)) else 1,
        "size": lambda data: len(data) if isinstance(data, (list, str, dict)) else 1,
        "count": lambda data: len(data) if isinstance(data, (list, str, dict)) else 1,
        "first": lambda data: data[0] if isinstance(data, list) and len(data) > 0 else data,
        "last": lambda data: data[-1] if isinstance(data, list) and len(data) > 0 else data,
        "keys": lambda data: list(data.keys()) if isinstance(data, dict) else [],
        "values": lambda data: list(data.values()) if isinstance(data, dict) else [data] if not isinstance(data, list) else data,
        "reverse": lambda data: data[::-1] if isinstance(data, list) else data,
        "sort": lambda data: sorted(data) if isinstance(data, list) else data,
        "unique": lambda data: list(set(data)) if isinstance(data, list) else data,
        "flatten": lambda data: _flatten(data),
        # Numeric functions
        "sum": lambda data: sum(data) if isinstance(data, list) else data,
        "avg": lambda data: sum(data) / len(data) if isinstance(data, list) and len(data) > 0 else data,
        "min": lambda data: min(data) if isinstance(data, list) and len(data) > 0 else data,
        "max": lambda data: max(data) if isinstance(data, list) and len(data) > 0 else data,
        # String functions
        "upper": lambda data: data.upper() if isinstance(data, str) else data,
        "lower": lambda data: data.lower() if isinstance(data, str) else data,
        "trim": lambda data: data.strip() if isinstance(data, str) else data,
        # Check functions
        "is_empty": lambda data: len(data) == 0 if isinstance(data, (list, str, dict)) else False,
        "is_null": lambda data: data is None,
    }

    def __init__(self):
        """Initialize EnhancedJSONPath processor."""
        # Pattern to match function calls at the end: .function_name(...)
        # This pattern captures the function name and any arguments
        self.function_pattern = re.compile(r'\.([a-z_]+)\(([^)]*)\)$')

    def extract(self, path: str, data: Any, index: int = 0) -> Any:
        """Extract value using enhanced JSONPath with function support.

        Args:
            path: JSONPath expression (may include function calls)
            data: Data to extract from
            index: Index to return if multiple matches (default: 0, -1 for all)

        Returns:
            Extracted value (with function applied if specified)

        Raises:
            ValueError: If path is invalid or no match found
        """
        try:
            # Check if path contains function call at the end
            func_match = self.function_pattern.search(path)

            if func_match:
                # Extract base path and function info
                base_path = path[:func_match.start()]
                func_name = func_match.group(1)
                args_str = func_match.group(2).strip()

                # Parse function arguments
                func_args = self._parse_arguments(args_str)

                # Check if base_path also contains function calls (chain)
                if self.function_pattern.search(base_path):
                    # First resolve the base path with its functions
                    base_data = self.extract(base_path, data, index)
                else:
                    # Extract base value using standard JSONPath
                    extract_path = base_path if base_path else "$"
                    result = base_jsonpath(data, extract_path)

                    if result is False:
                        raise ValueError(f"Invalid JSONPath expression: {extract_path}")

                    if len(result) == 0:
                        raise ValueError(f"No value found at path: {extract_path}")

                    # Get the data (all matches for array operations, or single if specified)
                    if index == -1:
                        # Return all matches
                        base_data = result
                    elif len(result) > 1:
                        base_data = result
                    else:
                        base_data = result[0]

                # Apply the current function
                extracted_data = self._apply_function(func_name, base_data, func_args)

                # Check if there are more function calls to apply
                remaining_path = path[func_match.end():]
                if remaining_path:
                    # Recursively apply remaining functions to the result
                    return self.extract("$" + remaining_path, extracted_data, index=0)
                else:
                    # No more functions, return the result
                    return extracted_data

            else:
                # No function call, use standard JSONPath
                result = base_jsonpath(data, path)

                if result is False:
                    raise ValueError(f"Invalid JSONPath expression: {path}")

                if len(result) == 0:
                    raise ValueError(f"No value found at path: {path}")

                if index == -1:
                    return result

                if index >= len(result):
                    raise ValueError(
                        f"Index {index} out of range (found {len(result)} matches)"
                    )

                return result[index]

        except Exception as e:
            raise ValueError(f"Enhanced JSONPath extraction failed: {e}")

    def _parse_arguments(self, args_str: str) -> List[str]:
        """Parse function arguments from argument string.

        Args:
            args_str: Argument string (e.g., "," or "'hello','world'" or "a,b,c")

        Returns:
            List of parsed arguments
        """
        if not args_str:
            return []

        import re as regex_module
        # Match quoted strings or unquoted values
        # Pattern explanation:
        # (['\"]).*?\1  - Match quoted strings (single or double quotes)
        # |([^,]+)       - OR match unquoted values (everything except commas)
        arg_pattern = r"(['\"])(.*?)\1|([^,]+)"

        func_args = []
        for match in regex_module.finditer(arg_pattern, args_str):
            if match.group(2):  # Quoted string
                func_args.append(match.group(2))
            elif match.group(3):  # Unquoted value
                func_args.append(match.group(3).strip())

        return func_args

    def _apply_function(self, func_name: str, data: Any, args: List[str] = None) -> Any:
        """Apply function to extracted data.

        Args:
            func_name: Function name
            data: Data to apply function to
            args: Function arguments

        Returns:
            Result of applying function

        Raises:
            ValueError: If function is not supported or execution fails
        """
        args = args or []

        # Handle special functions with arguments
        if func_name in ["split", "join", "contains", "starts_with", "ends_with", "matches"]:
            return self._apply_function_with_args(func_name, data, args)

        # Handle standard functions
        if func_name in self.FUNCTIONS:
            try:
                return self.FUNCTIONS[func_name](data)
            except Exception as e:
                raise ValueError(f"Function '{func_name}' execution failed: {e}")

        raise ValueError(f"Unsupported function: {func_name}")

    def _apply_function_with_args(self, func_name: str, data: Any, args: List[str]) -> Any:
        """Apply function with arguments.

        Args:
            func_name: Function name
            data: Data to apply function to
            args: Function arguments

        Returns:
            Result of applying function
        """
        if func_name == "split":
            if not isinstance(data, str):
                raise ValueError(f"split() requires string, got {type(data).__name__}")
            delimiter = args[0] if args and args[0] else ","
            return data.split(delimiter)

        elif func_name == "join":
            if not isinstance(data, list):
                raise ValueError(f"join() requires array, got {type(data).__name__}")
            delimiter = args[0] if args else ","
            return delimiter.join(str(item) for item in data)

        elif func_name == "contains":
            if isinstance(data, (list, str)):
                return args[0] in data if args else False
            elif isinstance(data, dict):
                return args[0] in data if args else False
            return False

        elif func_name == "starts_with":
            if not isinstance(data, str):
                raise ValueError(f"starts_with() requires string, got {type(data).__name__}")
            return data.startswith(args[0]) if args else False

        elif func_name == "ends_with":
            if not isinstance(data, str):
                raise ValueError(f"ends_with() requires string, got {type(data).__name__}")
            return data.endswith(args[0]) if args else False

        elif func_name == "matches":
            import re as regex_module
            if not isinstance(data, str):
                raise ValueError(f"matches() requires string, got {type(data).__name__}")
            pattern = args[0] if args else ""
            return bool(regex_module.search(pattern, data))

        raise ValueError(f"Unsupported function with args: {func_name}")


def _flatten(data: Any) -> List[Any]:
    """Flatten nested arrays.

    Args:
        data: Data to flatten

    Returns:
        Flattened list
    """
    if not isinstance(data, list):
        return [data]

    result = []
    for item in data:
        if isinstance(item, list):
            result.extend(_flatten(item))
        else:
            result.append(item)
    return result


# Global instance
_enhanced_jsonpath = EnhancedJSONPath()


def extract_value(path: str, data: Any, index: int = 0) -> Any:
    """Extract value using enhanced JSONPath.

    This is a convenience function that uses the global EnhancedJSONPath instance.

    Args:
        path: JSONPath expression (may include function calls)
        data: Data to extract from
        index: Index to return if multiple matches (default: 0, -1 for all)

    Returns:
        Extracted value

    Raises:
        ValueError: If path is invalid or no match found

    Examples:
        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> extract_value("$.users", data)
        [{"name": "Alice"}, {"name": "Bob"}]
        >>> extract_value("$.users.length()", data)
        2
        >>> extract_value("$.users.name", data)
        "Alice"
    """
    return _enhanced_jsonpath.extract(path, data, index)
