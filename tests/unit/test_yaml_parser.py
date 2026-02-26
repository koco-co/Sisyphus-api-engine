"""YAML 解析器单元测试（PAR-001～PAR-005 / TST-033）"""

import tempfile
from pathlib import Path

import pytest

from apirun.core.models import CaseModel
from apirun.errors import (
    FILE_NOT_FOUND,
    YAML_PARSE_ERROR,
    YAML_VALIDATION_ERROR,
    EngineError,
)
from apirun.parser.yaml_parser import parse_yaml


def test_parse_yaml_returns_case_model():
    """parse_yaml 返回 CaseModel 实例（PAR-001, PAR-005）"""
    yaml_content = """
config:
  name: "用例"
  project_id: "p1"
  scenario_id: "s1"
  environment:
    name: "dev"
    base_url: "https://api.example.com"
teststeps:
  - name: "GET"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "GET"
      url: "/get"
"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        f.write(yaml_content)
        path = Path(f.name)
    try:
        case = parse_yaml(path)
        assert isinstance(case, CaseModel)
        assert case.config.name == "用例"
        assert len(case.teststeps) == 1
        assert case.teststeps[0].keyword_type == "request"
    finally:
        path.unlink(missing_ok=True)


def test_parse_yaml_file_not_found():
    """文件不存在时抛出 EngineError(FILE_NOT_FOUND)（PAR-002）"""
    with pytest.raises(EngineError) as exc_info:
        parse_yaml("/nonexistent/path/case.yaml")
    assert exc_info.value.code == FILE_NOT_FOUND
    assert "不存在" in exc_info.value.message


def test_parse_yaml_syntax_error():
    """YAML 语法错误时抛出 EngineError(YAML_PARSE_ERROR)（PAR-003）"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        f.write("config:\n  name: [\n  invalid")
        path = Path(f.name)
    try:
        with pytest.raises(EngineError) as exc_info:
            parse_yaml(path)
        assert exc_info.value.code == YAML_PARSE_ERROR
    finally:
        path.unlink(missing_ok=True)


def test_parse_yaml_validation_error():
    """缺少必填字段等 Pydantic 校验失败时抛出 EngineError(YAML_VALIDATION_ERROR)（PAR-004）"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        f.write("config: {}\nteststeps: []")
        path = Path(f.name)
    try:
        with pytest.raises(EngineError) as exc_info:
            parse_yaml(path)
        assert exc_info.value.code == YAML_VALIDATION_ERROR
        assert "校验" in exc_info.value.message
    finally:
        path.unlink(missing_ok=True)


def test_parse_yaml_empty_file():
    """空 YAML 解析为空 dict 后校验失败"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8") as f:
        f.write("")
        path = Path(f.name)
    try:
        with pytest.raises(EngineError) as exc_info:
            parse_yaml(path)
        assert exc_info.value.code == YAML_VALIDATION_ERROR
    finally:
        path.unlink(missing_ok=True)
