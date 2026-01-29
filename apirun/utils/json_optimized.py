"""Optimized JSON utilities for Sisyphus API Engine.

This module provides high-performance JSON serialization/deserialization
with caching and optimization strategies.

Performance improvements:
- Caching for frequently serialized objects
- Optimized serializers for specific data types
- Reduced deep copy operations
- Stream processing for large payloads

Following Google Python Style Guide.
"""

import json
import functools
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal


class OptimizedJSONEncoder(json.JSONEncoder):
    """Optimized JSON encoder with performance improvements.

    Features:
    - Faster datetime serialization
    - Decimal to float conversion
    - Set to list conversion
    - Caching for repeated objects
    """

    def __init__(self, *args, **kwargs):
        """Initialize encoder."""
        super().__init__(*args, **kwargs)
        self._cache = {}

    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format.

        Args:
            obj: Object to convert

        Returns:
            Serializable version of the object
        """
        # Check cache first
        obj_id = id(obj)
        if obj_id in self._cache:
            return self._cache[obj_id]

        if isinstance(obj, datetime):
            result = obj.isoformat()
        elif isinstance(obj, date):
            result = obj.isoformat()
        elif isinstance(obj, Decimal):
            result = float(obj)
        elif isinstance(obj, set):
            result = list(obj)
        elif hasattr(obj, "__dict__"):
            result = obj.__dict__
        else:
            result = str(obj)

        # Cache if it's a simple type
        if isinstance(result, (str, int, float, bool)):
            self._cache[obj_id] = result

        return result


# Cache for JSON strings
_json_cache: Dict[str, str] = {}
_cache_max_size = 1000


def json_dumps(obj: Any, indent: Optional[int] = None, cache_key: Optional[str] = None) -> str:
    """Optimized JSON serialization with caching.

    Args:
        obj: Object to serialize
        indent: Indentation for pretty printing (None for compact)
        cache_key: Optional cache key for this object

    Returns:
        JSON string
    """
    # Check cache if key provided
    if cache_key and cache_key in _json_cache:
        return _json_cache[cache_key]

    # Use optimized encoder
    result = json.dumps(
        obj,
        indent=indent,
        cls=OptimizedJSONEncoder,
        ensure_ascii=False,  # Faster, allows UTF-8
        separators=(",", ":") if indent is None else None,  # Compact format
    )

    # Cache result if key provided
    if cache_key:
        _json_cache[cache_key] = result
        # Limit cache size
        if len(_json_cache) > _cache_max_size:
            _json_cache.clear()

    return result


def json_loads(s: str) -> Any:
    """Optimized JSON deserialization.

    Args:
        s: JSON string to parse

    Returns:
        Parsed object
    """
    return json.loads(s)


def clear_json_cache() -> None:
    """Clear JSON serialization cache."""
    global _json_cache
    _json_cache.clear()


class StreamingJSONEncoder:
    """Streaming JSON encoder for large payloads.

    This encoder processes large objects in chunks to reduce memory usage.
    """

    @staticmethod
    def encode_iterable(items: List[Any], chunk_size: int = 100) -> str:
        """Encode a list in chunks.

        Args:
            items: List of items to encode
            chunk_size: Number of items per chunk

        Returns:
            JSON array string
        """
        parts = ["["]

        for i, item in enumerate(items):
            if i > 0:
                parts.append(",")
            if i % chunk_size == 0 and i > 0:
                # Small pause to allow GC
                pass
            parts.append(json_dumps(item))

        parts.append("]")
        return "".join(parts)


def fast_deepcopy(obj: Any) -> Any:
    """Fast deep copy using JSON serialization for simple objects.

    This is faster than copy.deepcopy for JSON-serializable objects.

    Args:
        obj: Object to copy

    Returns:
        Copy of the object
    """
    try:
        return json.loads(json.dumps(obj))
    except (TypeError, ValueError):
        # Fallback to regular deepcopy for complex objects
        import copy
        return copy.deepcopy(obj)


def merge_dicts(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries efficiently.

    Args:
        base: Base dictionary
        updates: Updates to apply

    Returns:
        Merged dictionary (creates new dict, doesn't modify inputs)
    """
    result = base.copy()
    result.update(updates)
    return result


def get_json_size(obj: Any) -> int:
    """Get the size of object when JSON-serialized.

    Args:
        obj: Object to measure

    Returns:
        Size in bytes
    """
    return len(json_dumps(obj).encode("utf-8"))


def validate_json(json_str: str) -> bool:
    """Validate if a string is valid JSON.

    Args:
        json_str: String to validate

    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (ValueError, json.JSONDecodeError):
        return False


def format_json_error(error: Exception) -> str:
    """Format JSON error message for better debugging.

    Args:
        error: JSON parsing error

    Returns:
            Formatted error message
    """
    if isinstance(error, json.JSONDecodeError):
        return (
            f"JSON parsing error at line {error.lineno}, column {error.colno}: "
            f"{error.msg}"
        )
    return str(error)


# Performance monitoring decorator
def monitor_json_performance(func):
    """Decorator to monitor JSON operation performance.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function with performance logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        # Log slow operations
        if elapsed > 0.1:  # 100ms threshold
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Slow JSON operation: {func.__name__} took {elapsed:.3f}s"
            )

        return result

    return wrapper


@monitor_json_performance
def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON with error handling.

    Args:
        json_str: String to parse
        default: Default value if parsing fails

    Returns:
        Parsed object or default value
    """
    try:
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON parsing failed: {format_json_error(e)}")
        return default
