"""YAML 配置模型与解析单元测试"""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from apirun.core.models import (
    AssertionParams,
    CaseModel,
    Config,
    CustomParams,
    DbParams,
    Ddts,
    ExtractRule,
    RequestStepParams,
    StepDefinition,
    ValidateRule,
)
from apirun.errors import (
    FILE_NOT_FOUND,
    YAML_PARSE_ERROR,
    YAML_VALIDATION_ERROR,
    EngineError,
)


def test_request_step_params_default():
    """RequestStepParams 默认值"""
    p = RequestStepParams(url="/api/v1/users")
    assert p.method == "GET"
    assert p.timeout == 30
    assert p.allow_redirects is True


def test_config_minimal():
    """Config 最少必填字段"""
    c = Config(name="场景1", project_id="p1", scenario_id="s1")
    assert c.name == "场景1"
    assert c.priority == "P2"
    assert c.environment is None


def test_case_model_parse_minimal():
    """CaseModel 解析最小 YAML 结构"""
    data = {
        "config": {
            "name": "获取用户列表",
            "project_id": "proj-001",
            "scenario_id": "scen-001",
        },
        "teststeps": [
            {
                "name": "获取用户列表",
                "keyword_type": "request",
                "keyword_name": "http_request",
                "request": {"method": "GET", "url": "/api/v1/users"},
            },
        ],
    }
    case = CaseModel.model_validate(data)
    assert case.config.name == "获取用户列表"
    assert len(case.teststeps) == 1
    assert case.teststeps[0].keyword_type == "request"
    assert case.teststeps[0].request is not None
    assert case.teststeps[0].request.method == "GET"
    assert case.ddts is None


def test_step_definition_supports_all_keyword_types():
    """StepDefinition 支持五种 keyword_type 及其参数结构."""
    step_request = StepDefinition(
        name="请求",
        keyword_type="request",
        keyword_name="http_request",
        request=RequestStepParams(method="GET", url="/users"),
        extract=[ExtractRule(name="user_id", type="json", expression="$.data.id")],
        validate=[
            ValidateRule(
                target="status_code",
                comparator="eq",
                expected=200,
            )
        ],
    )
    assert step_request.request is not None
    assert step_request.extract is not None
    assert step_request.validate is not None

    step_assertion = StepDefinition(
        name="断言",
        keyword_type="assertion",
        keyword_name="json_assertion",
        assertion=AssertionParams(
            target="json",
            comparator="eq",
            expected=0,
            expression="$.code",
        ),
    )
    assert step_assertion.assertion is not None

    step_db = StepDefinition(
        name="数据库校验",
        keyword_type="db",
        keyword_name="db_operation",
        db=DbParams(
            datasource="db_main",
            sql="SELECT 1",
        ),
    )
    assert step_db.db is not None

    step_custom = StepDefinition(
        name="自定义关键字",
        keyword_type="custom",
        keyword_name="generate_business_code",
        custom=CustomParams(parameters={"prefix": "BIZ"}),
    )
    assert step_custom.custom is not None


def test_case_model_parse_full_types_from_dict():
    """CaseModel 解析包含 request/assertion/extract/db/custom 的结构."""
    data = {
        "config": {
            "name": "复合场景",
            "project_id": "proj-001",
            "scenario_id": "scen-001",
        },
        "teststeps": [
            {
                "name": "获取用户列表",
                "keyword_type": "request",
                "keyword_name": "http_request",
                "request": {"method": "GET", "url": "/api/v1/users"},
                "validate": [
                    {
                        "target": "status_code",
                        "comparator": "eq",
                        "expected": 200,
                    }
                ],
            },
            {
                "name": "独立断言",
                "keyword_type": "assertion",
                "keyword_name": "json_assertion",
                "assertion": {
                    "target": "json",
                    "expression": "$.code",
                    "comparator": "eq",
                    "expected": 0,
                },
            },
            {
                "name": "数据库验证",
                "keyword_type": "db",
                "keyword_name": "db_operation",
                "db": {
                    "datasource": "db_main",
                    "sql": "SELECT 1",
                },
            },
            {
                "name": "自定义关键字",
                "keyword_type": "custom",
                "keyword_name": "generate_business_code",
                "custom": {
                    "parameters": {"prefix": "BIZ"},
                },
            },
        ],
        "ddts": {
            "name": "数据集",
            "parameters": [
                {"user_email": "a@example.com"},
                {"user_email": "b@example.com"},
            ],
        },
    }
    case = CaseModel.model_validate(data)
    assert isinstance(case.config, Config)
    assert len(case.teststeps) == 4
    assert isinstance(case.ddts, Ddts)


