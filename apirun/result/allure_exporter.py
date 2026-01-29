"""Allure Exporter for Sisyphus API Engine.

This module implements Allure 2.x JSON format export for test execution results.
Following Google Python Style Guide.
"""

import json
import uuid
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from apirun.core.models import TestCase, TestCaseResult, StepResult, ErrorInfo

# Default patterns for identifying sensitive data fields
DEFAULT_SENSITIVE_PATTERNS = [
    "password",
    "pwd",
    "token",
    "secret",
    "key",
    "auth",
]


class AllureExporter:
    """Export test execution results to Allure 2.x format.

    This exporter:
    - Generates Allure-compatible JSON files
    - Creates allure-results directory structure
    - Supports test steps, attachments, labels, links
    - Handles test status and error details

    Attributes:
        output_dir: Directory to save Allure results (default: allure-results)
        mask_sensitive: Whether to mask sensitive data
    """

    def __init__(self, output_dir: str = "allure-results", mask_sensitive: bool = True):
        """Initialize AllureExporter.

        Args:
            output_dir: Directory to save Allure results
            mask_sensitive: Whether to mask sensitive data in responses
        """
        self.output_dir = Path(output_dir)
        self.mask_sensitive = mask_sensitive
        self.sensitive_patterns = DEFAULT_SENSITIVE_PATTERNS.copy()

    def collect(self, test_case: TestCase, test_result: TestCaseResult) -> str:
        """Collect test result and save as Allure JSON.

        Args:
            test_case: Test case that was executed
            test_result: Test case execution result

        Returns:
            Path to generated Allure JSON file
        """
        # Create output directory if not exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate Allure result object
        allure_result = self._to_allure_format(test_case, test_result)

        # Generate unique filename
        result_uuid = str(uuid.uuid4())
        result_file = self.output_dir / f"{result_uuid}-result.json"

        # Save to file
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(allure_result, f, ensure_ascii=False, indent=2)

        return str(result_file)

    def collect_batch(
        self, test_cases: List[TestCase], test_results: List[TestCaseResult]
    ) -> List[str]:
        """Collect multiple test results.

        Args:
            test_cases: List of test cases
            test_results: List of test case results

        Returns:
            List of paths to generated Allure JSON files
        """
        result_files = []
        for test_case, test_result in zip(test_cases, test_results):
            result_file = self.collect(test_case, test_result)
            result_files.append(result_file)
        return result_files

    def _to_allure_format(
        self, test_case: TestCase, test_result: TestCaseResult
    ) -> Dict[str, Any]:
        """Convert test result to Allure format.

        Args:
            test_case: Test case
            test_result: Test execution result

        Returns:
            Allure 2.x compatible JSON object
        """
        # Generate unique identifiers
        result_uuid = str(uuid.uuid4())
        history_id = str(hash(f"{test_case.name}-{test_case.description}"))

        # Convert status
        status_map = {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped",
            "error": "broken",
        }
        status = status_map.get(test_result.status, "failed")

        # Build base result object
        allure_result = {
            "uuid": result_uuid,
            "name": test_case.name,
            "fullName": f"{test_case.name}",
            "historyId": history_id,
            "time": self._format_time(test_result),
            "status": status,
            "steps": self._format_steps(test_result),
            "labels": self._format_labels(test_case, test_result),
            "links": [],
            "parameters": [],
            "attachments": [],
        }

        # Add status details if failed or has errors
        if test_result.status in ["failed", "error"] and test_result.error_info:
            allure_result["statusDetails"] = self._format_status_details(
                test_result.error_info
            )

        # Add parameters from data-driven testing
        if test_case.config and test_case.config.data_iterations:
            allure_result["parameters"] = self._format_data_parameters(test_result)

        # Add test case tags as labels
        if test_case.tags:
            for tag in test_case.tags:
                allure_result["labels"].append(
                    {"name": "tag", "value": tag}
                )

        return allure_result

    def _format_time(self, test_result: TestCaseResult) -> Dict[str, int]:
        """Format time information for Allure.

        Args:
            test_result: Test case result

        Returns:
            Time dictionary with start, stop, duration (in milliseconds)
        """
        start = test_result.start_time
        end = test_result.end_time
        duration_ms = int(test_result.duration * 1000)

        return {
            "start": int(start.timestamp() * 1000),
            "stop": int(end.timestamp() * 1000),
            "duration": duration_ms,
        }

    def _format_steps(self, test_result: TestCaseResult) -> List[Dict[str, Any]]:
        """Format test steps as Allure steps.

        Args:
            test_result: Test case result

        Returns:
            List of Allure step objects
        """
        allure_steps = []

        for step_result in test_result.step_results:
            step_uuid = str(uuid.uuid4())

            # Convert step status
            status_map = {
                "success": "passed",
                "failure": "failed",
                "skipped": "skipped",
                "error": "broken",
            }
            step_status = status_map.get(step_result.status, "failed")

            # Build step object
            allure_step = {
                "name": step_result.name,
                "status": step_status,
                "stage": "finished",
                "steps": [],  # Sub-steps (for loops, concurrent, etc.)
                "attachments": [],
                "parameters": [],
            }

            # Add timing information
            if step_result.start_time and step_result.end_time:
                start_ms = int(step_result.start_time.timestamp() * 1000)
                stop_ms = int(step_result.end_time.timestamp() * 1000)
                duration_ms = stop_ms - start_ms
                allure_step["start"] = start_ms
                allure_step["stop"] = stop_ms
                allure_step["duration"] = duration_ms

            # Add step type as parameter
            allure_step["parameters"].append({
                "name": "step_type",
                "value": step_result.name.split(" ")[0] if step_result.name else "unknown"
            })

            # Add performance metrics as parameters
            if step_result.performance:
                perf = step_result.performance
                allure_step["parameters"].extend([
                    {"name": "total_time", "value": f"{perf.total_time:.2f}ms"},
                    {"name": "response_size", "value": f"{perf.size} bytes"},
                ])

            # Add HTTP request/response as attachments
            if step_result.response:
                # Request attachment
                request_data = self._format_request_attachment(step_result)
                if request_data:
                    allure_step["attachments"].append(request_data)

                # Response attachment
                response_data = self._format_response_attachment(step_result)
                if response_data:
                    allure_step["attachments"].append(response_data)

            # Add validation results
            if step_result.validation_results:
                for idx, validation in enumerate(step_result.validation_results):
                    validation_step = {
                        "name": f"Validation: {validation.get('type', '')}",
                        "status": "passed" if validation.get("passed", False) else "failed",
                        "stage": "finished",
                        "parameters": [
                            {"name": "type", "value": validation.get("type", "")},
                            {"name": "path", "value": validation.get("path", "")},
                            {"name": "expect", "value": str(validation.get("expect", ""))},
                            {"name": "actual", "value": str(validation.get("actual", ""))},
                        ],
                    }
                    allure_step["steps"].append(validation_step)

            # Add error details if failed
            if step_result.status in ["failure", "error"] and step_result.error_info:
                allure_step["statusDetails"] = self._format_status_details(
                    step_result.error_info
                )

            # Add retry history as parameters
            if step_result.retry_count > 0:
                allure_step["parameters"].append({
                    "name": "retry_count",
                    "value": str(step_result.retry_count)
                })

            allure_steps.append(allure_step)

        return allure_steps

    def _format_request_attachment(self, step_result: StepResult) -> Optional[Dict[str, Any]]:
        """Format HTTP request as Allure attachment.

        Args:
            step_result: Step execution result

        Returns:
            Attachment object or None
        """
        if not step_result.response or not isinstance(step_result.response, dict):
            return None

        # Extract request information from response (if available)
        request_data = {
            "name": "HTTP Request",
            "source": f"request-{uuid.uuid4()}.txt",
            "type": "text/plain",
        }

        # Build request text
        request_lines = []
        if "method" in step_result.response:
            request_lines.append(f"Method: {step_result.response['method']}")
        if "url" in step_result.response:
            request_lines.append(f"URL: {step_result.response['url']}")

        if "request" in step_result.response:
            request = step_result.response["request"]
            if isinstance(request, dict):
                if "headers" in request:
                    request_lines.append("\nHeaders:")
                    for k, v in request["headers"].items():
                        request_lines.append(f"  {k}: {v}")
                if "body" in request:
                    request_lines.append("\nBody:")
                    request_lines.append(json.dumps(request["body"], indent=2, ensure_ascii=False))

        if request_lines:
            return request_data

        return None

    def _format_response_attachment(self, step_result: StepResult) -> Optional[Dict[str, Any]]:
        """Format HTTP response as Allure attachment.

        Args:
            step_result: Step execution result

        Returns:
            Attachment object or None
        """
        if not step_result.response or not isinstance(step_result.response, dict):
            return None

        response_data = {
            "name": "HTTP Response",
            "source": f"response-{uuid.uuid4()}.json",
            "type": "application/json",
        }

        return response_data

    def _format_status_details(self, error_info: ErrorInfo) -> Dict[str, str]:
        """Format error information for Allure.

        Args:
            error_info: Error information

        Returns:
            Status details dictionary
        """
        details = {
            "known": False,
            "muted": False,
            "flaky": False,
        }

        if error_info.message:
            details["message"] = error_info.message

        if error_info.trace:
            details["trace"] = error_info.trace

        return details

    def _format_labels(
        self, test_case: TestCase, test_result: TestCaseResult
    ) -> List[Dict[str, str]]:
        """Format labels for Allure report.

        Args:
            test_case: Test case
            test_result: Test execution result

        Returns:
            List of label objects
        """
        labels = []

        # Add suite label
        labels.append({"name": "suite", "value": test_case.name})

        # Add test case label
        labels.append({"name": "testClass", "value": test_case.name})

        # Add thread label (main thread)
        labels.append({"name": "thread", "value": "main"})

        # Add package label
        labels.append({"name": "package", "value": "sisyphus.tests"})

        # Add framework label
        labels.append({"name": "framework", "value": "sisyphus-api-engine"})

        # Add language label
        labels.append({"name": "language", "value": "python"})

        # Add profile label if specified
        if test_case.config and test_case.config.active_profile:
            labels.append({
                "name": "environment",
                "value": test_case.config.active_profile
            })

        # Add severity label based on tags
        if "critical" in test_case.tags or "P0" in test_case.tags:
            labels.append({"name": "severity", "value": "critical"})
        elif "P1" in test_case.tags:
            labels.append({"name": "severity", "value": "normal"})
        elif "P2" in test_case.tags:
            labels.append({"name": "severity", "value": "minor"})

        # Add epic/feature labels based on tags
        for tag in test_case.tags:
            if tag.startswith("epic:"):
                labels.append({"name": "epic", "value": tag[5:]})
            elif tag.startswith("feature:"):
                labels.append({"name": "feature", "value": tag[8:]})
            elif tag.startswith("story:"):
                labels.append({"name": "story", "value": tag[6:]})

        return labels

    def _format_data_parameters(self, test_result: TestCaseResult) -> List[Dict[str, str]]:
        """Format data-driven test parameters.

        Args:
            test_result: Test execution result

        Returns:
            List of parameter objects
        """
        parameters = []

        # Add extracted variables as parameters
        if test_result.final_variables:
            for key, value in test_result.final_variables.items():
                # Mask sensitive values
                if self.mask_sensitive and any(
                    pattern in key.lower() for pattern in self.sensitive_patterns
                ):
                    value = "***"

                parameters.append({
                    "name": key,
                    "value": str(value)
                })

        return parameters

    def generate_environment_file(self, env_vars: Dict[str, str] = None):
        """Generate environment.properties file for Allure report.

        Args:
            env_vars: Environment variables to include
        """
        env_file = self.output_dir / "environment.properties"

        # Default environment info
        properties = {
            "Framework": "Sisyphus API Engine",
            "Language": "Python",
            "Generated": datetime.now().isoformat(),
        }

        # Add custom environment variables
        if env_vars:
            properties.update(env_vars)

        # Write to file
        with open(env_file, "w", encoding="utf-8") as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")

    def generate_categories_file(self):
        """Generate categories.json file for Allure report."""
        categories_file = self.output_dir / "categories.json"

        categories = [
            {
                "name": "Passed tests",
                "matchedStatuses": ["passed"],
                "flaky": False,
            },
            {
                "name": "Failed tests",
                "matchedStatuses": ["failed"],
                "flaky": False,
            },
            {
                "name": "Broken tests",
                "matchedStatuses": ["broken", "error"],
                "flaky": False,
            },
            {
                "name": "Skipped tests",
                "matchedStatuses": ["skipped"],
                "flaky": False,
            },
            {
                "name": "Flaky tests",
                "matchedStatuses": ["passed", "failed", "broken"],
                "flaky": True,
            },
        ]

        with open(categories_file, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

    def save_attachment(self, content: str, filename: str = None) -> str:
        """Save attachment content and return reference.

        Args:
            content: Attachment content
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Attachment filename
        """
        if not filename:
            filename = f"{uuid.uuid4()}.txt"

        attachment_path = self.output_dir / filename

        # Ensure directory exists
        attachment_path.parent.mkdir(parents=True, exist_ok=True)

        # Save attachment
        with open(attachment_path, "w", encoding="utf-8") as f:
            f.write(content)

        return filename
