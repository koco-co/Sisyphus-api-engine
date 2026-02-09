"""Unit tests for V2YamlParser.

Tests the YAML parsing functionality including:
- File and string parsing
- Config parsing
- Step parsing (all types)
- Validation and extractor parsing
- Error handling
"""

import pathlib
import tempfile

import pytest

from apirun.core.models import (
    GlobalConfig,
    TestCase,
)
from apirun.parser.v2_yaml_parser import (
    V2YamlParser,
    YamlParseError,
    parse_yaml_file,
    parse_yaml_string,
)


class TestV2YamlParserInit:
    """Tests for V2YamlParser initialization."""

    def test_init(self):
        """Test parser initialization."""
        parser = V2YamlParser()
        assert parser is not None


class TestParseBasic:
    """Tests for basic YAML parsing."""

    @pytest.fixture
    def simple_yaml_content(self):
        """Simple YAML test case content."""
        return """
name: "Test Case"
description: "Test description"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "/api/test"
"""

    @pytest.fixture
    def temp_yaml_file(self, simple_yaml_content):
        """Create temporary YAML file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(simple_yaml_content)
            temp_path = f.name
        yield temp_path
        pathlib.Path(temp_path).unlink()

    def test_parse_simple_test_case(self, temp_yaml_file):
        """Test parsing simple test case."""
        parser = V2YamlParser()
        test_case = parser.parse(temp_yaml_file)

        assert isinstance(test_case, TestCase)
        assert test_case.name == 'Test Case'
        assert test_case.description == 'Test description'
        assert len(test_case.steps) == 1
        assert test_case.steps[0].name == 'Step 1'

    def test_parse_string(self, simple_yaml_content):
        """Test parsing YAML string."""
        parser = V2YamlParser()
        test_case = parser.parse_string(simple_yaml_content)

        assert isinstance(test_case, TestCase)
        assert test_case.name == 'Test Case'
        assert len(test_case.steps) == 1

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = V2YamlParser()
        with pytest.raises(FileNotFoundError):
            parser.parse('/nonexistent/file.yaml')

    def test_parse_empty_file(self):
        """Test parsing empty YAML file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write('')
            temp_path = f.name

        try:
            parser = V2YamlParser()
            with pytest.raises(YamlParseError, match='YAML 文件内容为空'):
                parser.parse(temp_path)
        finally:
            pathlib.Path(temp_path).unlink()

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML syntax."""
        invalid_yaml = """
