"""Unit tests for PollStepExecutor.

Tests for the polling mechanism in apirun/executor/poll_executor.py
Following Google Python Style Guide.

Includes tests for:
- Basic polling functionality
- JSONPath condition checking
- Status code checking
- Backoff strategies
- Timeout handling
"""

import pytest
import time
from unittest.mock import Mock, patch
from apirun.executor.poll_executor import PollStepExecutor
from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager


class TestPollStepExecutor:
    """Tests for PollStepExecutor basic functionality."""

    def test_initialization(self):
        """Test PollStepExecutor initialization."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        assert executor.variable_manager == vm
        assert executor.step == step

    def test_check_jsonpath_condition_eq(self):
        """Test JSONPath condition with equals operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {"status": "ACTIVE"}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.status",
            "operator": "eq",
            "expect": "ACTIVE"
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_check_jsonpath_condition_ne(self):
        """Test JSONPath condition with not-equals operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {"status": "PENDING"}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.status",
            "operator": "ne",
            "expect": "ACTIVE"
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_check_jsonpath_condition_gt(self):
        """Test JSONPath condition with greater-than operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {"count": 10}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.count",
            "operator": "gt",
            "expect": 5
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_check_jsonpath_condition_contains(self):
        """Test JSONPath condition with contains operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {"tags": ["tag1", "tag2", "tag3"]}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.tags",
            "operator": "contains",
            "expect": "tag2"
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_check_jsonpath_condition_exists(self):
        """Test JSONPath condition with exists operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {"status": "ACTIVE"}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.status",
            "operator": "exists"
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_check_jsonpath_condition_not_exists(self):
        """Test JSONPath exists condition with missing field."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": {}}
        condition = {
            "type": "jsonpath",
            "path": "$.data.status",
            "operator": "exists"
        }

        result = executor._check_condition(response, condition)

        assert result is False

    def test_check_status_code_condition(self):
        """Test status code condition checking."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"response": {"status_code": 200}}
        condition = {
            "type": "status_code",
            "operator": "eq",
            "expect": 200
        }

        result = executor._check_condition(response, condition)

        assert result is True

    def test_compare_values_eq(self):
        """Test value comparison with equals."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        assert executor._compare_values("ACTIVE", "ACTIVE", "eq") is True
        assert executor._compare_values("ACTIVE", "PENDING", "eq") is False
        assert executor._compare_values(10, 10, "eq") is True

    def test_compare_values_numeric(self):
        """Test numeric value comparisons."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        assert executor._compare_values(10, 5, "gt") is True
        assert executor._compare_values(5, 10, "gt") is False
        assert executor._compare_values(5, 10, "lt") is True
        assert executor._compare_values(10, 10, "ge") is True
        assert executor._compare_values(10, 10, "le") is True

    def test_compare_values_contains(self):
        """Test contains operator."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        assert executor._compare_values(["a", "b", "c"], "b", "contains") is True
        assert executor._compare_values("hello world", "world", "contains") is True
        assert executor._compare_values(["a", "b"], "c", "contains") is False

    def test_unsupported_condition_type(self):
        """Test unsupported condition type raises error."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        response = {"data": "test"}
        condition = {"type": "unsupported", "path": "$"}

        with pytest.raises(ValueError, match="Unsupported condition type"):
            executor._check_condition(response, condition)

    def test_unsupported_operator(self):
        """Test unsupported operator raises error."""
        vm = VariableManager()
        step = TestStep(name="test_poll", type="poll")

        executor = PollStepExecutor(vm, step)

        with pytest.raises(ValueError, match="Unsupported operator"):
            executor._compare_values(1, 1, "unsupported")


