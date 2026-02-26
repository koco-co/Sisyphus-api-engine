"""变量提取器 — 从响应/数据库结果中按规则提取变量，返回 ExtractResult（EXT-001～EXT-010）"""

from typing import Any

from jsonpath_ng import parse as jsonpath_parse

from apirun.core.models import ExtractRule
from apirun.result.models import ExtractResult


def _extract_json(body: Any, expression: str) -> Any:
    """从 body 用 JSONPath 提取；无匹配返回 None。"""
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


def _get_value(
    rule: ExtractRule,
    response: dict[str, Any] | None,
    variables: dict[str, Any],
    db_rows: list[dict[str, Any]] | None = None,
) -> Any:
    """
    根据 rule.type 与 rule.source_variable 从 response / variables / db_rows 提取值。
    source_variable 指定时从 variables[source_variable] 取数据源（视为 response 结构）；否则用 response。
    """
    # 数据源：默认上一请求响应，或 source_variable 指向的变量（EXT-009）
    data_source = response
    if rule.source_variable and rule.source_variable.strip():
        data_source = variables.get(rule.source_variable.strip())
        if not isinstance(data_source, dict):
            data_source = None

    if rule.type == "json":
        body = (data_source or {}).get("body") if data_source else None
        return _extract_json(body, rule.expression) if rule.expression else body

    if rule.type == "header":
        headers = (data_source or {}).get("headers") or {}
        return _extract_header(headers, rule.expression)

    if rule.type == "cookie":
        cookies = (data_source or {}).get("cookies") or {}
        return _extract_cookie(cookies, rule.expression)

    if rule.type == "db_result":
        if db_rows is None:
            return None
        return _extract_json(db_rows, rule.expression) if rule.expression else db_rows

    return None


def run_extract(
    rule: ExtractRule,
    response: dict[str, Any] | None = None,
    variables: dict[str, Any] | None = None,
    db_rows: list[dict[str, Any]] | None = None,
) -> ExtractResult:
    """
    执行单条提取规则，返回 ExtractResult（EXT-001～EXT-008）。
    - 提取失败且有 default 时使用 default、status=success（EXT-006）。
    - 提取失败且无 default 时 value 为 None、status=failed（EXT-007）。
    - scope 原样写入结果，供调用方写入对应变量池（EXT-004/005）。
    """
    variables = variables or {}
    value = _get_value(rule, response, variables, db_rows)

    # 提取失败：无匹配或数据源缺失
    failed = value is None and (rule.type != "json" or rule.expression != "$")

    if failed and rule.default is not None:
        value = rule.default
        failed = False

    status = "success" if not failed else "failed"
    return ExtractResult(
        name=rule.name,
        type=rule.type,
        expression=rule.expression,
        scope=rule.scope,
        value=value,
        status=status,
    )


def run_extract_batch(
    rules: list[ExtractRule],
    response: dict[str, Any] | None = None,
    variables: dict[str, Any] | None = None,
    db_rows: list[dict[str, Any]] | None = None,
) -> list[ExtractResult]:
    """批量执行提取规则，返回按规则顺序的 ExtractResult 列表。"""
    return [
        run_extract(r, response, variables, db_rows)
        for r in rules
    ]
