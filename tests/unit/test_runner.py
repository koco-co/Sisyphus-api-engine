"""场景执行器单元测试"""

import json
import tempfile
from pathlib import Path

import pytest

from apirun.core.models import CaseModel, Config, RequestStepParams, StepDefinition
from apirun.core.runner import load_case, run_case


def _minimal_yaml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8")
    f.write(content)
    f.flush()
    return Path(f.name)


@pytest.fixture
def minimal_case_path():
    """最小合法 YAML 用例路径（仅一个 GET 步骤）"""
    yaml_content = """
config:
  name: "获取用户列表"
  project_id: "proj-001"
  scenario_id: "scen-001"
  environment:
    name: "测试环境"
    base_url: "https://httpbin.org"
teststeps:
  - name: "GET 请求"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "GET"
      url: "/get"
"""
    path = _minimal_yaml(yaml_content)
    yield path
    path.unlink(missing_ok=True)


def test_run_case_returns_top_level_keys(minimal_case_path):
    """run_case 返回 ExecutionResult，model_dump 含规范要求的顶层字段"""
    case = load_case(minimal_case_path)
    result = run_case(case)
    data = result.model_dump()
    assert "execution_id" in data
    assert "scenario_id" in data
    assert "scenario_name" in data
    assert "project_id" in data
    assert "status" in data
    assert "start_time" in data
    assert "end_time" in data
    assert "duration" in data
    assert "summary" in data
    assert "environment" in data
    assert "steps" in data
    assert "data_driven" in data
    assert "variables" in data
    assert "logs" in data
    assert "error" in data


def test_run_case_summary_structure(minimal_case_path):
    """summary 包含规范要求字段"""
    case = load_case(minimal_case_path)
    result = run_case(case)
    data = result.model_dump()
    s = data["summary"]
    assert "total_steps" in s
    assert "passed_steps" in s
    assert "failed_steps" in s
    assert "total_requests" in s
    assert "avg_response_time" in s
    assert "pass_rate" in s


def test_run_case_steps_have_required_fields(minimal_case_path):
    """steps 每项包含 step_index, name, keyword_type, status 等"""
    case = load_case(minimal_case_path)
    result = run_case(case)
    data = result.model_dump()
    assert len(data["steps"]) >= 1
    step = data["steps"][0]
    assert "step_index" in step
    assert "name" in step
    assert "keyword_type" in step
    assert "keyword_name" in step
    assert "status" in step
    assert "request_detail" in step
    assert "response_detail" in step


def test_run_case_json_serializable(minimal_case_path):
    """ExecutionResult.model_dump() 可被 json.dumps 序列化"""
    case = load_case(minimal_case_path)
    result = run_case(case)
    data = result.model_dump()
    s = json.dumps(data, ensure_ascii=False)
    assert len(s) > 0
    back = json.loads(s)
    assert back["scenario_name"] == result.scenario_name
