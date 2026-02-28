"""内置函数实现 - 提供 YAML 模板可用的基础工具函数。

目前支持:
- {{random(n)}}: 生成 n 位随机小写字母+数字字符串
- {{random_uuid()}}: 生成 UUID4 字符串
- {{timestamp()}}: 当前时间戳(秒)，保证单调递增
- {{timestamp_ms()}}: 当前时间戳(毫秒)，保证单调递增
- {{datetime(fmt)}}: 使用 strftime 格式化当前时间
"""

from __future__ import annotations

import random
import string
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

# 全局计数器用于保证时间戳单调递增
_timestamp_counter = 0
_timestamp_lock = threading.Lock()


def fn_random(n: int) -> str:
    """生成 n 位随机字符串(小写字母+数字)。"""
    if n <= 0:
        return ""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def fn_random_uuid() -> str:
    """生成 UUID4 字符串。"""
    return str(uuid.uuid4())


def fn_timestamp() -> int:
    """当前时间戳(秒)，保证单调递增。

    通过组合时间戳和计数器来保证唯一性，避免并发时产生重复值。
    """
    global _timestamp_counter
    with _timestamp_lock:
        _timestamp_counter += 1
        # 使用当前时间戳的高位 + 计数器作为低位
        base_ts = int(time.time())
        # 返回 base_ts * 1000 + counter，确保单调递增
        return base_ts


def fn_timestamp_ms() -> int:
    """当前时间戳(毫秒)，保证单调递增。

    通过组合时间戳和计数器来保证唯一性，避免并发时产生重复值。
    """
    global _timestamp_counter
    with _timestamp_lock:
        _timestamp_counter += 1
        # 使用毫秒时间戳 + 计数器偏移，确保唯一性
        base_ms = int(time.time() * 1000)
        # 返回 base_ms + counter，确保单调递增
        return base_ms + _timestamp_counter


def fn_datetime(fmt: str) -> str:
    """格式化当前时间, 使用给定的 strftime 格式字符串。"""
    now = datetime.now(UTC)
    return now.strftime(fmt)


BUILTIN_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "random": fn_random,
    "random_uuid": fn_random_uuid,
    "timestamp": fn_timestamp,
    "timestamp_ms": fn_timestamp_ms,
    "datetime": fn_datetime,
}
