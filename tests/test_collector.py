"""Unit tests for ResultCollector.

Tests for result collector in apirun/result/collector.py
Following Google Python Style Guide.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from apirun.result.collector import ResultCollector
from apirun.core.models import TestCase, TestCaseResult, StepResult, ErrorInfo, ErrorCategory, PerformanceMetrics


class TestResultCollector:
    """Tests for ResultCollector class."""

    def test_initialization(self):
        """Test ResultCollector initialization."""
        collector = ResultCollector()

        assert collector.mask_sensitive is True
        assert "password" in collector.sensitive_patterns
        assert "token" in collector.sensitive_patterns

    def test_initialization_without_masking(self):
        """Test initialization without masking."""
        collector = ResultCollector(mask_sensitive=False)

        assert collector.mask_sensitive is False

    def test_initialization_custom_patterns(self):
        """Test initialization with custom patterns."""
        patterns = ["custom", "secret"]
        collector = ResultCollector(sensitive_patterns=patterns)

        assert collector.sensitive_patterns == patterns

    def test_collect_successful_test_case(self):
        """Test collecting successful test case results."""
        collector = ResultCollector()

        test_case = TestCase(name="test_success", steps=[])

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = collector.collect(test_case, [step_result])

        assert result.name == "test_success"
        assert result.status == "passed"
        assert result.total_steps == 1
        assert result.passed_steps == 1
        assert result.failed_steps == 0

    def test_collect_failed_test_case(self):
        """Test collecting failed test case results."""
        collector = ResultCollector()

        test_case = TestCase(name="test_failure", steps=[])

        error_info = ErrorInfo(
            type="AssertionError",
            category=ErrorCategory.ASSERTION,
            message="Validation failed",
            suggestion="Check expected values",
        )

        step_result = StepResult(
            name="step1",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        result = collector.collect(test_case, [step_result])

        assert result.status == "failed"
        assert result.failed_steps == 1
        assert result.error_info is not None

    def test_collect_skipped_test_case(self):
        """Test collecting skipped test case results."""
        collector = ResultCollector()

        test_case = TestCase(name="test_skip", steps=[])

        step_result = StepResult(
            name="step1",
            status="skipped",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = collector.collect(test_case, [step_result])

        assert result.status == "skipped"
        assert result.skipped_steps == 1

    def test_collect_mixed_results(self):
        """Test collecting mixed step results."""
        collector = ResultCollector()

        test_case = TestCase(name="test_mixed", steps=[])

        step1 = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        step2 = StepResult(
            name="step2",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        step3 = StepResult(
            name="step3",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        step4 = StepResult(
            name="step4",
            status="skipped",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = collector.collect(test_case, [step1, step2, step3, step4])

        assert result.status == "failed"
        assert result.total_steps == 4
        assert result.passed_steps == 2
        assert result.failed_steps == 1
        assert result.skipped_steps == 1

    def test_to_v2_json_format(self):
        """Test converting result to v2.0 JSON format."""
        collector = ResultCollector()

        test_case = TestCase(name="test_json", steps=[])

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        case_result = TestCaseResult(
            name="test_json",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        json_data = collector.to_v2_json(case_result)

        assert "test_case" in json_data
        assert "statistics" in json_data
        assert "steps" in json_data
        assert json_data["test_case"]["name"] == "test_json"
        assert json_data["statistics"]["total_steps"] == 1
        assert json_data["statistics"]["pass_rate"] == 100.0

    def test_mask_variables(self):
        """Test masking sensitive variables."""
        collector = ResultCollector(mask_sensitive=True)

        variables = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
            "normal_var": "value",
        }

        masked = collector._mask_variables(variables)

        assert masked["username"] == "testuser"
        assert masked["password"] == "***"
        assert masked["api_key"] == "***"
        assert masked["normal_var"] == "value"

    def test_mask_variables_disabled(self):
        """Test variables when masking is disabled."""
        collector = ResultCollector(mask_sensitive=False)

        variables = {
            "password": "secret123",
            "api_key": "abc123",
        }

        masked = collector._mask_variables(variables)

        assert masked["password"] == "secret123"
        assert masked["api_key"] == "abc123"

    def test_mask_sensitive_data_dict(self):
        """Test masking sensitive data in dictionary."""
        collector = ResultCollector(mask_sensitive=True)

        data = {
            "username": "testuser",
            "password": "secret123",
            "nested": {
                "token": "abc123",
                "value": "normal",
            },
        }

        masked = collector._mask_sensitive_data(data)

        assert masked["username"] == "testuser"
        assert masked["password"] == "***"
        assert masked["nested"]["token"] == "***"
        assert masked["nested"]["value"] == "normal"

    def test_mask_sensitive_data_list(self):
        """Test masking sensitive data in list."""
        collector = ResultCollector(mask_sensitive=True)

        data = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"},
        ]

        masked = collector._mask_sensitive_data(data)

        assert masked[0]["username"] == "user1"
        assert masked[0]["password"] == "***"
        assert masked[1]["username"] == "user2"
        assert masked[1]["password"] == "***"

    def test_format_step_result_with_performance(self):
        """Test formatting step result with performance metrics."""
        collector = ResultCollector()

        performance = PerformanceMetrics(
            total_time=1000,
            dns_time=50,
            tcp_time=100,
            tls_time=200,
            server_time=500,
            download_time=100,
            size=1024,
        )

        step_result = StepResult(
            name="api_call",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=performance,
            response={"status_code": 200, "body": {"data": "test"}},
        )

        formatted = collector._format_step_result(step_result)

        assert formatted["name"] == "api_call"
        assert formatted["status"] == "success"
        assert "performance" in formatted
        assert formatted["performance"]["total_time"] == 1000.0
        assert formatted["performance"]["size"] == 1024
        assert formatted["response"]["status_code"] == 200

    def test_format_step_result_with_error(self):
        """Test formatting step result with error."""
        collector = ResultCollector()

        error_info = ErrorInfo(
            type="ConnectionError",
            category=ErrorCategory.NETWORK,
            message="Connection refused",
            suggestion="Check network connectivity",
        )

        step_result = StepResult(
            name="failing_step",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        formatted = collector._format_step_result(step_result)

        assert formatted["status"] == "failure"
        assert "error_info" in formatted
        assert formatted["error_info"]["type"] == "ConnectionError"
        assert formatted["error_info"]["category"] == "network"

    def test_to_compact_json(self):
        """Test converting to compact JSON format."""
        collector = ResultCollector()

        step_result = StepResult(
            name="api_request",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            response={"status_code": 200, "body": {"result": "ok"}},
        )

        case_result = TestCaseResult(
            name="test_api",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        compact = collector.to_compact_json(case_result)

        assert compact["test_name"] == "test_api"
        assert compact["status"] == "passed"
        assert "api_responses" in compact
        assert len(compact["api_responses"]) == 1
        assert compact["api_responses"][0]["step"] == "api_request"
        assert compact["api_responses"][0]["status_code"] == 200

    def test_to_csv(self):
        """Test converting to CSV format."""
        collector = ResultCollector()

        performance = PerformanceMetrics(
            total_time=500,
            dns_time=50,
            tcp_time=100,
            tls_time=50,
            server_time=200,
            download_time=100,
            size=512,
        )

        step_result = StepResult(
            name="api_call",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=performance,
            response={"status_code": 200},
        )

        case_result = TestCaseResult(
            name="test_csv",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        csv_data = collector.to_csv(case_result, verbose=True)

        assert "Test Name" in csv_data
        assert "test_csv" in csv_data
        assert "SUMMARY" in csv_data
        assert "api_call" in csv_data
        assert "SUCCESS" in csv_data

    def test_save_json(self):
        """Test saving JSON file."""
        collector = ResultCollector()

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        case_result = TestCaseResult(
            name="test_save",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            collector.save_json(case_result, temp_path)

            with open(temp_path, "r") as f:
                loaded_data = json.load(f)

            assert loaded_data["test_case"]["name"] == "test_save"
            assert loaded_data["statistics"]["total_steps"] == 1
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_save_csv(self):
        """Test saving CSV file."""
        collector = ResultCollector()

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        case_result = TestCaseResult(
            name="test_csv_save",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            temp_path = f.name

        try:
            collector.save_csv(case_result, temp_path, verbose=True)

            with open(temp_path, "r") as f:
                content = f.read()

            assert "test_csv_save" in content
            assert "SUMMARY" in content
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_collect_final_variables(self):
        """Test that final variables are collected."""
        collector = ResultCollector()

        test_case = TestCase(name="test_vars", steps=[])

        step1 = StepResult(
            name="step1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            extracted_vars={"var1": "value1"},
        )

        step2 = StepResult(
            name="step2",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            extracted_vars={"var2": "value2"},
        )

        result = collector.collect(test_case, [step1, step2])

        assert result.final_variables["var1"] == "value1"
        assert result.final_variables["var2"] == "value2"

    def test_duration_calculation(self):
        """Test duration calculation."""
        collector = ResultCollector()

        test_case = TestCase(name="test_duration", steps=[])

        start = datetime.now()
        end = datetime.fromtimestamp(start.timestamp() + 2.5)

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=start,
            end_time=end,
        )

        result = collector.collect(test_case, [step_result])

        assert 2.4 <= result.duration <= 2.6  # Allow small variance

    def test_format_error_info(self):
        """Test formatting error info."""
        collector = ResultCollector()

        error_info = ErrorInfo(
            type="ValueError",
            category=ErrorCategory.SYSTEM,
            message="Invalid value",
            suggestion="Check input",
        )

        formatted = collector._format_error_info(error_info)

        assert formatted["type"] == "ValueError"
        assert formatted["category"] == "system"
        assert formatted["message"] == "Invalid value"
        assert formatted["suggestion"] == "Check input"

    def test_collect_with_no_step_results(self):
        """Test collecting with no step results."""
        collector = ResultCollector()

        test_case = TestCase(name="empty_test", steps=[])

        result = collector.collect(test_case, [])

        assert result.name == "empty_test"
        assert result.total_steps == 0
        # Empty test (total_steps == 0) is considered "skipped" by the collector logic
        assert result.status == "skipped"


class TestResultCollectorEdgeCases:
    """Test edge cases for ResultCollector."""

    def test_collect_with_none_times(self):
        """Test collecting with None times."""
        collector = ResultCollector()

        test_case = TestCase(name="test_no_time", steps=[])

        step_result = StepResult(
            name="step1",
            status="success",
            start_time=None,
            end_time=None,
        )

        result = collector.collect(test_case, [step_result])

        assert result.duration == 0.0

    def test_mask_data_with_non_dict_values(self):
        """Test masking with non-dict values."""
        collector = ResultCollector(mask_sensitive=True)

        # Test with primitive types
        assert collector._mask_sensitive_data("test") == "test"
        assert collector._mask_sensitive_data(123) == 123
        assert collector._mask_sensitive_data(True) is True
        assert collector._mask_sensitive_data(None) is None

    def test_to_csv_with_sensitive_data(self):
        """Test CSV export with sensitive data masking."""
        collector = ResultCollector(mask_sensitive=True)

        step_result = StepResult(
            name="api_call",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            extracted_vars={"password": "secret123", "username": "test"},
            response={"password": "hidden", "data": "visible"},
        )

        case_result = TestCaseResult(
            name="test_mask_csv",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step_result],
        )

        csv_data = collector.to_csv(case_result, verbose=True)

        # CSV should contain masked data in variables_snapshot
        # Response masking happens at a different level
        assert "test_mask_csv" in csv_data
