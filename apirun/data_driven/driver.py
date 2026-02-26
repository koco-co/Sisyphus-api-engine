"""数据驱动执行器 — YAML 内联 / CSV 文件，每轮注入变量并执行（DDT-001～DDT-008）"""

from pathlib import Path
from typing import Any, Callable

from apirun.core.models import CaseModel
from apirun.parser.csv_parser import parse_csv
from apirun.result.models import DataDrivenResult, DataDrivenRun, ExecutionResult, ExecutionSummary


def get_parameter_sets(case: CaseModel) -> tuple[bool, str, str, list[dict[str, Any]]]:
    """
    获取数据驱动参数集。
    返回 (enabled, source, dataset_name, list[parameters])。
    ddts 与 csv_datasource 二选一，ddts 优先。
    """
    if case.ddts and case.ddts.parameters:
        return True, "yaml_inline", case.ddts.name or "ddts", case.ddts.parameters
    csv_path = getattr(case.config, "csv_datasource", None) or ""
    if csv_path and str(csv_path).strip():
        rows = parse_csv(csv_path)
        name = Path(csv_path).stem
        return True, "csv_file", name, rows
    return False, "yaml_inline", "", []


def run_data_driven(
    case: CaseModel,
    run_case_fn: Callable[[CaseModel, dict[str, Any]], ExecutionResult],
) -> tuple[DataDrivenResult, ExecutionResult | None]:
    """
    执行数据驱动：每轮注入参数并调用 run_case_fn，汇总为 DataDrivenResult（DDT-003～DDT-008）。
    返回 (DataDrivenResult, 第一轮 ExecutionResult 用于合并顶层输出)。
    """
    enabled, source, dataset_name, param_list = get_parameter_sets(case)
    if not enabled or not param_list:
        return (
            DataDrivenResult(
                enabled=False,
                source=source,
                dataset_name=dataset_name,
                total_runs=0,
                passed_runs=0,
                failed_runs=0,
                pass_rate=0.0,
                runs=[],
            ),
            None,
        )

    runs: list[DataDrivenRun] = []
    passed = 0
    failed = 0
    first_result: ExecutionResult | None = None
    for run_index, parameters in enumerate(param_list):
        result = run_case_fn(case, parameters)
        if first_result is None:
            first_result = result
        status = result.status
        if status == "passed":
            passed += 1
        else:
            failed += 1
        duration = result.duration
        runs.append(
            DataDrivenRun(
                run_index=run_index,
                parameters=parameters,
                status=status,
                duration=duration,
                summary=result.summary,
                steps=result.steps,
            )
        )
    pass_rate = round((passed / len(param_list)) * 100, 1) if param_list else 0.0
    ddr = DataDrivenResult(
        enabled=True,
        source=source,
        dataset_name=dataset_name,
        total_runs=len(param_list),
        passed_runs=passed,
        failed_runs=failed,
        pass_rate=pass_rate,
        runs=runs,
    )
    return ddr, first_result