name: "Test"
steps: [
    invalid yaml content
"""

        parser = V2YamlParser()
        with pytest.raises(YamlParseError):
            parser.parse_string(invalid_yaml)

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        parser = V2YamlParser()
        with pytest.raises(YamlParseError, match='YAML 内容为空'):
            parser.parse_string('')


class TestParseConfig:
    """Tests for config section parsing."""

    def test_parse_config_with_profiles(self):
        """Test parsing config with profiles."""
        yaml_content = """
name: "Test"
config:
  profiles:
    dev:
      base_url: "http://dev.example.com"
      variables:
        api_key: "dev_key"
      timeout: 10
    prod:
      base_url: "http://prod.example.com"
  active_profile: "dev"
  variables:
    global_var: "value"
  timeout: 30
  retry_times: 3
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config is not None
        assert isinstance(test_case.config, GlobalConfig)
        assert test_case.config.active_profile == 'dev'
        assert 'dev' in test_case.config.profiles
        assert 'prod' in test_case.config.profiles
        assert test_case.config.profiles['dev'].base_url == 'http://dev.example.com'
        assert test_case.config.profiles['dev'].variables['api_key'] == 'dev_key'
        assert test_case.config.variables['global_var'] == 'value'
        assert test_case.config.timeout == 30
        assert test_case.config.retry_times == 3

    def test_parse_config_no_profiles(self):
        """Test parsing config without profiles."""
        yaml_content = """
name: "Test"
config:
  variables:
    var1: "value1"
  timeout: 20
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config is not None
        assert test_case.config.profiles == {}
        assert test_case.config.variables['var1'] == 'value1'
        assert test_case.config.timeout == 20

    def test_parse_config_none(self):
        """Test parsing with no config section."""
        yaml_content = """
name: "Test"
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config is None

    def test_parse_concurrent_config(self):
        """Test parsing concurrent configuration."""
        yaml_content = """
name: "Test"
config:
  concurrent: true
  concurrent_threads: 5
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.concurrent is True
        assert test_case.config.concurrent_threads == 5

    def test_parse_data_source_config(self):
        """Test parsing data source configuration."""
        yaml_content = """
name: "Test"
config:
  data_source:
    type: csv
    file_path: "data.csv"
  data_iterations: true
  variable_prefix: "data_"
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.data_source is not None
        assert test_case.config.data_source['type'] == 'csv'
        assert test_case.config.data_iterations is True
        assert test_case.config.variable_prefix == 'data_'


class TestParseSteps:
    """Tests for step parsing."""

    def test_parse_request_step(self):
        """Test parsing request step."""
        yaml_content = """
name: "Test"
steps:
  - name: "Get User"
    type: request
    method: GET
    url: "/api/users"
    params:
      id: 123
    headers:
      Authorization: "Bearer token"
    body:
      name: "test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert len(test_case.steps) == 1
        step = test_case.steps[0]
        assert step.name == 'Get User'
        assert step.type == 'request'
        assert step.method == 'GET'  # Parser returns string, not enum
        assert step.url == '/api/users'
        assert step.params == {'id': 123}
        assert step.headers == {'Authorization': 'Bearer token'}
        assert step.body == {'name': 'test'}

    def test_parse_database_step(self):
        """Test parsing database step."""
        yaml_content = """
name: "Test"
steps:
  - name: "Query DB"
    type: database
    database: "test_db"
    operation: query
    sql: "SELECT * FROM users WHERE id = 1"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'database'
        assert step.database == 'test_db'
        assert step.operation == 'query'
        assert step.sql == 'SELECT * FROM users WHERE id = 1'

    def test_parse_wait_step(self):
        """Test parsing wait step."""
        yaml_content = """
name: "Test"
steps:
  - name: "Wait"
    type: wait
    seconds: 5
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'wait'
        assert step.seconds == 5

    def test_parse_wait_step_with_condition(self):
        """Test parsing wait step with condition."""
        yaml_content = """
name: "Test"
steps:
  - name: "Wait for condition"
    type: wait
    condition: "${status} == 'ready'"
    interval: 2
    max_wait: 30
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'wait'
        assert step.condition == "${status} == 'ready'"
        assert step.interval == 2
        assert step.max_wait == 30

    def test_parse_loop_step(self):
        """Test parsing loop step."""
        yaml_content = """
name: "Test"
steps:
  - name: "For loop"
    type: loop
    loop_type: for
    loop_count: 5
    loop_variable: "i"
    loop_steps:
      - name: "Sub step"
        type: request
        method: GET
        url: "/api/items/${i}"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'loop'
        assert step.loop_type == 'for'
        assert step.loop_count == 5
        assert step.loop_variable == 'i'
        assert step.loop_steps is not None
        assert len(step.loop_steps) == 1

    def test_parse_while_loop(self):
        """Test parsing while loop."""
        yaml_content = """
name: "Test"
steps:
  - name: "While loop"
    type: loop
    loop_type: while
    loop_condition: "${count} < 10"
    loop_steps:
      - name: "Action"
        type: request
        method: POST
        url: "/api/action"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.loop_type == 'while'
        assert step.loop_condition == '${count} < 10'

    def test_parse_concurrent_step(self):
        """Test parsing concurrent step."""
        yaml_content = """
name: "Test"
steps:
  - name: "Concurrent requests"
    type: concurrent
    max_concurrency: 10
    concurrent_steps:
      - name: "Request 1"
        type: request
        method: GET
        url: "/api/1"
      - name: "Request 2"
        type: request
        method: GET
        url: "/api/2"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'concurrent'
        assert step.max_concurrency == 10
        assert step.concurrent_steps is not None
        assert len(step.concurrent_steps) == 2

    def test_parse_script_step(self):
        """Test parsing script step."""
        yaml_content = """
name: "Test"
steps:
  - name: "Execute script"
    type: script
    script: |
      result = sum([1, 2, 3])
      set_var("total", result)
    script_type: python
    allow_imports: true
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'script'
        assert 'result = sum([1, 2, 3])' in step.script
        assert step.script_type == 'python'
        assert step.allow_imports is True

    def test_parse_step_default_type(self):
        """Test step defaults to request type."""
        yaml_content = """
name: "Test"
steps:
  - name: "Default type"
    method: GET
    url: "/api/test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.type == 'request'


class TestParseValidations:
    """Tests for validation parsing."""

    def test_parse_validations(self):
        """Test parsing validation rules."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    validations:
      - type: eq
        path: "$.status"
        expect: 200
        description: "Check status"
      - type: contains
        path: "$.data.name"
        expect: "test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.validations) == 2

        val1 = step.validations[0]
        assert val1.type == 'eq'
        assert val1.path == '$.status'
        assert val1.expect == 200
        assert val1.description == 'Check status'

        val2 = step.validations[1]
        assert val2.type == 'contains'
        assert val2.path == '$.data.name'
        assert val2.expect == 'test'

    def test_parse_validation_default_values(self):
        """Test validation default values."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    validations:
      - path: "$.value"
        expect: 100
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.validations) == 1
        val = step.validations[0]
        assert val.type == 'eq'  # default
        assert val.path == '$.value'
        assert val.description == ''  # default


class TestParseExtractors:
    """Tests for extractor parsing."""

    def test_parse_extractors(self):
        """Test parsing variable extractors."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    extractors:
      - name: token
        type: jsonpath
        path: "$.data.token"
      - name: user_id
        type: regex
        path: "id=(\\\\d+)"
        index: 0
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.extractors) == 2

        ext1 = step.extractors[0]
        assert ext1.name == 'token'
        assert ext1.type == 'jsonpath'
        assert ext1.path == '$.data.token'

        ext2 = step.extractors[1]
        assert ext2.name == 'user_id'
        assert ext2.type == 'regex'
        assert ext2.path == 'id=(\\d+)'
        assert ext2.index == 0

    def test_parse_extractor_defaults(self):
        """Test extractor default values."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    extractors:
      - name: value
        path: "$.data.value"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.extractors) == 1
        ext = step.extractors[0]
        assert ext.type == 'jsonpath'  # default
        assert ext.index == 0  # default

    def test_parse_regex_extractor_with_pattern_group(self):
        """Test parsing regex extractor with semantic field names (pattern/group)."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    extractors:
      - name: user_id
        type: regex
        pattern: '"userId":\\s*(\\d+)'
        group: 1
        description: "Extract user ID using pattern/group syntax"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.extractors) == 1
        ext = step.extractors[0]
        assert ext.name == 'user_id'
        assert ext.type == 'regex'
        assert ext.path == '"userId":\\s*(\\d+)'
        assert ext.index == 1

    def test_parse_regex_extractor_backward_compatible(self):
        """Test that regex extractor still supports old path/index syntax."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    extractors:
      - name: user_id
        type: regex
        path: '"userId":\\s*(\\d+)'
        index: 1
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert len(step.extractors) == 1
        ext = step.extractors[0]
        assert ext.name == 'user_id'
        assert ext.type == 'regex'
        assert ext.path == '"userId":\\s*(\\d+)'
        assert ext.index == 1

    def test_parse_regex_extractor_pattern_fallback_to_path(self):
        """Test that pattern takes precedence over path when both are present."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    extractors:
      - name: user_id
        type: regex
        pattern: '"userId":\\s*(\\d+)'
        group: 1
        path: '"userId":\\s*"OLD"'
        index: 0
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        ext = step.extractors[0]
        # pattern should take precedence
        assert ext.path == '"userId":\\s*(\\d+)'
        assert ext.index == 1

    def test_parse_multiple_extractors(self):
        """Test parsing multiple extractors in a single step (Bug fix verification)."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: POST
    url: "/api/test"
    extractors:
      - name: order_id
        type: jsonpath
        path: "$.data.orderId"
      - name: amount
        type: regex
        pattern: '"amount":\\s*([\\d.]+)'
        group: 1
      - name: user_id
        type: jsonpath
        path: "$.data.userId"
      - name: auth_token
        type: header
        path: "Authorization"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        # Verify all extractors are parsed (not just the last one)
        assert len(step.extractors) == 4

        # Verify each extractor
        extractors_dict = {ext.name: ext for ext in step.extractors}
        assert 'order_id' in extractors_dict
        assert 'amount' in extractors_dict
        assert 'user_id' in extractors_dict
        assert 'auth_token' in extractors_dict

        # Verify types and paths
        assert extractors_dict['order_id'].type == 'jsonpath'
        assert extractors_dict['order_id'].path == '$.data.orderId'
        assert extractors_dict['amount'].type == 'regex'
        assert extractors_dict['amount'].path == '"amount":\\s*([\\d.]+)'
        assert extractors_dict['amount'].index == 1
        assert extractors_dict['user_id'].type == 'jsonpath'
        assert extractors_dict['user_id'].path == '$.data.userId'
        assert extractors_dict['auth_token'].type == 'header'


class TestParseStepControl:
    """Tests for step control parsing."""

    def test_parse_skip_if(self):
        """Test parsing skip_if condition."""
        yaml_content = """
