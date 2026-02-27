"""事件发布器 — 场景/步骤开始与完成事件推送（WS-001～WS-003）"""

from datetime import datetime, timezone
from typing import Any, Protocol


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self._ws: Any = None

    def emit(
        self,
        event_type: str,
        *,
        step_index: int | None = None,
        status: str | None = None,
        timestamp: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "event_type": event_type,
            "step_index": step_index,
            "status": status,
            "timestamp": timestamp or _timestamp(),
            "data": data or {},
        }
        try:
            import json as _json
            # 可选依赖：仅当安装了 websocket-client 时实际发送
            try:
                import websocket
            except ImportError:
                return
            if self._ws is None:
                self._ws = websocket.create_connection(self.url)
            self._ws.send(_json.dumps(payload, ensure_ascii=False))
        except Exception:
            # WS-003: 连接失败或发送失败时降级，不抛异常
            self._ws = None
