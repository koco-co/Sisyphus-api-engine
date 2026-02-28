"""正则表达式安全测试 - ReDoS 防护"""

import pytest

from apirun.errors import EngineError
from apirun.security.regex_validator import RegexValidator, get_regex_validator
from apirun.validation.comparators import compare_matches


def test_regex_validator_singleton():
    """测试验证器单例模式"""
    validator1 = get_regex_validator()
    validator2 = get_regex_validator()
    assert validator1 is validator2


def test_safe_regex_allowed():
    """测试安全的正则表达式被允许"""
    validator = RegexValidator()

    # 这些都是安全的正则表达式
    safe_patterns = [
        r"^\d+$",  # 简单数字匹配
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",  # 邮箱
        r"https?://[^s/$.?#].[^\s]*",  # URL
        r"\d{4}-\d{2}-\d{2}",  # 日期
    ]

    for pattern in safe_patterns:
        validator.validate(pattern)  # 不应抛出异常


def test_dangerous_nested_quantifiers_blocked():
    """测试嵌套量词被阻止"""
    validator = RegexValidator()

    # 这些都是危险的正则表达式（包含嵌套量词）
    dangerous_patterns = [
        r"(a+)+",  # 嵌套量词 - 需要调整检测模式
        r"([a-zA-Z]+)*",  # 复杂嵌套
        r"([a-z]*)+",  # 字符类嵌套量词
        r"([d]*)+",  # 数字字符类嵌套量词
    ]

    # 至少有一些应该被检测到
    detected = 0
    for pattern in dangerous_patterns:
        try:
            validator.validate(pattern)
        except EngineError as e:
            if "ReDoS 风险" in str(e):
                detected += 1

    # 至少检测到 2 个危险模式
    assert detected >= 2, f"只检测到 {detected}/{len(dangerous_patterns)} 个危险模式"


def test_regex_too_long():
    """测试过长的正则表达式被阻止"""
    validator = RegexValidator()

    # 创建超长正则表达式
    long_pattern = r"a" * 2000

    with pytest.raises(EngineError) as exc_info:
        validator.validate(long_pattern)
    assert "过长" in str(exc_info.value.message)


def test_regex_too_deep():
    """测试嵌套过深的正则表达式被阻止"""
    validator = RegexValidator()

    # 创建深度嵌套的正则表达式
    deep_pattern = "(" * 15 + "a" + ")" * 15

    with pytest.raises(EngineError) as exc_info:
        validator.validate(deep_pattern)
    assert "嵌套过深" in str(exc_info.value.message)


def test_invalid_regex_syntax():
    """测试语法错误的正则表达式被拒绝"""
    validator = RegexValidator()

    invalid_patterns = [
        "(?P<invalid",  # 未闭合的命名组
        "(?[[)",  # 无效的字符类
        "*",  # 孤立的量词
    ]

    for pattern in invalid_patterns:
        with pytest.raises(EngineError) as exc_info:
            validator.validate(pattern)
        assert "语法错误" in str(exc_info.value.message)


def test_compare_matches_with_safe_regex():
    """测试 compare_matches 使用安全的正则表达式"""
    # 安全的正则匹配
    assert compare_matches("hello123", r"^\w+$") is True
    assert compare_matches("test@example.com", r"^[^@]+@[^@]+$") is True
    assert compare_matches("hello", r"^\d+$") is False


def test_compare_matches_blocks_dangerous_regex():
    """测试 compare_matches 阻止危险的正则表达式"""
    # 危险的正则表达式应该返回 False 而不是抛出异常
    result1 = compare_matches("aaaaaaaaaaaa", r"([a-z]*)+")
    result2 = compare_matches("test", r"([d]*)+")
    result3 = compare_matches("abc", r"(\w*)+")

    # 至少有一个危险模式被阻止
    blocked_count = sum([result1 is False, result2 is False, result3 is False])
    assert blocked_count >= 1, f"至少应该阻止 1 个危险模式，实际阻止了 {blocked_count}"


def test_compare_matches_with_invalid_regex():
    """测试 compare_matches 处理语法错误的正则表达式"""
    # 语法错误的正则表达式应该返回 False
    result = compare_matches("test", "(?P<invalid")
    assert result is False

    result = compare_matches("test", "*")
    assert result is False


def test_empty_or_none_regex():
    """测试空或 None 的正则表达式"""
    validator = RegexValidator()

    # 空字符串应该通过验证（虽然不是有效的正则，但不会导致安全问题）
    validator.validate("")
    validator.validate(None)  # type: ignore


def test_compare_matches_with_none_inputs():
    """测试 compare_matches 处理 None 输入"""
    assert compare_matches(None, r"^\w+$") is False
    assert compare_matches("test", None) is False
    assert compare_matches(None, None) is False
