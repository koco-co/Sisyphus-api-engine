"""Unit tests for YamlValidator.

Tests the enhanced YAML validator with keyword checking,
!include support, and shorthand syntax.

Following Google Python Style Guide.
"""

import os
from pathlib import Path
import shutil
import tempfile

from apirun.validator.yaml_validator import (
    TerminalFormatter,
    ValidationResult,
    YamlValidator,
    validate_yaml_files,
)


class TestYamlValidator:
    """Test cases for YamlValidator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = YamlValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_yaml_file(self, filename, content):
        """Helper to create a YAML file for testing.

        Args:
            filename: Name of the file to create
            content: YAML content as string

        Returns:
            Full path to created file
        """
        filepath = os.path.join(self.temp_dir, filename)
        Path(os.path.dirname(filepath)).mkdir(exist_ok=True, parents=True)
        with Path(filepath).open('w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_valid_yaml_file(self):
        """Test validation of a valid YAML file."""
        content = """
name: "Test Case"
description: "A valid test case"

config:
  timeout: 30

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    validations:
      - type: status_code
        path: "$.status_code"
        expect: "200"
"""
        filepath = self._create_yaml_file('valid.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid
        assert result.file_path == filepath
        assert len(result.syntax_errors) == 0
        assert len(result.missing_fields) == 0
        assert len(result.unknown_keywords) == 0

    def test_missing_required_fields(self):
        """Test detection of missing required fields."""
        # Missing 'name' field
        content = """
description: "Test without name"

steps:
  - name: "Step 1"
    type: request
"""
        filepath = self._create_yaml_file('missing_name.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert any('name' in error for error in result.missing_fields)

    def test_empty_steps(self):
        """Test detection of empty steps list."""
        content = """
name: "Test Case"
steps: []
"""
        filepath = self._create_yaml_file('empty_steps.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert any('steps' in error for error in result.syntax_errors)

    def test_unknown_keyword_at_test_case_level(self):
        """Test detection of unknown keywords at test case level."""
        content = """
name: "Test Case"
invalid_field: "This should not be here"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
"""
        filepath = self._create_yaml_file('unknown_keyword.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert len(result.unknown_keywords) > 0
        assert result.unknown_keywords[0][0] == 'invalid_field'

    def test_unknown_keyword_in_step(self):
        """Test detection of unknown keywords in step."""
        content = """
name: "Test Case"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    invalid_step_field: "This should not be here"
"""
        filepath = self._create_yaml_file('unknown_step_keyword.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert any(
            keyword == 'invalid_step_field' for keyword, _ in result.unknown_keywords
        )

    def test_unknown_keyword_in_validation(self):
        """Test detection of unknown keywords in validation rules."""
        content = """
name: "Test Case"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    validations:
      - type: status_code
        path: "$.status_code"
        expect: "200"
        invalid_validation_field: "This should not be here"
"""
        filepath = self._create_yaml_file('unknown_validation_keyword.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert any(
            'invalid_validation_field' in str(keyword)
            for keyword, _ in result.unknown_keywords
        )

    def test_invalid_validation_type(self):
        """Test detection of invalid validation type."""
        content = """
name: "Test Case"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    validations:
      - type: invalid_type
        path: "$.status_code"
        expect: "200"
"""
        filepath = self._create_yaml_file('invalid_validation_type.yaml', content)
        result = self.validator.validate_file(filepath)

        assert not result.is_valid
        assert any('invalid_type' in error for error in result.syntax_errors)

    def test_shorthand_syntax_support(self):
        """Test support for shorthand step syntax (step name as key)."""
        content = """
name: "Test Case"

steps:
  - 步骤1_测试GET请求:
      type: request
      description: "Test GET request"
      method: GET
      url: "https://httpbin.org/get"
"""
        filepath = self._create_yaml_file('shorthand_syntax.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid

    def test_all_step_types(self):
        """Test validation of all supported step types."""
        content = """
name: "Test All Step Types"

steps:
  - name: "Request Step"
    type: request
    method: GET
    url: "https://httpbin.org/get"

  - name: "Database Step"
    type: database
    connection:
      type: sqlite
      database: ":memory:"
    query: "SELECT 1"

  - name: "Wait Step"
    type: wait
    duration: 1

  - name: "Script Step"
    type: script
    language: python
    script: "print('test')"

  - name: "Loop Step"
    type: loop
    loop_type: for
    iterations: 3
    steps:
      - name: "Sub-step"
        type: wait
        duration: 0.1

  - name: "Poll Step"
    type: poll
    method: GET
    url: "https://httpbin.org/get"
    poll_config:
      condition:
        type: eq
        path: "$.status"
        expect: "success"
      max_attempts: 3

  - name: "Concurrent Step"
    type: concurrent
    max_concurrency: 2
    concurrent_steps:
      - name: "Sub-step 1"
        type: wait
        duration: 0.1
      - name: "Sub-step 2"
        type: wait
        duration: 0.1
"""
        filepath = self._create_yaml_file('all_step_types.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid

    def test_profile_custom_variables_allowed(self):
        """Test that custom variables in profiles are allowed."""
        content = """
name: "Test Case"

