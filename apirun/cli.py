"""CLI 入口点 - sisyphus 命令"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click  # type: ignore[reportMissingImports]
import yaml

from apirun.core.models import EnvironmentConfig
from apirun.core.runner import load_case, run_case
from apirun.errors import EngineError
from apirun.result.allure_reporter import generate as generate_allure
from apirun.result.html_reporter import generate as generate_html
from apirun.result.json_reporter import to_json, to_json_engine_error
from apirun.result.text_reporter import render as render_text

# 为避免类型检查器对 click 动态属性报错，这里通过 getattr 创建别名。
command = getattr(click, "command")
option = getattr(click, "option")
echo = getattr(click, "echo")
Choice = getattr(click, "Choice")


def _find_sisyphus_config(start: Path) -> Path | None:
    """从当前目录向上查找 .sisyphus/config.yaml。"""
    for candidate in (start, *start.parents):
        config_path = candidate / ".sisyphus" / "config.yaml"
        if config_path.exists() and config_path.is_file():
            return config_path
    return None


def _load_active_profile_environment() -> EnvironmentConfig | None:
    """加载 active_profile 对应环境配置，失败时降级为 None。"""
    config_path = _find_sisyphus_config(Path.cwd())
    if config_path is None:
        return None

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return None

    if not isinstance(raw, dict):
        return None
    active = raw.get("active_profile")
    profiles = raw.get("profiles")
    if not isinstance(active, str) or not isinstance(profiles, dict):
        return None

    profile_data = profiles.get(active)
    if not isinstance(profile_data, dict):
        return None

    base_url = profile_data.get("base_url")
    variables = profile_data.get("variables")
    if not isinstance(base_url, str) or not base_url.strip():
        return None
    if variables is None:
        variables = {}
    if not isinstance(variables, dict):
        return None

    return EnvironmentConfig(name=active, base_url=base_url, variables=variables)


def _run_single_case(
    path: str,
    output_format: str,
    verbose: bool = False,
    allure_dir: str | None = None,
    html_dir: str | None = None,
    fallback_environment: EnvironmentConfig | None = None,
) -> dict[str, Any]:
    """执行单个 YAML 用例并返回结果 dict（引擎异常时抛出）。"""
    case_model = load_case(path)
    if case_model.config.environment is None and fallback_environment is not None:
        case_model.config.environment = fallback_environment
    exec_result = run_case(case_model, verbose=verbose)
    result: dict[str, Any] = exec_result.model_dump()

    if output_format == "json":
        return result
    if output_format == "allure":
        generate_allure(result, Path(allure_dir or "allure-results"))
        render_text(result, verbose=verbose)
        return result
    if output_format == "html":
        generate_html(result, Path(html_dir or "html-report"))
        render_text(result, verbose=verbose)
        return result

    render_text(result, verbose=verbose)
    return result


@command()
@option(
    "--case",
    required=False,
    help="单个 YAML 测试用例文件路径",
)
@option(
    "--cases",
    required=False,
    help="YAML 用例目录路径, 批量执行该目录下所有用例 (*.yaml, *.yml, 递归)",
)
@option(
    "-O",
    "--output-format",
    "output_format",
    type=Choice(["text", "json", "allure", "html"]),
    default="text",
    help="输出格式: text(默认) / json / allure / html",
)
@option("--allure-dir", default=None, help="Allure 报告输出目录")
@option("--html-dir", default=None, help="HTML 报告输出目录")
@option("-v", "--verbose", is_flag=True, help="详细输出模式")
def main(
    case: str | None,
    cases: str | None,
    output_format: str,
    allure_dir: str | None,
    html_dir: str | None,
    verbose: bool,
) -> None:
    """sisyphus-api-engine: YAML 驱动的接口自动化测试引擎.

    - --case:   执行单个 YAML 用例
    - --cases:  批量执行目录下所有 YAML 用例 (递归)
    """
    if not case and not cases:
        echo("必须指定 --case 或 --cases 之一", err=True)
        sys.exit(1)
    fallback_environment = _load_active_profile_environment()

    # 批量执行模式: sisyphus --cases tests/
    if cases:
        base = Path(cases)
        if not base.exists() or not base.is_dir():
            echo(f"目录不存在或不是目录: {base}", err=True)
            sys.exit(1)

        yaml_files = sorted(
            set(base.rglob("*.yaml")).union(base.rglob("*.yml")),
            key=str,
        )

        if not yaml_files:
            echo(
                f"目录 {base} 下未找到 YAML 用例 (*.yaml, *.yml)",
                err=True,
            )
            sys.exit(1)

        results: list[dict[str, Any]] = []
        has_error = False

        for path in yaml_files:
            try:
                result = _run_single_case(
                    str(path),
                    output_format,
                    verbose=verbose,
                    allure_dir=allure_dir,
                    html_dir=html_dir,
                    fallback_environment=fallback_environment,
                )
                results.append(result)
            except EngineError as e:
                has_error = True
                if output_format == "json":
                    # 批量模式下仍返回结构化 JSON 错误对象
                    err_json = to_json_engine_error(
                        execution_id="",
                        scenario_id="",
                        scenario_name="",
                        project_id="",
                        code=e.code,
                        message=e.message,
                        detail=e.detail,
                    )
                    results.append(__import__("json").loads(err_json))
                else:
                    echo(e.message, err=True)
                continue
            except Exception as e:  # noqa: BLE001
                has_error = True
                if output_format == "json":
                    err_json = to_json_engine_error(
                        execution_id="",
                        scenario_id="",
                        scenario_name="",
                        project_id="",
                        code="ENGINE_INTERNAL_ERROR",
                        message=str(e),
                        detail=None,
                    )
                    results.append(__import__("json").loads(err_json))
                else:
                    echo(str(e), err=True)
                continue

        if output_format == "json":
            echo(to_json(results, ensure_ascii=False, indent=2))

        # CLI-015: 断言失败(status=failed)时 exit 0，仅引擎异常时 exit 1
        if has_error:
            sys.exit(1)
        sys.exit(0)

    # 单用例模式: sisyphus --case xxx.yaml
    path = case or ""
    try:
        result = _run_single_case(
            path,
            output_format,
            verbose=verbose,
            allure_dir=allure_dir,
            html_dir=html_dir,
            fallback_environment=fallback_environment,
        )
    except EngineError as e:
        if output_format == "json":
            err_json = to_json_engine_error(
                execution_id="",
                scenario_id="",
                scenario_name="",
                project_id="",
                code=e.code,
                message=e.message,
                detail=e.detail,
            )
            echo(err_json)
        else:
            echo(e.message, err=True)
        sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        if output_format == "json":
            err_json = to_json_engine_error(
                execution_id="",
                scenario_id="",
                scenario_name="",
                project_id="",
                code="ENGINE_INTERNAL_ERROR",
                message=str(e),
                detail=None,
            )
            echo(err_json)
        else:
            echo(str(e), err=True)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        if output_format == "json":
            err_json = to_json_engine_error(
                execution_id="",
                scenario_id="",
                scenario_name="",
                project_id="",
                code="ENGINE_INTERNAL_ERROR",
                message=str(e),
                detail=None,
            )
            echo(err_json)
        else:
            echo(str(e), err=True)
        sys.exit(1)

    if output_format == "json":
        echo(to_json(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
