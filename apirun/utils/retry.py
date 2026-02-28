"""HTTP 请求重试工具 — 自动重试失败的请求（网络错误、5xx 等）"""

import logging
import time
from collections.abc import Callable
from typing import Any

import requests

from apirun.config import Config

logger = logging.getLogger("sisyphus")

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.RequestException,
)


def should_retry_on_status_code(status_code: int) -> bool:
    """
    判断 HTTP 状态码是否应该重试。

    Args:
        status_code: HTTP 状态码

    Returns:
        True 如果应该重试，False 否则
    """
    # 5xx 服务器错误应该重试
    if 500 <= status_code < 600:
        return True

    # 429 Too Many Requests 应该重试
    if status_code == 429:
        return True

    # 其他状态码（包括 4xx）不重试
    return False


def should_retry_on_exception(exception: Exception) -> bool:
    """
    判断异常是否应该重试。

    Args:
        exception: 捕获的异常

    Returns:
        True 如果应该重试，False 否则
    """
    # 网络错误、超时等应该重试
    return isinstance(exception, RETRYABLE_EXCEPTIONS)


def calculate_backoff(attempt: int, base_backoff: float = 0.5) -> float:
    """
    计算指数退避的等待时间。

    Args:
        attempt: 当前尝试次数（从 0 开始）
        base_backoff: 基础退避时间（秒）

    Returns:
        等待时间（秒）
    """
    # 指数退避：base_backoff * (2 ^ attempt)
    # 例如: 0.5, 1.0, 2.0, 4.0, 8.0 秒
    return base_backoff * (2**attempt)


def execute_with_retry(
    func: Callable[..., Any],
    max_retries: int | None = None,
    base_backoff: float = 0.5,
    max_backoff: float = 30.0,
    retry_on_5xx: bool = True,
    **kwargs: Any,
) -> Any:
    """
    执行函数并在失败时自动重试。

    Args:
        func: 要执行的函数（通常是 requests.request）
        max_retries: 最大重试次数（None 表示使用配置）
        base_backoff: 基础退避时间（秒）
        max_backoff: 最大退避时间（秒）
        retry_on_5xx: 是否在 5xx 错误时重试
        **kwargs: 传递给 func 的参数

    Returns:
        函数的返回值（通常是 requests.Response）

    Raises:
        Exception: 重试次数用尽后仍未成功
    """
    config = Config()

    # 从配置获取最大重试次数
    if max_retries is None:
        max_retries = getattr(config, "HTTP_MAX_RETRIES", 3)

    # 确保 max_retries 不为 None
    if max_retries is None:
        max_retries = 3

    last_exception: Exception | None = None
    last_response: requests.Response | None = None

    for attempt in range(max_retries + 1):  # +1 因为第一次不算重试
        try:
            response = func(**kwargs)

            # 检查状态码
            if retry_on_5xx and should_retry_on_status_code(response.status_code):
                logger.warning(
                    f"HTTP 请求返回可重试状态码: {response.status_code}, "
                    f"尝试 {attempt + 1}/{max_retries + 1}"
                )
                last_response = response

                # 最后一次尝试不再等待
                if attempt < max_retries:
                    backoff = min(calculate_backoff(attempt, base_backoff), max_backoff)
                    logger.debug(f"等待 {backoff:.1f} 秒后重试...")
                    time.sleep(backoff)
                    continue

            # 成功或不需要重试
            if attempt > 0:
                logger.info(f"HTTP 请求重试成功（第 {attempt + 1} 次尝试）")
            return response

        except Exception as e:
            last_exception = e

            # 判断是否应该重试
            if not should_retry_on_exception(e):
                logger.error(f"HTTP 请求遇到不可重试的异常: {type(e).__name__}: {e}")
                raise

            logger.warning(
                f"HTTP 请求失败（可重试）: {type(e).__name__}: {e}, "
                f"尝试 {attempt + 1}/{max_retries + 1}"
            )

            # 最后一次尝试不再等待
            if attempt < max_retries:
                backoff = min(calculate_backoff(attempt, base_backoff), max_backoff)
                logger.debug(f"等待 {backoff:.1f} 秒后重试...")
                time.sleep(backoff)
                continue

    # 所有重试都失败了
    if last_exception is not None:
        logger.error(f"HTTP 请求重试 {max_retries} 次后仍然失败")
        raise last_exception

    if last_response is not None:
        # 状态码重试失败
        raise requests.exceptions.HTTPError(
            f"HTTP 请求返回错误状态码 {last_response.status_code}，"
            f"重试 {max_retries} 次后仍然失败"
        )

    # 不应该到达这里
    raise RuntimeError("重试逻辑异常：没有异常也没有响应")
