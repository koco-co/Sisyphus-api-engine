"""WebSocket 发布器增强测试"""

import sys
from unittest.mock import MagicMock, patch


def test_noop_publisher():
    """测试 NoOpPublisher 不推送任何内容"""

    from apirun.websocket.publisher import NoOpPublisher

    publisher = NoOpPublisher()

    # 不应该抛出任何异常
    publisher.emit("test_event", step_index=0, status="passed")
    publisher.emit("another_event", data={"key": "value"})


def test_ws_publisher_without_websocket_client():
    """测试未安装 websocket-client 时不会报错"""

    # 模拟 websocket-client 未安装
    with patch.dict(sys.modules, {"websocket": None}):
        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000")

        # 不应该抛出异常
        publisher.emit("test_event", step_index=0, status="passed")


def test_ws_publisher_connection_failure():
    """测试 WebSocket 连接失败时的降级处理"""

    # 模拟 websocket 模块存在但连接失败
    fake_websocket = MagicMock()
    fake_websocket.create_connection.side_effect = ConnectionRefusedError("Connection refused")

    with patch.dict(sys.modules, {"websocket": fake_websocket}):
        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000", max_retries=2)

        # 不应该抛出异常，应该记录错误并返回
        publisher.emit("test_event", step_index=0, status="passed")


def test_ws_publisher_send_failure_with_reconnect():
    """测试发送失败时会尝试重连"""

    connection_count = {"value": 0}
    send_calls = []

    class FakeWebSocket:
        def __init__(self, url):
            connection_count["value"] += 1

        def send(self, data):
            send_calls.append({"connection": connection_count["value"], "data": data})
            # 每次发送都失败
            raise ConnectionError("Connection lost")

        def close(self):
            pass

    # 第一次调用返回第一个连接对象，后续调用返回新的连接对象
    connections = [FakeWebSocket("ws://localhost")]

    def create_connection(url, timeout=None):
        ws = FakeWebSocket(url)
        connections.append(ws)
        return ws

    fake_websocket = MagicMock()
    fake_websocket.create_connection.side_effect = create_connection

    with patch.dict(sys.modules, {"websocket": fake_websocket}):
        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000", max_retries=2)

        # 发送失败后会尝试重连（虽然重连后的发送也会失败）
        publisher.emit("test_event", step_index=0, status="passed")

        # 至少应该创建 2 个连接对象（第一次 + 重连）
        assert connection_count["value"] >= 2, f"应该至少尝试 2 次连接，实际: {connection_count['value']}"
        # 至少应该尝试 2 次发送（第一次 + 重连后）
        assert len(send_calls) >= 2, f"应该至少尝试 2 次发送，实际: {len(send_calls)}"


def test_ws_publisher_close():
    """测试显式关闭连接"""

    closed = {"value": False}

    class FakeWebSocket:
        def close(self):
            closed["value"] = True

    fake_websocket = MagicMock()
    fake_websocket.create_connection.return_value = FakeWebSocket()

    with patch.dict(sys.modules, {"websocket": fake_websocket}):
        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000")
        publisher.emit("test_event")  # 建立连接
        publisher.close()  # 关闭连接

        assert closed["value"], "连接应该被关闭"


def test_ws_publisher_payload_format():
    """测试推送消息格式"""

    sent_payloads = []

    class FakeWebSocket:
        def send(self, data):
            sent_payloads.append(data)

        def close(self):
            pass

    fake_websocket = MagicMock()
    fake_websocket.create_connection.return_value = FakeWebSocket()

    with patch.dict(sys.modules, {"websocket": fake_websocket}):
        import json

        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000")

        publisher.emit(
            "step_start",
            step_index=5,
            status="running",
            data={"message": "Testing"},
        )

        assert len(sent_payloads) == 1

        payload = json.loads(sent_payloads[0])
        assert payload["event_type"] == "step_start"
        assert payload["step_index"] == 5
        assert payload["status"] == "running"
        assert payload["data"] == {"message": "Testing"}
        assert "timestamp" in payload


def test_ws_publisher_reconnect_limit():
    """测试重连次数限制"""

    connection_attempts = {"value": 0}

    def create_connection_that_fails(url, timeout=None):
        connection_attempts["value"] += 1
        raise ConnectionError("Always fails")

    fake_websocket = MagicMock()
    fake_websocket.create_connection.side_effect = create_connection_that_fails

    with patch.dict(sys.modules, {"websocket": fake_websocket}):
        from apirun.websocket.publisher import WsPublisher

        publisher = WsPublisher("ws://localhost:8000", max_retries=3)

        # 应该尝试连接 3 次
        publisher.emit("test_event")

        assert connection_attempts["value"] == 3, f"应该尝试 3 次，实际: {connection_attempts['value']}"
