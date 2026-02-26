"""数据库执行器单元测试（DB-001～DB-011 / TST-028）"""

from unittest.mock import MagicMock, patch

import pytest

from apirun.core.models import DbParams
from apirun.errors import DB_DATASOURCE_NOT_FOUND, EngineError
from apirun.executor.db import execute_db_step, execute_db_step_safe


def test_datasource_not_found():
    """数据源未找到时返回 DB_DATASOURCE_NOT_FOUND（DB-009）"""
    params = DbParams(datasource="nonexistent", sql="SELECT 1")
    out = execute_db_step_safe(params, variables={})
    assert out["error"] is not None
    assert out["error"]["code"] == DB_DATASOURCE_NOT_FOUND
    assert out["rows"] == []
    assert out["db_detail"] is None


def test_datasource_from_variables():
    """datasource 从变量池解析（DB-001）"""
    params = DbParams(datasource="db_main", sql="SELECT 1 AS x")
    variables = {
        "db_main": {
            "host": "localhost",
            "port": 3306,
            "user": "u",
            "password": "p",
            "database": "d",
            "driver": "mysql",
        },
    }
    with patch("apirun.executor.db._execute_mysql") as m:
        m.return_value = (["x"], [{"x": 1}])
        out = execute_db_step(params, variables=variables)
    assert out["error"] is None
    assert out["db_detail"]["row_count"] == 1
    assert out["db_detail"]["columns"] == ["x"]
    assert out["rows"] == [{"x": 1}]
    assert out["db_detail"]["sql_rendered"] == "SELECT 1 AS x"


def test_sql_variable_replacement():
    """SQL 中 {{变量}} 替换（DB-004）"""
    params = DbParams(datasource="db_main", sql="SELECT {{id}} AS id")
    variables = {
        "db_main": {"host": "localhost", "port": 3306, "user": "u", "password": "p", "database": "d", "driver": "mysql"},
        "id": 42,
    }
    with patch("apirun.executor.db._execute_mysql") as m:
        m.return_value = (["id"], [{"id": 42}])
        out = execute_db_step(params, variables=variables)
    assert out["error"] is None
    assert "42" in out["db_detail"]["sql_rendered"]


def test_db_detail_structure():
    """返回 db_detail 结构（DB-006）"""
    params = DbParams(datasource="db_main", sql="SELECT 1")
    variables = {
        "db_main": {"host": "h", "port": 3306, "user": "u", "password": "p", "database": "d", "driver": "mysql"},
    }
    with patch("apirun.executor.db._execute_mysql") as m:
        m.return_value = (["a", "b"], [{"a": 1, "b": 2}])
        out = execute_db_step(params, variables=variables)
    d = out["db_detail"]
    assert d["datasource"] == "db_main"
    assert d["sql"] == "SELECT 1"
    assert d["sql_rendered"] == "SELECT 1"
    assert d["row_count"] == 1
    assert d["columns"] == ["a", "b"]
    assert d["rows"] == [{"a": 1, "b": 2}]
    assert "execution_time" in d


def test_execute_db_step_safe_catches_engine_error():
    """execute_db_step_safe 捕获 EngineError 返回 error 字典"""
    params = DbParams(datasource="missing", sql="SELECT 1")
    out = execute_db_step_safe(params, variables={})
    assert "error" in out
    assert out["error"]["code"] == DB_DATASOURCE_NOT_FOUND
