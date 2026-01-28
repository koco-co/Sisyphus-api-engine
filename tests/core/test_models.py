"""Unit tests for core models.

Tests for data models in apirun/core/models.py
Following Google Python Style Guide.
"""

import pytest
from datetime import datetime
from apirun.core.models import (
    HttpMethod,
    ErrorCategory,
    ProfileConfig,
    GlobalConfig,
    ValidationRule,
    Extractor,
    TestStep,
    TestCase,
    StepResult,
    TestCaseResult,
    ErrorInfo,
    PerformanceMetrics,
)


class TestHttpMethod:
    """Tests for HttpMethod enum."""

    def test_http_method_values(self):
        """Test HttpMethod enum has correct values."""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"
        assert HttpMethod.PATCH.value == "PATCH"
        assert HttpMethod.HEAD.value == "HEAD"
        assert HttpMethod.OPTIONS.value == "OPTIONS"


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_error_category_values(self):
        """Test ErrorCategory enum has correct values."""
        assert ErrorCategory.ASSERTION.value == "assertion"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.PARSING.value == "parsing"
        assert ErrorCategory.BUSINESS.value == "business"
        assert ErrorCategory.SYSTEM.value == "system"


class TestProfileConfig:
    """Tests for ProfileConfig dataclass."""

    def test_create_profile_config(self):
        """Test creating ProfileConfig with default values."""
        profile = ProfileConfig(base_url="http://example.com")
        assert profile.base_url == "http://example.com"
        assert profile.variables == {}
        assert profile.timeout == 30
        assert profile.verify_ssl is True

    def test_create_profile_config_with_custom_values(self):
        """Test creating ProfileConfig with custom values."""
        profile = ProfileConfig(
            base_url="http://example.com",
            variables={"key": "value"},
            timeout=60,
            verify_ssl=False,
        )
        assert profile.variables == {"key": "value"}
        assert profile.timeout == 60
        assert profile.verify_ssl is False


class TestGlobalConfig:
    """Tests for GlobalConfig dataclass."""

    def test_create_global_config_minimal(self):
        """Test creating GlobalConfig with minimal parameters."""
        config = GlobalConfig(name="Test Suite")
        assert config.name == "Test Suite"
        assert config.description == ""
        assert config.profiles == {}
        assert config.variables == {}
        assert config.timeout == 30

    def test_create_global_config_full(self):
        """Test creating GlobalConfig with all parameters."""
        profiles = {
            "dev": ProfileConfig(base_url="http://dev.api.com"),
            "prod": ProfileConfig(base_url="http://prod.api.com"),
        }
        config = GlobalConfig(
            name="Full Config",
            description="Full description",
            profiles=profiles,
            active_profile="dev",
            variables={"key": "value"},
            timeout=60,
            retry_times=3,
            concurrent=True,
            concurrent_threads=5,
        )
        assert config.name == "Full Config"
        assert len(config.profiles) == 2
        assert config.active_profile == "dev"
        assert config.variables == {"key": "value"}
        assert config.timeout == 60
        assert config.retry_times == 3
        assert config.concurrent is True
        assert config.concurrent_threads == 5


class TestValidationRule:
    """Tests for ValidationRule dataclass."""

    def test_create_validation_rule_minimal(self):
        """Test creating ValidationRule with minimal parameters."""
        rule = ValidationRule(type="eq", path="$.field", expect="value")
        assert rule.type == "eq"
        assert rule.path == "$.field"
        assert rule.expect == "value"
        assert rule.description == ""

    def test_create_validation_rule_full(self):
        """Test creating ValidationRule with all parameters."""
        rule = ValidationRule(
            type="eq",
            path="$.data.user_id",
            expect=123,
            description="Verify user ID",
        )
        assert rule.type == "eq"
        assert rule.path == "$.data.user_id"
        assert rule.expect == 123
        assert rule.description == "Verify user ID"


class TestExtractor:
    """Tests for Extractor dataclass."""

    def test_create_extractor(self):
        """Test creating Extractor."""
        extractor = Extractor(
            name="user_id",
            type="jsonpath",
            path="$.data.id",
            index=0,
        )
        assert extractor.name == "user_id"
        assert extractor.type == "jsonpath"
        assert extractor.path == "$.data.id"
        assert extractor.index == 0


