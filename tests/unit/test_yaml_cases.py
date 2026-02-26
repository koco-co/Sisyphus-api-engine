"""YAML 用例解析测试 - 覆盖 tests/yaml 下示例。"""

from __future__ import annotations

from pathlib import Path

import yaml

from apirun.core.models import CaseModel


def test_full_step_types_yaml_can_be_parsed():
    """full_step_types.yaml 应能被 CaseModel 正常解析。"""
    yaml_path = (
        Path(__file__)
        .resolve()
        .parent.parent
        .joinpath("yaml/full_step_types.yaml")
    )
    assert yaml_path.exists()
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    case = CaseModel.model_validate(data)
    assert case.config.name.startswith("用户注册")
    assert len(case.teststeps) >= 5

