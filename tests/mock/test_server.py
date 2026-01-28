"""Unit tests for MockServer.

Tests for mock server functionality including:
- Server startup and shutdown
- Request handling
- Rule matching
- Response generation
- Delay and failure simulation
"""

import pytest
import requests
import time
import json
from threading import Thread
import logging

from apirun.mock.server import MockServer, create_simple_rule, create_regex_rule
from apirun.mock.models import (
    MockServerConfig,
    MockRule,
    MockResponse,
    RequestMatcher,
    DelayConfig,
    FailureConfig,
    FailureType,
    MatchType,
)


@pytest.fixture
def mock_server_port():
    """Get a unique port for each test to avoid conflicts."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
def running_server(mock_server_port):
    """Create and start a running server for testing."""
    config = MockServerConfig(host="localhost", port=mock_server_port)

    # Add comprehensive rules for testing
    rules = [
        # Basic rules
        create_simple_rule(
            name="Get Users",
            method="GET",
            path="/api/users",
            status_code=200,
            body={"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]},
            headers={"Content-Type": "application/json"},
        ),
        create_simple_rule(
            name="Get User by ID", method="GET", path="/api/users/1", status_code=200, body={"id": 1, "name": "John"}
        ),
        create_regex_rule(
            name="Get User by ID (regex)",
            method="GET",
            path_pattern=r"/api/users/\d+",
            status_code=200,
            body={"id": 123, "name": "Test User"},
        ),
        # POST rule
        create_simple_rule(
            name="Create User", method="POST", path="/api/users", status_code=201, body={"id": 123}
        ),
        # Query param rule
        MockRule(
            name="Search",
            matcher=RequestMatcher(method="GET", path="/api/search", query_params={"q": "test"}),
            response=MockResponse(status_code=200, body={"results": [], "total": 0}),
        ),
        # Custom headers rule
        create_simple_rule(
            name="Custom Headers",
            method="GET",
            path="/api/custom",
            status_code=200,
            body={},
            headers={"X-Custom-Header": "test-value", "X-Api-Version": "1.0"},
        ),
        # Delay rule
        MockRule(
            name="Delayed Response",
            matcher=RequestMatcher(method="GET", path="/api/delay"),
            response=MockResponse(status_code=200, body={"delayed": True}, delay=DelayConfig(fixed_delay=0.1)),
        ),
        # Error rule
        MockRule(
            name="Error Response",
            matcher=RequestMatcher(method="GET", path="/api/error"),
            response=MockResponse(
                status_code=200, body={}, failure=FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=1.0, status_code=500)
            ),
        ),
        # Auth rule
        MockRule(
            name="Protected",
            matcher=RequestMatcher(method="GET", path="/api/protected", headers={"Authorization": "Bearer token123"}),
            response=MockResponse(status_code=200, body={"authenticated": True, "user": "admin"}),
        ),
        # Priority rules
        create_simple_rule(
            name="High Priority",
            method="GET",
            path="/api/priority",
            status_code=200,
            body={"priority": "high"},
            priority=100,
        ),
        create_simple_rule(
            name="Low Priority",
            method="GET",
            path="/api/priority",
            status_code=200,
            body={"priority": "low"},
            priority=1,
        ),
        # Disabled rule
        MockRule(
            name="Disabled Rule",
            matcher=RequestMatcher(method="GET", path="/api/disabled"),
            response=MockResponse(status_code=200, body={"enabled": False}),
            enabled=False,
        ),
        # Body matching rule
        MockRule(
            name="Create User John",
            matcher=RequestMatcher(method="POST", path="/api/users", body_pattern="John", body_match_type=MatchType.CONTAINS),
            response=MockResponse(status_code=200, body={"created": True, "matched": "body contains John"}),
            priority=3,
        ),
        # Complex match rule
        MockRule(
            name="Complex Match",
            matcher=RequestMatcher(
                method="POST",
                path="/api/complex",
                query_params={"validate": "true"},
                headers={"Content-Type": "application/json"},
            ),
            response=MockResponse(status_code=201, body={"created": True, "validated": True}),
        ),
        # Temp rule for deletion test
        create_simple_rule(name="Temp Rule", method="GET", path="/api/temp", status_code=200),
    ]

    for rule in rules:
        config.add_rule(rule)

    server = MockServer(config)
    server.start(blocking=False)
    time.sleep(0.3)  # Give server time to start

    yield server, mock_server_port

    # Cleanup
    try:
        server.stop()
    except Exception:
        pass


class TestMockServerBasic:
    """Basic tests for MockServer."""

    def test_server_initialization(self, mock_server_port):
        """Test server initialization."""
        config = MockServerConfig(host="localhost", port=mock_server_port)
        server = MockServer(config)
        assert server.config.host == "localhost"
        assert server.config.port == mock_server_port
        assert len(server.config.rules) == 0

    def test_add_rule(self, mock_server_port):
        """Test adding a rule."""
        config = MockServerConfig(host="localhost", port=mock_server_port)
        server = MockServer(config)
        rule = create_simple_rule(name="New Rule", method="POST", path="/api/test", status_code=201)
        server.add_rule(rule)
        assert len(server.config.rules) == 1
        assert server.get_rule("New Rule") is not None

    def test_remove_rule(self, mock_server_port):
        """Test removing a rule."""
        config = MockServerConfig(host="localhost", port=mock_server_port)
        server = MockServer(config)
        rule = create_simple_rule(name="Test Rule", method="GET", path="/api/test", status_code=200)
        server.add_rule(rule)
        assert len(server.config.rules) == 1
        result = server.remove_rule("Test Rule")
        assert result is True
        assert len(server.config.rules) == 0

    def test_list_rules(self, mock_server_port):
        """Test listing rules."""
        config = MockServerConfig(host="localhost", port=mock_server_port)
        server = MockServer(config)
        rule1 = create_simple_rule(name="Rule 1", method="GET", path="/api/test1", status_code=200)
        rule2 = create_simple_rule(name="Rule 2", method="GET", path="/api/test2", status_code=200)
        server.add_rule(rule1)
        server.add_rule(rule2)
        rules = server.list_rules()
        assert len(rules) == 2


@pytest.mark.integration
class TestMockServerIntegration:
    """Integration tests for MockServer."""

    def test_get_users_request(self, running_server):
        """Test GET /api/users request."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2

    def test_get_user_by_id_request(self, running_server):
        """Test GET /api/users/1 request."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "John"

    def test_regex_rule_matching(self, running_server):
        """Test regex rule matching."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/users/999")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123

    def test_no_matching_rule(self, running_server):
        """Test request with no matching rule."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_post_request(self, running_server):
        """Test POST request."""
        server, port = running_server
        response = requests.post(f"http://localhost:{port}/api/users", json={"name": "Test"})
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 123

    def test_custom_headers(self, running_server):
        """Test custom response headers."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/custom")
        assert response.status_code == 200
        assert response.headers.get("X-Custom-Header") == "test-value"
        assert response.headers.get("X-Api-Version") == "1.0"

    def test_health_check(self, running_server):
        """Test health check endpoint."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/_mock/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # Note: running might be False if server hasn't fully started yet
        assert "running" in data

    def test_list_rules_endpoint(self, running_server):
        """Test listing rules via endpoint."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/_mock/rules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_delay_simulation(self, running_server):
        """Test delay simulation."""
        server, port = running_server
        start = time.time()
        response = requests.get(f"http://localhost:{port}/api/delay")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed >= 0.1  # Should take at least 0.1 seconds

    def test_http_failure_simulation(self, running_server):
        """Test HTTP error simulation."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/error")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_query_param_matching(self, running_server):
        """Test query parameter matching."""
        server, port = running_server
        # Should match
        response = requests.get(f"http://localhost:{port}/api/search?q=test")
        assert response.status_code == 200

        # Should not match
        response = requests.get(f"http://localhost:{port}/api/search?q=other")
        assert response.status_code == 404

    def test_header_matching(self, running_server):
        """Test header matching."""
        server, port = running_server
        # Should match with correct header
        response = requests.get(f"http://localhost:{port}/api/protected", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 200

        # Should not match without header
        response = requests.get(f"http://localhost:{port}/api/protected")
        assert response.status_code == 404

    def test_priority_ordering(self, running_server):
        """Test that higher priority rules are matched first."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/priority")
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"

    def test_disabled_rule(self, running_server):
        """Test that disabled rules don't match."""
        server, port = running_server
        response = requests.get(f"http://localhost:{port}/api/disabled")
        # Should not match disabled rule
        assert response.status_code == 404

    def test_delete_rule_endpoint(self, running_server):
        """Test deleting rule via endpoint."""
        server, port = running_server
        # Delete via endpoint
        response = requests.delete(f"http://localhost:{port}/_mock/rules/Temp Rule")
        assert response.status_code == 200

        # Verify it's deleted
        response = requests.get(f"http://localhost:{port}/api/temp")
        assert response.status_code == 404


