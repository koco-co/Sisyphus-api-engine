"""断言比较器 — 17 种比较逻辑（VLD-001～VLD-017）"""

import logging
import re
from collections.abc import Callable
from typing import Any

from apirun.security import regex_validator

logger = logging.getLogger("sisyphus")

# 类型匹配合法值
TYPE_NAMES = ("int", "str", "list", "dict", "bool", "null")


def _ensure_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x)


def compare_eq(actual: Any, expected: Any) -> bool:
    """等于（VLD-001）"""
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    return actual == expected


def compare_neq(actual: Any, expected: Any) -> bool:
    """不等于（VLD-002）"""
    return not compare_eq(actual, expected)


def compare_gt(actual: Any, expected: Any) -> bool:
    """大于（VLD-003）"""
    if actual is None or expected is None:
        return False
    try:
        return float(actual) > float(expected)
    except (TypeError, ValueError):
        return False


def compare_gte(actual: Any, expected: Any) -> bool:
    """大于等于（VLD-004）"""
    if actual is None or expected is None:
        return compare_eq(actual, expected)
    try:
        return float(actual) >= float(expected)
    except (TypeError, ValueError):
        return False


def compare_lt(actual: Any, expected: Any) -> bool:
    """小于（VLD-005）"""
    if actual is None or expected is None:
        return False
    try:
        return float(actual) < float(expected)
    except (TypeError, ValueError):
        return False


def compare_lte(actual: Any, expected: Any) -> bool:
    """小于等于（VLD-006）"""
    if actual is None or expected is None:
        return compare_eq(actual, expected)
    try:
        return float(actual) <= float(expected)
    except (TypeError, ValueError):
        return False


def compare_contains(actual: Any, expected: Any) -> bool:
    """包含（VLD-007）：字符串或列表包含 expected"""
    if actual is None:
        return False
    if isinstance(actual, str):
        return _ensure_str(expected) in actual
    if isinstance(actual, (list, tuple)):
        return expected in actual
    return _ensure_str(expected) in _ensure_str(actual)


def compare_not_contains(actual: Any, expected: Any) -> bool:
    """不包含（VLD-008）"""
    return not compare_contains(actual, expected)


def compare_startswith(actual: Any, expected: Any) -> bool:
    """前缀（VLD-009）"""
    if actual is None or expected is None:
        return False
    return _ensure_str(actual).startswith(_ensure_str(expected))


def compare_endswith(actual: Any, expected: Any) -> bool:
    """后缀（VLD-010）"""
    if actual is None or expected is None:
        return False
    return _ensure_str(actual).endswith(_ensure_str(expected))


def compare_matches(actual: Any, expected: Any) -> bool:
    """正则匹配（VLD-011）- 带 ReDoS 防护"""
    if actual is None or expected is None:
        return False

    pattern = str(expected)

    # ReDoS 安全验证
    try:
        regex_validator.validate(pattern)
    except Exception as e:
        logger.warning(f"正则表达式验证失败: {pattern}, 错误: {e}")
        return False

    try:
        return re.search(pattern, _ensure_str(actual)) is not None
    except re.error as e:
        logger.debug(f"正则匹配失败: pattern={pattern}, 错误: {e}")
        return False
    except Exception:
        logger.error(f"正则匹配发生未预期错误: pattern={pattern}", exc_info=True)
        return False


def compare_type_match(actual: Any, expected: Any) -> bool:
    """类型匹配（VLD-012）：expected 为类型名 int/str/list/dict/bool/null"""
    if expected is None or str(expected).strip().lower() == "null":
        return actual is None
    name = _ensure_str(expected).strip().lower()
    if name not in TYPE_NAMES:
        return False
    if name == "null":
        return actual is None
    if name == "int":
        return isinstance(actual, int) and not isinstance(actual, bool)
    if name == "str":
        return isinstance(actual, str)
    if name == "list":
        return isinstance(actual, list)
    if name == "dict":
        return isinstance(actual, dict)
    if name == "bool":
        return isinstance(actual, bool)
    return False


def _length_of(x: Any) -> int:
    if x is None:
        return 0
    if isinstance(x, (str, list, tuple, dict)):
        return len(x)
    return 0


def compare_length_eq(actual: Any, expected: Any) -> bool:
    """长度等于（VLD-013）"""
    try:
        exp_len = int(expected)
    except (TypeError, ValueError):
        return False
    return _length_of(actual) == exp_len


def compare_length_gt(actual: Any, expected: Any) -> bool:
    """长度大于（VLD-014）"""
    try:
        exp_len = int(expected)
    except (TypeError, ValueError):
        return False
    return _length_of(actual) > exp_len


def compare_length_lt(actual: Any, expected: Any) -> bool:
    """长度小于（VLD-015）"""
    try:
        exp_len = int(expected)
    except (TypeError, ValueError):
        return False
    return _length_of(actual) < exp_len


def compare_is_null(actual: Any, expected: Any) -> bool:
    """为空（VLD-016）：actual 为 None 或空字符串/空列表等"""
    if actual is None:
        return True
    if isinstance(actual, str) and actual.strip() == "":
        return True
    if isinstance(actual, (list, dict)) and len(actual) == 0:
        return True
    return False


def compare_is_not_null(actual: Any, expected: Any) -> bool:
    """不为空（VLD-017）"""
    return not compare_is_null(actual, expected)


# 比较器注册表：comparator 名称 -> 函数
COMPARATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": compare_eq,
    "neq": compare_neq,
    "gt": compare_gt,
    "gte": compare_gte,
    "lt": compare_lt,
    "lte": compare_lte,
    "contains": compare_contains,
    "not_contains": compare_not_contains,
    "startswith": compare_startswith,
    "endswith": compare_endswith,
    "matches": compare_matches,
    "type_match": compare_type_match,
    "length_eq": compare_length_eq,
    "length_gt": compare_length_gt,
    "length_lt": compare_length_lt,
    "is_null": compare_is_null,
    "is_not_null": compare_is_not_null,
}


def compare(comparator: str, actual: Any, expected: Any) -> bool:
    """根据 comparator 名称执行比较，未知名称返回 False。"""
    fn = COMPARATORS.get(comparator)
    if fn is None:
        return False
    return fn(actual, expected)
