"""场景执行器 - 解析 YAML、按序执行步骤、生成 JSON 输出"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from apirun.core.models import CaseModel, Config, StepDefinition
from apirun.executor.request import execute_request_step


def load_case(yaml_path: str | Path) -> CaseModel:
    """加载并校验 YAML 用例"""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML 文件不存在: {yaml_path}")
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not data:
        raise ValueError("YAML 内容为空")
    try:
        return CaseModel.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"YAML 结构校验失败: {e}") from e


def run_case(case: CaseModel) -> dict[str, Any]:
    """执行用例，返回符合 JSON 输出规范的顶层结构"""
    execution_id = f"exec-{uuid.uuid4().hex[:12]}"
    config: Config = case.config
    base_url = ""
    if config.environment:
        base_url = config.environment.base_url or ""
    variables = dict(config.variables or {})
    if config.environment and config.environment.variables:
        variables.update(config.environment.variables)

    start_time = datetime.now(timezone.utc)
    steps_result: list[dict[str, Any]] = []
    total_assertions = 0
    passed_assertions = 0
    total_requests = 0
    response_times: list[int] = []
    status = "passed"

    for i, step in enumerate(case.teststeps):
        if not step.enabled:
            continue
        step_start = datetime.now(timezone.utc)
        if step.keyword_type == "request" and step.request:
            total_requests += 1
            out = execute_request_step(step.request, base_url, variables)
            response_times.append(out.get("response_time") or 0)
            step_end = datetime.now(timezone.utc)
            step_status = "failed" if out.get("error") else "passed"
            if step_status == "failed":
                status = "failed"
            steps_result.append({
                "step_index": i,
                "name": step.name,
                "keyword_type": "request",
                "keyword_name": step.keyword_name or "http_request",
                "status": step_status,
                "start_time": step_start.isoformat(),
                "end_time": step_end.isoformat(),
                "duration": out.get("response_time", 0),
                "error": out.get("error"),
                "request_detail": {
                    "method": step.request.method,
                    "url": base_url + step.request.url if not step.request.url.startswith("http") else step.request.url,
                    "headers": step.request.headers,
                    "params": step.request.params,
                    "body": step.request.json_body,
                    "body_type": "json" if step.request.json_body else "none",
                    "timeout": step.request.timeout,
                    "allow_redirects": step.request.allow_redirects,
                    "verify_ssl": step.request.verify,
                },
                "response_detail": {
                    "status_code": out.get("status_code"),
                    "headers": out.get("headers", {}),
                    "body": out.get("body"),
                    "body_size": out.get("body_size", 0),
                    "response_time": out.get("response_time", 0),
                    "cookies": out.get("cookies", {}),
                },
                "assertion_results": None,
                "extract_results": None,
                "db_detail": None,
                "custom_detail": None,
            })
        else:
            step_end = datetime.now(timezone.utc)
            steps_result.append({
                "step_index": i,
                "name": step.name,
                "keyword_type": step.keyword_type,
                "keyword_name": step.keyword_name,
                "status": "skipped",
                "start_time": step_start.isoformat(),
                "end_time": step_end.isoformat(),
                "duration": 0,
                "error": None,
                "request_detail": None,
                "response_detail": None,
                "assertion_results": None,
                "extract_results": None,
                "db_detail": None,
                "custom_detail": None,
            })

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    passed_steps = sum(1 for s in steps_result if s["status"] == "passed")
    failed_steps = sum(1 for s in steps_result if s["status"] == "failed")
    avg_rt = int(sum(response_times) / len(response_times)) if response_times else 0
    max_rt = max(response_times) if response_times else 0
    min_rt = min(response_times) if response_times else 0

    summary = {
        "total_steps": len(steps_result),
        "passed_steps": passed_steps,
        "failed_steps": failed_steps,
        "skipped_steps": sum(1 for s in steps_result if s["status"] == "skipped"),
        "error_steps": 0,
        "total_assertions": total_assertions,
        "passed_assertions": passed_assertions,
        "failed_assertions": 0,
        "pass_rate": round((passed_assertions / total_assertions * 100), 1) if total_assertions else 100.0,
        "total_requests": total_requests,
        "total_db_operations": 0,
        "total_extractions": 0,
        "avg_response_time": avg_rt,
        "max_response_time": max_rt,
        "min_response_time": min_rt,
        "total_data_driven_runs": 0,
    }

    environment = None
    if config.environment:
        environment = {
            "name": config.environment.name,
            "base_url": config.environment.base_url,
            "variables": config.environment.variables or {},
        }

    return {
        "execution_id": execution_id,
        "scenario_id": config.scenario_id,
        "scenario_name": config.name,
        "project_id": config.project_id,
        "status": status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration": duration_ms,
        "summary": summary,
        "environment": environment,
        "steps": steps_result,
        "data_driven": None,
        "variables": variables,
        "logs": [],
        "error": None,
    }
