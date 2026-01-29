"""Template Functions for Sisyphus API Engine.

This module provides built-in functions that can be used in variable templates.
These functions are automatically available in all template expressions.

Available functions:
- random(): Generate random integer
- random_str(): Generate random string
- uuid(): Generate UUID
- timestamp(): Generate current timestamp
- date(): Generate formatted date string
- now(): Generate current datetime

Following Google Python Style Guide.
"""

import random
import string
import uuid
from datetime import datetime
from typing import Optional


def random_int(min_val: int = 0, max_val: int = 1000000) -> int:
    """Generate a random integer.

    Args:
        min_val: Minimum value (default: 0)
        max_val: Maximum value (default: 1000000)

    Returns:
        Random integer between min_val and max_val

    Examples:
        ${random()} -> 123456
        ${random(1, 100)} -> 42
    """
    return random.randint(min_val, max_val)


def random_str(length: int = 8, chars: Optional[str] = None) -> str:
    """Generate a random string.

    Args:
        length: Length of the string (default: 8)
        chars: Character set to use (default: alphanumeric)

    Returns:
        Random string of specified length

    Examples:
        ${random_str()} -> "aB3xK9mZ"
        ${random_str(16)} -> "xY7mP2kL9qR4nT3j"
        ${random_str(4, 'ABC')} -> "ABCA"
    """
    if chars is None:
        chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def uuid_str() -> str:
    """Generate a random UUID string (without dashes).

    Returns:
        UUID string without dashes

    Examples:
        ${uuid()} -> "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    """
    return uuid.uuid4().hex


def uuid4() -> str:
    """Generate a standard UUID v4 string (with dashes).

    Returns:
        Standard UUID v4 string

    Examples:
        ${uuid4()} -> "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
    """
    return str(uuid.uuid4())


def timestamp() -> int:
    """Generate current Unix timestamp.

    Returns:
        Current Unix timestamp (seconds since epoch)

    Examples:
        ${timestamp()} -> 1706508000
    """
    return int(datetime.now().timestamp())


def timestamp_ms() -> int:
    """Generate current Unix timestamp in milliseconds.

    Returns:
        Current Unix timestamp in milliseconds

    Examples:
        ${timestamp_ms()} -> 1706508000000
    """
    return int(datetime.now().timestamp() * 1000)


def date(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Generate formatted current date/time string.

    Args:
        format_str: strftime format string (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        Formatted date/time string

    Examples:
        ${date()} -> "2026-01-29 13:30:00"
        ${date('%Y-%m-%d')} -> "2026-01-29"
        ${date('%Y%m%d')} -> "20260129"
    """
    return datetime.now().strftime(format_str)


def now() -> datetime:
    """Get current datetime object.

    Returns:
        Current datetime object

    Examples:
        ${now()} -> datetime object
        ${now().strftime('%Y-%m-%d')} -> "2026-01-29"
    """
    return datetime.now()


def choice(choices: list) -> any:
    """Choose a random element from a list.

    Args:
        choices: List of choices

    Returns:
        Randomly chosen element

    Examples:
        ${choice(['a', 'b', 'c'])} -> "b"
        ${choice([1, 2, 3])} -> 2
    """
    return random.choice(choices)


def randint(min_val: int = 0, max_val: int = 100) -> int:
    """Alias for random_int() for compatibility.

    Args:
        min_val: Minimum value (default: 0)
        max_val: Maximum value (default: 100)

    Returns:
        Random integer between min_val and max_val
    """
    return random_int(min_val, max_val)


# Dictionary of all built-in functions
TEMPLATE_FUNCTIONS = {
    "random": random_int,
    "randint": randint,
    "random_str": random_str,
    "uuid": uuid_str,
    "uuid4": uuid4,
    "timestamp": timestamp,
    "timestamp_ms": timestamp_ms,
    "date": date,
    "now": now,
    "choice": choice,
}


def get_template_functions() -> dict:
    """Get all available template functions.

    Returns:
        Dictionary of function name to function object
    """
    return TEMPLATE_FUNCTIONS.copy()
