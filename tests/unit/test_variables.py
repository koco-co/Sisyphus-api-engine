"""变量替换与内置函数单元测试"""

from __future__ import annotations

import re

from apirun.utils.functions import (
    fn_datetime,
    fn_random,
    fn_random_uuid,
    fn_timestamp,
    fn_timestamp_ms,
)
from apirun.utils.variables import render_template


def test_fn_random_length_and_charset():
    value = fn_random(12)
    assert len(value) == 12
    assert re.fullmatch(r"[a-z0-9]{12}", value)


def test_fn_random_uuid_format():
    value = fn_random_uuid()
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value
    )


def test_timestamp_monotonic():
    t1 = fn_timestamp()
    t2 = fn_timestamp()
    assert isinstance(t1, int)
    assert t2 >= t1


def test_timestamp_ms_monotonic():
    t1 = fn_timestamp_ms()
    t2 = fn_timestamp_ms()
    assert isinstance(t1, int)
    assert t2 >= t1


def test_datetime_format():
    s = fn_datetime("%Y-%m-%d")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", s)


def test_render_template_simple_str():
    tpl = "Hello, {{name}}"
    result = render_template(tpl, {"name": "World"})
    assert result == "Hello, World"


def test_render_template_full_expression_returns_raw_type():
    tpl = "{{count}}"
    result = render_template(tpl, {"count": 123})
    assert isinstance(result, int)
    assert result == 123


def test_render_template_nested_dict_and_list():
    tpl = {
        "url": "/api/{{version}}/users/{{user_id}}",
        "headers": {"X-Request-ID": "{{req_id}}"},
        "ids": ["{{id1}}", "{{id2}}"],
    }
    variables = {
        "version": "v1",
        "user_id": 42,
        "req_id": "abc",
        "id1": 1,
        "id2": 2,
    }
    rendered = render_template(tpl, variables)
    assert rendered["url"] == "/api/v1/users/42"
    assert rendered["headers"]["X-Request-ID"] == "abc"
    # 未包含模板占位符的列表元素保持原始类型
    assert rendered["ids"] == [1, 2]


def test_render_template_builtin_function_random():
    tpl = "user_{{random(8)}}"
    rendered = render_template(tpl, {})
    assert rendered.startswith("user_")
    suffix = rendered.split("_", 1)[1]
    assert len(suffix) == 8

