"""变量替换工具 - 负责解析并渲染 {{var}} / {{func()}} 模板。

支持特性:
- 递归渲染 dict / list / str 结构中的变量引用
- 变量优先从 variables 字典中读取
- 未找到的函数名若在内置函数表中, 则按 {{func(...)}} 语法调用
"""

from __future__ import annotations

import re
from typing import Any

from apirun.utils.functions import BUILTIN_FUNCTIONS


_TEMPLATE_PATTERN = re.compile(r"\{\{\s*(?P<expr>[^}]+?)\s*\}\}")


class VariableRenderError(Exception):
    """变量渲染错误。"""


def _eval_function(expr: str) -> Any:
    """解析并执行内置函数表达式, 如 random(8) / random_uuid()."""
    name, _, args_part = expr.partition("(")
    name = name.strip()
    args_part = args_part.rstrip(")")
    func = BUILTIN_FUNCTIONS.get(name)
    if not func:
        raise VariableRenderError(f"未知内置函数: {name}")

    args: list[Any] = []
    if args_part.strip():
        # 简单按逗号分割, 去掉两侧空白与引号; 暂不支持复杂嵌套表达式
        for raw in args_part.split(","):
            token = raw.strip()
            if not token:
                continue
            # 去掉成对引号
            if (token.startswith("'") and token.endswith("'")) or (
                token.startswith('"') and token.endswith('"')
            ):
                args.append(token[1:-1])
            else:
                # 尝试解析为 int, 失败则按字符串处理
                try:
                    args.append(int(token))
                except ValueError:
                    args.append(token)
    return func(*args)


def _render_string(template: str, variables: dict[str, Any]) -> Any:
    """渲染单个字符串模板。

    若字符串整体就是一个 {{...}} 表达式:
    - 如果是变量名, 返回变量实际值(保持原类型)
    - 如果是函数调用, 返回函数执行结果(保持原类型)

    其他情况按普通模板字符串处理, 返回 str。
    """

    def replace(match: re.Match[str]) -> str:
        expr = match.group("expr").strip()
        # 仅变量名
        if "(" not in expr and ")" not in expr:
            if expr not in variables:
                raise VariableRenderError(f"变量未找到: {expr}")
            return str(variables[expr])
        # 函数调用
        value = _eval_function(expr)
        return str(value)

    # 整个字符串正好是一个 {{...}} 表达式时, 尝试返回原始类型
    full_match = _TEMPLATE_PATTERN.fullmatch(template.strip())
    if full_match:
        expr = full_match.group("expr").strip()
        if "(" not in expr and ")" not in expr:
            if expr not in variables:
                raise VariableRenderError(f"变量未找到: {expr}")
            return variables[expr]
        return _eval_function(expr)

    try:
        return _TEMPLATE_PATTERN.sub(replace, template)
    except VariableRenderError:
        raise


def render_value(value: Any, variables: dict[str, Any]) -> Any:
    """递归渲染任意值中的变量引用。

    - str: 按模板字符串处理
    - dict: 递归处理 key 和 value
    - list/tuple: 递归处理每个元素
    - 其他类型: 原样返回
    """
    if isinstance(value, str):
        return _render_string(value, variables)
    if isinstance(value, dict):
        return {render_value(k, variables): render_value(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [render_value(item, variables) for item in value]
    if isinstance(value, tuple):
        return tuple(render_value(item, variables) for item in value)
    return value


def render_template(template: Any, variables: dict[str, Any] | None = None) -> Any:
    """对给定模板执行变量替换。

    Args:
        template: 任意 Python 值, 包含待替换的 {{var}} 模板
        variables: 变量字典

    Returns:
        渲染后的值, 尽量保持原始类型语义。
    """
    variables = variables or {}
    return render_value(template, variables)

