"""变量池管理器单元测试（VAR-010、VAR-011）"""

import pytest

from apirun.utils.variable_pool import VariablePool


def test_get_priority():
    """分层优先级：data_driven > extracted > scenario > environment > global_params"""
    pool = VariablePool()
    pool.set_global_params({"a": "global"})
    pool.set_environment({"a": "env"})
    pool.set_scenario({"a": "scenario"})
    pool._extracted["a"] = "extracted"
    pool._data_driven["a"] = "data_driven"
    assert pool.get("a") == "data_driven"
    pool._data_driven.clear()
    assert pool.get("a") == "extracted"
    pool._extracted.clear()
    assert pool.get("a") == "scenario"
    pool._scenario.clear()
    assert pool.get("a") == "env"
    pool._environment.clear()
    assert pool.get("a") == "global"


def test_set_scope_global():
    """scope=global 写入 extracted 层（VAR-011）"""
    pool = VariablePool()
    pool.set("x", 1, scope="global")
    assert pool._extracted.get("x") == 1
    assert pool.get("x") == 1


def test_set_scope_environment():
    """scope=environment 写入 environment 层（VAR-011）"""
    pool = VariablePool()
    pool.set("y", 2, scope="environment")
    assert pool._environment.get("y") == 2
    assert pool.get("y") == 2


def test_get_missing_raises():
    """不存在的 key 调用 get 抛出 KeyError"""
    pool = VariablePool()
    with pytest.raises(KeyError):
        pool.get("missing")


def test_get_or_none():
    """get_or_none 不存在返回 None"""
    pool = VariablePool()
    assert pool.get_or_none("missing") is None
    pool.set("k", "v", scope="global")
    assert pool.get_or_none("k") == "v"


def test_as_dict_merge():
    """as_dict 合并各层，高优先级覆盖低"""
    pool = VariablePool()
    pool.set_global_params({"a": 1})
    pool.set_scenario({"a": 2, "b": 3})
    pool.set("a", 4, scope="global")
    d = pool.as_dict()
    assert d["a"] == 4
    assert d["b"] == 3
