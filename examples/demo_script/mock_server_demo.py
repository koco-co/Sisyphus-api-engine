#!/usr/bin/env python3
"""Mock服务器演示脚本.

演示如何使用内置Mock服务器进行API测试。
运行此脚本后，可以使用 examples/11_Mock服务器测试.yaml 进行测试。
"""

import time
from apirun.mock import MockServer, MockServerConfig, MockRule, MockResponse
from apirun.mock.models import RequestMatcher, MatchType, DelayConfig, FailureConfig, FailureType
from apirun.mock.server import create_simple_rule, create_regex_rule


def setup_mock_server() -> MockServer:
    """创建并配置Mock服务器."""
    # 创建服务器配置
    config = MockServerConfig(host="localhost", port=8888)

    # 1. 简单规则：获取用户列表
    rule1 = create_simple_rule(
        name="Get Users",
        method="GET",
        path="/api/users",
        status_code=200,
        body={"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]},
        headers={"Content-Type": "application/json"},
    )
    config.add_rule(rule1)

    # 2. 精确路径匹配：获取单个用户
    rule2 = create_simple_rule(
        name="Get User by ID",
        method="GET",
        path="/api/users/1",
        status_code=200,
        body={"id": 1, "name": "John", "email": "john@example.com"},
    )
    config.add_rule(rule2)

    # 3. 正则表达式匹配：任意用户ID
    rule3 = create_regex_rule(
        name="Get User by ID (regex)",
        method="GET",
        path_pattern=r"/api/users/\d+",
        status_code=200,
        body={"id": 123, "name": "Test User", "email": "test@example.com"},
        priority=5,
    )
    config.add_rule(rule3)

    # 4. 创建用户
    rule4 = create_simple_rule(
        name="Create User",
        method="POST",
        path="/api/users",
        status_code=201,
        body={"id": 123, "created": True},
        headers={"Content-Type": "application/json"},
    )
    config.add_rule(rule4)

    # 5. 查询参数匹配
    matcher5 = RequestMatcher(method="GET", path="/api/search", query_params={"q": "test"})
    response5 = MockResponse(status_code=200, body={"results": [], "total": 0})
    rule5 = MockRule(name="Search", matcher=matcher5, response=response5)
    config.add_rule(rule5)

    # 6. 自定义响应头
    rule6 = create_simple_rule(
        name="Custom Headers",
        method="GET",
        path="/api/custom",
        status_code=200,
        body={},
        headers={"X-Custom-Header": "test-value", "X-Api-Version": "1.0"},
    )
    config.add_rule(rule6)

    # 7. 延迟模拟
    matcher7 = RequestMatcher(method="GET", path="/api/delay")
    response7 = MockResponse(
        status_code=200, body={"delayed": True}, delay=DelayConfig(fixed_delay=0.2)
    )
    rule7 = MockRule(name="Delayed Response", matcher=matcher7, response=response7)
    config.add_rule(rule7)

    # 8. HTTP错误模拟
    matcher8 = RequestMatcher(method="GET", path="/api/error")
    failure8 = FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=1.0, status_code=500)
    response8 = MockResponse(status_code=200, body={}, failure=failure8)
    rule8 = MockRule(name="Error Response", matcher=matcher8, response=response8)
    config.add_rule(rule8)

    # 9. 需要认证的接口
    matcher9 = RequestMatcher(
        method="GET", path="/api/protected", headers={"Authorization": "Bearer token123"}
    )
    response9 = MockResponse(status_code=200, body={"authenticated": True, "user": "admin"})
    rule9 = MockRule(name="Protected", matcher=matcher9, response=response9)
    config.add_rule(rule9)

    # 10. 优先级测试 - 高优先级
    rule10 = create_simple_rule(
        name="High Priority",
        method="GET",
        path="/api/priority",
        status_code=200,
        body={"priority": "high"},
        priority=100,
    )
    config.add_rule(rule10)

    # 11. 优先级测试 - 低优先级
    rule11 = create_simple_rule(
        name="Low Priority",
        method="GET",
        path="/api/priority",
        status_code=200,
        body={"priority": "low"},
        priority=1,
    )
    config.add_rule(rule11)

    # 12. Body匹配
    matcher12 = RequestMatcher(
        method="POST", path="/api/users", body_pattern="John", body_match_type=MatchType.CONTAINS
    )
    response12 = MockResponse(status_code=200, body={"created": True, "matched": "body contains John"})
    rule12 = MockRule(name="Create User John", matcher=matcher12, response=response12, priority=3)
    config.add_rule(rule12)

    # 13. 复杂匹配条件
    matcher13 = RequestMatcher(
        method="POST",
        path="/api/complex",
        query_params={"validate": "true"},
        headers={"Content-Type": "application/json"},
    )
    response13 = MockResponse(status_code=201, body={"created": True, "validated": True})
    rule13 = MockRule(name="Complex Match", matcher=matcher13, response=response13)
    config.add_rule(rule13)

    # 创建服务器
    server = MockServer(config)

    return server


def main():
    """主函数."""
    print("=" * 60)
    print("Sisyphus API Engine - Mock服务器演示")
    print("=" * 60)
    print()

    # 设置并启动服务器
    print("正在启动Mock服务器...")
    server = setup_mock_server()
    server.start(blocking=False)

    print(f"✓ Mock服务器已启动: http://localhost:8888")
    print()
    print("已配置的规则:")
    print("-" * 60)

    for i, rule in enumerate(server.config.rules, 1):
        status = "✓" if rule.enabled else "✗"
        print(f"{i:2d}. [{status}] {rule.name}")
        print(f"      方法: {rule.matcher.method}, 路径: {rule.matcher.path}")
        print(f"      优先级: {rule.priority}, 描述: {rule.description}")

    print()
    print("-" * 60)
    print("可用的管理端点:")
    print("  GET  http://localhost:8888/_mock/health   - 健康检查")
    print("  GET  http://localhost:8888/_mock/rules    - 列出所有规则")
    print(" POST  http://localhost:8888/_mock/rules    - 添加新规则")
    print(" DELETE http://localhost:8888/_mock/rules/<name> - 删除规则")
    print()
    print("-" * 60)
    print("测试示例:")
    print("  1. 运行测试用例:")
    print("     sisyphus-api-engine --cases examples/11_Mock服务器测试.yaml")
    print()
    print("  2. 使用curl测试:")
    print("     curl http://localhost:8888/api/users")
    print("     curl http://localhost:8888/api/users/1")
    print("     curl -X POST http://localhost:8888/api/users -d '{\"name\":\"Alice\"}'")
    print()
    print("-" * 60)
    print("按 Ctrl+C 停止服务器")
    print()

    try:
        # 保持服务器运行
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("正在停止Mock服务器...")
        server.stop()
        print("✓ Mock服务器已停止")


if __name__ == "__main__":
    main()
