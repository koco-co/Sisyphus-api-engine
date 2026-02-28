"""正则表达式安全验证器 — 防止 ReDoS（正则表达式拒绝服务）攻击"""

import re
import threading
from typing import Final

from apirun.errors import REGEX_VALIDATION_ERROR, EngineError


class RegexValidator:
    """正则表达式安全验证器，检测和阻止潜在的 ReDoS 攻击"""

    # ReDoS 危险模式（精确检测嵌套量词和复杂重复）
    DANGEROUS_PATTERNS: Final[list[tuple[str, str]]] = [
        # 字符类嵌套量词
        (r"\(\[.\?\]\*[+\*]\)", "字符类嵌套量词"),
        (r"\(\[.\?\]\+\)[+\*]", "字符类嵌套量词"),
        (r"\(\[[a-zA-Z]\]\*\)\+", "字符类嵌套量词"),
        (r"\(\[[a-zA-Z]\]\+\)\*", "字符类嵌套量词"),
        (r"\(\[.*?\]\*[+\*]\)", "任意字符类嵌套量词"),
        # 分组嵌套
        (r"\([a-z]+\)\*[+\*]", "字母分组嵌套量词"),
        (r"\(\w+\)\*[+\*]", "单词字符分组嵌套量词"),
        (r"\([a-zA-Z]+\)\*[+\*]", "字母分组嵌套量词"),
        # 双重嵌套
        (r"\(\[[a-z]\]\*\)\+", "双重字符类嵌套"),
        (r"\(([a-z]+)\*\)\+", "双重分组嵌套"),
        (r"\(\[.*?\]\)\*[+\*]", "字符类分组嵌套"),
    ]

    # 安全限制
    MAX_REGEX_LENGTH: Final[int] = 1000  # 正则表达式最大长度
    MAX_NESTED_GROUPS: Final[int] = 10  # 最大嵌套括号层数
    EXECUTION_TIMEOUT: Final[float] = 1.0  # 执行超时（秒）

    def __init__(self) -> None:
        """初始化验证器"""
        self._lock = threading.Lock()

    def _count_nested_groups(self, pattern: str) -> int:
        """计算括号嵌套深度"""
        max_depth = 0
        current_depth = 0
        in_char_class = False
        escaped = False

        for char in pattern:
            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == "[" and not in_char_class:
                in_char_class = True
                continue

            if char == "]" and in_char_class:
                in_char_class = False
                continue

            if in_char_class:
                continue

            if char == "(":
                current_depth += 1
                if current_depth > max_depth:
                    max_depth = current_depth
            elif char == ")":
                current_depth -= 1

        return max_depth

    def validate(self, pattern: str) -> None:
        """
        验证正则表达式是否安全。

        Args:
            pattern: 要验证的正则表达式

        Raises:
            EngineError: 如果正则表达式不安全
        """
        if not pattern or not isinstance(pattern, str):
            return

        # 检查长度
        if len(pattern) > self.MAX_REGEX_LENGTH:
            raise EngineError(
                REGEX_VALIDATION_ERROR,
                f"正则表达式过长（{len(pattern)} > {self.MAX_REGEX_LENGTH}）",
                detail=f"最大允许 {self.MAX_REGEX_LENGTH} 字符，实际 {len(pattern)} 字符",
            )

        # 检查嵌套深度
        nested_depth = self._count_nested_groups(pattern)
        if nested_depth > self.MAX_NESTED_GROUPS:
            raise EngineError(
                REGEX_VALIDATION_ERROR,
                f"正则表达式嵌套过深（{nested_depth} > {self.MAX_NESTED_GROUPS}）",
                detail=f"最大允许 {self.MAX_NESTED_GROUPS} 层，实际 {nested_depth} 层",
            )

        # 检查危险模式
        # 额外检查常见的 ReDoS 模式
        if re.search(r"\(\[.*?\]\*[+\*]\)", pattern) or re.search(r"\(\[.*?\]\+\)[+\*]", pattern):
            raise EngineError(
                REGEX_VALIDATION_ERROR,
                "检测到潜在 ReDoS 风险: 字符类嵌套量词",
                detail=f"模式: {pattern}",
            )

        for dangerous_pattern, description in self.DANGEROUS_PATTERNS:
            try:
                if re.search(dangerous_pattern, pattern):
                    raise EngineError(
                        REGEX_VALIDATION_ERROR,
                        f"检测到潜在 ReDoS 风险: {description}",
                        detail=f"模式: {pattern}, 匹配的危险规则: {dangerous_pattern}",
                    )
            except re.error:
                # 某些危险模式本身可能导致 re.error，跳过
                continue

        # 尝试编译正则表达式，捕获语法错误
        try:
            re.compile(pattern)
        except re.error as e:
            raise EngineError(
                REGEX_VALIDATION_ERROR,
                f"正则表达式语法错误: {str(e)}",
                detail=f"模式: {pattern}, 错误: {str(e)}",
            )


# 全局单例
_regex_validator_instance: RegexValidator | None = None
_validator_lock = threading.Lock()


def get_regex_validator() -> RegexValidator:
    """获取正则表达式验证器单例"""
    global _regex_validator_instance
    if _regex_validator_instance is None:
        with _validator_lock:
            if _regex_validator_instance is None:
                _regex_validator_instance = RegexValidator()
    return _regex_validator_instance
