"""JSON 报告 — 将执行结果输出为 JSON 字符串（RPT-001～RPT-004）"""

from typing import Any

from apirun.result.models import ExecutionResult


def to_json(
    result: ExecutionResult | dict[str, Any] | list[dict[str, Any]],
    ensure_ascii: bool = False,
    indent: int | None = 2,
) -> str:
    """
    将执行结果序列化为 JSON 字符串（RPT-001、RPT-002）。
    - ensure_ascii=False 支持中文
    - 支持单结果、dict 或批量 list[dict]
    """
    import json

    if isinstance(result, ExecutionResult):
        data = result.model_dump()
    else:
        data = result
    return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)


def to_json_engine_error(
    execution_id: str,
    scenario_id: str,
    scenario_name: str,
    project_id: str,
    code: str,
    message: str,
    detail: str | None = None,
) -> str:
    """
    引擎级异常时的 JSON 输出（RPT-004）：status=error + error 对象。
    """
    import json

    data = {
        "execution_id": execution_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "project_id": project_id,
        "status": "error",
        "start_time": None,
        "end_time": None,
        "duration": 0,
        "summary": None,
        "environment": None,
        "steps": [],
        "data_driven": None,
        "variables": {},
        "logs": [],
        "error": {"code": code, "message": message, "detail": detail},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
