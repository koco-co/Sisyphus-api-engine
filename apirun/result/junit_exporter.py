"""JUnit XML Exporter for Sisyphus API Engine.

This module implements JUnit XML format output for CI/CD integration.
Following Google Python Style Guide.
"""

from datetime import datetime
from io import StringIO
import pathlib
import xml.etree.ElementTree as ET

from apirun.core.models import StepResult, TestCaseResult


class JUnitExporter:
    """Export test results to JUnit XML format.

    JUnit XML format is widely used by CI/CD systems:
    - Jenkins
    - GitHub Actions
    - GitLab CI
    - CircleCI
    - Travis CI
    - And many more

    Format specification:
    - <testsuites>: Root element containing all test suites
    - <testsuite>: A test suite (test case)
    - <testcase>: A single test case (step)
    - <failure>: Failure element for failed tests
    - <error>: Error element for errored tests
    - <skipped>: Skipped element for skipped tests
    """

    def __init__(self, package_name: str = 'sisyphus.api'):
        """Initialize JUnitExporter.

        Args:
            package_name: Package name for the test suite
        """
        self.package_name = package_name

    def to_junit_xml(self, result: TestCaseResult) -> str:
        """Convert test result to JUnit XML format.

        Args:
            result: Test case result

        Returns:
            JUnit XML string
        """
        # Create root element
        testsuites = ET.Element('testsuites')
        testsuites.set('name', result.name)
        testsuites.set('time', str(round(result.duration, 3)))
        testsuites.set('tests', str(result.total_steps))
        testsuites.set('failures', str(result.failed_steps))
        testsuites.set('errors', '0')
        testsuites.set('skipped', str(result.skipped_steps))
        testsuites.set('timestamp', result.start_time.isoformat())

        # Create testsuite element
        testsuite = ET.SubElement(testsuites, 'testsuite')
        testsuite.set('name', result.name)
        testsuite.set('package', self.package_name)
        testsuite.set('time', str(round(result.duration, 3)))
        testsuite.set('tests', str(result.total_steps))
        testsuite.set('failures', str(result.failed_steps))
        testsuite.set('errors', '0')
        testsuite.set('skipped', str(result.skipped_steps))
        testsuite.set('timestamp', result.start_time.isoformat())

        # Add properties if available
        if result.final_variables:
            properties = ET.SubElement(testsuite, 'properties')
            for key, value in result.final_variables.items():
                prop = ET.SubElement(properties, 'property')
                prop.set('name', str(key))
                prop.set('value', str(value))

        # Add system-out and system-err for test case info
        system_out = ET.SubElement(testsuite, 'system-out')
        system_out.text = self._generate_test_summary(result)

        # Add test cases (steps)
        for step_result in result.step_results:
            testcase = self._create_testcase_element(step_result, result)
            testsuite.append(testcase)

        # Generate XML string
        return self._prettify_xml(testsuites)

    def _create_testcase_element(
        self, step_result: StepResult, test_result: TestCaseResult
    ) -> ET.Element:
        """Create a testcase XML element.

        Args:
            step_result: Step result
            test_result: Test case result (for context)

        Returns:
            Testcase XML element
        """
        testcase = ET.Element('testcase')
        testcase.set('name', step_result.name)
        testcase.set('classname', f'{self.package_name}.{test_result.name}')

        # Calculate duration
        duration = 0.0
        if step_result.start_time and step_result.end_time:
            duration = (step_result.end_time - step_result.start_time).total_seconds()
        testcase.set('time', str(round(duration, 3)))

        # Add timestamp
        if step_result.start_time:
            testcase.set('timestamp', step_result.start_time.isoformat())

        # Handle failure/error/skipped status
        if step_result.status == 'failure':
            failure = ET.SubElement(testcase, 'failure')
            failure.set(
                'type',
                step_result.error_info.type
                if step_result.error_info
                else 'AssertionError',
            )
            failure.set(
                'message',
                step_result.error_info.message
                if step_result.error_info
                else 'Step failed',
            )

            # Build failure details
            failure_text = self._build_failure_details(step_result)
            failure.text = failure_text

        elif step_result.status == 'error':
            error = ET.SubElement(testcase, 'error')
            error.set(
                'type',
                step_result.error_info.type if step_result.error_info else 'Error',
            )
            error.set(
                'message',
                step_result.error_info.message
                if step_result.error_info
                else 'Step error',
            )

            # Build error details
            error_text = self._build_error_details(step_result)
            error.text = error_text

        elif step_result.status == 'skipped':
            skipped = ET.SubElement(testcase, 'skipped')
            skipped.set('message', 'Step was skipped')

        # Add system-out with step details
        system_out = ET.SubElement(testcase, 'system-out')
        system_out.text = self._build_step_output(step_result)

        return testcase

    def _build_failure_details(self, step_result: StepResult) -> str:
        """Build detailed failure information.

        Args:
            step_result: Step result

        Returns:
            Formatted failure details
        """
        lines = []
        lines.append(f'Step: {step_result.name}')
        lines.append(f'Status: {step_result.status.upper()}')

        if step_result.error_info:
            lines.append(f'Error Type: {step_result.error_info.type}')
            lines.append(f'Error Category: {step_result.error_info.category.value}')
            lines.append(f'Message: {step_result.error_info.message}')
            if step_result.error_info.suggestion:
                lines.append(f'Suggestion: {step_result.error_info.suggestion}')
            if step_result.error_info.stack_trace:
                lines.append(f'\nStack Trace:\n{step_result.error_info.stack_trace}')

        # Add validation failures if present
        if step_result.validation_results:
            lines.append('\nValidation Failures:')
            for validation in step_result.validation_results:
                if not validation.get('passed', True):
                    lines.append(f'  - {validation.get("description", "N/A")}')
                    lines.append(f'    Path: {validation.get("path", "N/A")}')
                    lines.append(f'    Expected: {validation.get("expected", "N/A")}')
                    lines.append(f'    Actual: {validation.get("actual", "N/A")}')

        # Add response info if available
        if step_result.response:
            lines.append('\nResponse:')
            if isinstance(step_result.response, dict):
                if 'status_code' in step_result.response:
                    lines.append(
                        f'  Status Code: {step_result.response["status_code"]}'
                    )
                if 'body' in step_result.response:
                    lines.append(f'  Body: {str(step_result.response["body"])[:200]}')

        return '\n'.join(lines)

    def _build_error_details(self, step_result: StepResult) -> str:
        """Build detailed error information.

        Args:
            step_result: Step result

        Returns:
            Formatted error details
        """
        return self._build_failure_details(step_result)

    def _build_step_output(self, step_result: StepResult) -> str:
        """Build step output for system-out.

        Args:
            step_result: Step result

        Returns:
            Formatted step output
        """
        lines = []
        lines.append(f'Step: {step_result.name}')
        lines.append(f'Status: {step_result.status.upper()}')

        # Add timing info
        if step_result.start_time and step_result.end_time:
            duration = (step_result.end_time - step_result.start_time).total_seconds()
            lines.append(f'Duration: {duration:.3f}s')

        # Add retry count
        if step_result.retry_count > 0:
            lines.append(f'Retries: {step_result.retry_count}')

        # Add performance metrics if available
        if step_result.performance:
            perf = step_result.performance
            lines.append('\nPerformance Metrics:')
            lines.append(f'  Total Time: {perf.total_time:.2f}ms')
            if perf.dns_time > 0:
                lines.append(f'  DNS Time: {perf.dns_time:.2f}ms')
            if perf.tcp_time > 0:
                lines.append(f'  TCP Time: {perf.tcp_time:.2f}ms')
            if perf.tls_time > 0:
                lines.append(f'  TLS Time: {perf.tls_time:.2f}ms')
            if perf.server_time > 0:
                lines.append(f'  Server Time: {perf.server_time:.2f}ms')
            if perf.download_time > 0:
                lines.append(f'  Download Time: {perf.download_time:.2f}ms')

        # Add extracted variables if present
        if step_result.extracted_vars:
            lines.append('\nExtracted Variables:')
            for key, value in step_result.extracted_vars.items():
                lines.append(f'  {key}: {value}')

        return '\n'.join(lines)

    def _generate_test_summary(self, result: TestCaseResult) -> str:
        """Generate test summary for system-out.

        Args:
            result: Test case result

        Returns:
            Formatted test summary
        """
        lines = []
        lines.append('=' * 60)
        lines.append(f'Test Case: {result.name}')
        lines.append(f'Status: {result.status.upper()}')
        lines.append(f'Duration: {result.duration:.2f}s')
        lines.append('')
        lines.append('Statistics:')
        lines.append(f'  Total Steps: {result.total_steps}')
        lines.append(f'  Passed: {result.passed_steps}')
        lines.append(f'  Failed: {result.failed_steps}')
        lines.append(f'  Skipped: {result.skipped_steps}')
        lines.append(
            f'  Pass Rate: {(result.passed_steps / result.total_steps * 100) if result.total_steps > 0 else 0:.1f}%'
        )
        lines.append('=' * 60)

        return '\n'.join(lines)

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Prettify XML with proper indentation.

        Args:
            elem: Root XML element

        Returns:
            Prettified XML string
        """
        # Add indentation
        self._indent(elem)

        # Generate XML string
        output = StringIO()
        ET.ElementTree(elem).write(
            output,
            encoding='unicode',
            xml_declaration=True,
        )
        return output.getvalue()

    def _indent(self, elem: ET.Element, level: int = 0) -> None:
        """Indent XML elements for pretty printing.

        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent = '\n' + '  ' * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def save_junit_xml(self, result: TestCaseResult, output_path: str) -> None:
        """Save result as JUnit XML file.

        Args:
            result: Test case result
            output_path: Output file path
        """
        xml_content = self.to_junit_xml(result)

        with pathlib.Path(output_path).open('w', encoding='utf-8') as f:
            f.write(xml_content)


