#!/usr/bin/env python3
"""用于测试的简易 Mock HTTP 服务器"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class MockHandler(BaseHTTPRequestHandler):
    """模拟 API 响应"""

    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_empty(self, status: int = 200):
        """发送空响应"""
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # /api/v1/users - 用户列表
        if path == "/api/v1/users":
            self._send_json(
                {
                    "code": 0,
                    "message": "OK",
                    "data": [
                        {"id": 1, "name": "Alice", "email": "alice@example.com"},
                        {"id": 2, "name": "Bob", "email": "bob@example.com"},
                    ],
                    "active": True,
                }
            )
            return

        # /api/users?email=xxx - 数据驱动测试
        if path == "/api/users":
            email = query.get("email", [""])[0]
            self._send_json({"code": 0, "message": "OK", "data": {"email": email, "found": True}})
            return

        # /api/status - 状态检查
        if path == "/api/status":
            self._send_json({"code": 0, "message": "OK", "active": True})
            return

        # /api/v1/users/:id - 单个用户
        if path.startswith("/api/v1/users/"):
            self._send_json({"id": 1, "name": "Alice", "email": "alice@example.com"})
            return

        # /api/items/:id - 数据驱动测试 (CSV)
        if path.startswith("/api/items/"):
            item_id = path.split("/")[-1]
            items = {"1": {"id": 1, "name": "Alice"}, "2": {"id": 2, "name": "Bob"}}
            data = items.get(item_id, {"id": item_id, "name": "Unknown"})
            self._send_json({"code": 0, "data": data})
            return

        # /api/me - 当前用户信息
        if path == "/api/me":
            self._send_json({"id": 1, "name": "Test User", "email": "test@example.com"})
            return

        # /api/health - 健康检查
        if path == "/api/health":
            self._send_json({"status": "ok", "database": "connected"})
            return

        # 未找到路径
        self._send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        """处理 POST 请求"""
        path = urlparse(self.path).path

        # /api/register - 注册
        if path == "/api/register":
            self._send_json(
                {"id": 1, "email": "test@example.com", "token": "mock-token-123456"}, status=201
            )
            return

        # /api/login - 登录
        if path == "/api/login":
            self._send_json({"token": "mock-token-abcdef", "user": {"id": 1, "name": "Test User"}})
            return

        self._send_json({"error": "Not Found"}, 404)

    def log_message(self, format: str, *args):
        """抑制默认日志输出"""
        pass


def main():
    """启动 Mock 服务器"""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    server = HTTPServer(("localhost", port), MockHandler)
    print(f"🚀 Mock API 服务器已启动: http://localhost:{port}", file=sys.stderr)
    print("📝 按 Ctrl+C 停止服务器", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ 服务器已停止", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
