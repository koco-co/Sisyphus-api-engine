"""Text 报告 — rich 终端美化输出（RPT-005～RPT-007）"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render(
    result: dict[str, Any],
    verbose: bool = False,
) -> None:
    """
    将执行结果渲染为终端文本（RPT-005、RPT-006）。
    verbose=True 时显示步骤请求/响应等详情（RPT-007）。
    """
    console = Console()
    scenario_name = result.get("scenario_name", "")
    status = result.get("status", "")
    duration = result.get("duration", 0)
    summary = result.get("summary") or {}
    steps = result.get("steps") or []

    status_style = (
        "green" if status == "passed" else ("red" if status in ("failed", "error") else "yellow")
    )
    header = f"[bold]{scenario_name}[/bold]  [{status_style}]{status}[/]  ({duration}ms)"
    console.print(Panel(header, title="场景执行", border_style="blue"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("步骤", style="dim")
    table.add_column("名称")
    table.add_column("类型")
    table.add_column("状态")
    table.add_column("耗时(ms)")
    for s in steps:
        idx = s.get("step_index", "")
        name = s.get("name", "")
        ktype = s.get("keyword_type", "")
        st = s.get("status", "")
        dur = s.get("duration", 0)
        st_style = "green" if st == "passed" else ("red" if st in ("failed", "error") else "yellow")
        table.add_row(str(idx), name, ktype, f"[{st_style}]{st}[/]", str(dur))
    console.print(table)

    summary_text = (
        f"步骤: {summary.get('passed_steps', 0)}/{summary.get('total_steps', 0)} 通过 | "
        f"断言: {summary.get('passed_assertions', 0)}/{summary.get('total_assertions', 0)} 通过"
    )
    console.print(f"  [dim]{summary_text}[/dim]")

    if verbose and steps:
        console.print()
        for s in steps:
            if s.get("request_detail"):
                console.print(
                    Panel(
                        f"[bold]步骤 {s.get('step_index')}[/bold] {s.get('name')}\n"
                        f"请求: {s.get('request_detail', {}).get('method')} {s.get('request_detail', {}).get('url')}\n"
                        f"响应状态: {s.get('response_detail', {}).get('status_code')}",
                        title="请求详情",
                        border_style="dim",
                    )
                )
