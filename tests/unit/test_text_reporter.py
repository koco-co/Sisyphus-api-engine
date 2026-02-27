"""Text 报告单元测试（TST-034）"""

from apirun.result.text_reporter import render


def test_render_text_minimal_result():
    """rich 渲染不抛异常，输出包含场景名与步骤表。"""
    result = {
        "scenario_name": "测试场景",
        "status": "passed",
        "duration": 100,
        "summary": {"total_steps": 1, "passed_steps": 1, "total_assertions": 1, "passed_assertions": 1},
        "steps": [
            {"step_index": 0, "name": "请求", "keyword_type": "request", "status": "passed", "duration": 50},
        ],
    }
    render(result)
    # 无异常即通过；可选 capfd 断言 stdout 含 "测试场景" / "步骤"


def test_render_text_verbose():
    """verbose=True 时渲染请求详情。"""
    result = {
        "scenario_name": "场景",
        "status": "failed",
        "duration": 0,
        "summary": {"total_steps": 1, "passed_steps": 0, "total_assertions": 0, "passed_assertions": 0},
        "steps": [
            {
                "step_index": 0,
                "name": "GET",
                "keyword_type": "request",
                "status": "failed",
                "duration": 0,
                "request_detail": {"method": "GET", "url": "https://example.com"},
                "response_detail": {"status_code": 404},
            },
        ],
    }
    render(result, verbose=True)
