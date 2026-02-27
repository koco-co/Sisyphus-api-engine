"""HTML 报告生成 — 自包含单文件 HTML（RPT-011～RPT-012）"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _status_class(status: str) -> str:
    return {
        "passed": "status-passed",
        "failed": "status-failed",
        "error": "status-error",
        "skipped": "status-skipped",
    }.get(status, "status-error")


def generate(result: dict[str, Any], output_dir: str | Path) -> str:
    """
    生成自包含 HTML 报告文件（RPT-011、RPT-012）。
    - 包含摘要、步骤详情、断言、响应数据
    - 返回写入的 HTML 文件路径
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenario_name = _escape(result.get("scenario_name") or "场景")
    status = result.get("status") or "passed"
    duration = result.get("duration") or 0
    summary = result.get("summary") or {}
    steps = result.get("steps") or []

    steps_rows = []
    for s in steps:
        name = _escape(s.get("name") or "")
        ktype = _escape(s.get("keyword_type") or "")
        st = s.get("status") or "skipped"
        dur = s.get("duration") or 0
        sc = _status_class(st)
        steps_rows.append(
            f"<tr><td>{s.get('step_index', 0)}</td><td>{name}</td><td>{ktype}</td>"
            f'<td class="{sc}">{st}</td><td>{dur} ms</td></tr>'
        )
    steps_table = "\n".join(steps_rows)

    # 步骤详情（折叠）：请求/响应/断言
    details_sections = []
    for i, s in enumerate(steps):
        parts = []
        if s.get("request_detail"):
            req = s["request_detail"]
            parts.append(
                "<strong>请求</strong>: " + _escape(f"{req.get('method', '')} {req.get('url', '')}")
            )
        if s.get("response_detail"):
            resp = s["response_detail"]
            body = resp.get("body")
            if body is not None:
                try:
                    body_str = json.dumps(body, ensure_ascii=False, indent=2)
                except (TypeError, ValueError):
                    body_str = str(body)
                if len(body_str) > 2000:
                    body_str = body_str[:2000] + "\n..."
                parts.append("<strong>响应 body</strong>: <pre>" + _escape(body_str) + "</pre>")
        if s.get("assertion_results"):
            ar_list = s["assertion_results"]
            ar_rows = [
                f"<tr><td>{_escape(str(a.get('target')))}</td><td>{_escape(str(a.get('comparator')))}</td>"
                f"<td>{_escape(str(a.get('actual')))}</td><td>{_escape(str(a.get('expected')))}</td>"
                f'<td class="{_status_class(a.get("status") or "failed")}">{a.get("status")}</td></tr>'
                for a in ar_list
            ]
            parts.append(
                "<strong>断言</strong>: <table><tr><th>target</th><th>comparator</th><th>actual</th><th>expected</th><th>status</th></tr>"
                + "".join(ar_rows)
                + "</table>"
            )
        if parts:
            details_sections.append(
                f'<div class="step-detail"><h4>步骤 {i}: {_escape(s.get("name") or "")}</h4>'
                + "".join(parts)
                + "</div>"
            )
    details_html = "\n".join(details_sections)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>执行报告 - {scenario_name}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; background: #f5f5f5; }}
h1 {{ margin-bottom: 0.25rem; }}
.summary {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }}
.summary span {{ background: #fff; padding: 0.5rem 1rem; border-radius: 6px; box-shadow: 0 1px 2px #ccc; }}
table {{ border-collapse: collapse; background: #fff; width: 100%; box-shadow: 0 1px 2px #ccc; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
th {{ background: #f0f0f0; }}
.status-passed {{ color: #0a0; }}
.status-failed {{ color: #c00; }}
.status-error {{ color: #c00; }}
.status-skipped {{ color: #888; }}
.step-detail {{ margin: 1rem 0; padding: 1rem; background: #fff; border-radius: 6px; box-shadow: 0 1px 2px #ccc; }}
.step-detail pre {{ overflow: auto; max-height: 200px; font-size: 12px; }}
</style>
</head>
<body>
<h1>{scenario_name}</h1>
<p>状态: <span class="{_status_class(status)}">{status}</span> | 耗时: {duration} ms</p>
<div class="summary">
<span>总步骤: {summary.get("total_steps", 0)}</span>
<span>通过: {summary.get("passed_steps", 0)}</span>
<span>失败: {summary.get("failed_steps", 0)}</span>
<span>断言通过率: {summary.get("pass_rate", 0)}%</span>
</div>
<h2>步骤概览</h2>
<table>
<thead><tr><th>步骤</th><th>名称</th><th>类型</th><th>状态</th><th>耗时(ms)</th></tr></thead>
<tbody>
{steps_table}
</tbody>
</table>
<h2>步骤详情</h2>
{details_html}
</body>
</html>
"""
    # 文件名带时间戳避免覆盖
    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in (result.get("scenario_name") or "report")
    )
    filename = f"{safe_name.strip() or 'report'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = output_dir / filename
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
