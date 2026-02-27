"""EngineError 与错误码常量单元测试（ERR-001~003）"""

import pytest

from apirun import errors as err_module
from apirun.errors import FILE_NOT_FOUND, YAML_PARSE_ERROR, EngineError


def test_engine_error_attributes():
    """EngineError 具备 code / message / detail 属性"""
    e = EngineError("CODE", "msg", detail="detail")
    assert e.code == "CODE"
    assert e.message == "msg"
    assert e.detail == "detail"
    assert str(e) == "msg"


def test_engine_error_detail_optional():
    """detail 可为 None"""
    e = EngineError("CODE", "msg")
    assert e.detail is None


def test_engine_error_to_dict():
    """to_dict() 返回符合 JSON 规范的 error 对象"""
    e = EngineError("FILE_NOT_FOUND", "文件不存在", detail=None)
    d = e.to_dict()
    assert d == {"code": "FILE_NOT_FOUND", "message": "文件不存在", "detail": None}
    e2 = EngineError("X", "m", detail="stack")
    assert e2.to_dict()["detail"] == "stack"


def test_engine_level_error_codes_defined():
    """引擎级错误码常量已定义"""
    assert getattr(err_module, "FILE_NOT_FOUND") == "FILE_NOT_FOUND"
    assert getattr(err_module, "YAML_PARSE_ERROR") == "YAML_PARSE_ERROR"
    assert getattr(err_module, "YAML_VALIDATION_ERROR") == "YAML_VALIDATION_ERROR"
    assert getattr(err_module, "CSV_FILE_NOT_FOUND") == "CSV_FILE_NOT_FOUND"
    assert getattr(err_module, "CSV_PARSE_ERROR") == "CSV_PARSE_ERROR"
    assert getattr(err_module, "ENGINE_INTERNAL_ERROR") == "ENGINE_INTERNAL_ERROR"
    assert getattr(err_module, "TIMEOUT_ERROR") == "TIMEOUT_ERROR"


def test_step_level_error_codes_defined():
    """步骤级错误码常量已定义"""
    assert getattr(err_module, "REQUEST_TIMEOUT") == "REQUEST_TIMEOUT"
    assert getattr(err_module, "REQUEST_SSL_ERROR") == "REQUEST_SSL_ERROR"
    assert getattr(err_module, "REQUEST_CONNECTION_ERROR") == "REQUEST_CONNECTION_ERROR"
    assert getattr(err_module, "ASSERTION_FAILED") == "ASSERTION_FAILED"
    assert getattr(err_module, "EXTRACT_FAILED") == "EXTRACT_FAILED"
    assert getattr(err_module, "DB_CONNECTION_ERROR") == "DB_CONNECTION_ERROR"
    assert getattr(err_module, "DB_QUERY_ERROR") == "DB_QUERY_ERROR"
    assert getattr(err_module, "DB_DATASOURCE_NOT_FOUND") == "DB_DATASOURCE_NOT_FOUND"
    assert getattr(err_module, "KEYWORD_NOT_FOUND") == "KEYWORD_NOT_FOUND"
    assert getattr(err_module, "KEYWORD_EXECUTION_ERROR") == "KEYWORD_EXECUTION_ERROR"
    assert getattr(err_module, "VARIABLE_NOT_FOUND") == "VARIABLE_NOT_FOUND"
    assert getattr(err_module, "VARIABLE_RENDER_ERROR") == "VARIABLE_RENDER_ERROR"


def test_engine_error_is_catchable():
    """EngineError 可作为 Exception 被捕获"""
    with pytest.raises(EngineError) as exc_info:
        raise EngineError(FILE_NOT_FOUND, "not found")
    assert exc_info.value.code == FILE_NOT_FOUND
    with pytest.raises(Exception):
        raise EngineError(YAML_PARSE_ERROR, "parse error")
