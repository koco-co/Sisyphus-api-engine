"""断言验证器 — 按 target 提取实际值、执行比较、返回 AssertionResult（VLD-018～VLD-027）"""

from typing import Any

from jsonpath_ng import parse as jsonpath_parse

from apirun.result.models import AssertionResult
from apirun.utils.variables import render_template

from .comparators import compare


def _extract_json(body: Any, expression: str) -> Any:
    """从 body 用 JSONPath 提取值；无匹配返回 None。"""
    if body is None:
        return None
    try:
        expr = jsonpath_parse(expression)
        matches = expr.find(body)
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0].value
        return [m.value for m in matches]
    except Exception:
        return None


def _extract_header(headers: dict[str, Any], name: str) -> Any:
    """从 headers 按名称取值（大小写不敏感）。"""
    if not headers:
        return None
    name_lower = name.strip().lower()
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return None


def _extract_cookie(cookies: dict[str, Any], name: str) -> Any:
    """从 cookies 按名称取值。"""
    if not cookies:
        return None
    return cookies.get(name.strip()) or cookies.get(name.strip().lower())


def _extract_actual(
    target: str,
    expression: str | None,
    response: dict[str, Any] | None,
    variables: dict[str, Any],
    db_rows: list[dict[str, Any]] | None = None,
) -> Any:
    """
    根据 target 从 response / variables / db_rows 提取实际值。
    - json: JSONPath 从 response["body"] 提取
    - header: expression 为 header 名称，从 response["headers"] 提取
    - cookie: expression 为 cookie 名称，从 response["cookies"] 提取
    - status_code: 从 response["status_code"]
    - response_time: 从 response["response_time"]
    - env_variable: expression 为变量名，从 variables 提取
    - db_result: expression 为 JSONPath（含 $.length），从 db_rows 提取
    """
    if target == "json":
        body = response.get("body") if response else None
        return _extract_json(body, expression or "$") if expression else body

    if target == "header":
        headers = (response or {}).get("headers") or {}
        return _extract_header(headers, expression or "")

    if target == "cookie":
        cookies = (response or {}).get("cookies") or {}
        return _extract_cookie(cookies, expression or "")

    if target == "status_code":
        return (response or {}).get("status_code") if response else None

    if target == "response_time":
        return (response or {}).get("response_time") if response else None

    if target == "env_variable":
        if not expression:
            return None
        return variables.get(expression.strip())

    if target == "db_result":
        if db_rows is None:
            return None
        if expression and expression.strip() == "$.length":
            return len(db_rows)
        if expression:
            # 对 db_rows 做 JSONPath（db_rows 为 list[dict]）
            return _extract_json(db_rows, expression)
        return db_rows

    return None


def run_assertion(
    target: str,
    comparator: str,
    expected: Any,
    expression: str | None,
    message: str | None,
    response: dict[str, Any] | None = None,
    variables: dict[str, Any] | None = None,
    db_rows: list[dict[str, Any]] | None = None,
) -> AssertionResult:
    """
    执行单条断言，返回 AssertionResult（VLD-018～VLD-026）。
    - expected 会先经 render_template 做变量替换（VLD-024）。
    - 失败时 message 为自定义消息或默认描述（VLD-026）。
    """
    variables = variables or {}
    expected_rendered = render_template(expected, variables)
    actual = _extract_actual(target, expression, response, variables, db_rows)

    passed = compare(comparator, actual, expected_rendered)

    if passed:
        return AssertionResult(
            target=target,
            expression=expression,
            comparator=comparator,
            expected=expected_rendered,
            actual=actual,
            status="passed",
            message=None,
        )

    # 失败时：优先使用自定义 message，否则默认描述（VLD-026）
    if message and str(message).strip():
        msg = str(message).strip()
    else:
        msg = f"断言失败: 期望 {comparator} {expected_rendered}, 实际为 {actual}"

    return AssertionResult(
        target=target,
        expression=expression,
        comparator=comparator,
        expected=expected_rendered,
        actual=actual,
        status="failed",
        message=msg,
    )
