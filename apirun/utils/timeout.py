"""超时执行工具"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("sisyphus")

DEFAULT_STEP_TIMEOUT = 300  # 默认步骤超时：5 分钟


def execute_with_timeout(
    func: Callable[..., Any],
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    timeout: int = DEFAULT_STEP_TIMEOUT,
    timeout_error: tuple[str, str] | None = None,
) -> Any:
    """
    执行函数并设置超时限制。

    Args:
        func: 要执行的函数
        args: 位置参数
        kwargs: 关键字参数
        timeout: 超时时间（秒）
        timeout_error: 超时时返回的错误信息 (code, message)

    Returns:
        函数执行结果

    Raises:
        TimeoutError: 如果函数执行超时
    """
    kwargs = kwargs or {}
    result = None
    exception = None
    thread_completed = threading.Event()

    def target() -> None:
        nonlocal result, exception
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            exception = e
        finally:
            thread_completed.set()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if not thread_completed.is_set():
        # 超时了，线程仍在运行
        logger.warning(f"函数执行超时: {func.__name__}, 超时时间: {timeout}秒")
        if timeout_error:
            from apirun.errors import EngineError

            error_code, error_message = timeout_error
            raise EngineError(
                error_code,
                error_message,
                detail=f"步骤执行超过 {timeout} 秒限制",
            )
        raise TimeoutError(f"函数 {func.__name__} 执行超时（{timeout}秒）")

    if exception is not None:
        raise exception

    return result

