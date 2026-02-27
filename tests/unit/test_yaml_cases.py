"""YAML 用例解析测试 - 覆盖 tests/yaml 下示例（YML-001～YML-009）。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from apirun.core.models import CaseModel


def test_full_step_types_yaml_can_be_parsed():
    """full_step_types.yaml 应能被 CaseModel 正常解析。"""
    yaml_path = Path(__file__).resolve().parent.parent.joinpath("yaml/full_step_types.yaml")
    assert yaml_path.exists()
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    case = CaseModel.model_validate(data)
    assert case.config.name.startswith("用户注册")
    assert len(case.teststeps) >= 5


def _yaml_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "yaml"


@pytest.mark.parametrize(
    "yaml_name",
    [
        "simple_get.yaml",
        "multi_step_e2e.yaml",
        "data_driven_inline.yaml",
        "data_driven_csv.yaml",
        "variable_extraction.yaml",
        "all_comparators.yaml",
        "error_cases.yaml",
        "pre_post_sql.yaml",
    ],
)
def test_each_yaml_loads_and_parses(yaml_name: str):
    """YML-002～YML-009：各 YAML 可被 load_case 解析并 run_case 可执行一轮。"""
    from apirun.core.runner import load_case, run_case

    yaml_path = _yaml_dir() / yaml_name
    if not yaml_path.exists():
        pytest.skip(f"缺少 {yaml_name}")
    case = load_case(yaml_path)
    assert case.config.name
    assert len(case.teststeps) >= 1
    result = run_case(case)
    assert result.scenario_name == case.config.name
    assert len(result.steps) == len(case.teststeps)
