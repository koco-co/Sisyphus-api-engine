"""Result Collector for Sisyphus API Engine.

This module implements collection and formatting of test execution results.
Following Google Python Style Guide.
"""

import json
from typing import Any, Dict, List
from datetime import datetime

from apirun.core.models import TestCase, TestCaseResult, StepResult


class ResultCollector:
    """Collect and format test execution results.

    This collector:
    - Aggregates step results
    - Calculates statistics
    - Formats output as v2.0 JSON
    - Masks sensitive data
    """

    def __init__(self, mask_sensitive: bool = True, sensitive_patterns: List[str] = None):
        """Initialize ResultCollector.

        Args:
            mask_sensitive: Whether to mask sensitive data
            sensitive_patterns: List of patterns to identify sensitive fields
        """
        self.mask_sensitive = mask_sensitive
        self.sensitive_patterns = sensitive_patterns or [
            "password",
            "pwd",
            "token",
            "secret",
            "key",
            "auth",
        ]

    def collect(
        self, test_case: TestCase, step_results: List[StepResult]
    ) -> TestCaseResult:
        """Collect and aggregate test case results.

        Args:
            test_case: Test case that was executed
            step_results: List of step execution results

        Returns:
            TestCaseResult object
        """
        start_time = None
        end_time = None

        if step_results:
            valid_starts = [sr.start_time for sr in step_results if sr.start_time]
            valid_ends = [sr.end_time for sr in step_results if sr.end_time]

            if valid_starts:
                start_time = min(valid_starts)
            if valid_ends:
                end_time = max(valid_ends)

        duration = 0.0
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()

        # Calculate statistics
        total_steps = len(step_results)
        passed_steps = sum(1 for sr in step_results if sr.status == "success")
        failed_steps = sum(1 for sr in step_results if sr.status == "failure")
        skipped_steps = sum(1 for sr in step_results if sr.status == "skipped")

        # Determine overall status
        if failed_steps > 0:
            status = "failed"
        elif skipped_steps == total_steps:
            status = "skipped"
        else:
            status = "passed"

        # Collect final variables
        final_variables = {}
        for sr in step_results:
            final_variables.update(sr.extracted_vars)

        # Get error info if failed
        error_info = None
        if status == "failed":
            for sr in step_results:
                if sr.status == "failure" and sr.error_info:
                    error_info = sr.error_info
                    break

        return TestCaseResult(
            name=test_case.name,
            status=status,
            start_time=start_time or datetime.now(),
            end_time=end_time or datetime.now(),
            duration=duration,
            total_steps=total_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            step_results=step_results,
            final_variables=final_variables,
            error_info=error_info,
        )

    def to_v2_json(self, result: TestCaseResult) -> Dict[str, Any]:
        """Convert result to v2.0 JSON format.

        Args:
            result: Test case result

        Returns:
            v2.0 compliant JSON dictionary
        """
        json_data = {
            "test_case": {
                "name": result.name,
                "status": result.status,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "duration": result.duration,
            },
            "statistics": {
                "total_steps": result.total_steps,
                "passed_steps": result.passed_steps,
                "failed_steps": result.failed_steps,
                "skipped_steps": result.skipped_steps,
                "pass_rate": (
                    result.passed_steps / result.total_steps * 100
                    if result.total_steps > 0
                    else 0
                ),
            },
            "steps": [],
            "final_variables": self._mask_variables(result.final_variables),
        }

        # Add step results
        for step_result in result.step_results:
            step_data = self._format_step_result(step_result)
            json_data["steps"].append(step_data)

        # Add error info if present
        if result.error_info:
            json_data["error_info"] = self._format_error_info(result.error_info)

        return json_data

    def _format_step_result(self, step_result: StepResult) -> Dict[str, Any]:
        """Format step result for JSON output.

        Args:
            step_result: Step result

        Returns:
            Formatted step data
        """
        step_data = {
            "name": step_result.name,
            "status": step_result.status,
            "start_time": step_result.start_time.isoformat()
            if step_result.start_time
            else None,
            "end_time": step_result.end_time.isoformat() if step_result.end_time else None,
            "retry_count": step_result.retry_count,
        }

        # Add performance metrics if available
        if step_result.performance:
            step_data["performance"] = {
                "total_time": round(step_result.performance.total_time, 2),
                "dns_time": round(step_result.performance.dns_time, 2),
                "tcp_time": round(step_result.performance.tcp_time, 2),
                "tls_time": round(step_result.performance.tls_time, 2),
                "server_time": round(step_result.performance.server_time, 2),
                "download_time": round(step_result.performance.download_time, 2),
                "size": step_result.performance.size,
            }

        # Add response (masked)
        if step_result.response:
            step_data["response"] = self._mask_sensitive_data(step_result.response)

        # Add extracted variables
        if step_result.extracted_vars:
            step_data["extracted_vars"] = self._mask_variables(
                step_result.extracted_vars
            )

        # Add validation results
        if step_result.validation_results:
            step_data["validations"] = step_result.validation_results

        # Add error info if present
        if step_result.error_info:
            step_data["error_info"] = self._format_error_info(step_result.error_info)

        # Add variables snapshot if in debug mode
        if step_result.variables_snapshot:
            step_data["variables_snapshot"] = self._mask_variables(
                step_result.variables_snapshot.get("extracted", {})
            )

        return step_data

    def _format_error_info(self, error_info) -> Dict[str, Any]:
        """Format error info for JSON output.

        Args:
            error_info: ErrorInfo object

        Returns:
            Formatted error data
        """
        return {
            "type": error_info.type,
            "category": error_info.category.value if hasattr(error_info.category, 'value') else str(error_info.category),
            "message": error_info.message,
            "suggestion": error_info.suggestion,
        }

    def _mask_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive variables.

        Args:
            variables: Variable dictionary

        Returns:
            Masked variable dictionary
        """
        if not self.mask_sensitive:
            return variables

        masked = {}
        for key, value in variables.items():
            if any(pattern in key.lower() for pattern in self.sensitive_patterns):
                masked[key] = "***"
            else:
                masked[key] = value

        return masked

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in response.

        Args:
            data: Data to mask

        Returns:
            Masked data
        """
        if not self.mask_sensitive:
            return data

        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(pattern in key.lower() for pattern in self.sensitive_patterns):
                    masked[key] = "***"
                else:
                    masked[key] = self._mask_sensitive_data(value)
            return masked

        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]

        else:
            return data

    def save_json(self, result: TestCaseResult, output_path: str) -> None:
        """Save result as JSON file.

        Args:
            result: Test case result
            output_path: Output file path
        """
        json_data = self.to_v2_json(result)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
