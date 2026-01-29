"""Unit tests for JUnit XML and HTML exporters.

This module contains tests for the JUnit XML and HTML report exporters.
"""

import unittest
import tempfile
import os
from datetime import datetime

from apirun.result.junit_exporter import JUnitExporter, MultiTestSuiteJUnitExporter
from apirun.result.html_exporter import HTMLExporter
from apirun.core.models import (
    TestCaseResult,
    StepResult,
    PerformanceMetrics,
    ErrorInfo,
    ErrorCategory,
)


class TestJUnitExporter(unittest.TestCase):
    """Test cases for JUnit XML exporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = JUnitExporter()

    def test_export_simple_result(self):
        """Test exporting a simple test result."""
        # Create a simple test result
        step1 = StepResult(
            name="Test Step 1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=100.0),
        )

        result = TestCaseResult(
            name="Test Case",
            status="passed",
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
            type="AssertionError",
            category=ErrorCategory.ASSERTION,
            message="Expected 200 but got 404",
            suggestion="Check the URL and parameters",
        )

        step1 = StepResult(
            name="Failed Step",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        result = TestCaseResult(
            name="Failed Test Case",
            status="failed",
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
            name="Step",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name="Test",
            status="passed",
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
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('<?xml version=', content)
                self.assertIn('<testsuites', content)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestMultiTestSuiteJUnitExporter(unittest.TestCase):
    """Test cases for multi-test suite JUnit XML exporter."""

    def test_export_multiple_results(self):
        """Test exporting multiple test results."""
        exporter = MultiTestSuiteJUnitExporter()

        # Create two test results
        step1 = StepResult(
            name="Step 1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result1 = TestCaseResult(
            name="Test Case 1",
            status="passed",
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
            name="Test Case 2",
            status="passed",
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
            name="Test Step 1",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            performance=PerformanceMetrics(total_time=100.0),
        )

        result = TestCaseResult(
            name="Test Case",
            status="passed",
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
            type="AssertionError",
            category=ErrorCategory.ASSERTION,
            message="Expected 200 but got 404",
        )

        step1 = StepResult(
            name="Failed Step",
            status="failure",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_info=error_info,
        )

        result = TestCaseResult(
            name="Failed Test Case",
            status="failed",
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
            name="Step",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name="Test",
            status="passed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=1.0,
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            skipped_steps=0,
            step_results=[step1],
            final_variables={
                "username": "testuser",
                "api_key": "abc123",
                "token": "xyz789",
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
            name="Step",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name="Test",
            status="passed",
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
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('<!DOCTYPE html>', content)
                self.assertIn('<html', content)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_html_theme_support(self):
        """Test HTML theme support (light/dark)."""
        light_exporter = HTMLExporter(theme="light")
        dark_exporter = HTMLExporter(theme="dark")

        step1 = StepResult(
            name="Step",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result = TestCaseResult(
            name="Test",
            status="passed",
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


if __name__ == '__main__':
    unittest.main()
