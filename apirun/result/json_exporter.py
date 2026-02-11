"""JSON Exporter for Sisyphus API Engine.

This module implements JSON format export for test execution results.
Following Google Python Style Guide.
"""

import csv
from datetime import datetime
from io import StringIO
import json
import pathlib
from typing import Any

from apirun.core.models import StepResult, TestCase, TestCaseResult

# Default patterns for identifying sensitive data fields
DEFAULT_SENSITIVE_PATTERNS = [
    'password',
    'pwd',
    'token',
    'secret',
    'key',
    'auth',
]


class JSONExporter:
    """Export test execution results to JSON format.

    This exporter:
    - Aggregates step results
    - Calculates statistics
    - Formats output as v2.0 JSON
    - Masks sensitive data
    - Supports CSV export
    """

    def __init__(
        self, mask_sensitive: bool = True, sensitive_patterns: list[str] = None
    ):
        """Initialize JSONExporter.

        Args:
            mask_sensitive: Whether to mask sensitive data
            sensitive_patterns: List of patterns to identify sensitive fields
        """
        self.mask_sensitive = mask_sensitive
        self.sensitive_patterns = (
            sensitive_patterns or DEFAULT_SENSITIVE_PATTERNS.copy()
        )

    def collect(
        self, test_case: TestCase, step_results: list[StepResult], variable_manager=None
    ) -> TestCaseResult:
        """Collect and aggregate test case results.

        Args:
            test_case: Test case that was executed
            step_results: List of step execution results
            variable_manager: Optional variable manager to collect final variables

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
        passed_steps = sum(1 for sr in step_results if sr.status == 'success')
        failed_steps = sum(1 for sr in step_results if sr.status == 'failure')
        skipped_steps = sum(1 for sr in step_results if sr.status == 'skipped')

        # Determine overall status
        if failed_steps > 0:
            status = 'failed'
        elif skipped_steps == total_steps:
            status = 'skipped'
        else:
            status = 'passed'

        # Collect final variables (including global, profile, and extracted variables)
        final_variables = {}

        # Add global config variables
        if test_case.config and test_case.config.variables:
            final_variables.update(test_case.config.variables)

        # Add active profile variables (including base_url)
        if (
            test_case.config
            and test_case.config.active_profile
            and test_case.config.profiles
        ):
            profile_name = test_case.config.active_profile
            profile = test_case.config.profiles.get(profile_name)
            if profile:
                if profile.variables:
                    final_variables.update(profile.variables)
                if profile.base_url:
                    final_variables['base_url'] = profile.base_url

        # Add extracted variables from steps
        for sr in step_results:
            final_variables.update(sr.extracted_vars)

        # Add runtime variable manager state if available
        if variable_manager and hasattr(variable_manager, 'get_all_variables'):
            try:
                final_variables.update(variable_manager.get_all_variables())
            except Exception:
                # Ignore variable export issues to avoid breaking result generation
                pass

        # Get error info if failed
        error_info = None
        if status == 'failed':
            for sr in step_results:
                if sr.status == 'failure' and sr.error_info:
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

    def to_v2_json(self, result: TestCaseResult) -> dict[str, Any]:
        """Convert result to v2.0 JSON format.

        Args:
            result: Test case result

        Returns:
            v2.0 compliant JSON dictionary
        """
        json_data = {
            'test_case': {
                'name': result.name,
                'status': result.status,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'duration': result.duration,
            },
            'statistics': {
                'total_steps': result.total_steps,
                'passed_steps': result.passed_steps,
                'failed_steps': result.failed_steps,
                'skipped_steps': result.skipped_steps,
                'pass_rate': (
                    result.passed_steps / result.total_steps * 100
                    if result.total_steps > 0
                    else 0
                ),
            },
            'steps': [],
            'final_variables': self._mask_variables(result.final_variables),
        }

        # Add step results
        for step_result in result.step_results:
            step_data = self._format_step_result(step_result)
            json_data['steps'].append(step_data)

        # Add error info if present
        if result.error_info:
            json_data['error_info'] = self._format_error_info(result.error_info)

        return json_data

    def _format_step_result(self, step_result: StepResult) -> dict[str, Any]:
        """Format step result for JSON output.

        Args:
            step_result: Step result

        Returns:
            Formatted step data
        """
        step_data = {
            'name': step_result.name,
            'status': step_result.status,
            'start_time': step_result.start_time.isoformat()
            if step_result.start_time
            else None,
            'end_time': step_result.end_time.isoformat()
            if step_result.end_time
            else None,
            'retry_count': step_result.retry_count,
        }

        # Add performance metrics if available
        if step_result.performance:
            step_data['performance'] = {
                'total_time': round(step_result.performance.total_time, 2),
                'dns_time': round(step_result.performance.dns_time, 2),
                'tcp_time': round(step_result.performance.tcp_time, 2),
                'tls_time': round(step_result.performance.tls_time, 2),
                'server_time': round(step_result.performance.server_time, 2),
                'download_time': round(step_result.performance.download_time, 2),
                'size': step_result.performance.size,
            }

        # Add response (masked)
        if step_result.response:
            step_data['response'] = self._mask_sensitive_data(step_result.response)

        # Add extracted variables
        if step_result.extracted_vars:
            step_data['extracted_vars'] = self._mask_variables(
                step_result.extracted_vars
            )

        # Add validation results
        if step_result.validation_results:
            step_data['validations'] = step_result.validation_results

        # Add error info if present
        if step_result.error_info:
            step_data['error_info'] = self._format_error_info(step_result.error_info)

        # Add variables snapshot if in debug mode
        if step_result.variables_snapshot:
            step_data['variables_snapshot'] = self._mask_variables(
                step_result.variables_snapshot.get('extracted', {})
            )

        return step_data

    def _format_error_info(self, error_info) -> dict[str, Any]:
        """Format error info for JSON output.

        Args:
            error_info: ErrorInfo object

        Returns:
            Formatted error data
        """
        return {
            'type': error_info.type,
            'category': error_info.category.value
            if hasattr(error_info.category, 'value')
            else str(error_info.category),
            'message': error_info.message,
            'suggestion': error_info.suggestion,
        }

    def _filter_non_serializable(self, obj: Any) -> Any:
        """Filter out non-serializable objects.

        Args:
            obj: Object to filter

        Returns:
            Filtered object or placeholder string
        """
        import types

        # Check for non-serializable types
        if isinstance(obj, (types.ModuleType, types.FunctionType, type(lambda: None))):
            return f'<{type(obj).__name__}: {getattr(obj, "__name__", "N/A")}>'

        if isinstance(obj, dict):
            return {k: self._filter_non_serializable(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [self._filter_non_serializable(item) for item in obj]

        if isinstance(obj, tuple):
            return tuple(self._filter_non_serializable(item) for item in obj)

        if isinstance(obj, set):
            return {self._filter_non_serializable(item) for item in obj}

        # For other types, try to serialize
        try:
            import json

            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return f'<{type(obj).__name__}>'

    def _mask_variables(self, variables: dict[str, Any]) -> dict[str, Any]:
        """Mask sensitive variables.

        Args:
            variables: Variable dictionary

        Returns:
            Masked variable dictionary
        """
        # First filter non-serializable objects
        filtered = self._filter_non_serializable(variables)

        if not self.mask_sensitive:
            return filtered

        masked = {}
        for key, value in filtered.items():
            if any(pattern in key.lower() for pattern in self.sensitive_patterns):
                masked[key] = '***'
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
                    masked[key] = '***'
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

        with pathlib.Path(output_path).open('w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

    def to_compact_json(self, result: TestCaseResult) -> dict[str, Any]:
        """Convert result to compact JSON format (API responses only).

        This format focuses on API responses and minimal test information.
        Suitable for quick API testing and response extraction.

        Args:
            result: Test case result

        Returns:
            Compact JSON dictionary with API responses
        """
        compact_data = {
            'test_name': result.name,
            'status': result.status,
            'duration': round(result.duration, 2),
            'timestamp': result.start_time.isoformat() if result.start_time else None,
            'api_responses': [],
        }

        # Add statistics
        compact_data['statistics'] = {
            'total': result.total_steps,
            'passed': result.passed_steps,
            'failed': result.failed_steps,
            'skipped': result.skipped_steps,
        }

        # Process each step
        for step_result in result.step_results:
            # Only include steps that have responses (API requests)
            if step_result.response:
                response_data = {
                    'step': step_result.name,
                    'status': step_result.status,
                    'step_index': len(compact_data['api_responses']),
                }

                # Add response data (masked)
                if step_result.response:
                    response_data['response'] = self._mask_sensitive_data(
                        step_result.response
                    )

                # Add status code if available
                if isinstance(step_result.response, dict):
                    if 'status_code' in step_result.response:
                        response_data['status_code'] = step_result.response[
                            'status_code'
                        ]
                    if 'body' in step_result.response:
                        response_data['body'] = step_result.response['body']

                # Add duration if available
                if step_result.start_time and step_result.end_time:
                    duration = (
                        step_result.end_time - step_result.start_time
                    ).total_seconds()
                    response_data['duration'] = round(duration, 3)

                # Add error info if failed
                if step_result.error_info:
                    response_data['error'] = {
                        'type': step_result.error_info.type,
                        'message': step_result.error_info.message,
                    }

                compact_data['api_responses'].append(response_data)

        return compact_data

    def to_csv(self, result: TestCaseResult, verbose: bool = False) -> str:
        """Convert result to CSV format.

        This format generates a CSV with step-by-step details,
        suitable for data analysis in Excel or other tools.

        Args:
            result: Test case result
            verbose: If True, include all performance metrics.
                    If False, only include essential fields.

        Returns:
            CSV formatted string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Write header based on verbose mode
        if verbose:
            # Verbose mode: all performance metrics
            header = [
                'Test Name',
                'Step Name',
                'Step Index',
                'Status',
                'Start Time',
                'End Time',
                'Duration (s)',
                'HTTP Status Code',
                'Response Size (bytes)',
                'Total Time (ms)',
                'DNS Time (ms)',
                'TCP Time (ms)',
                'TLS Time (ms)',
                'Server Time (ms)',
                'Download Time (ms)',
                'Error Type',
                'Error Message',
            ]
        else:
            # Ultra-compact mode: only step name and response info
            header = [
                'Step',
                'Status Code',
                'Status',
            ]
        writer.writerow(header)

        # Write summary row
        pass_rate = (
            result.passed_steps / result.total_steps * 100
            if result.total_steps > 0
            else 0
        )

        if verbose:
            # Verbose mode: all fields
            writer.writerow([
                result.name,
                'SUMMARY',
                '',
                result.status.upper(),
                result.start_time.isoformat() if result.start_time else '',
                result.end_time.isoformat() if result.end_time else '',
                round(result.duration, 3),
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                f'Passed: {result.passed_steps}/{result.total_steps} ({pass_rate:.1f}%)',
            ])
        else:
            # Ultra-compact mode: no summary row, only steps
            pass

        # Write step rows
        for idx, step_result in enumerate(result.step_results, start=1):
            duration = 0.0
            if step_result.start_time and step_result.end_time:
                duration = (
                    step_result.end_time - step_result.start_time
                ).total_seconds()

            # Get HTTP status code from response
            status_code = ''
            if step_result.response and isinstance(step_result.response, dict):
                status_code = step_result.response.get('status_code', '')

            if verbose:
                # Verbose mode: all fields including performance metrics
                # Get response size
                size = ''
                if step_result.performance:
                    size = (
                        str(step_result.performance.size)
                        if step_result.performance.size > 0
                        else ''
                    )

                # Get performance metrics
                total_time = ''
                dns_time = ''
                tcp_time = ''
                tls_time = ''
                server_time = ''
                download_time = ''

                if step_result.performance:
                    total_time = f'{step_result.performance.total_time:.2f}'
                    dns_time = f'{step_result.performance.dns_time:.2f}'
                    tcp_time = f'{step_result.performance.tcp_time:.2f}'
                    tls_time = f'{step_result.performance.tls_time:.2f}'
                    server_time = f'{step_result.performance.server_time:.2f}'
                    download_time = f'{step_result.performance.download_time:.2f}'

                # Get error info
                error_type = ''
                error_message = ''
                if step_result.error_info:
                    error_type = step_result.error_info.type
                    error_message = step_result.error_info.message

                row = [
                    result.name,
                    step_result.name,
                    idx,
                    step_result.status.upper(),
                    step_result.start_time.isoformat()
                    if step_result.start_time
                    else '',
                    step_result.end_time.isoformat() if step_result.end_time else '',
                    round(duration, 3),
                    status_code,
                    size,
                    total_time,
                    dns_time,
                    tcp_time,
                    tls_time,
                    server_time,
                    download_time,
                    error_type,
                    error_message,
                ]
            else:
                # Ultra-compact mode: only step and response info
                row = [
                    step_result.name,
                    status_code,
                    step_result.status.upper(),
                ]

            writer.writerow(row)

        return output.getvalue()

    def save_csv(
        self, result: TestCaseResult, output_path: str, verbose: bool = False
    ) -> None:
        """Save result as CSV file.

        Args:
            result: Test case result
            output_path: Output file path
            verbose: If True, include all performance metrics.
                    If False, only include essential fields.
        """
        csv_data = self.to_csv(result, verbose=verbose)

        with pathlib.Path(output_path).open('w', encoding='utf-8', newline='') as f:
            f.write(csv_data)
