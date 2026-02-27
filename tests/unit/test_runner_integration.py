"""场景运行器端到端集成测试（TST-035）"""

from pathlib import Path

from apirun.core.runner import load_case, run_case


def test_full_flow_load_and_run():
    """完整流程：load_case → run_case，结果含顶层字段与 steps。"""
    yaml_path = Path(__file__).resolve().parent.parent / "yaml" / "full_step_types.yaml"
    case = load_case(yaml_path)
    result = run_case(case)
    assert result.execution_id.startswith("exec-")
    assert result.scenario_name
    assert result.status in ("passed", "failed", "error", "skipped")
    assert result.duration >= 0
    assert result.summary.total_steps == len(case.teststeps)
    assert len(result.steps) == len(case.teststeps)
    for i, step in enumerate(result.steps):
        assert step.step_index == i
        assert step.name == case.teststeps[i].name
        assert step.keyword_type in ("request", "assertion", "extract", "db", "custom")
        assert step.status in ("passed", "failed", "error", "skipped")
