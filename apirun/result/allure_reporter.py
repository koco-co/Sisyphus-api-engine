"""Allure 报告生成 — 写入 allure-results 目录（RPT-008～RPT-010）"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def _iso_to_epoch_ms(iso_str: str) -> int:
    """将 ISO 8601 时间转为毫秒时间戳。"""
    if not iso_str:
        return 0
    s = iso_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0


def _allure_status(status: str) -> str:
    """引擎 status 映射为 Allure status。"""
    return {"passed": "passed", "failed": "failed", "error": "broken", "skipped": "skipped"}.get(
        status, "broken"
    )


def _step_to_allure_step(step: dict[str, Any], step_uuid_prefix: str) -> dict[str, Any]:
    """将 StepResult 转为 Allure Step，断言结果作为 Attachment（RPT-009、RPT-010）。"""
    start_ms = _iso_to_epoch_ms(step.get("start_time") or "")
    duration_ms = step.get("duration") or 0
    stop_ms = start_ms + duration_ms if start_ms else 0
    allure_status = _allure_status(step.get("status") or "passed")
    name = step.get("name") or f"步骤 {step.get('step_index', 0)}"
    keyword = step.get("keyword_type") or ""
    if keyword:
        name = f"[{keyword}] {name}"

    attachments: list[dict[str, Any]] = []
    assertion_results = step.get("assertion_results") or []
    if assertion_results:
        att_uuid = f"{step_uuid_prefix}-assertions"
        attachments.append(
            {
                "name": "断言结果",
                "source": f"{att_uuid}.json",
                "type": "application/json",
            }
        )
        # 调用方需写入同名 JSON 文件到目录

    return {
        "name": name,
        "status": allure_status,
        "start": start_ms,
        "stop": stop_ms,
        "attachments": attachments,
        "steps": [],
    }


def generate(
    result: dict[str, Any],
    output_dir: str | Path,
) -> list[str]:
    """
    根据 ExecutionResult 生成 Allure 结果文件（RPT-008）。
    - 写入 output_dir（即 --allure-dir）
    - 返回写入的文件路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_uuid = uuid.uuid4().hex
    written: list[str] = []

    start_time = result.get("start_time") or ""
    end_time = result.get("end_time") or ""
    duration = result.get("duration") or 0
    start_ms = _iso_to_epoch_ms(start_time)
    stop_ms = _iso_to_epoch_ms(end_time) if end_time else start_ms + duration
    scenario_name = result.get("scenario_name") or "场景"
    status = result.get("status") or "passed"

    steps_allure: list[dict[str, Any]] = []
    step_attachments: list[tuple[str, str]] = []  # (attachment_uuid, content)

    for i, step in enumerate(result.get("steps") or []):
        step_prefix = f"{result_uuid}-step{i}"
        allure_step = _step_to_allure_step(step, step_prefix)
        # 为断言结果写入 attachment 文件
        assertion_results = step.get("assertion_results") or []
        if assertion_results:
            att_uuid = f"{step_prefix}-assertions"
            step_attachments.append(
                (att_uuid, json.dumps(assertion_results, ensure_ascii=False, indent=2))
            )
            # allure_step 里已有 attachments 引用 att_uuid.json
        steps_allure.append(allure_step)

    # 写入 *-result.json（Allure 2 格式）
    result_body = {
        "uuid": result_uuid,
        "name": scenario_name,
        "status": _allure_status(status),
        "start": start_ms,
        "stop": stop_ms,
        "steps": steps_allure,
        "attachments": [],
        "parameters": [],
    }
    result_path = output_dir / f"{result_uuid}-result.json"
    result_path.write_text(json.dumps(result_body, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(str(result_path))

    # 写入 assertion attachment 文件
    for att_uuid, content in step_attachments:
        ext = "json"
        att_path = output_dir / f"{att_uuid}.{ext}"
        att_path.write_text(content, encoding="utf-8")
        written.append(str(att_path))

    return written
