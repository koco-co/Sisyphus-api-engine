"""数据库执行器 — 执行 SQL 并返回 db_detail，支持 MySQL/PostgreSQL（DB-001～DB-011）"""

import time
from typing import Any

from apirun.core.models import DbParams
from apirun.errors import (
    DB_CONNECTION_ERROR,
    DB_DATASOURCE_NOT_FOUND,
    DB_QUERY_ERROR,
    EngineError,
)
from apirun.result.models import DbDetail
from apirun.security import sql_validator
from apirun.utils.variables import render_template


def _resolve_datasource(
    datasource_name: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """
    从变量池解析数据源配置（DB-001）。
    期望 variables[datasource_name] 为 dict，含 host/port/user/password/database/driver。
    """
    cfg = variables.get(datasource_name)
    if cfg is None or not isinstance(cfg, dict):
        raise EngineError(
            DB_DATASOURCE_NOT_FOUND,
            f"数据源未找到: {datasource_name}",
        )
    return cfg


def _execute_mysql(
    conn_config: dict[str, Any], sql_rendered: str
) -> tuple[list[str], list[dict[str, Any]]]:
    """MySQL 查询，返回 (columns, rows)。"""
    import pymysql

    conn = pymysql.connect(
        host=conn_config.get("host", "localhost"),
        port=int(conn_config.get("port", 3306)),
        user=conn_config.get("user", ""),
        password=conn_config.get("password", ""),
        database=conn_config.get("database", ""),
        charset=conn_config.get("charset", "utf8mb4"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql_rendered)
            rows = cur.fetchall()
            columns = list(rows[0].keys()) if rows else []
            # 确保每行是 dict，且值为可 JSON 序列化
            out = [dict(r) for r in rows]
            return columns, out
    finally:
        conn.close()


def _execute_postgres(
    conn_config: dict[str, Any], sql_rendered: str
) -> tuple[list[str], list[dict[str, Any]]]:
    """PostgreSQL 查询，返回 (columns, rows)。"""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(
        host=conn_config.get("host", "localhost"),
        port=int(conn_config.get("port", 5432)),
        user=conn_config.get("user", ""),
        password=conn_config.get("password", ""),
        dbname=conn_config.get("database", ""),
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql_rendered)
            rows = cur.fetchall()
            columns = list(rows[0].keys()) if rows else []
            out = [dict(r) for r in rows]
            return columns, out
    finally:
        conn.close()


def execute_db_step(
    params: DbParams,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    执行数据库步骤（DB-002～DB-006）。
    返回: db_detail (dict), rows (list), error (dict|None)
    """
    variables = variables or {}
    try:
        conn_config = _resolve_datasource(params.datasource, variables)
    except EngineError as e:
        return {
            "db_detail": None,
            "rows": [],
            "error": e.to_dict(),
        }

    sql_rendered = render_template(params.sql, variables)
    if not isinstance(sql_rendered, str):
        sql_rendered = str(sql_rendered)

    # SQL 安全验证（防止注入攻击）
    try:
        sql_validator.validate(sql_rendered)
    except EngineError as e:
        return {
            "db_detail": None,
            "rows": [],
            "error": e.to_dict(),
        }

    driver = (conn_config.get("driver") or "mysql").lower()
    start = time.perf_counter()
    empty_detail = {
        "datasource": params.datasource,
        "sql": params.sql,
        "sql_rendered": sql_rendered,
        "row_count": 0,
        "columns": [],
        "rows": [],
        "execution_time": 0,
    }
    try:
        if driver in ("mysql", "pymysql"):
            columns, rows = _execute_mysql(conn_config, sql_rendered)
        elif driver in ("postgres", "postgresql", "psycopg2"):
            columns, rows = _execute_postgres(conn_config, sql_rendered)
        else:
            raise EngineError(
                DB_CONNECTION_ERROR,
                f"不支持的数据库驱动: {driver}",
            )
    except EngineError:
        raise
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        empty_detail["execution_time"] = elapsed_ms
        # 连接阶段异常多为 DB_CONNECTION_ERROR，执行阶段为 DB_QUERY_ERROR
        code = DB_QUERY_ERROR
        if (
            "connect" in str(e).lower()
            or "connection" in str(e).lower()
            or "refused" in str(e).lower()
        ):
            code = DB_CONNECTION_ERROR
        return {
            "db_detail": empty_detail,
            "rows": [],
            "error": {"code": code, "message": str(e), "detail": None},
        }

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    db_detail = DbDetail(
        datasource=params.datasource,
        sql=params.sql,
        sql_rendered=sql_rendered,
        row_count=len(rows),
        columns=columns,
        rows=rows,
        execution_time=elapsed_ms,
    ).model_dump()
    return {"db_detail": db_detail, "rows": rows, "error": None}


def execute_db_step_safe(
    params: DbParams,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """执行数据库步骤，捕获连接异常返回 error 而非抛错。"""
    try:
        return execute_db_step(params, variables)
    except EngineError as e:
        return {
            "db_detail": None,
            "rows": [],
            "error": e.to_dict(),
        }
