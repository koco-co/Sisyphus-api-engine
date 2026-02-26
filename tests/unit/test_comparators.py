"""断言比较器单元测试（VLD-001～VLD-017 / TST-025）"""

import pytest

from apirun.validation.comparators import (
    compare,
    compare_contains,
    compare_endswith,
    compare_eq,
    compare_gt,
    compare_gte,
    compare_length_eq,
    compare_length_gt,
    compare_length_lt,
    compare_lt,
    compare_lte,
    compare_matches,
    compare_neq,
    compare_not_contains,
    compare_startswith,
    compare_type_match,
    compare_is_null,
    compare_is_not_null,
    COMPARATORS,
)


def test_eq():
    assert compare_eq(1, 1) is True
    assert compare_eq("a", "a") is True
    assert compare_eq(None, None) is True
    assert compare_eq(1, 2) is False


def test_neq():
    assert compare_neq(1, 2) is True
    assert compare_neq(1, 1) is False


def test_gt_gte_lt_lte():
    assert compare_gt(3, 2) is True
    assert compare_gt(2, 3) is False
    assert compare_gte(2, 2) is True
    assert compare_lt(1, 2) is True
    assert compare_lte(2, 2) is True


def test_contains_not_contains():
    assert compare_contains("hello world", "world") is True
    assert compare_contains("hello", "x") is False
    assert compare_contains([1, 2, 3], 2) is True
    assert compare_not_contains("hello", "x") is True
    assert compare_not_contains([1, 2], 3) is True


def test_startswith_endswith():
    assert compare_startswith("hello", "hel") is True
    assert compare_startswith("hello", "x") is False
    assert compare_endswith("hello", "lo") is True
    assert compare_endswith("hello", "x") is False


def test_matches():
    assert compare_matches("abc123", r"\d+") is True
    assert compare_matches("abc", r"^[0-9]+$") is False


def test_type_match():
    assert compare_type_match(1, "int") is True
    assert compare_type_match("x", "str") is True
    assert compare_type_match([], "list") is True
    assert compare_type_match({}, "dict") is True
    assert compare_type_match(True, "bool") is True
    assert compare_type_match(None, "null") is True
    assert compare_type_match(1, "str") is False


def test_length_eq_gt_lt():
    assert compare_length_eq("abc", 3) is True
    assert compare_length_eq([1, 2, 3], 3) is True
    assert compare_length_gt("abcd", 3) is True
    assert compare_length_lt("ab", 3) is True


def test_is_null_is_not_null():
    assert compare_is_null(None, None) is True
    assert compare_is_null("", None) is True
    assert compare_is_null("  ", None) is True
    assert compare_is_null([], None) is True
    assert compare_is_null("x", None) is False
    assert compare_is_not_null("x", None) is True
    assert compare_is_not_null(None, None) is False


def test_compare_registry():
    """17 种比较器均已注册"""
    assert len(COMPARATORS) == 17
    assert compare("eq", 1, 1) is True
    assert compare("unknown", 1, 1) is False
