"""Unit tests for JUnit XML and HTML exporters.

This module contains tests for the JUnit XML and HTML report exporters.
"""

from datetime import datetime
import pathlib
import tempfile
import unittest

from apirun.core.models import (
    ErrorCategory,
    ErrorInfo,
    PerformanceMetrics,
    StepResult,
    TestCaseResult,
)
from apirun.result.html_exporter import HTMLExporter
from apirun.result.junit_exporter import JUnitExporter, MultiTestSuiteJUnitExporter


class TestJUnitExporter(unittest.TestCase):
    """Test cases for JUnit XML exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = JUnitExporter()

    def test_export_simple_result(self):
        """Test exporting a simple test result."""
        # Create a simple test result
        step1 = StepResult(
            name='Test Step 1',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=100.0),
        )

        result = TestCaseResult(
            name='Test Case',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Export to XML
        xml_content = self.exporter.to_junit_xml(result)

        # Verify XML content
        self.assertIn('<?xml version=', xml_content)
        self.assertIn('<testsuites', xml_content)
        self.assertIn('name="Test Case"', xml_content)
        self.assertIn('tests="1"', xml_content)
        self.assertIn('failures="0"', xml_content)
        self.assertIn('<testcase name="Test Step 1"', xml_content)
        self.assertIn('Status: SUCCESS', xml_content)  # Status is in system-out

    def test_export_with_failure(self):
        """Test exporting a test result with failures."""
        error_info = ErrorInfo(
            type='AssertionError',
            category=ErrorCategory.ASSERTION,
            message='Expected 200 but got 404',
            suggestion='Check the URL and parameters',
        )

        step1 = StepResult(
            name='Failed Step',
            status='failure',
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        result = TestCaseResult(
            name='Failed Test Case',
            status='failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=0,
            failed_steps=1,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Export to XML
        xml_content = self.exporter.to_junit_xml(result)

        # Verify failure is included
        self.assertIn('<failure', xml_content)
        self.assertIn('type="AssertionError"', xml_content)
        self.assertIn('Expected 200 but got 404', xml_content)

    def test_save_to_file(self):
        """Test saving JUnit XML to a file."""
        step1 = StepResult(
            name='Step',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name='Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name

        try:
            self.exporter.save_junit_xml(result, temp_path)

            # Verify file exists and has content
            self.assertTrue(pathlib.Path(temp_path).exists())
            with pathlib.Path(temp_path).open() as f:
                content = f.read()
                self.assertIn('<?xml version=', content)
                self.assertIn('<testsuites', content)
        finally:
            # Clean up
            if pathlib.Path(temp_path).exists():
                pathlib.Path(temp_path).unlink()


class TestMultiTestSuiteJUnitExporter(unittest.TestCase):
    """Test cases for multi-test suite JUnit XML exporter."""

    def test_export_multiple_results(self):
        """Test exporting multiple test results."""
        exporter = MultiTestSuiteJUnitExporter()

        # Create two test results
        step1 = StepResult(
            name='Step 1',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result1 = TestCaseResult(
            name='Test Case 1',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        result2 = TestCaseResult(
            name='Test Case 2',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        exporter.add_result(result1)
        exporter.add_result(result2)

        # Export to XML
        xml_content = exporter.to_junit_xml()

        # Verify aggregated content
        self.assertIn('<testsuites', xml_content)
        self.assertIn('tests="2"', xml_content)
        self.assertIn('Test Case 1', xml_content)
        self.assertIn('Test Case 2', xml_content)


class TestHTMLExporter(unittest.TestCase):
    """Test cases for HTML exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = HTMLExporter()

    def test_export_simple_result(self):
        """Test exporting a simple test result."""
        step1 = StepResult(
            name='Test Step 1',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=100.0),
        )

        result = TestCaseResult(
            name='Test Case',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.5,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify HTML content
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<title>Sisyphus API Test Report</title>', html_content)
        self.assertIn('Test Case', html_content)
        self.assertIn('Test Step 1', html_content)
        self.assertIn('passed', html_content)
        self.assertIn('Total Steps', html_content)
        self.assertIn('✓', html_content)

    def test_export_with_failure(self):
        """Test exporting a test result with failures."""
        error_info = ErrorInfo(
            type='AssertionError',
            category=ErrorCategory.ASSERTION,
            message='Expected 200 but got 404',
        )

        step1 = StepResult(
            name='Failed Step',
            status='failure',
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        result = TestCaseResult(
            name='Failed Test Case',
            status='failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=0,
            failed_steps=1,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify failure is included
        self.assertIn('error-box', html_content)
        self.assertIn('AssertionError', html_content)
        self.assertIn('Expected 200 but got 404', html_content)
        self.assertIn('✗', html_content)

    def test_export_with_variables(self):
        """Test exporting with final variables."""
        step1 = StepResult(
            name='Step',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name='Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={
                'username': 'testuser',
                'api_key': 'abc123',
                'token': 'xyz789',
            },
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify variables are included
        self.assertIn('Final Variables', html_content)
        self.assertIn('username', html_content)
        self.assertIn('testuser', html_content)

    def test_save_to_file(self):
        """Test saving HTML to a file."""
        step1 = StepResult(
            name='Step',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name='Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            self.exporter.save_html(result, temp_path)

            # Verify file exists and has content
            self.assertTrue(pathlib.Path(temp_path).exists())
            with pathlib.Path(temp_path).open() as f:
                content = f.read()
                self.assertIn('<!DOCTYPE html>', content)
                self.assertIn('<html', content)
        finally:
            # Clean up
            if pathlib.Path(temp_path).exists():
                pathlib.Path(temp_path).unlink()

    def test_html_theme_support(self):
        """Test HTML theme support (light/dark)."""
        light_exporter = HTMLExporter(theme='light')
        dark_exporter = HTMLExporter(theme='dark')

        step1 = StepResult(
            name='Step',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name='Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={},
        )

        # Export with different themes
        light_html = light_exporter.to_html(result)
        dark_html = dark_exporter.to_html(result)

        # Verify different colors
        self.assertIn('#ffffff', light_html)  # Light theme
        self.assertIn('#1e1e1e', dark_html)  # Dark theme

    def test_new_visualization_sections(self):
        """Test new visualization sections (timeline, variable flow, dependency, performance)."""
        # Create steps with performance metrics and variable data
        step1 = StepResult(
            name='Step 1',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(
                total_time=150.0, dns_time=20.0, tcp_time=30.0
            ),
            extracted_vars={'user_id': '12345'},
            variables_snapshot={},
        )

        step2 = StepResult(
            name='Step 2',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=200.0, server_time=100.0),
            extracted_vars={'token': 'abc123'},
            variables_snapshot={'user_id': '12345'},
            variables_delta={'token': {'new_value': 'abc123'}},
        )

        result = TestCaseResult(
            name='Visualization Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=2,
            passed_steps=2,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1, step2],
            final_variables={'user_id': '12345', 'token': 'abc123'},
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify new visualization sections exist
        self.assertIn('Execution Timeline', html_content)
        self.assertIn('Variable Flow', html_content)
        self.assertIn('Dependency Graph', html_content)
        self.assertIn('Performance Analysis', html_content)

        # Verify timeline components
        self.assertIn('timeline-container', html_content)
        self.assertIn('timeline-bar-wrapper', html_content)

        # Verify variable flow components
        self.assertIn('variable-flow-container', html_content)
        self.assertIn('variable-flow-event', html_content)

        # Verify dependency components
        self.assertIn('dependency-container', html_content)

        # Verify performance analysis components
        self.assertIn('performance-overview', html_content)
        self.assertIn('response-time-chart', html_content)
        self.assertIn('Total Execution Time', html_content)
        self.assertIn('Average Response Time', html_content)

    def test_timeline_with_multiple_steps(self):
        """Test timeline visualization with multiple steps."""
        steps = []
        for i in range(5):
            step = StepResult(
                name=f'Step {i + 1}',
                status='success' if i < 4 else 'failure',
                start_time=datetime.now(),
                end_time=datetime.now(),
                performance=PerformanceMetrics(total_time=100.0 + i * 50),
            )
            steps.append(step)

        result = TestCaseResult(
            name='Timeline Test',
            status='failed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=5.0,
            total_steps=5,
            passed_steps=4,
            failed_steps=1,
            skipped_steps=0,
            step_results=steps,
            final_variables={},
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify timeline bars are generated
        self.assertIn('timeline-bar-fill', html_content)
        # Check that timeline section exists and contains multiple bars
        self.assertIn('timeline-container', html_content)
        self.assertIn('timeline-chart', html_content)
        # Verify at least some timeline bars are present
        self.assertGreater(html_content.count('timeline-bar-wrapper'), 0)

    def test_performance_analysis_metrics(self):
        """Test performance analysis visualization."""
        steps = []
        total_times = [100, 250, 150, 300, 200]

        for i, time in enumerate(total_times):
            step = StepResult(
                name=f'API Request {i + 1}',
                status='success',
                start_time=datetime.now(),
                end_time=datetime.now(),
                performance=PerformanceMetrics(
                    total_time=time,
                    dns_time=10.0,
                    tcp_time=20.0,
                    server_time=time * 0.5,
                ),
            )
            steps.append(step)

        result = TestCaseResult(
            name='Performance Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=5.0,
            total_steps=5,
            passed_steps=5,
            failed_steps=0,
            skipped_steps=0,
            step_results=steps,
            final_variables={},
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify performance sections
        self.assertIn('Slowest Steps', html_content)
        self.assertIn('Fastest Steps', html_content)
        self.assertIn('Response Time Distribution', html_content)
        self.assertIn('perf-bar-item', html_content)

        # Check that statistics are calculated
        self.assertIn('1000.00ms', html_content)  # Total time (sum of all)
        self.assertIn('200.00ms', html_content)  # Average time

    def test_variable_flow_tracking(self):
        """Test variable flow diagram."""
        step1 = StepResult(
            name='Login',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            extracted_vars={'user_id': '123', 'session_token': 'xyz'},
        )

        step2 = StepResult(
            name='Get Profile',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            extracted_vars={'username': 'john'},
            variables_snapshot={'user_id': '123'},
        )

        result = TestCaseResult(
            name='Variable Flow Test',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=2,
            passed_steps=2,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1, step2],
            final_variables={
                'user_id': '123',
                'session_token': 'xyz',
                'username': 'john',
            },
        )

        # Export to HTML
        html_content = self.exporter.to_html(result)

        # Verify variable flow events are shown
        self.assertIn('variable-flow-event', html_content)
        self.assertIn('Created', html_content)
        self.assertIn('user_id', html_content)
        self.assertIn('session_token', html_content)

    def test_chinese_language_support(self):
        """Test Chinese language support for new visualizations."""
        zh_exporter = HTMLExporter(language='zh')

        step1 = StepResult(
            name='测试步骤',
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=100.0),
            extracted_vars={'user_id': '123'},
        )

        result = TestCaseResult(
            name='测试用例',
            status='passed',
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={'user_id': '123'},
        )

        # Export to HTML
        html_content = zh_exporter.to_html(result)

        # Verify Chinese labels
        self.assertIn('执行时序图', html_content)
        self.assertIn('变量流转图', html_content)
        self.assertIn('依赖关系图', html_content)
        self.assertIn('性能分析', html_content)
        self.assertIn('总执行时间', html_content)
        self.assertIn('平均响应时间', html_content)


if __name__ == '__main__':
    unittest.main()
