"""CLI 入口点 - sisyphus 命令"""

import json
import sys
from pathlib import Path
from typing import Any

import click

from apirun.core.runner import load_case, run_case


def _run_single_case(path: str, output_format: str) -> dict[str, Any]:
    """执行单个 YAML 用例并返回结果."""
    try:
        case_model = load_case(path)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise
    except ValueError as e:
        click.echo(str(e), err=True)
        raise

    try:
        result: dict[str, Any] = run_case(case_model)
    except Exception as e:  # noqa: BLE001
        click.echo(f"执行失败: {e}", err=True)
        raise

    if output_format == "json":
        # 单用例 json 输出由调用方统一处理
        return result

    click.echo(f"执行测试用例: {path}")
    click.echo(f"场景: {result.get('scenario_name', '')} 状态: {result.get('status', '')}")
    return result


@click.command()
@click.option(
    "--case",
    required=False,
    help="单个 YAML 测试用例文件路径",
)
@click.option(
    "--cases",
    required=False,
    help="YAML 用例目录路径, 批量执行该目录下所有用例 (*.yaml, *.yml, 递归)",
)
@click.option(
    "-O",
    "--output-format",
    "output_format",
    type=click.Choice(["text", "json", "allure", "html"]),
    default="text",
    help="输出格式: text(默认) / json / allure / html",
)
@click.option("--allure-dir", default=None, help="Allure 报告输出目录")
@click.option("--html-dir", default=None, help="HTML 报告输出目录")
@click.option("-v", "--verbose", is_flag=True, help="详细输出模式")
def main(
    case: str | None,
    cases: str | None,
    output_format: str,
    allure_dir: str | None,  # noqa: ARG001
    html_dir: str | None,  # noqa: ARG001
    verbose: bool,  # noqa: ARG001
) -> None:
    """sisyphus-api-engine: YAML 驱动的接口自动化测试引擎.

    - --case:   执行单个 YAML 用例
    - --cases:  批量执行目录下所有 YAML 用例 (递归)
    """
    if not case and not cases:
        click.echo("必须指定 --case 或 --cases 之一", err=True)
        sys.exit(1)

    # 批量执行模式: sisyphus --cases tests/
    if cases:
        base = Path(cases)
        if not base.exists() or not base.is_dir():
            click.echo(f"目录不存在或不是目录: {base}", err=True)
            sys.exit(1)

        yaml_files = sorted(
            set(base.rglob("*.yaml")).union(base.rglob("*.yml")),
            key=str,
        )

        if not yaml_files:
            click.echo(
                f"目录 {base} 下未找到 YAML 用例 (*.yaml, *.yml)",
                err=True,
            )
            sys.exit(1)

        results: list[dict[str, Any]] = []
        has_error = False

        for path in yaml_files:
            try:
                result = _run_single_case(str(path), output_format)
                results.append(result)
            except Exception:  # noqa: BLE001
                has_error = True
                # 错误已经在 _run_single_case 中输出, 继续执行其他用例
                continue

        if output_format == "json":
            click.echo(json.dumps(results, ensure_ascii=False, indent=2))

        if has_error:
            sys.exit(1)
        sys.exit(0)

    # 单用例模式: sisyphus --case xxx.yaml
    path = case or ""
    try:
        result = _run_single_case(path, output_format)
    except Exception:  # noqa: BLE001
        sys.exit(1)

    if output_format == "json":
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