class TestTestStep:
    """Tests for TestStep dataclass."""

    def test_create_request_step_minimal(self):
        """Test creating request step with minimal parameters."""
        step = TestStep(
            name="Test Step",
            type="request",
            url="http://example.com",
        )
        assert step.name == "Test Step"
        assert step.type == "request"
        assert step.url == "http://example.com"
        assert step.method is None

    def test_create_request_step_full(self):
        """Test creating request step with all parameters."""
        step = TestStep(
            name="POST Request",
            type="request",
            method="POST",
            url="http://example.com/api",
            headers={"Content-Type": "application/json"},
            body={"key": "value"},
            timeout=30,
        )
        assert step.name == "POST Request"
        assert step.method == "POST"
        assert step.headers == {"Content-Type": "application/json"}
        assert step.body == {"key": "value"}

    def test_create_script_step(self):
        """Test creating script step."""
        step = TestStep(
            name="Script Step",
            type="script",
            script="print('test')",
            script_type="python",
            allow_imports=True,
        )
        assert step.name == "Script Step"
        assert step.type == "script"
        assert step.script == "print('test')"
        assert step.script_type == "python"
        assert step.allow_imports is True

    def test_create_loop_step(self):
        """Test creating loop step."""
        step = TestStep(
            name="Loop Step",
            type="loop",
            loop_type="for",
            loop_count=5,
            loop_variable="i",
            loop_steps=[{"name": "inner", "type": "request", "url": "http://example.com"}],
        )
        assert step.name == "Loop Step"
        assert step.type == "loop"
        assert step.loop_type == "for"
        assert step.loop_count == 5
        assert step.loop_variable == "i"
        assert len(step.loop_steps) == 1


class TestModelTestCase:
    """Tests for TestCase dataclass."""

    def test_create_test_case_minimal(self):
        """Test creating TestCase with minimal parameters."""
        from apirun.core.models import TestCase as ModelTestCase
        test_case = ModelTestCase(name="Test Case")
        assert test_case.name == "Test Case"
        assert test_case.description == ""
        assert test_case.config is None
        assert test_case.steps == []
        assert test_case.enabled is True

    def test_create_test_case_full(self):
        """Test creating TestCase with all parameters."""
        from apirun.core.models import TestCase as ModelTestCase
        config = GlobalConfig(name="Config")
        steps = [
            TestStep(name="Step 1", type="request", url="http://example.com"),
            TestStep(name="Step 2", type="request", url="http://example.com"),
        ]
        test_case = ModelTestCase(
            name="Full Test Case",
            description="Full test case",
            config=config,
            steps=steps,
            tags=["smoke", "integration"],
            enabled=True,
        )
        assert test_case.name == "Full Test Case"
        assert len(test_case.steps) == 2
        assert test_case.tags == ["smoke", "integration"]
        assert test_case.enabled is True


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_create_step_result(self):
        """Test creating StepResult."""
        start_time = datetime.now()
        end_time = datetime.now()
        result = StepResult(
            name="Test Step",
            status="success",
            start_time=start_time,
            end_time=end_time,
            retry_count=0,
            variables_snapshot={},
        )
        assert result.name == "Test Step"
        assert result.status == "success"
        assert result.retry_count == 0
        assert isinstance(result.variables_snapshot, dict)


class TestErrorInfo:
    """Tests for ErrorInfo dataclass."""

    def test_create_error_info(self):
        """Test creating ErrorInfo."""
        error = ErrorInfo(
            type="ValueError",
            category=ErrorCategory.SYSTEM,
            message="Invalid value",
            suggestion="Check the value",
        )
        assert error.type == "ValueError"
        assert error.category == ErrorCategory.SYSTEM
        assert error.message == "Invalid value"
        assert error.suggestion == "Check the value"


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""

    def test_create_performance_metrics_default(self):
        """Test creating PerformanceMetrics with default values."""
        metrics = PerformanceMetrics()
        assert metrics.total_time == 0.0
        assert metrics.dns_time == 0.0
        assert metrics.tcp_time == 0.0
        assert metrics.tls_time == 0.0
        assert metrics.server_time == 0.0
        assert metrics.download_time == 0.0
        assert metrics.upload_time == 0.0
        assert metrics.size == 0

    def test_create_performance_metrics_full(self):
        """Test creating PerformanceMetrics with all values."""
        metrics = PerformanceMetrics(
            total_time=1000.0,
            dns_time=50.0,
            tcp_time=80.0,
            tls_time=120.0,
            server_time=400.0,
            download_time=250.0,
            upload_time=100.0,
            size=1024,
        )
        assert metrics.total_time == 1000.0
        assert metrics.dns_time == 50.0
        assert metrics.tcp_time == 80.0
        assert metrics.tls_time == 120.0
        assert metrics.server_time == 400.0
        assert metrics.download_time == 250.0
        assert metrics.upload_time == 100.0
        assert metrics.size == 1024


class TestTestCaseResult:
    """Tests for TestCaseResult dataclass."""

    def test_create_test_case_result(self):
        """Test creating TestCaseResult."""
        start_time = datetime.now()
        end_time = datetime.now()
        result = TestCaseResult(
            name="Test Case",
            status="passed",
            start_time=start_time,
            end_time=end_time,
            duration=1.5,
            total_steps=5,
            passed_steps=5,
            failed_steps=0,
            skipped_steps=0,
        )
        assert result.name == "Test Case"
        assert result.status == "passed"
        assert result.duration == 1.5
        assert result.total_steps == 5
        assert result.passed_steps == 5
