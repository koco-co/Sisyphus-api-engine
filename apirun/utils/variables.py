"""变量替换工具 - 负责解析并渲染 {{var}} / {{func()}} 模板。

支持特性:
- 递归渲染 dict / list / str 结构中的变量引用
- 变量优先从 variables 字典中读取
- 内置函数与全局参数函数: {{func(...)}} 或 {{方法名}}（VAR-009）
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from apirun.utils.functions import BUILTIN_FUNCTIONS

# 平台注册的全局参数函数：{{方法名}} / {{方法名(参数)}}（VAR-009）
GLOBAL_PARAM_FUNCTIONS: dict[str, Callable[..., Any]] = {}


def register_global_param_function(name: str, func: Callable[..., Any]) -> None:
    """注册全局参数函数，供模板 {{name}} 或 {{name(...)}} 调用。"""
    GLOBAL_PARAM_FUNCTIONS[name] = func


_TEMPLATE_PATTERN = re.compile(r"\{\{\s*(?P<expr>[^}]+?)\s*\}\}")


class VariableRenderError(Exception):
    """变量渲染错误。"""


def _parse_func_args(args_part: str) -> list[Any]:
    """解析函数参数字符串为列表。"""
    args: list[Any] = []
    for raw in args_part.split(","):
        token = raw.strip()
        if not token:
            continue
        if (token.startswith("'") and token.endswith("'")) or (
            token.startswith('"') and token.endswith('"')
        ):
            args.append(token[1:-1])
        else:
            try:
                args.append(int(token))
            except ValueError:
                args.append(token)
    return args


def _eval_function(expr: str) -> Any:
    """解析并执行函数表达式：先内置函数，再全局参数函数（VAR-009）。"""
    name, _, args_part = expr.partition("(")
    name = name.strip()
    args_part = args_part.rstrip(")")
    func = BUILTIN_FUNCTIONS.get(name) or GLOBAL_PARAM_FUNCTIONS.get(name)
    if not func:
        raise VariableRenderError(f"未知函数: {name}")
    args = _parse_func_args(args_part)
    return func(*args)


def _render_string(template: str, variables: dict[str, Any]) -> Any:
    """渲染单个字符串模板。

    若字符串整体就是一个 {{...}} 表达式:
    - 如果是变量名, 返回变量实际值(保持原类型)
    - 如果是函数调用, 返回函数执行结果(保持原类型)

    其他情况按普通模板字符串处理, 返回 str。
    """

    def _resolve_expr(expr: str) -> Any:
        # 仅变量名：先 variables，再全局参数函数无参调用（VAR-009）
        if "(" not in expr and ")" not in expr:
            if expr in variables:
                return variables[expr]
            if expr in GLOBAL_PARAM_FUNCTIONS:
                return GLOBAL_PARAM_FUNCTIONS[expr]()
            raise VariableRenderError(f"变量或函数未找到: {expr}")
        return _eval_function(expr)

    def replace(match: re.Match[str]) -> str:
        expr = match.group("expr").strip()
        return str(_resolve_expr(expr))

    # 整个字符串正好是一个 {{...}} 表达式时, 尝试返回原始类型
    full_match = _TEMPLATE_PATTERN.fullmatch(template.strip())
    if full_match:
        expr = full_match.group("expr").strip()
        return _resolve_expr(expr)

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
