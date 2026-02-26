"""变量提取器单元测试（EXT-001～EXT-009 / TST-027）"""

import pytest

from apirun.core.models import ExtractRule
from apirun.extractor.extractor import run_extract, run_extract_batch


def test_extract_json():
    """type=json JSONPath 提取（EXT-001）"""
    resp = {"body": {"code": 0, "data": {"id": "user-1", "token": "t1"}}, "headers": {}, "cookies": {}}
    rule = ExtractRule(name="user_id", type="json", expression="$.data.id", scope="global")
    r = run_extract(rule, response=resp)
    assert r.status == "success"
    assert r.value == "user-1"
    assert r.type == "json"
    assert r.scope == "global"


def test_extract_header():
    """type=header 按名称取值（EXT-002）"""
    resp = {"headers": {"Content-Type": "application/json", "X-Request-Id": "req-1"}}
    rule = ExtractRule(name="ct", type="header", expression="Content-Type", scope="global")
    r = run_extract(rule, response=resp)
    assert r.status == "success"
    assert r.value == "application/json"


def test_extract_cookie():
    """type=cookie 按名称取值（EXT-003）"""
    resp = {"cookies": {"SESSIONID": "sess-123"}}
    rule = ExtractRule(name="sid", type="cookie", expression="SESSIONID", scope="environment")
    r = run_extract(rule, response=resp)
    assert r.status == "success"
    assert r.value == "sess-123"
    assert r.scope == "environment"


def test_extract_scope_in_result():
    """scope 写入结果供调用方使用（EXT-004/005）"""
    resp = {"body": {"x": 1}}
    rule_global = ExtractRule(name="v", type="json", expression="$.x", scope="global")
    rule_env = ExtractRule(name="v2", type="json", expression="$.x", scope="environment")
    r1 = run_extract(rule_global, response=resp)
    r2 = run_extract(rule_env, response=resp)
    assert r1.scope == "global"
    assert r2.scope == "environment"


def test_extract_fail_use_default():
    """提取失败时使用 default（EXT-006）"""
    resp = {"body": {"a": 1}}
    rule = ExtractRule(
        name="missing",
        type="json",
        expression="$.not_exist",
        scope="global",
        default="fallback",
    )
    r = run_extract(rule, response=resp)
    assert r.status == "success"
    assert r.value == "fallback"


def test_extract_fail_no_default():
    """提取失败且无 default 时 status=failed（EXT-007）"""
    resp = {"body": {"a": 1}}
    rule = ExtractRule(name="missing", type="json", expression="$.not_exist", scope="global")
    r = run_extract(rule, response=resp)
    assert r.status == "failed"
    assert r.value is None


def test_extract_returns_extract_result():
    """返回 ExtractResult 结构（EXT-008）"""
    resp = {"body": {"id": 1}}
    rule = ExtractRule(name="id", type="json", expression="$.id", scope="global")
    r = run_extract(rule, response=resp)
    assert r.name == "id"
    assert r.type == "json"
    assert r.expression == "$.id"
    assert r.scope == "global"
    assert r.value == 1
    assert r.status == "success"


def test_source_variable():
    """source_variable 指定数据源（EXT-009）"""
    # 默认用 response
    resp1 = {"body": {"id": 1}}
    rule1 = ExtractRule(name="id", type="json", expression="$.id", scope="global")
    r1 = run_extract(rule1, response=resp1)
    assert r1.value == 1
    # 从 variables 中取数据源
    saved_resp = {"body": {"id": 2}}
    variables = {"last_login_response": saved_resp}
    rule2 = ExtractRule(
        name="id2",
        type="json",
        expression="$.id",
        scope="global",
        source_variable="last_login_response",
    )
    r2 = run_extract(rule2, response=resp1, variables=variables)
    assert r2.value == 2


def test_db_result_type():
    """type=db_result 从 rows JSONPath 提取（EXT-010）"""
    db_rows = [{"id": 1, "email": "a@b.com"}, {"id": 2, "email": "b@b.com"}]
    rule = ExtractRule(name="first_email", type="db_result", expression="$[0].email", scope="global")
    r = run_extract(rule, variables={}, db_rows=db_rows)
    assert r.status == "success"
    assert r.value == "a@b.com"


def test_run_extract_batch():
    """批量提取返回顺序结果列表"""
    resp = {"body": {"a": 1, "b": 2}, "headers": {"X": "h"}}
    rules = [
        ExtractRule(name="va", type="json", expression="$.a", scope="global"),
        ExtractRule(name="vb", type="json", expression="$.b", scope="global"),
    ]
    results = run_extract_batch(rules, response=resp)
    assert len(results) == 2
    assert results[0].value == 1 and results[1].value == 2
