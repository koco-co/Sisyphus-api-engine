"""WebSocket 事件发布器单元测试（WS-001～WS-004）"""

from apirun.websocket.publisher import NoOpPublisher, WsPublisher


def test_noop_publisher_emit():
    """NoOpPublisher.emit 不抛异常。"""
    p = NoOpPublisher()
    p.emit("scenario_start", data={"name": "test"})
    p.emit("step_done", step_index=0, status="passed")


def test_ws_publisher_emit_no_connection():
    """WsPublisher 在无连接或未安装 websocket 时不抛异常（WS-003）。"""
    p = WsPublisher("ws://localhost:9999")
    p.emit("scenario_start", data={})
    p.emit("step_done", step_index=0, status="passed")
