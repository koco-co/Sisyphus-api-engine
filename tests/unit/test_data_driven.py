"""数据驱动单元测试（DDT-001～DDT-008 / TST-030）"""

import pytest

from apirun.core.models import CaseModel, Config, Ddts, StepDefinition
from apirun.data_driven.driver import get_parameter_sets, run_data_driven
from apirun.result.models import ExecutionResult, ExecutionSummary


@pytest.fixture
def case_with_ddts():
    """带 ddts 的 CaseModel"""
    return CaseModel(
        config=Config(name="n", project_id="p", scenario_id="s"),
        teststeps=[
            StepDefinition(name="s1", keyword_type="request", keyword_name="http", request=None),
        ],
        ddts=Ddts(
            name="登录数据集",
            parameters=[
                {"user": "a", "expected": 200},
                {"user": "b", "expected": 200},
            ],
        ),
    )


def test_get_parameter_sets_yaml_inline(case_with_ddts):
    """DDT-001: ddts 时返回 yaml_inline 与 parameters 列表"""
    enabled, source, name, params = get_parameter_sets(case_with_ddts)
    assert enabled is True
    assert source == "yaml_inline"
    assert name == "登录数据集"
    assert len(params) == 2
    assert params[0] == {"user": "a", "expected": 200}


def test_run_data_driven_returns_result(case_with_ddts):
    """run_data_driven 返回 DataDrivenResult 与首轮 ExecutionResult（DDT-005～DDT-007）"""

    def fake_run(case: CaseModel, params: dict):
        return ExecutionResult(
            execution_id="e1",
            scenario_id="s",
            scenario_name=case.config.name,
            project_id="p",
            status="passed",
            duration=100,
            summary=ExecutionSummary(total_steps=1, passed_steps=1),
            steps=[],
        )

    ddr, first = run_data_driven(case_with_ddts, fake_run)
    assert ddr.enabled is True
    assert ddr.source == "yaml_inline"
    assert ddr.dataset_name == "登录数据集"
    assert ddr.total_runs == 2
    assert ddr.passed_runs == 2
    assert len(ddr.runs) == 2
    assert ddr.runs[0].run_index == 0
    assert ddr.runs[0].parameters == {"user": "a", "expected": 200}
    assert first is not None
    assert first.execution_id == "e1"


def test_get_parameter_sets_no_ddts():
    """无 ddts 且无 csv_datasource 时 enabled=False"""
    case = CaseModel(
        config=Config(name="n", project_id="p", scenario_id="s"),
        teststeps=[],
        ddts=None,
    )
    enabled, _, _, params = get_parameter_sets(case)
    assert enabled is False
    assert params == []
