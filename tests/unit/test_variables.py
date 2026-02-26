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
from apirun.utils.variables import (
    GLOBAL_PARAM_FUNCTIONS,
    register_global_param_function,
    render_template,
)


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


def test_global_param_function_no_args():
    """VAR-009: {{方法名}} 调用平台注册的全局参数函数（无参）。"""
    try:
        register_global_param_function("platform_sn", lambda: "SN-001")
        out = render_template("{{platform_sn}}", {})
        assert out == "SN-001"
    finally:
        GLOBAL_PARAM_FUNCTIONS.pop("platform_sn", None)


def test_global_param_function_with_args():
    """VAR-009: {{方法名(参数)}} 调用平台注册的全局参数函数。"""
    try:
        register_global_param_function("concat", lambda a, b: f"{a}_{b}")
        out = render_template("{{concat('x', 'y')}}", {})
        assert out == "x_y"
    finally:
        GLOBAL_PARAM_FUNCTIONS.pop("concat", None)


def test_variable_takes_precedence_over_global_func():
    """变量优先于全局参数函数同名。"""
    try:
        register_global_param_function("foo", lambda: "from_func")
        out = render_template("{{foo}}", {"foo": "from_var"})
        assert out == "from_var"
    finally:
        GLOBAL_PARAM_FUNCTIONS.pop("foo", None)

