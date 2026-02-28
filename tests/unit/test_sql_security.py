"""SQL 安全验证测试"""

from apirun.core.models import DbParams
from apirun.executor.db import execute_db_step


def test_sql_injection_blocking_or_union(monkeypatch):
    """SQL 注入防护：阻止 OR 1=1 和 UNION SELECT 攻击"""

    # 模拟数据库连接函数，防止真实连接
    def fake_connect(**kwargs):
        raise RuntimeError("不应该执行到这里 - SQL 应该在验证阶段被拦截")

    monkeypatch.setattr("pymysql.connect", fake_connect)
    monkeypatch.setattr("psycopg2.connect", fake_connect)

    variables = {
        "test_db": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "driver": "mysql",
        }
    }

    # 测试 OR 1=1 注入
    params_or = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users WHERE id = 1 OR 1=1",
    )

    result = execute_db_step(params_or, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]
    # 验证是经典注入模式或条件注入之一
    assert "经典注入模式" in result["error"]["message"] or "条件注入" in result["error"]["message"]

    # 测试 UNION SELECT 注入
    params_union = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin",
    )

    result = execute_db_step(params_union, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]
    assert "UNION 注入" in result["error"]["message"]


def test_sql_injection_blocking_comment(monkeypatch):
    """SQL 注入防护：阻止注释符注入"""

    def fake_connect(**kwargs):
        raise RuntimeError("不应该执行到这里 - SQL 应该在验证阶段被拦截")

    monkeypatch.setattr("pymysql.connect", fake_connect)

    variables = {
        "test_db": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "driver": "mysql",
        }
    }

    # 测试 -- 注释符
    params_dash = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users WHERE id = 1 -- DROP TABLE users",
    )

    result = execute_db_step(params_dash, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]
    assert "SQL 注释符" in result["error"]["message"]

    # 测试 /* */ 注释符
    params_star = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users WHERE id = 1 /* 注释 */",
    )

    result = execute_db_step(params_star, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]
    assert "多行注释" in result["error"]["message"]


def test_sql_injection_blocking_destructive(monkeypatch):
    """SQL 注入防护：阻止破坏性语句"""

    def fake_connect(**kwargs):
        raise RuntimeError("不应该执行到这里 - SQL 应该在验证阶段被拦截")

    monkeypatch.setattr("pymysql.connect", fake_connect)

    variables = {
        "test_db": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "driver": "mysql",
        }
    }

    # 测试 DROP
    params_drop = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users; DROP TABLE users",
    )

    result = execute_db_step(params_drop, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]
    assert "破坏性语句" in result["error"]["message"]

    # 测试 DELETE
    params_delete = DbParams(
        datasource="test_db",
        sql="SELECT * FROM users; DELETE FROM users",
    )

    result = execute_db_step(params_delete, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 安全检查失败" in result["error"]["message"]


def test_sql_length_limit(monkeypatch):
    """SQL 安全：阻止超长 SQL"""

    def fake_connect(**kwargs):
        raise RuntimeError("不应该执行到这里 - SQL 应该在验证阶段被拦截")

    monkeypatch.setattr("pymysql.connect", fake_connect)

    variables = {
        "test_db": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "driver": "mysql",
        }
    }

    # 创建超长 SQL（超过 10000 字符）
    long_sql = "SELECT * FROM users WHERE id IN (" + ",".join(["1"] * 11000) + ")"

    params = DbParams(
        datasource="test_db",
        sql=long_sql,
    )

    result = execute_db_step(params, variables)
    assert result["db_detail"] is None
    assert result["error"] is not None
    assert "SQL 语句过长" in result["error"]["message"]


def test_safe_sql_allowed(monkeypatch):
    """安全 SQL：允许正常的 SELECT 查询"""

    # 这个测试不需要真实连接，只需要验证通过安全检查
    # 由于没有真实数据库，预期会连接失败，但不应该是安全检查失败

    variables = {
        "test_db": {
            "host": "localhost",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "driver": "mysql",
        }
    }

    params = DbParams(
        datasource="test_db",
        sql="SELECT id, name, email FROM users WHERE status = 'active'",
    )

    result = execute_db_step(params, variables)
    # 安全检查应该通过，因此 db_detail 不为 None（虽然会连接失败）
    # 或者 error 不会是 SQL 安全检查失败
    if result["error"]:
        assert "SQL 安全检查失败" not in result["error"]["message"]
        assert result["error"]["code"] in ("DB_CONNECTION_ERROR", "DB_QUERY_ERROR")
