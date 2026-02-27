"""场景执行器 - 解析 YAML、按序执行步骤、生成 JSON 输出"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from apirun.core.models import CaseModel, Config, DbParams, ExtractRule, StepDefinition
from apirun.data_driven.driver import get_parameter_sets, run_data_driven
from apirun.executor.custom import execute_custom_step_safe
from apirun.executor.db import execute_db_step_safe
from apirun.executor.request import execute_request_step
from apirun.extractor.extractor import run_extract_batch
from apirun.result.log_collector import LogCollector
from apirun.result.models import DataDrivenResult, ExecutionResult, ExecutionSummary
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


def run_case(
    case: CaseModel,
    data_driven_vars: dict[str, Any] | None = None,
    verbose: bool = False,
    publisher: Any = None,
) -> ExecutionResult:
    """执行用例，返回 ExecutionResult 模型。支持数据驱动、日志收集与可选事件发布器（WS-004）。"""
    from apirun.websocket.publisher import NoOpPublisher as _NoOp
    if publisher is None:
        publisher = _NoOp()
    execution_id = f"exec-{uuid.uuid4().hex[:12]}"
    config: Config = case.config
    base_url = ""
    if config.environment:
        base_url = config.environment.base_url or ""

    # 数据驱动：无 data_driven_vars 且 case 配置了 ddts 或 csv_datasource 时执行多轮（RUN-020～RUN-023）
    if data_driven_vars is None:
        enabled, source, dataset_name, param_list = get_parameter_sets(case)
        if enabled and param_list:
            ddr, first_result = run_data_driven(
                case,
                lambda params: run_case(
                    case, data_driven_vars=params, verbose=verbose, publisher=publisher
                ),
            )
            if first_result is not None:
                d = first_result.model_dump()
                d["data_driven"] = ddr.model_dump()
                d["summary"] = {**d["summary"], "total_data_driven_runs": ddr.total_runs}
                return ExecutionResult.model_validate(d)

    pool = VariablePool()
    pool.set_scenario(config.variables or {})
    if data_driven_vars:
        pool.set_data_driven(data_driven_vars)
    if config.environment and config.environment.variables:
        pool.set_environment(config.environment.variables)
    variables = pool.as_dict()

    logs = LogCollector(verbose=verbose)
    logs.info(f"开始执行场景: {config.name}")
    try:
        publisher.emit(
            "scenario_start",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"execution_id": execution_id, "scenario_name": config.name},
        )
    except Exception:
        pass

    # RUN-018: 前置 SQL 执行
    if config.pre_sql:
        for stmt in config.pre_sql.statements or []:
            execute_db_step_safe(
                DbParams(datasource=config.pre_sql.datasource, sql=stmt),
                variables,
            )

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
            logs.info(f"[步骤 {i}] 开始执行: {step.name}", step_index=i)
            try:
                publisher.emit("step_start", step_index=i, data={"name": step.name})
            except Exception:
                pass
            if not step.enabled:
                # RUN-008: enabled=false 时生成 skipped StepResult
                step_end = datetime.now(timezone.utc)
                logs.info(f"[步骤 {i}] 完成: skipped", step_index=i)
                try:
                    publisher.emit("step_done", step_index=i, status="skipped")
                except Exception:
                    pass
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )
                continue

            if step.keyword_type == "request" and step.request:
                # request 步骤
                total_requests += 1
                variables = pool.as_dict()
                req_url = (base_url.rstrip("/") + "/" + step.request.url.lstrip("/")) if base_url and not step.request.url.startswith(("http://", "https://")) else step.request.url
                logs.debug(f"[步骤 {i}] 发送 {step.request.method or 'GET'} 请求 → {req_url}", step_index=i)
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

            elif step.keyword_type == "db" and step.db:
                # RUN-011: db 步骤（DB-001～DB-011）
                extract_results = None
                assertion_results = None
                variables = pool.as_dict()
                db_out = execute_db_step_safe(step.db, variables)
                db_detail = db_out.get("db_detail")
                db_rows = db_out.get("rows") or []
                step_error = db_out.get("error")
                if step_error:
                    step_status = "error"
                else:
                    # DB-010/011: db.extract 与 db.validate
                    if step.db.extract:
                        rules = [
                            ExtractRule(
                                name=r.name,
                                type="db_result",
                                expression=r.expression,
                                scope=r.scope,
                                default=r.default,
                            )
                            for r in step.db.extract
                        ]
                        ex_results = run_extract_batch(rules, variables=variables, db_rows=db_rows)
                        extract_results = [r.model_dump() for r in ex_results]
                        total_extractions += len(ex_results)
                        for er in ex_results:
                            if er.status == "success" and er.value is not None:
                                pool.set(er.name, er.value, scope=er.scope)
                        if any(r.status == "failed" for r in ex_results):
                            step_status = "failed"
                    if step.db.validate:
                        variables = pool.as_dict()
                        ar_list = []
                        for vr in step.db.validate:
                            ar = run_assertion(
                                target="db_result",
                                comparator=vr.comparator,
                                expected=vr.expected,
                                expression=vr.expression,
                                message=vr.message,
                                variables=variables,
                                db_rows=db_rows,
                            )
                            ar_list.append(ar.model_dump())
                            total_assertions += 1
                            if ar.status == "passed":
                                passed_assertions += 1
                            else:
                                failed_assertions += 1
                                step_status = "failed"
                        assertion_results = ar_list
                step_end = datetime.now(timezone.utc)
                duration_db = (db_detail or {}).get("execution_time", 0)
                steps_result.append({
                    **_step_result_base(step, i, step_start, step_end, duration_db, step_status, step_error),
                    "db_detail": db_detail,
                    "extract_results": extract_results if step.db.extract and not step_error else None,
                    "assertion_results": assertion_results if step.db.validate and not step_error else None,
                })

            elif step.keyword_type == "custom" and step.custom:
                # RUN-012: custom 步骤（CST-001～CST-007）
                variables = pool.as_dict()
                custom_out = execute_custom_step_safe(
                    step.keyword_name or "",
                    step.custom,
                    variables,
                )
                custom_detail = custom_out.get("custom_detail")
                step_error = custom_out.get("error")
                return_value = custom_out.get("return_value")
                if step_error:
                    step_status = "error"
                    duration_custom = (custom_detail or {}).get("execution_time", 0)
                else:
                    step_status = "passed"
                    duration_custom = (custom_detail or {}).get("execution_time", 0)
                    if step.custom.extract and return_value is not None:
                        fake_response = {"body": return_value, "headers": {}, "cookies": {}}
                        ex_results = run_extract_batch(
                            step.custom.extract, fake_response, variables, db_rows=None
                        )
                        extract_results = [r.model_dump() for r in ex_results]
                        total_extractions += len(ex_results)
                        if any(r.status == "failed" for r in ex_results):
                            step_status = "failed"
                        for er in ex_results:
                            if er.status == "success" and er.value is not None:
                                pool.set(er.name, er.value, scope=er.scope)
                step_end = datetime.now(timezone.utc)
                steps_result.append({
                    **_step_result_base(
                        step, i, step_start, step_end, duration_custom, step_status, step_error
                    ),
                    "custom_detail": custom_detail,
                    "extract_results": extract_results if step.custom.extract and not step_error else None,
                })

            else:
                step_end = datetime.now(timezone.utc)
                steps_result.append(
                    _step_result_base(step, i, step_start, step_end, 0, "skipped", None)
                )

            logs.info(f"[步骤 {i}] 完成: {step_status}", step_index=i)
            try:
                publisher.emit("step_done", step_index=i, status=step_status)
            except Exception:
                pass
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
            logs.info(f"[步骤 {i}] 完成: error", step_index=i)
            try:
                publisher.emit("step_done", step_index=i, status="error")
            except Exception:
                pass

    # RUN-019: 后置 SQL 执行（无论成功失败）
    if config.post_sql:
        variables = pool.as_dict()
        for stmt in config.post_sql.statements or []:
            execute_db_step_safe(
                DbParams(datasource=config.post_sql.datasource, sql=stmt),
                variables,
            )

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    logs.info(f"场景执行完毕: {scenario_status} ({duration_ms}ms)")
    try:
        publisher.emit(
            "scenario_done",
            timestamp=end_time.isoformat(),
            data={"status": scenario_status, "duration_ms": duration_ms},
        )
    except Exception:
        pass

    # RUN-016: 场景整体 status（已在上方循环中维护 scenario_status）
    # RUN-017: summary 断言统计
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
        "total_db_operations": sum(1 for s in steps_result if s.get("db_detail") is not None),
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
        "logs": logs.to_list(),
        "error": None,
    }
    return ExecutionResult.model_validate(result_dict)
