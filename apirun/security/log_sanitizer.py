"""日志脱敏器"""

import re
from typing import Any


class LogSanitizer:
    """日志脱敏器"""

    PATTERN_PAIRS = [
        (re.compile(r'(["\']?password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.I), r"\1***\3"),
        (re.compile(r'(["\']?token["\']?\s*[:=]\s*["\'])([^"\']{20,})(["\'])', re.I), r"\1***\3"),
        (re.compile(r'(["\']?api[_-]?key["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.I), r"\1***\3"),
        (re.compile(r"(Authorization:\s*Bearer\s+)([^\s]+)", re.I), r"\1***"),
    ]

    def sanitize(self, data: Any) -> Any:
        if isinstance(data, str):
            result = data
            for pattern, replacement in self.PATTERN_PAIRS:
                result = pattern.sub(replacement, result)
            return result
        if isinstance(data, dict):
            return {k: self.sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.sanitize(item) for item in data]
        return data