def test_load_case_file_not_found():
    """load_case 文件不存在应抛 EngineError(FILE_NOT_FOUND)"""
    from apirun.core.runner import load_case

    with pytest.raises(EngineError) as exc_info:
        load_case("/nonexistent/path.yaml")
    assert exc_info.value.code == FILE_NOT_FOUND


def test_load_case_invalid_yaml():
    """load_case 无效 YAML 应抛 EngineError(YAML_PARSE_ERROR / YAML_VALIDATION_ERROR)"""
    from apirun.core.runner import load_case

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        f.write(b"invalid: [[[ yaml")
        f.flush()
        path = f.name
    try:
        with pytest.raises(EngineError) as exc_info:
            load_case(path)
        assert exc_info.value.code in {YAML_PARSE_ERROR, YAML_VALIDATION_ERROR}
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_case_missing_config():
    """load_case 缺少 config 应校验失败，抛 EngineError(YAML_VALIDATION_ERROR)"""
    from apirun.core.runner import load_case

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        f.write(b"teststeps: []\n")
        f.flush()
        path = f.name
    try:
        with pytest.raises(EngineError) as exc_info:
            load_case(path)
        assert exc_info.value.code == YAML_VALIDATION_ERROR
    finally:
        Path(path).unlink(missing_ok=True)


def test_request_step_params_json_data_files_mutually_exclusive():
    """MDL-015: json / data / files 三者互斥，最多填一个。"""
    RequestStepParams(method="GET", url="/api", json_body={"a": 1})
    RequestStepParams(method="POST", url="/api", data={"b": "2"})
    RequestStepParams(method="POST", url="/api", files={"f": "path"})
    with pytest.raises(ValidationError, match="互斥"):
        RequestStepParams(method="POST", url="/api", json_body={"a": 1}, data={"b": "2"})
    with pytest.raises(ValidationError, match="互斥"):
        RequestStepParams(method="POST", url="/api", json_body={"a": 1}, files={"f": "x"})


def test_case_model_csv_datasource_and_ddts_exclusive():
    """MDL-016: config.csv_datasource 与 ddts 不能同时配置。"""
    CaseModel.model_validate(
        {
            "config": {
                "name": "n",
                "project_id": "p",
                "scenario_id": "s",
                "csv_datasource": "data.csv",
            },
            "teststeps": [
                {
                    "name": "s",
                    "keyword_type": "request",
                    "keyword_name": "r",
                    "request": {"url": "/"},
                }
            ],
        }
    )
    CaseModel.model_validate(
        {
            "config": {"name": "n", "project_id": "p", "scenario_id": "s"},
            "teststeps": [
                {
                    "name": "s",
                    "keyword_type": "request",
                    "keyword_name": "r",
                    "request": {"url": "/"},
                }
            ],
            "ddts": {"name": "d", "parameters": [{"x": 1}]},
        }
    )
    with pytest.raises(ValidationError, match="互斥"):
        CaseModel.model_validate(
            {
                "config": {
                    "name": "n",
                    "project_id": "p",
                    "scenario_id": "s",
                    "csv_datasource": "data.csv",
                },
                "teststeps": [
                    {
                        "name": "s",
                        "keyword_type": "request",
                        "keyword_name": "r",
                        "request": {"url": "/"},
                    }
                ],
                "ddts": {"name": "d", "parameters": [{"x": 1}]},
            }
        )