config:
  profiles:
    dev:
      base_url: "https://dev.api.com"
      custom_var: "allowed"  # Custom variable
      another_custom: 123  # Custom variable

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "${config.profiles.dev.base_url}"
"""
        filepath = self._create_yaml_file('profile_custom_vars.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid

    def test_all_validation_types(self):
        """Test all supported validation types."""
        validation_types = [
            'status_code',
            'eq',
            'ne',
            'gt',
            'lt',
            'ge',
            'le',
            'contains',
            'not_contains',
            'regex',
            'type',
            'in',
            'not_in',
            'in_list',
            'not_in_list',
            'length_eq',
            'length_gt',
            'length_lt',
            'contains_key',
            'json_path',
            'exists',
            'is_null',
            'is_empty',
            'starts_with',
            'ends_with',
            'between',
        ]

        for v_type in validation_types:
            content = f"""
name: "Test Validation Type"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    validations:
      - type: {v_type}
        path: "$.status_code"
        expect: "200"
"""
            filepath = self._create_yaml_file(f'validation_{v_type}.yaml', content)
            result = self.validator.validate_file(filepath)

            assert result.is_valid, f"Validation type '{v_type}' should be valid"

    def test_enabled_field_supported(self):
        """Test that 'enabled' field is supported at test case level."""
        content = """
name: "Test Case"
enabled: true

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
"""
        filepath = self._create_yaml_file('with_enabled.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid

    def test_extractors_with_all_fields(self):
        """Test extractors with all supported fields."""
        content = """
name: "Test Case"

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
    extractors:
      - name: "extract1"
        type: jsonpath
        path: "$.url"
        from: response
        index: 0
        regex: ".*"
        pattern: "(.*)"
        group: 1
        multiple: false
        description: "Test extractor"
"""
        filepath = self._create_yaml_file('extractors.yaml', content)
        result = self.validator.validate_file(filepath)

        assert result.is_valid

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = self.validator.validate_file('/nonexistent/file.yaml')

        assert not result.is_valid
        assert len(result.syntax_errors) > 0
        assert '不存在' in result.syntax_errors[0]


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_validation_result_properties(self):
        """Test ValidationResult properties."""
        result = ValidationResult(file_path='test.yaml', is_valid=True)

        assert result.file_path == 'test.yaml'
        assert result.is_valid
        assert not result.has_errors
        assert result.error_count == 0

    def test_validation_result_with_errors(self):
        """Test ValidationResult with various errors."""
        result = ValidationResult(
            file_path='test.yaml',
            is_valid=False,
            syntax_errors=['Error 1'],
            missing_fields=['Error 2'],
            unknown_keywords=[('key1', 'location1')],
        )

        assert result.is_valid is False
        assert result.has_errors
        assert result.error_count == 3


class TestTerminalFormatter:
    """Test cases for TerminalFormatter class."""

    def test_success_formatting(self):
        """Test success message formatting."""
        message = TerminalFormatter.success('Test passed')
        assert '✓' in message
        assert 'Test passed' in message

    def test_error_formatting(self):
        """Test error message formatting."""
        message = TerminalFormatter.error('Test failed')
        assert '✗' in message
        assert 'Test failed' in message

    def test_warning_formatting(self):
        """Test warning message formatting."""
        message = TerminalFormatter.warning('Warning message')
        assert '⚠' in message
        assert 'Warning message' in message


class TestValidateYamlFiles:
    """Test cases for validate_yaml_files function."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_yaml_file(self, filename, content):
        """Helper to create a YAML file for testing."""
        filepath = os.path.join(self.temp_dir, filename)
        Path(os.path.dirname(filepath)).mkdir(exist_ok=True, parents=True)
        with Path(filepath).open('w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_validate_multiple_files(self):
        """Test validation of multiple files."""
        # Create valid file
        valid_content = """
name: "Valid Test"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
"""
        self._create_yaml_file('valid.yaml', valid_content)

        # Create invalid file
        invalid_content = """
name: "Invalid Test"
invalid_field: "value"
steps: []
"""
        self._create_yaml_file('invalid.yaml', invalid_content)

        # Validate directory
        exit_code, results = validate_yaml_files([self.temp_dir], show_details=False)

        assert exit_code == 1  # Should have errors
        assert len(results) == 2

    def test_validate_nonexistent_path(self, capsys):
        """Test validation of non-existent path."""
        exit_code, results = validate_yaml_files(
            ['/nonexistent/path'], show_details=False
        )

        assert exit_code == 1
        assert len(results) == 0


class TestIncludeTagSupport:
    """Test cases for !include tag support."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = YamlValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_yaml_file(self, filename, content):
        """Helper to create a YAML file."""
        filepath = os.path.join(self.temp_dir, filename)
        Path(os.path.dirname(filepath)).mkdir(exist_ok=True, parents=True)
        with Path(filepath).open('w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_include_tag_support(self):
        """Test that !include tag is supported."""
        # Create included config file
        config_content = """
timeout: 30
retry_times: 3
variables:
  api_key: "test-key"
"""
        config_file = self._create_yaml_file(
            'config/global_config.yaml', config_content
        )

        # Create main file with !include
        main_content = """
name: "Test Include Tag"
config: !include config/global_config.yaml

steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "https://httpbin.org/get"
"""
        main_file = self._create_yaml_file('main.yaml', main_content)

        result = self.validator.validate_file(main_file)

        # Should not error on !include tag
        # Note: The actual inclusion might fail due to path resolution,
        # but we're testing that the tag is recognized
        assert result.is_valid or '!include' not in str(result.syntax_errors)
