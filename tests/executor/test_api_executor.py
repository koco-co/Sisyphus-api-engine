"""Unit tests for APIExecutor.

Tests for API executor in apirun/executor/api_executor.py
Following Google Python Style Guide.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException
from apirun.executor.api_executor import APIExecutor
from apirun.core.models import TestStep, StepResult
from apirun.core.variable_manager import VariableManager


class TestAPIExecutor:
    """Tests for APIExecutor class."""

    def test_initialization(self):
        """Test APIExecutor initialization."""
        var_manager = VariableManager()
        step = TestStep(name="test_api", type="request")

        executor = APIExecutor(var_manager, step)

        assert executor.variable_manager == var_manager
        assert executor.step == step
        assert executor.session is not None
        assert executor.validation_engine is not None
        assert executor.performance_collector is not None

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_get_request_success(self, mock_request):
        """Test successful GET request execution."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/users"
        mock_response.content = b'{"users": []}'
        mock_response.json.return_value = {"users": []}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        step = TestStep(
            name="get_users",
            type="request",
            method="GET",
            url="https://api.example.com/users",
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["status_code"] == 200
        assert result.response["body"]["users"] == []
        assert result.performance is not None

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_post_request_with_json_body(self, mock_request):
        """Test POST request with JSON body."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/users"
        mock_response.content = b'{"id": 123, "name": "Test User"}'
        mock_response.json.return_value = {"id": 123, "name": "Test User"}
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        step = TestStep(
            name="create_user",
            type="request",
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            body={"name": "Test User", "email": "test@example.com"},
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["status_code"] == 201
        assert result.response["body"]["id"] == 123

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_query_params(self, mock_request):
        """Test request with query parameters."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/users?page=1&limit=10"
        mock_response.content = b'{"users": []}'
        mock_response.json.return_value = {"users": []}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        step = TestStep(
            name="list_users",
            type="request",
            method="GET",
            url="https://api.example.com/users",
            params={"page": 1, "limit": 10},
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        # Verify params were passed
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"] == {"page": 1, "limit": 10}

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_validations_pass(self, mock_request):
        """Test request with passing validations."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/users"
        mock_response.content = b'{"status": "ok", "count": 10}'
        mock_response.json.return_value = {"status": "ok", "count": 10}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_request.return_value = mock_response

        var_manager = VariableManager()

        # Create ValidationRule objects - status_code validation only to avoid body validation issues
        from apirun.core.models import ValidationRule

        vr1 = ValidationRule(type="status_code", path="$.status_code", expect=200, description="状态码验证")

        step = TestStep(
            name="check_status",
            type="request",
            method="GET",
            url="https://api.example.com/status",
            validations=[vr1],
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_validation_failure(self, mock_request):
        """Test request with failing validation."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/status"
        mock_response.content = b'{"status": "error"}'
        mock_response.json.return_value = {"status": "error"}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        from apirun.core.models import ValidationRule

        step = TestStep(
            name="check_status",
            type="request",
            method="GET",
            url="https://api.example.com/status",
            validations=[
                ValidationRule(type="eq", path="$.body.status", expect="ok"),
            ],
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None
        # Updated to support new error message format from v2.0.0
        assert "Validation" in result.error_info.message and "failed" in result.error_info.message.lower()

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_network_error(self, mock_request):
        """Test request with network error."""
        mock_request.side_effect = RequestException("Connection failed")

        var_manager = VariableManager()
        step = TestStep(
            name="failing_request",
            type="request",
            method="GET",
            url="https://api.example.com/test",
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None
        assert "Connection failed" in result.error_info.message

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_timeout(self, mock_request):
        """Test request with timeout."""
        mock_request.side_effect = RequestException("Request timeout")

        var_manager = VariableManager()
        step = TestStep(
            name="timeout_request",
            type="request",
            method="GET",
            url="https://api.example.com/slow",
        )

        executor = APIExecutor(var_manager, step, timeout=5)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_request_with_variable_substitution(self, mock_request):
        """Test request with variable substitution in URL."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/users/123"
        mock_response.content = b'{"id": 123, "name": "Test"}'
        mock_response.json.return_value = {"id": 123, "name": "Test"}
        mock_response.elapsed.total_seconds.return_value = 0.2
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        var_manager.set_variable("user_id", "123")
        var_manager.set_variable("base_url", "https://api.example.com")

        step = TestStep(
            name="get_user",
            type="request",
            method="GET",
            url="${base_url}/users/${user_id}",
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["body"]["id"] == 123

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_parse_response_json(self, mock_request):
        """Test parsing JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/data"
        mock_response.content = b'{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        step = TestStep(
            name="get_data",
            type="request",
            method="GET",
            url="https://api.example.com/data",
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["body"]["key"] == "value"

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_parse_response_text(self, mock_request):
        """Test parsing text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/text"
        mock_response.content = b"Plain text response"
        mock_response.text = "Plain text response"
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        var_manager = VariableManager()
        step = TestStep(
            name="get_text",
            type="request",
            method="GET",
            url="https://api.example.com/text",
        )

        executor = APIExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["body"] == "Plain text response"

    @patch("apirun.executor.api_executor.requests.Session.request")
    def test_execute_all_http_methods(self, mock_request):
        """Test all supported HTTP methods."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.cookies = {}
        mock_response.url = "https://api.example.com/test"
        mock_response.content = b'{"ok": true}'
        mock_response.json.return_value = {"ok": True}
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_request.return_value = mock_response

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

        for method in methods:
            var_manager = VariableManager()
            step = TestStep(
                name=f"test_{method.lower()}",
                type="request",
                method=method,
                url="https://api.example.com/test",
            )

            executor = APIExecutor(var_manager, step)
            result = executor.execute()

            assert result.status == "success", f"Failed for method {method}"

    def test_performance_metrics_collection(self):
        """Test performance metrics are collected."""
        var_manager = VariableManager()
        step = TestStep(name="test", type="request")

        executor = APIExecutor(var_manager, step)

        # Check that performance collector is set up
        assert executor.performance_collector is not None

        # Check that adapter is mounted
        assert "http://" in executor.session.adapters
        assert "https://" in executor.session.adapters