name: "Test"
steps:
  - name: "Conditional step"
    type: request
    method: GET
    url: "/api/test"
    skip_if: "${skip_this} == true"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.skip_if == '${skip_this} == true'

    def test_parse_only_if(self):
        """Test parsing only_if condition."""
        yaml_content = """
name: "Test"
steps:
  - name: "Conditional step"
    type: request
    method: GET
    url: "/api/test"
    only_if: "${run_this} == true"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.only_if == '${run_this} == true'

    def test_parse_depends_on(self):
        """Test parsing depends_on."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "/api/step1"
  - name: "Step 2"
    type: request
    method: GET
    url: "/api/step2"
    depends_on:
      - "Step 1"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[1]
        assert step.depends_on == ['Step 1']

    def test_parse_timeout_and_retry(self):
        """Test parsing timeout and retry."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    timeout: 60
    retry_times: 5
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.timeout == 60
        assert step.retry_times == 5

    def test_parse_retry_policy(self):
        """Test parsing retry policy."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    retry_policy:
      max_attempts: 3
      strategy: exponential
      base_delay: 1.0
      max_delay: 10.0
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.retry_policy is not None
        assert step.retry_policy['max_attempts'] == 3
        assert step.retry_policy['strategy'] == 'exponential'


class TestParseSetupTeardown:
    """Tests for setup/teardown parsing."""

    def test_parse_setup_teardown(self):
        """Test parsing step-level setup/teardown."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
    setup:
      - name: "Setup step"
        type: request
        method: POST
        url: "/api/setup"
    teardown:
      - name: "Teardown step"
        type: request
        method: POST
        url: "/api/teardown"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.setup is not None
        assert step.teardown is not None
        assert len(step.setup) == 1
        assert len(step.teardown) == 1

    def test_parse_test_case_setup_teardown(self):
        """Test parsing test case-level setup/teardown."""
        yaml_content = """