class TestPollStepExecutorIntegration:
    """Integration tests for PollStepExecutor with mocked HTTP requests."""

    @patch('apirun.executor.poll_executor.APIExecutor')
    def test_polling_success_on_first_attempt(self, mock_api_executor):
        """Test polling succeeds on first attempt."""
        vm = VariableManager()
        step = TestStep(
            name="wait_for_ready",
            type="poll",
            url="http://example.com/status",
            method="GET",
            poll_config={
                "condition": {
                    "type": "jsonpath",
                    "path": "$.status",
                    "operator": "eq",
                    "expect": "ready"
                },
                "max_attempts": 3,
                "interval": 100,  # 100ms for fast testing
                "timeout": 5000,
                "backoff": "fixed"
            }
        )

        # Mock successful response on first attempt
        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.return_value = {"status": "ready"}

        executor = PollStepExecutor(vm, step)
        rendered_step = {
            "method": "GET",
            "url": "http://example.com/status",
            "poll_config": step.poll_config
        }

        result = executor._execute_step(rendered_step)

        assert result["success"] is True
        assert result["condition_met"] is True
        assert result["attempts"] == 1
        assert mock_api_instance._execute_step.call_count == 1

    @patch('apirun.executor.poll_executor.APIExecutor')
    def test_polling_success_after_multiple_attempts(self, mock_api_executor):
        """Test polling succeeds after multiple attempts."""
        vm = VariableManager()
        step = TestStep(
            name="wait_for_ready",
            type="poll",
            url="http://example.com/status",
            method="GET",
            poll_config={
                "condition": {
                    "type": "jsonpath",
                    "path": "$.status",
                    "operator": "eq",
                    "expect": "ready"
                },
                "max_attempts": 5,
                "interval": 50,  # 50ms for fast testing
                "timeout": 5000,
                "backoff": "fixed"
            }
        )

        # Mock responses: first 2 fail, 3rd succeeds
        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.side_effect = [
            {"status": "pending"},
            {"status": "pending"},
            {"status": "ready"}
        ]

        executor = PollStepExecutor(vm, step)
        rendered_step = {
            "method": "GET",
            "url": "http://example.com/status",
            "poll_config": step.poll_config
        }

        result = executor._execute_step(rendered_step)

        assert result["success"] is True
        assert result["attempts"] == 3
        assert mock_api_instance._execute_step.call_count == 3

    @patch('apirun.executor.poll_executor.APIExecutor')
    def test_polling_timeout_continue(self, mock_api_executor):
        """Test polling timeout with continue behavior."""
        vm = VariableManager()
        step = TestStep(
            name="wait_for_ready",
            type="poll",
            url="http://example.com/status",
            method="GET",
            poll_config={
                "condition": {
                    "type": "jsonpath",
                    "path": "$.status",
                    "operator": "eq",
                    "expect": "ready"
                },
                "max_attempts": 3,
                "interval": 50,
                "timeout": 1000,  # 1 second
                "backoff": "fixed"
            },
            on_timeout={
                "behavior": "continue",
                "message": "Operation timed out"
            }
        )

        # Mock always failing response
        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.return_value = {"status": "pending"}

        executor = PollStepExecutor(vm, step)
        rendered_step = {
            "method": "GET",
            "url": "http://example.com/status",
            "poll_config": step.poll_config,
            "on_timeout": step.on_timeout
        }

        result = executor._execute_step(rendered_step)

        assert result["success"] is False
        assert result["max_attempts_reached"] is True
        assert result["message"] == "Operation timed out"

    @patch('apirun.executor.poll_executor.APIExecutor')
    def test_polling_timeout_fail(self, mock_api_executor):
        """Test polling timeout with fail behavior (default)."""
        vm = VariableManager()
        step = TestStep(
            name="wait_for_ready",
            type="poll",
            url="http://example.com/status",
            method="GET",
            poll_config={
                "condition": {
                    "type": "jsonpath",
                    "path": "$.status",
                    "operator": "eq",
                    "expect": "ready"
                },
                "max_attempts": 3,
                "interval": 50,
                "timeout": 1000,
                "backoff": "fixed"
            },
            on_timeout={
                "behavior": "fail",
                "message": "Custom timeout message"
            }
        )

        # Mock always failing response
        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.return_value = {"status": "pending"}

        executor = PollStepExecutor(vm, step)
        rendered_step = {
            "method": "GET",
            "url": "http://example.com/status",
            "poll_config": step.poll_config,
            "on_timeout": step.on_timeout
        }

        with pytest.raises(TimeoutError, match="Custom timeout message"):
            executor._execute_step(rendered_step)


class TestBackoffStrategies:
    """Tests for different backoff strategies."""

    @patch('apirun.executor.poll_executor.APIExecutor')
    @patch('apirun.executor.poll_executor.time.sleep')
    def test_fixed_backoff(self, mock_sleep, mock_api_executor):
        """Test fixed backoff strategy."""
        vm = VariableManager()
        step = TestStep(
            name="test_poll",
            type="poll",
            poll_config={
                "condition": {"type": "jsonpath", "path": "$.status", "operator": "eq", "expect": "ready"},
                "max_attempts": 3,
                "interval": 100,
                "backoff": "fixed"
            }
        )

        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.side_effect = [
            {"status": "pending"},
            {"status": "pending"},
            {"status": "ready"}
        ]

        executor = PollStepExecutor(vm, step)
        executor._execute_step({"poll_config": step.poll_config})

        # With fixed backoff, should sleep the same interval each time
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert all(sleep_time == 0.1 for sleep_time in sleep_calls)

    @patch('apirun.executor.poll_executor.APIExecutor')
    @patch('apirun.executor.poll_executor.time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_api_executor):
        """Test exponential backoff strategy."""
        vm = VariableManager()
        step = TestStep(
            name="test_poll",
            type="poll",
            poll_config={
                "condition": {"type": "jsonpath", "path": "$.status", "operator": "eq", "expect": "ready"},
                "max_attempts": 4,
                "interval": 100,
                "backoff": "exponential"
            }
        )

        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.side_effect = [
            {"status": "pending"},
            {"status": "pending"},
            {"status": "pending"},
            {"status": "ready"}
        ]

        executor = PollStepExecutor(vm, step)
        executor._execute_step({"poll_config": step.poll_config})

        # With exponential backoff: 0.1, 0.2, 0.4
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [0.1, 0.2, 0.4]

    @patch('apirun.executor.poll_executor.APIExecutor')
    @patch('apirun.executor.poll_executor.time.sleep')
    def test_linear_backoff(self, mock_sleep, mock_api_executor):
        """Test linear backoff strategy."""
        vm = VariableManager()
        step = TestStep(
            name="test_poll",
            type="poll",
            poll_config={
                "condition": {"type": "jsonpath", "path": "$.status", "operator": "eq", "expect": "ready"},
                "max_attempts": 4,
                "interval": 100,
                "backoff": "linear"
            }
        )

        mock_api_instance = Mock()
        mock_api_executor.return_value = mock_api_instance
        mock_api_instance._execute_step.side_effect = [
            {"status": "pending"},
            {"status": "pending"},
            {"status": "pending"},
            {"status": "ready"}
        ]

        executor = PollStepExecutor(vm, step)
        executor._execute_step({"poll_config": step.poll_config})

        # With linear backoff: 0.1, 0.2, 0.3
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 0.1
        assert sleep_calls[1] == 0.2
        assert abs(sleep_calls[2] - 0.3) < 0.001  # Allow for floating point precision