class MultiTestSuiteJUnitExporter:
    """Export multiple test results to a single JUnit XML file.

    This is useful when running multiple test cases and generating
    a single JUnit XML report for all of them.
    """

    def __init__(self, package_name: str = 'sisyphus.api'):
        """Initialize MultiTestSuiteJUnitExporter.

        Args:
            package_name: Package name for the test suite
        """
        self.package_name = package_name
        self.results: list[TestCaseResult] = []

    def add_result(self, result: TestCaseResult) -> None:
        """Add a test result to the collection.

        Args:
            result: Test case result
        """
        self.results.append(result)

    def to_junit_xml(self) -> str:
        """Convert all test results to JUnit XML format.

        Returns:
            JUnit XML string
        """
        # Calculate aggregated statistics
        total_tests = sum(r.total_steps for r in self.results)
        total_failures = sum(r.failed_steps for r in self.results)
        total_skipped = sum(r.skipped_steps for r in self.results)
        total_duration = sum(r.duration for r in self.results)

        # Get earliest and latest timestamps
        start_times = [r.start_time for r in self.results if r.start_time]
        end_times = [r.end_time for r in self.results if r.end_time]
        earliest_start = min(start_times) if start_times else datetime.now()
        latest_end = max(end_times) if end_times else datetime.now()

        # Create root element
        testsuites = ET.Element('testsuites')
        testsuites.set('name', 'Sisyphus API Test Suite')
        testsuites.set('time', str(round(total_duration, 3)))
        testsuites.set('tests', str(total_tests))
        testsuites.set('failures', str(total_failures))
        testsuites.set('errors', '0')
        testsuites.set('skipped', str(total_skipped))
        testsuites.set('timestamp', earliest_start.isoformat())

        # Create a testsuite for each test case
        for result in self.results:
            exporter = JUnitExporter(package_name=self.package_name)
            # Parse the XML string and append to testsuites
            xml_str = exporter.to_junit_xml(result)
            suite_elem = ET.fromstring(xml_str)

            # Find the testsuite element and append it
            testsuite = suite_elem.find('testsuite')
            if testsuite is not None:
                testsuites.append(testsuite)

        # Generate XML string
        return self._prettify_xml(testsuites)

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Prettify XML with proper indentation.

        Args:
            elem: Root XML element

        Returns:
            Prettified XML string
        """
        # Add indentation
        self._indent(elem)

        # Generate XML string
        output = StringIO()
        ET.ElementTree(elem).write(
            output,
            encoding='unicode',
            xml_declaration=True,
        )
        return output.getvalue()

    def _indent(self, elem: ET.Element, level: int = 0) -> None:
        """Indent XML elements for pretty printing.

        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent = '\n' + '  ' * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def save_junit_xml(self, output_path: str) -> None:
        """Save all results as JUnit XML file.

        Args:
            output_path: Output file path
        """
        xml_content = self.to_junit_xml()

        with pathlib.Path(output_path).open('w', encoding='utf-8') as f:
            f.write(xml_content)