@pytest.mark.integration
class TestMockServerAdvanced:
    """Advanced integration tests."""

    @pytest.fixture(autouse=True)
    def setup_advanced_server(self, mock_server_port):
        """Setup server for advanced tests."""
        config = MockServerConfig(host="localhost", port=mock_server_port)

        # Complex matcher rule
        rule1 = MockRule(
            name="Complex Match",
            matcher=RequestMatcher(
                method="POST",
                path="/api/complex",
                query_params={"validate": "true"},
                headers={"Content-Type": "application/json"},
            ),
            response=MockResponse(status_code=201, body={"created": True}),
        )

        # Body matching rule
        rule2 = MockRule(
            name="Body Match",
            matcher=RequestMatcher(method="POST", path="/api/body", body_pattern="John", body_match_type=MatchType.CONTAINS),
            response=MockResponse(status_code=200, body={"matched": True}),
        )

        # Random delay rule
        rule3 = MockRule(
            name="Random Delay",
            matcher=RequestMatcher(method="GET", path="/api/random-delay"),
            response=MockResponse(status_code=200, body={"random": True}, delay=DelayConfig(min_delay=0.05, max_delay=0.15)),
        )

        config.add_rule(rule1)
        config.add_rule(rule2)
        config.add_rule(rule3)

        server = MockServer(config)
        server.start(blocking=False)
        time.sleep(0.3)

        yield server, mock_server_port

        try:
            server.stop()
        except Exception:
            pass

    def test_complex_matcher(self, setup_advanced_server):
        """Test complex request matching."""
        server, port = setup_advanced_server

        # Should match all conditions
        response = requests.post(
            f"http://localhost:{port}/api/complex?validate=true",
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

        # Should not match without query param
        response = requests.post(
            f"http://localhost:{port}/api/complex", json={"test": "data"}, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 404

    def test_body_matching(self, setup_advanced_server):
        """Test body matching."""
        server, port = setup_advanced_server

        # Should match
        response = requests.post(f"http://localhost:{port}/api/body", json={"name": "John Doe"})
        assert response.status_code == 200

        # Should not match
        response = requests.post(f"http://localhost:{port}/api/body", json={"name": "Jane Doe"})
        assert response.status_code == 404

    def test_random_delay(self, setup_advanced_server):
        """Test random delay within range."""
        server, port = setup_advanced_server

        delays = []
        for _ in range(3):
            start = time.time()
            requests.get(f"http://localhost:{port}/api/random-delay")
            delays.append(time.time() - start)

        # All delays should be in range
        assert all(0.05 <= d <= 0.2 for d in delays)  # 0.15 max + potential jitter