name: "Test"
setup:
  - name: "Global setup"
    type: request
    method: POST
    url: "/api/setup"
teardown:
  - name: "Global teardown"
    type: request
    method: POST
    url: "/api/teardown"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.setup is not None
        assert test_case.teardown is not None
        assert len(test_case.setup) == 1
        assert len(test_case.teardown) == 1


class TestParseTagsAndEnabled:
    """Tests for tags and enabled flag parsing."""

    def test_parse_tags(self):
        """Test parsing tags."""
        yaml_content = """
name: "Test"
tags:
  - "smoke"
  - "api"
  - "critical"
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.tags == ['smoke', 'api', 'critical']

    def test_parse_enabled_true(self):
        """Test parsing enabled=true."""
        yaml_content = """
name: "Test"
enabled: true
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.enabled is True

    def test_parse_enabled_false(self):
        """Test parsing enabled=false."""
        yaml_content = """
name: "Test"
enabled: false
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.enabled is False

    def test_parse_enabled_default(self):
        """Test enabled defaults to true."""
        yaml_content = """
name: "Test"
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.enabled is True


class TestValidateYaml:
    """Tests for YAML validation."""

    @pytest.fixture
    def valid_yaml_file(self):
        """Create valid YAML file."""
        content = """
name: "Valid Test"
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        yield temp_path
        pathlib.Path(temp_path).unlink()

    def test_validate_valid_file(self, valid_yaml_file):
        """Test validating valid YAML file."""
        parser = V2YamlParser()
        errors = parser.validate_yaml(valid_yaml_file)
        assert errors == []

    def test_validate_missing_name(self):
        """Test validating YAML with missing name."""
        yaml_content = """
