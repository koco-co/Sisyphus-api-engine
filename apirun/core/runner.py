"""场景执行器 - 解析 YAML、按序执行步骤、生成 JSON 输出"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from apirun.core.models import CaseModel, Config, StepDefinition
from apirun.executor.request import execute_request_step
from apirun.extractor.extractor import run_extract_batch
from apirun.result.models import ExecutionResult
from apirun.utils.variable_pool import VariablePool
from apirun.validation.validator import run_assertion


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


def _step_result_base(
    step: StepDefinition,
    step_index: int,
    step_start: datetime,
    step_end: datetime,
    duration_ms: int,
    status: str,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建步骤结果公共字段。"""
    return {
        "step_index": step_index,
        "name": step.name,
        "keyword_type": step.keyword_type,
        "keyword_name": step.keyword_name or "",
        "status": status,
        "start_time": step_start.isoformat(),
        "end_time": step_end.isoformat(),
        "duration": duration_ms,
        "error": error,
        "request_detail": None,
        "response_detail": None,
        "assertion_results": None,
        "extract_results": None,
        "db_detail": None,
        "custom_detail": None,
    }


def run_case(case: CaseModel) -> ExecutionResult:
    """执行用例，返回 ExecutionResult 模型（RUN-008～RUN-028）。"""
    execution_id = f"exec-{uuid.uuid4().hex[:12]}"
    config: Config = case.config
    base_url = ""
    if config.environment:
        base_url = config.environment.base_url or ""

    pool = VariablePool()
    pool.set_scenario(config.variables or {})
    if config.environment and config.environment.variables:
        pool.set_environment(config.environment.variables)
    variables = pool.as_dict()

    start_time = datetime.now(timezone.utc)
    steps_result: list[dict[str, Any]] = []
    total_assertions = 0
    passed_assertions = 0
    failed_assertions = 0
    total_requests = 0
    total_extractions = 0
    response_times: list[int] = []
    last_response: dict[str, Any] | None = None
    scenario_status = "passed"

    for i, step in enumerate(case.teststeps):
        step_start = datetime.now(timezone.utc)
        step_status = "passed"
        step_error: dict[str, Any] | None = None
        assertion_results: list[dict[str, Any]] | None = None
        extract_results: list[dict[str, Any]] | None = None
        request_detail: dict[str, Any] | None = None
        response_detail: dict[str, Any] | None = None

        try:
            if not step.enabled:
                # RUN-008: enabled=false 时生成 skipped StepResult
                step_end = datetime.now(timezone.utc)
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )
                continue

            if step.keyword_type == "request" and step.request:
                # request 步骤
                total_requests += 1
                variables = pool.as_dict()
                out = execute_request_step(step.request, base_url, variables)
                rt = out.get("response_time") or 0
                response_times.append(rt)
                last_response = out

                if out.get("error"):
                    step_status = "failed"
                else:
                    # RUN-013: 内联 extract
                    if step.extract:
                        ex_results = run_extract_batch(
                            step.extract, out, variables, db_rows=None
                        )
                        extract_results = [r.model_dump() for r in ex_results]
                        total_extractions += len(ex_results)
                        for er in ex_results:
                            if er.status == "success" and er.value is not None:
                                pool.set(er.name, er.value, scope=er.scope)
                    # RUN-014: 内联 validate
                    if step.validate:
                        variables = pool.as_dict()
                        ar_list = []
                        for vr in step.validate:
                            ar = run_assertion(
                                target=vr.target,
                                comparator=vr.comparator,
                                expected=vr.expected,
                                expression=vr.expression,
                                message=vr.message,
                                response=out,
                                variables=variables,
                            )
                            ar_list.append(ar.model_dump())
                            total_assertions += 1
                            if ar.status == "passed":
                                passed_assertions += 1
                            else:
                                failed_assertions += 1
                                step_status = "failed"
                        assertion_results = ar_list

                request_detail = {
                    "method": step.request.method or "GET",
                    "url": (
                        (base_url.rstrip("/") + "/" + step.request.url.lstrip("/"))
                        if base_url and not step.request.url.startswith(("http://", "https://"))
                        else step.request.url
                    ),
                    "headers": step.request.headers or {},
                    "params": step.request.params,
                    "body": step.request.json_body,
                    "body_type": "json" if step.request.json_body else "none",
                    "timeout": step.request.timeout or 30,
                    "allow_redirects": step.request.allow_redirects,
                    "verify_ssl": step.request.verify,
                }
                response_detail = {
                    "status_code": out.get("status_code"),
                    "headers": out.get("headers", {}),
                    "body": out.get("body"),
                    "body_size": out.get("body_size", 0),
                    "response_time": out.get("response_time", 0),
                    "cookies": out.get("cookies", {}),
                }
                step_end = datetime.now(timezone.utc)
                steps_result.append({
                    **_step_result_base(
                        step, i, step_start, step_end, rt, step_status, out.get("error")
                    ),
                    "request_detail": request_detail,
                    "response_detail": response_detail,
                    "assertion_results": assertion_results,
                    "extract_results": extract_results,
                })

            elif step.keyword_type == "assertion" and step.assertion:
                # RUN-009: 独立断言步骤
                ap = step.assertion
                variables = pool.as_dict()
                resp = last_response
                if ap.source_variable and ap.source_variable.strip():
                    val = pool.get_or_none(ap.source_variable)
                    if isinstance(val, dict):
                        resp = val
                ar = run_assertion(
                    target=ap.target,
                    comparator=ap.comparator,
                    expected=ap.expected,
                    expression=ap.expression,
                    message=ap.message,
                    response=resp,
                    variables=variables,
                )
                total_assertions += 1
                if ar.status == "passed":
                    passed_assertions += 1
                else:
                    failed_assertions += 1
                    step_status = "failed"
                assertion_results = [ar.model_dump()]
                step_end = datetime.now(timezone.utc)
                steps_result.append({
                    **_step_result_base(step, i, step_start, step_end, 0, step_status, None),
                    "assertion_results": assertion_results,
                })

            elif step.keyword_type == "extract" and step.extract:
                # RUN-010: 独立提取步骤
                variables = pool.as_dict()
                ex_results = run_extract_batch(
                    step.extract, last_response, variables, db_rows=None
                )
                extract_results = [r.model_dump() for r in ex_results]
                total_extractions += len(ex_results)
                any_failed = any(r.status == "failed" for r in ex_results)
                if any_failed:
                    step_status = "failed"
                for er in ex_results:
                    if er.status == "success" and er.value is not None:
                        pool.set(er.name, er.value, scope=er.scope)
                step_end = datetime.now(timezone.utc)
                steps_result.append({
                    **_step_result_base(step, i, step_start, step_end, 0, step_status, None),
                    "extract_results": extract_results,
                })

            elif step.keyword_type == "db":
                # RUN-011: db 步骤暂未实现，记为 skipped
                step_end = datetime.now(timezone.utc)
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )

            elif step.keyword_type == "custom":
                # RUN-012: custom 步骤暂未实现，记为 skipped
                step_end = datetime.now(timezone.utc)
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )

            else:
                step_end = datetime.now(timezone.utc)
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )

            if step_status == "failed":
                scenario_status = "failed"

        except Exception as e:
            # RUN-015: 步骤异常捕获，status=error，不中断后续
            step_end = datetime.now(timezone.utc)
            step_error = {
                "code": "ENGINE_INTERNAL_ERROR",
                "message": str(e),
                "detail": None,
            }
            steps_result.append({
                **_step_result_base(step, i, step_start, step_end, 0, "error", step_error),
            })
            scenario_status = "error"

    # RUN-016: 场景整体 status（已在上方循环中维护 scenario_status）
    # RUN-017: summary 断言统计
    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    passed_steps = sum(1 for s in steps_result if s["status"] == "passed")
    failed_steps = sum(1 for s in steps_result if s["status"] == "failed")
    error_steps = sum(1 for s in steps_result if s["status"] == "error")
    skipped_steps = sum(1 for s in steps_result if s["status"] == "skipped")
    pass_rate = (
        round((passed_assertions / total_assertions * 100), 1)
        if total_assertions else 100.0
    )
    avg_rt = int(sum(response_times) / len(response_times)) if response_times else 0
    max_rt = max(response_times) if response_times else 0
    min_rt = min(response_times) if response_times else 0

    summary = {
        "total_steps": len(steps_result),
        "passed_steps": passed_steps,
        "failed_steps": failed_steps,
        "skipped_steps": skipped_steps,
        "error_steps": error_steps,
        "total_assertions": total_assertions,
        "passed_assertions": passed_assertions,
        "failed_assertions": failed_assertions,
        "pass_rate": pass_rate,
        "total_requests": total_requests,
        "total_db_operations": 0,
        "total_extractions": total_extractions,
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

    # RUN-027/028: 返回 ExecutionResult 模型
    result_dict: dict[str, Any] = {
        "execution_id": execution_id,
        "scenario_id": config.scenario_id,
        "scenario_name": config.name,
        "project_id": config.project_id,
        "status": scenario_status,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration": duration_ms,
        "summary": summary,
        "environment": environment,
        "steps": steps_result,
        "data_driven": None,
        "variables": pool.snapshot(),
        "logs": [],
        "error": None,
    }
    return ExecutionResult.model_validate(result_dict)
