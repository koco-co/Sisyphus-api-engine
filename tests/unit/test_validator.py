"""断言验证器单元测试（VLD-018～VLD-026 / TST-026）"""

import pytest

from apirun.result.models import AssertionResult
from apirun.validation.validator import run_assertion


def test_target_status_code():
    """target=status_code（VLD-021）"""
    resp = {"status_code": 200, "headers": {}, "body": None, "cookies": {}, "response_time": 100}
    r = run_assertion("status_code", "eq", 200, None, None, response=resp)
    assert r.status == "passed"
    assert r.actual == 200
    r2 = run_assertion("status_code", "eq", 201, None, None, response=resp)
    assert r2.status == "failed"
    assert r2.actual == 200
    assert r2.expected == 201


def test_target_response_time():
    """target=response_time（VLD-022）"""
    resp = {"status_code": 200, "response_time": 50}
    r = run_assertion("response_time", "lte", 100, None, None, response=resp)
    assert r.status == "passed"
    assert r.actual == 50


def test_target_json():
    """target=json JSONPath 提取（VLD-018）"""
    resp = {"body": {"code": 0, "data": {"id": "user-1"}}, "headers": {}, "cookies": {}}
    r = run_assertion("json", "eq", 0, "$.code", None, response=resp)
    assert r.status == "passed"
    assert r.actual == 0
    r2 = run_assertion("json", "eq", "user-1", "$.data.id", None, response=resp)
    assert r2.status == "passed"
    assert r2.actual == "user-1"


def test_target_header():
    """target=header（VLD-019）"""
    resp = {"headers": {"Content-Type": "application/json", "X-Request-Id": "req-1"}}
    r = run_assertion("header", "eq", "application/json", "Content-Type", None, response=resp)
    assert r.status == "passed"
    assert r.actual == "application/json"


def test_target_cookie():
    """target=cookie（VLD-020）"""
    resp = {"cookies": {"SESSIONID": "sess-123"}}
    r = run_assertion("cookie", "eq", "sess-123", "SESSIONID", None, response=resp)
    assert r.status == "passed"
    assert r.actual == "sess-123"


def test_target_env_variable():
    """target=env_variable（VLD-023）"""
    r = run_assertion(
        "env_variable", "eq", "expected_val", "my_var", None, variables={"my_var": "expected_val"}
    )
    assert r.status == "passed"
    assert r.actual == "expected_val"


def test_expected_variable_replacement():
    """expected 中 {{变量}} 替换（VLD-024）"""
    resp = {"status_code": 200}
    r = run_assertion(
        "status_code", "eq", "{{code}}", None, None, response=resp, variables={"code": 200}
    )
    assert r.status == "passed"
    assert r.expected == 200


def test_returns_assertion_result():
    """返回 AssertionResult 结构（VLD-025）"""
    resp = {"status_code": 200}
    r = run_assertion("status_code", "eq", 200, None, None, response=resp)
    assert isinstance(r, AssertionResult)
    assert r.target == "status_code"
    assert r.comparator == "eq"
    assert r.expected == 200
    assert r.actual == 200
    assert r.status == "passed"
    assert r.message is None


def test_failed_custom_message():
    """失败时使用自定义 message（VLD-026）"""
    resp = {"status_code": 200}
    r = run_assertion("status_code", "eq", 201, None, "期望 201 创建成功", response=resp)
    assert r.status == "failed"
    assert r.message == "期望 201 创建成功"


def test_failed_default_message():
    """失败时无自定义 message 则使用默认描述"""
    resp = {"status_code": 200}
    r = run_assertion("status_code", "eq", 201, None, None, response=resp)
    assert r.status == "failed"
    assert "201" in (r.message or "")
    assert "200" in (r.message or "")


def test_db_result_length():
    """db_result $.length 内置（VLD-027）"""
    db_rows = [{"id": 1, "email": "a@b.com"}, {"id": 2, "email": "b@b.com"}]
    r = run_assertion("db_result", "eq", 2, "$.length", None, db_rows=db_rows)
    assert r.status == "passed"
    assert r.actual == 2


def test_db_result_expression():
    """db_result JSONPath 从 rows 提取"""
    db_rows = [{"id": 1, "email": "a@b.com"}]
    r = run_assertion("db_result", "eq", "a@b.com", "$[0].email", None, db_rows=db_rows)
    assert r.status == "passed"
    assert r.actual == "a@b.com"