steps:
  - name: "Step"
    type: request
    method: GET
    url: "/api/test"
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            parser = V2YamlParser()
            errors = parser.validate_yaml(temp_path)
            assert any('缺少必填字段: name' in e for e in errors)
        finally:
            pathlib.Path(temp_path).unlink()

    def test_validate_missing_steps(self):
        """Test validating YAML with missing steps."""
        yaml_content = """
name: "Test"
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            parser = V2YamlParser()
            errors = parser.validate_yaml(temp_path)
            assert any('缺少必填字段: steps' in e for e in errors)
        finally:
            pathlib.Path(temp_path).unlink()

    def test_validate_empty_steps(self):
        """Test validating YAML with empty steps."""
        yaml_content = """
name: "Test"
steps: []
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            parser = V2YamlParser()
            errors = parser.validate_yaml(temp_path)
            assert any('不能为空' in e for e in errors)
        finally:
            pathlib.Path(temp_path).unlink()

    def test_validate_invalid_steps_type(self):
        """Test validating YAML with invalid steps type."""
        yaml_content = """
name: "Test"
steps: "invalid"
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            parser = V2YamlParser()
            errors = parser.validate_yaml(temp_path)
            assert any('必须是列表' in e for e in errors)
        finally:
            pathlib.Path(temp_path).unlink()

    def test_validate_file_not_found(self):
        """Test validating non-existent file."""
        parser = V2YamlParser()
        errors = parser.validate_yaml('/nonexistent/file.yaml')
        assert any('文件不存在' in e for e in errors)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def temp_yaml_file(self):
        """Create temporary YAML file."""
        content = """
name: "Test Case"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "/api/test"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        yield temp_path
        pathlib.Path(temp_path).unlink()

    def test_parse_yaml_file(self, temp_yaml_file):
        """Test parse_yaml_file convenience function."""
        test_case = parse_yaml_file(temp_yaml_file)
        assert isinstance(test_case, TestCase)
        assert test_case.name == 'Test Case'

    def test_parse_yaml_string(self):
        """Test parse_yaml_string convenience function."""
        yaml_content = """
name: "Test Case"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "/api/test"
"""
        test_case = parse_yaml_string(yaml_content)
        assert isinstance(test_case, TestCase)
        assert test_case.name == 'Test Case'


class TestStepNameSyntax:
    """Tests for alternative step name syntax."""

    def test_parse_step_with_dict_syntax(self):
        """Test parsing step using dictionary syntax."""
        yaml_content = """
name: "Test"
steps:
  - "Step Name":
      type: request
      method: GET
      url: "/api/test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.name == 'Step Name'

    def test_parse_step_with_name_field(self):
        """Test parsing step using name field."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step Name"
    type: request
    method: GET
    url: "/api/test"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.name == 'Step Name'


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_with_missing_optional_fields(self):
        """Test parsing with minimal required fields."""
        yaml_content = """
name: "Test"
steps:
  - name: "Minimal Step"
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        step = test_case.steps[0]
        assert step.name == 'Minimal Step'
        assert step.type == 'request'  # default

    def test_parse_with_null_values(self):
        """Test parsing with null values."""
        yaml_content = """
name: "Test"
description: null
tags: []
steps: []
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.description is None  # null stays as None
        assert test_case.tags == []

    def test_parse_multiple_steps(self):
        """Test parsing multiple steps."""
        yaml_content = """
name: "Test"
steps:
  - name: "Step 1"
    type: request
    method: GET
    url: "/api/step1"
  - name: "Step 2"
    type: request
    method: POST
    url: "/api/step2"
  - name: "Step 3"
    type: wait
    seconds: 1
"""
        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert len(test_case.steps) == 3
        assert test_case.steps[0].name == 'Step 1'
        assert test_case.steps[1].name == 'Step 2'
        assert test_case.steps[2].name == 'Step 3'
