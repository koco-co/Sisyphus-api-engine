"""事件发布器 — 场景/步骤开始与完成事件推送（WS-001～WS-003）"""

import logging
import time
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger("sisyphus")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


class EventPublisher(Protocol):
    """事件发布器协议：推送场景开始/步骤开始/步骤完成/场景完成（WS-001、WS-002）。"""

    def emit(
        self,
        event_type: str,
        *,
        step_index: int | None = None,
        status: str | None = None,
        timestamp: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """推送一条事件。消息格式：event_type / step_index / status / timestamp / data（WS-002）。"""
        ...


class NoOpPublisher:
    """不推送任何内容的发布器（默认）。"""

    def emit(
        self,
        event_type: str,
        *,
        step_index: int | None = None,
        status: str | None = None,
        timestamp: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        pass


class WsPublisher:
    """
    通过 WebSocket 推送事件的发布器。
    连接失败或发送失败时不抛异常，不影响用例执行（WS-003）。

    改进：
    - 添加重连机制（最多 3 次）
    - 添加连接超时（5 秒）
    - 改进错误处理和日志记录
    - 添加资源清理方法
    """

    def __init__(self, url: str, max_retries: int = 3, timeout: int = 5) -> None:
        """
        初始化 WebSocket 发布器。

        Args:
            url: WebSocket 服务器 URL
            max_retries: 最大重试次数（默认 3）
            timeout: 连接超时时间（秒，默认 5）
        """
        self.url = url
        self._ws: Any = None
        self._max_retries = max_retries
        self._timeout = timeout
        self._consecutive_failures = 0

    def _connect(self) -> Any:
        """建立 WebSocket 连接，支持重试。"""
        # 可选依赖：仅当安装了 websocket-client 时实际连接
        try:
            import websocket
        except ImportError:
            logger.debug("websocket-client 未安装，跳过 WebSocket 推送")
            return None

        for attempt in range(self._max_retries):
            try:
                logger.debug(f"WebSocket 连接尝试 {attempt + 1}/{self._max_retries}: {self.url}")
                ws = websocket.create_connection(self.url, timeout=self._timeout)
                self._consecutive_failures = 0  # 重置失败计数
                logger.info(f"WebSocket 连接成功: {self.url}")
                return ws
            except Exception as e:
                self._consecutive_failures += 1
                if attempt < self._max_retries - 1:
                    # 指数退避：等待 2^attempt 秒
                    wait_time = 2**attempt
                    logger.warning(
                        f"WebSocket 连接失败（第 {attempt + 1} 次）：{e}，"
                        f"{wait_time} 秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"WebSocket 连接失败（已重试 {self._max_retries} 次）：{e}，"
                        f"放弃连接"
                    )
        return None

    def emit(
        self,
        event_type: str,
        *,
        step_index: int | None = None,
        status: str | None = None,
        timestamp: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """推送事件到 WebSocket 服务器。"""
        payload = {
            "event_type": event_type,
            "step_index": step_index,
            "status": status,
            "timestamp": timestamp or _timestamp(),
            "data": data or {},
        }

        try:
            import json as _json

            # 可选依赖检查
            try:
                import websocket  # noqa: F401
            except ImportError:
                return

            # 如果未连接，尝试建立连接
            if self._ws is None:
                self._ws = self._connect()
                if self._ws is None:
                    return  # 连接失败，放弃发送

            try:
                # 发送消息
                self._ws.send(_json.dumps(payload, ensure_ascii=False))
                logger.debug(f"WebSocket 事件推送成功: {event_type}")
            except Exception as e:
                # 发送失败，可能是连接断开，尝试重连
                logger.warning(f"WebSocket 发送失败: {e}，尝试重连...")
                self._close_connection()
                self._ws = self._connect()
                if self._ws is not None:
                    # 重连成功，重试发送
                    try:
                        self._ws.send(_json.dumps(payload, ensure_ascii=False))
                        logger.info(f"WebSocket 重连后发送成功: {event_type}")
                    except Exception as retry_error:
                        logger.error(f"WebSocket 重连后发送仍失败: {retry_error}")
                        self._close_connection()

        except Exception as e:
            # 捕获所有未预期的错误
            logger.error(f"WebSocket 推送发生未预期错误: {e}", exc_info=True)
            self._close_connection()

    def _close_connection(self) -> None:
        """关闭 WebSocket 连接（安全清理）。"""
        if self._ws is not None:
            try:
                self._ws.close()
                logger.debug("WebSocket 连接已关闭")
            except Exception as e:
                logger.warning(f"WebSocket 关闭时发生错误: {e}")
            finally:
                self._ws = None

    def close(self) -> None:
        """显式关闭 WebSocket 连接（资源清理）。"""
        self._close_connection()

    def __del__(self) -> None:
        """析构时自动清理资源。"""
        self._close_connection()

