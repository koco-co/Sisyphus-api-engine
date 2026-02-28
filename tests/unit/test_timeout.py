"""超时执行工具测试"""

import time

from apirun.errors import STEP_TIMEOUT, EngineError
from apirun.utils.timeout import execute_with_timeout


def test_execute_with_timeout_success():
    """测试超时工具 - 正常执行"""

    def quick_function(x: int, y: int) -> int:
        return x + y

    result = execute_with_timeout(quick_function, args=(1, 2), timeout=5)
    assert result == 3


def test_execute_with_timeout_no_timeout():
    """测试超时工具 - 未超时"""

    def slow_function() -> str:
        time.sleep(0.1)
        return "completed"

    result = execute_with_timeout(slow_function, timeout=5)
    assert result == "completed"


def test_execute_with_timeout_raises():
    """测试超时工具 - 抛出 TimeoutError"""

    def infinite_loop() -> None:
        while True:
            time.sleep(0.1)

    try:
        execute_with_timeout(infinite_loop, timeout=1)
        assert False, "应该抛出 TimeoutError"
    except TimeoutError as e:
        assert "超时" in str(e)
        assert "1秒" in str(e)


def test_execute_with_timeout_custom_error():
    """测试超时工具 - 自定义超时错误"""

    def infinite_loop() -> None:
        while True:
            time.sleep(0.1)

    try:
        execute_with_timeout(
            infinite_loop,
            timeout=1,
            timeout_error=(STEP_TIMEOUT, "步骤执行超时"),
        )
        assert False, "应该抛出 EngineError"
    except EngineError as e:
        assert e.code == STEP_TIMEOUT
        assert e.message == "步骤执行超时"
        assert "1 秒限制" in e.detail


def test_execute_with_timeout_propagates_exception():
    """测试超时工具 - 传播函数异常"""

    def failing_function() -> None:
        raise ValueError("函数执行失败")

    try:
        execute_with_timeout(failing_function, timeout=5)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert str(e) == "函数执行失败"
