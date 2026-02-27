"""自定义关键字执行器单元测试（CST-001～CST-007）"""

from apirun.core.models import CustomParams
from apirun.executor.custom import (
    KEYWORD_REGISTRY,
    execute_custom_step_safe,
    register_keyword,
)
from apirun.keyword import Keyword


@register_keyword
class EchoKeyword(Keyword):
    name = "echo"

    def execute(self, **kwargs):
        return kwargs.get("message", "")


@register_keyword
class FailingKeyword(Keyword):
    name = "failing"

    def execute(self, **kwargs):
        raise RuntimeError("intended failure")


def test_execute_custom_step_success():
    params = CustomParams(parameters={"message": "hello"})
    out = execute_custom_step_safe("echo", params, {})
    assert out.get("error") is None
    assert out["return_value"] == "hello"
    detail = out["custom_detail"]
    assert detail["keyword_name"] == "echo"
    assert detail["parameters_input"] == {"message": "hello"}
    assert detail["return_value"] == "hello"
    assert detail["execution_time"] >= 0


def test_execute_custom_step_keyword_not_found():
    params = CustomParams(parameters={})
    out = execute_custom_step_safe("nonexistent_keyword", params, {})
    assert out["error"] is not None
    assert out["error"]["code"] == "KEYWORD_NOT_FOUND"
    assert out["return_value"] is None
    assert out["custom_detail"] is None


def test_execute_custom_step_execution_error():
    params = CustomParams(parameters={})
    out = execute_custom_step_safe("failing", params, {})
    assert out["error"] is not None
    assert out["error"]["code"] == "KEYWORD_EXECUTION_ERROR"
    assert "intended failure" in out["error"]["message"]
    assert out["custom_detail"] is not None
    assert out["custom_detail"]["return_value"] is None


def test_execute_custom_step_parameters_rendered():
    params = CustomParams(parameters={"message": "{{greet}}"})
    out = execute_custom_step_safe("echo", params, {"greet": "world"})
    assert out.get("error") is None
    assert out["return_value"] == "world"


def test_register_keyword():
    assert "echo" in KEYWORD_REGISTRY
    assert "failing" in KEYWORD_REGISTRY
    assert KEYWORD_REGISTRY["echo"] is EchoKeyword
