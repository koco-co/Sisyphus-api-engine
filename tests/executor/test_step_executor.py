"""Unit tests for StepExecutor.

Tests for step executor base class in apirun/executor/step_executor.py
Following Google Python Style Guide.
"""

import pytest
from datetime import datetime
from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep, StepResult, ErrorCategory
from apirun.core.variable_manager import VariableManager


class MockStepExecutor(StepExecutor):
    """Mock executor for testing StepExecutor base class."""

    def _execute_step(self, rendered_step):
        # Simple implementation that returns success
        return type(
            "Result",
            (),
            {
                "response": {"status": "ok"},
                "performance": self._create_performance_metrics(total_time=100),
            },
        )()


class TestStepExecutor:
    """Tests for StepExecutor base class."""

    def test_initialization(self):
        """Test StepExecutor initialization."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        assert executor.variable_manager == var_manager
        assert executor.step == step
        assert executor.timeout == 30
        assert executor.retry_times == 0

    def test_initialization_with_custom_timeout_and_retry(self):
        """Test initialization with custom timeout and retry."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", timeout=60, retry_times=3)

        executor = MockStepExecutor(var_manager, step, timeout=120, retry_times=5)

        assert executor.timeout == 60  # step timeout takes precedence
        assert executor.retry_times == 3  # step retry_times takes precedence

    def test_execute_success(self):
        """Test successful step execution."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.name == "test_step"
        assert result.response == {"status": "ok"}
        assert result.performance is not None

    def test_should_execute_no_conditions(self):
        """Test _should_execute with no conditions."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        assert executor._should_execute() is True

    def test_should_execute_with_skip_if_true(self):
        """Test _should_execute with skip_if=True."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", skip_if="true")

        executor = MockStepExecutor(var_manager, step)

        assert executor._should_execute() is False

    def test_should_execute_with_skip_if_false(self):
        """Test _should_execute with skip_if=false."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", skip_if="false")

        executor = MockStepExecutor(var_manager, step)

        assert executor._should_execute() is True

    def test_should_execute_with_only_if_true(self):
        """Test _should_execute with only_if=true."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", only_if="true")

        executor = MockStepExecutor(var_manager, step)

        assert executor._should_execute() is True

    def test_should_execute_with_only_if_false(self):
        """Test _should_execute with only_if=false."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", only_if="false")

        executor = MockStepExecutor(var_manager, step)

        assert executor._should_execute() is False

    def test_should_execute_with_depends_on_success(self):
        """Test _should_execute with depends_on and successful dependency."""
        var_manager = VariableManager()

        # Create successful dependency result
        dep_result = StepResult(
            name="dep_step",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        step = TestStep(name="test_step", type="request", depends_on=["dep_step"])

        executor = MockStepExecutor(var_manager, step, previous_results=[dep_result])

        assert executor._should_execute() is True

    def test_should_execute_with_depends_on_failure(self):
        """Test _should_execute with depends_on and failed dependency."""
        var_manager = VariableManager()

        # Create failed dependency result
        dep_result = StepResult(
            name="dep_step",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        step = TestStep(name="test_step", type="request", depends_on=["dep_step"])

        executor = MockStepExecutor(var_manager, step, previous_results=[dep_result])

        assert executor._should_execute() is False

    def test_should_execute_with_depends_on_not_found(self):
        """Test _should_execute with depends_on and dependency not found."""
        var_manager = VariableManager()

        step = TestStep(name="test_step", type="request", depends_on=["missing_step"])

        executor = MockStepExecutor(var_manager, step, previous_results=[])

        assert executor._should_execute() is False

    def test_render_step_basic(self):
        """Test _render_step with basic fields."""
        var_manager = VariableManager()
        var_manager.set_variable("base_url", "https://api.example.com")

        step = TestStep(
            name="test_step",
            type="request",
            method="GET",
            url="${base_url}/users",
        )

        executor = MockStepExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["name"] == "test_step"
        assert rendered["type"] == "request"
        assert rendered["method"] == "GET"
        assert rendered["url"] == "https://api.example.com/users"

    def test_render_step_with_params(self):
        """Test _render_step with params."""
        var_manager = VariableManager()
        var_manager.set_variable("user_id", "123")

        step = TestStep(
            name="test_step",
            type="request",
            url="/users",
            params={"id": "${user_id}"},
        )

        executor = MockStepExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["params"] == {"id": "123"}

    def test_render_step_with_headers(self):
        """Test _render_step with headers."""
        var_manager = VariableManager()
        var_manager.set_variable("token", "abc123")

        step = TestStep(
            name="test_step",
            type="request",
            url="/users",
            headers={"Authorization": "Bearer ${token}"},
        )

        executor = MockStepExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["headers"] == {"Authorization": "Bearer abc123"}

    def test_render_step_with_body_dict(self):
        """Test _render_step with dict body."""
        var_manager = VariableManager()
        var_manager.set_variable("username", "testuser")

        step = TestStep(
            name="test_step",
            type="request",
            url="/users",
            body={"name": "${username}", "email": "test@example.com"},
        )

        executor = MockStepExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["body"]["name"] == "testuser"
        assert rendered["body"]["email"] == "test@example.com"

    def test_render_step_with_body_string(self):
        """Test _render_step with string body."""
        var_manager = VariableManager()
        var_manager.set_variable("data", "testdata")

        step = TestStep(
            name="test_step",
            type="request",
            url="/data",
            body='{"value": "${data}"}',
        )

        executor = MockStepExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["body"] == '{"value": "testdata"}'

    def test_create_performance_metrics(self):
        """Test _create_performance_metrics method."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        metrics = executor._create_performance_metrics(
            total_time=1000,
            dns_time=50,
            tcp_time=100,
            tls_time=200,
            server_time=500,
            download_time=100,
            upload_time=50,
            size=1024,
        )

        assert metrics.total_time == 1000
        assert metrics.dns_time == 50
        assert metrics.tcp_time == 100
        assert metrics.tls_time == 200
        assert metrics.server_time == 500
        assert metrics.download_time == 100
        assert metrics.upload_time == 50
        assert metrics.size == 1024

    def test_execute_with_skip_if(self):
        """Test execute with skip_if condition."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", skip_if="true")

        executor = MockStepExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "skipped"
        assert result.name == "test_step"

    def test_execute_with_only_if_false(self):
        """Test execute with only_if=false."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", only_if="false")

        executor = MockStepExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "skipped"
        assert result.name == "test_step"

    def test_create_error_info_assertion_error(self):
        """Test _create_error_info with AssertionError."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        error = AssertionError("Validation failed")
        error_info = executor._create_error_info(error)

        assert error_info.type == "AssertionError"
        assert error_info.category == ErrorCategory.ASSERTION
        assert "Validation failed" in error_info.message
        assert error_info.suggestion is not None

    def test_create_error_info_network_error(self):
        """Test _create_error_info with network error."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        error = ConnectionError("Connection refused")
        error_info = executor._create_error_info(error)

        assert error_info.type == "ConnectionError"
        assert error_info.category == ErrorCategory.NETWORK
        assert "Connection refused" in error_info.message

    def test_create_error_info_timeout_error(self):
        """Test _create_error_info with timeout error."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request")

        executor = MockStepExecutor(var_manager, step)

        error = TimeoutError("Request timeout")
        error_info = executor._create_error_info(error)

        assert error_info.type == "TimeoutError"
        assert error_info.category == ErrorCategory.TIMEOUT
        assert "Request timeout" in error_info.message


class TestStepExecutorWithRetry:
    """Tests for StepExecutor retry mechanism."""

    def test_retry_manager_initialization_with_policy(self):
        """Test retry manager initialization with retry policy."""
        var_manager = VariableManager()
        step = TestStep(
            name="test_step",
            type="request",
            retry_policy={
                "max_attempts": 3,
                "strategy": "exponential",
                "base_delay": 1.0,
                "max_delay": 10.0,
            },
        )

        executor = MockStepExecutor(var_manager, step)

        assert executor.retry_manager is not None
        assert executor.retry_manager.policy.max_attempts == 3

    def test_retry_manager_initialization_with_legacy_retry_times(self):
        """Test retry manager initialization with legacy retry_times."""
        var_manager = VariableManager()
        step = TestStep(name="test_step", type="request", retry_times=2)

        executor = MockStepExecutor(var_manager, step)

        assert executor.retry_manager is not None
        assert executor.retry_manager.policy.max_attempts == 2
