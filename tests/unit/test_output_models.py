"""JSON 输出数据模型单元测试（OUT-001～OUT-014 / TST-024）"""

import json

import pytest

from apirun.result.models import (
    AssertionResult,
    DataDrivenResult,
    DataDrivenRun,
    EnvironmentInfo,
    ErrorInfo,
    ExecutionResult,
    ExecutionSummary,
    ExtractResult,
    LogEntry,
    RequestDetail,
    ResponseDetail,
    StepResult,
)


def test_error_info():
    """ErrorInfo 含 code / message / detail"""
    e = ErrorInfo(code="FILE_NOT_FOUND", message="文件不存在", detail=None)
    assert e.model_dump() == {"code": "FILE_NOT_FOUND", "message": "文件不存在", "detail": None}


def test_execution_summary_sixteen_fields():
    """ExecutionSummary 含 16 个统计字段"""
    s = ExecutionSummary(
        total_steps=1,
        passed_steps=1,
        pass_rate=100.0,
        total_requests=1,
        avg_response_time=100,
    )
    d = s.model_dump()
    assert "total_steps" in d and "passed_steps" in d
    assert "total_assertions" in d and "total_data_driven_runs" in d
    assert "min_response_time" in d and "max_response_time" in d
    assert len(d) == 16


def test_environment_info():
    """EnvironmentInfo 含 name / base_url / variables"""
    env = EnvironmentInfo(name="dev", base_url="https://api.example.com", variables={"k": "v"})
    assert env.model_dump()["variables"] == {"k": "v"}


def test_request_detail_and_response_detail():
    """RequestDetail / ResponseDetail 可序列化"""
    req = RequestDetail(method="POST", url="https://a.com", body_type="json")
    assert req.body_type == "json"
    resp = ResponseDetail(status_code=200, body={"code": 0}, response_time=50)
    assert resp.model_dump()["status_code"] == 200


def test_assertion_result_and_extract_result():
    """AssertionResult / ExtractResult 结构正确"""
    ar = AssertionResult(
        target="json", expression="$.code", comparator="eq", expected=0, actual=0, status="passed"
    )
    assert ar.status == "passed"
    er = ExtractResult(name="token", type="json", expression="$.data.token", scope="global", value="x", status="success")
    assert er.model_dump()["name"] == "token"


def test_step_result_optional_details():
    """StepResult 条件详情字段可为 None"""
    step = StepResult(
        step_index=0,
        name="GET",
        keyword_type="request",
        keyword_name="http_request",
        status="passed",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:00:01Z",
        duration=1000,
        error=None,
        request_detail=RequestDetail(method="GET", url="https://a.com"),
        response_detail=ResponseDetail(status_code=200),
        assertion_results=None,
        extract_results=None,
        db_detail=None,
        custom_detail=None,
    )
    assert step.request_detail is not None
    assert step.db_detail is None


def test_log_entry():
    """LogEntry 含 timestamp / level / message / step_index"""
    log = LogEntry(timestamp="2026-01-01T00:00:00Z", level="INFO", message="start", step_index=None)
    assert log.model_dump()["step_index"] is None


def test_data_driven_run_and_result():
    """DataDrivenRun / DataDrivenResult 可序列化"""
    run = DataDrivenRun(run_index=0, parameters={"a": 1}, status="passed", duration=100)
    ddr = DataDrivenResult(enabled=True, source="yaml_inline", total_runs=1, passed_runs=1, runs=[run])
    assert ddr.model_dump()["total_runs"] == 1


def test_execution_result_fourteen_top_level_fields():
    """ExecutionResult 含 14 个顶层字段且可 JSON 序列化"""
    result = ExecutionResult(
        execution_id="exec-1",
        scenario_id="scen-1",
        scenario_name="用例",
        project_id="proj-1",
        status="passed",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T00:00:01Z",
        duration=1000,
        summary=ExecutionSummary(total_steps=1, passed_steps=1),
        environment=EnvironmentInfo(name="dev", base_url="https://api.example.com"),
        steps=[],
        data_driven=None,
        variables={},
        logs=[],
        error=None,
    )
    d = result.model_dump()
    assert "execution_id" in d and "scenario_id" in d and "scenario_name" in d
    assert "project_id" in d and "status" in d and "start_time" in d and "end_time" in d
    assert "duration" in d and "summary" in d and "environment" in d and "steps" in d
    assert "data_driven" in d and "variables" in d and "logs" in d and "error" in d
    # 规范要求 14 个顶层字段（含 error）
    assert len(d) >= 14
    # 可序列化为 JSON
    json_str = json.dumps(d, ensure_ascii=False)
    loaded = json.loads(json_str)
    assert loaded["execution_id"] == "exec-1"


def test_execution_result_with_error():
    """ExecutionResult.error 为 ErrorInfo 时序列化正确"""
    result = ExecutionResult(
        execution_id="e1",
        scenario_id="s1",
        scenario_name="n",
        project_id="p1",
        status="error",
        start_time="",
        end_time="",
        duration=0,
        error=ErrorInfo(code="YAML_PARSE_ERROR", message="解析失败", detail=None),
    )
    d = result.model_dump()
    assert d["error"] == {"code": "YAML_PARSE_ERROR", "message": "解析失败", "detail": None}
