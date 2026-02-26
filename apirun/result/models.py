"""JSON 输出数据模型 — 符合 Sisyphus-api-engine JSON 输出规范（OUT-001～OUT-014）"""

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# OUT-001 错误信息
# ---------------------------------------------------------------------------
class ErrorInfo(BaseModel):
    """错误信息：code / message / detail"""

    code: str
    message: str
    detail: str | None = None


# ---------------------------------------------------------------------------
# OUT-002 执行摘要（16 字段）
# ---------------------------------------------------------------------------
class ExecutionSummary(BaseModel):
    """执行摘要统计"""

    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    error_steps: int = 0
    total_assertions: int = 0
    passed_assertions: int = 0
    failed_assertions: int = 0
    pass_rate: float = 100.0
    total_requests: int = 0
    total_db_operations: int = 0
    total_extractions: int = 0
    avg_response_time: int = 0
    max_response_time: int = 0
    min_response_time: int = 0
    total_data_driven_runs: int = 0


# ---------------------------------------------------------------------------
# OUT-003 环境快照
# ---------------------------------------------------------------------------
class EnvironmentInfo(BaseModel):
    """环境信息快照"""

    name: str = ""
    base_url: str = ""
    variables: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# OUT-004 请求详情
# ---------------------------------------------------------------------------
class RequestDetail(BaseModel):
    """HTTP 请求详情"""

    method: str = "GET"
    url: str = ""
    headers: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] | None = None
    body: Any = None
    body_type: str = "none"  # json / form / multipart / raw / none
    timeout: int = 30
    allow_redirects: bool = True
    verify_ssl: bool = True


# ---------------------------------------------------------------------------
# OUT-005 响应详情
# ---------------------------------------------------------------------------
class ResponseDetail(BaseModel):
    """HTTP 响应详情"""

    status_code: int = 0
    headers: dict[str, Any] = Field(default_factory=dict)
    body: Any = None
    body_size: int = 0
    response_time: int = 0
    cookies: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# OUT-006 断言结果
# ---------------------------------------------------------------------------
class AssertionResult(BaseModel):
    """单条断言结果"""

    target: str
    expression: str | None = None
    comparator: str
    expected: Any = None
    actual: Any = None
    status: str  # passed / failed
    message: str | None = None


# ---------------------------------------------------------------------------
# OUT-007 提取结果
# ---------------------------------------------------------------------------
class ExtractResult(BaseModel):
    """单条变量提取结果"""

    name: str
    type: str  # json / header / cookie / db_result
    expression: str
    scope: str = "global"  # global / environment
    value: Any = None
    status: str  # success / failed


# ---------------------------------------------------------------------------
# OUT-008 数据库操作详情
# ---------------------------------------------------------------------------
class DbDetail(BaseModel):
    """数据库操作详情"""

    datasource: str = ""
    sql: str = ""
    sql_rendered: str = ""
    row_count: int = 0
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    execution_time: int = 0


# ---------------------------------------------------------------------------
# OUT-009 自定义关键字详情
# ---------------------------------------------------------------------------
class CustomDetail(BaseModel):
    """自定义关键字执行详情"""

    keyword_name: str = ""
    parameters_input: dict[str, Any] = Field(default_factory=dict)
    return_value: Any = None
    execution_time: int = 0


# ---------------------------------------------------------------------------
# OUT-010 步骤结果（通用 12 字段 + 条件详情）
# ---------------------------------------------------------------------------
class StepResult(BaseModel):
    """单步执行结果"""

    step_index: int = 0
    name: str = ""
    keyword_type: str = ""
    keyword_name: str = ""
    status: str = "passed"  # passed / failed / error / skipped
    start_time: str = ""
    end_time: str = ""
    duration: int = 0
    error: ErrorInfo | None = None
    request_detail: RequestDetail | None = None
    response_detail: ResponseDetail | None = None
    assertion_results: list[AssertionResult] | None = None
    extract_results: list[ExtractResult] | None = None
    db_detail: DbDetail | None = None
    custom_detail: CustomDetail | None = None


# ---------------------------------------------------------------------------
# OUT-011 日志条目
# ---------------------------------------------------------------------------
class LogEntry(BaseModel):
    """单条执行日志"""

    timestamp: str = ""
    level: str = "INFO"  # DEBUG / INFO / WARNING / ERROR
    message: str = ""
    step_index: int | None = None


# ---------------------------------------------------------------------------
# OUT-012 数据驱动单轮结果
# ---------------------------------------------------------------------------
class DataDrivenRun(BaseModel):
    """数据驱动单轮执行结果"""

    run_index: int = 0
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: str = "passed"
    duration: int = 0
    summary: ExecutionSummary = Field(default_factory=ExecutionSummary)
    steps: list[StepResult] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OUT-013 数据驱动汇总结果
# ---------------------------------------------------------------------------
class DataDrivenResult(BaseModel):
    """数据驱动测试汇总"""

    enabled: bool = False
    source: str = "yaml_inline"  # yaml_inline / csv_file
    dataset_name: str = ""
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    pass_rate: float = 0.0
    runs: list[DataDrivenRun] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OUT-014 顶层执行结果（14 字段，可 model_dump 序列化）
# ---------------------------------------------------------------------------
class ExecutionResult(BaseModel):
    """顶层执行结果，符合 JSON 输出规范"""

    execution_id: str = ""
    scenario_id: str = ""
    scenario_name: str = ""
    project_id: str = ""
    status: str = "passed"  # passed / failed / error / skipped
    start_time: str = ""
    end_time: str = ""
    duration: int = 0
    summary: ExecutionSummary = Field(default_factory=ExecutionSummary)
    environment: EnvironmentInfo | None = None
    steps: list[StepResult] = Field(default_factory=list)
    data_driven: DataDrivenResult | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    logs: list[LogEntry] = Field(default_factory=list)
    error: ErrorInfo | None = None
