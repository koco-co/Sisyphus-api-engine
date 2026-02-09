"""Integration tests for nested variable reference feature.

Tests for the new feature that allows variables in config.variables
to reference config.profiles.* values.
"""

from apirun.parser.v2_yaml_parser import V2YamlParser


class TestNestedVariableReference:
    """Tests for nested variable reference in YAML config."""

    def test_parse_yaml_with_nested_references(self):
        """Test parsing YAML with nested variable references."""
        yaml_content = """
name: "测试用例"
config:
  profiles:
    dev:
      variables:
        test_suffix: "0202093000"
    prod:
      variables:
        test_suffix: "PROD123"
  active_profile: "dev"

  variables:
    category_name: "test_${config.profiles.dev.variables.test_suffix}"
    datasource_name: "ds_${config.profiles.dev.variables.test_suffix}"

steps:
  - name: "测试步骤"
    type: request
    url: "https://httpbin.org/get"
    method: GET
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        # Verify the test case was parsed
        assert test_case.name == '测试用例'
        assert test_case.config is not None
        assert test_case.config.variables is not None

        # Verify nested references were rendered correctly
        assert 'category_name' in test_case.config.variables
        assert test_case.config.variables['category_name'] == 'test_0202093000'

        assert 'datasource_name' in test_case.config.variables
        assert test_case.config.variables['datasource_name'] == 'ds_0202093000'

    def test_multiple_nested_references(self):
        """Test multiple nested references in one variable."""
        yaml_content = """
name: "多级嵌套引用测试"
config:
  profiles:
    ci_62:
      variables:
        test_suffix: "0202093000"
        env: "ci"
  active_profile: "ci_62"

  variables:
    # Combine multiple nested references
    combined: "${config.profiles.ci_62.variables.test_suffix}_${config.profiles.ci_62.variables.env}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.variables['combined'] == '0202093000_ci'

    def test_reference_active_profile(self):
        """Test referencing active_profile variable."""
        yaml_content = """
name: "Active Profile 引用测试"
config:
  profiles:
    dev:
      base_url: "http://dev.api.com"
    prod:
      base_url: "http://prod.api.com"
  active_profile: "dev"

  variables:
    environment: "${config.active_profile}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        # active_profile 可以直接引用
        assert test_case.config.variables['environment'] == 'dev'

    def test_known_limitation_dynamic_key_access(self):
        """Test known limitation: cannot dynamically access dictionary keys."""
        yaml_content = """
name: "动态键访问限制测试"
config:
  profiles:
    dev:
      base_url: "http://dev.api.com"
  active_profile: "dev"

  variables:
    # ❌ 这不支持 - Jinja2 不允许嵌套的 ${}
    # api_url: "${config.profiles.${config.active_profile}.base_url}"

    # ✅ 正确做法: 直接指定 profile 名称
    api_url: "${config.profiles.dev.base_url}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        # 直接引用可以工作
        assert test_case.config.variables['api_url'] == 'http://dev.api.com'

    def test_complex_nested_scenario(self):
        """Test complex nested reference scenario from the actual use case."""
        yaml_content = """
name: "复杂嵌套场景"
config:
  profiles:
    ci_62:
      variables:
        test_suffix: "0202093000"
        prefix: "test"
  active_profile: "ci_62"

  variables:
    category_name: "test_${config.profiles.ci_62.variables.test_suffix}"
    datasource_name: "ds_${config.profiles.ci_62.variables.test_suffix}"
    full_name: "${config.profiles.ci_62.variables.prefix}_${config.profiles.ci_62.variables.test_suffix}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.variables['category_name'] == 'test_0202093000'
        assert test_case.config.variables['datasource_name'] == 'ds_0202093000'
        assert test_case.config.variables['full_name'] == 'test_0202093000'

    def test_nested_reference_with_non_string_values(self):
        """Test nested references with numeric values."""
        yaml_content = """
name: "数值嵌套引用"
config:
  profiles:
    dev:
      variables:
        timeout: 30
        retry_count: 3
  active_profile: "dev"

  variables:
    dev_timeout: "${config.profiles.dev.variables.timeout}"
    max_retries: "${config.profiles.dev.variables.retry_count}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        # Numeric values should be rendered as strings
        assert test_case.config.variables['dev_timeout'] == '30'
        assert test_case.config.variables['max_retries'] == '3'

    def test_backward_compatibility(self):
        """Test that old syntax without nested references still works."""
        yaml_content = """
name: "向后兼容性测试"
config:
  profiles:
    dev:
      base_url: "http://dev.api.com"
  active_profile: "dev"

  variables:
    # Old-style variables without nested references
    api_key: "12345"
    username: "testuser"
    base_url: "http://static.url.com"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.variables['api_key'] == '12345'
        assert test_case.config.variables['username'] == 'testuser'
        assert test_case.config.variables['base_url'] == 'http://static.url.com'

    def test_empty_config_context(self):
        """Test handling of empty config context."""
        yaml_content = """
name: "空配置上下文测试"
config:
  variables:
    simple_var: "value"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        # Should work fine without profiles
        assert test_case.config.variables['simple_var'] == 'value'

    def test_mixed_variables(self):
        """Test mixing nested references with regular variables."""
        yaml_content = """
name: "混合变量测试"
config:
  profiles:
    dev:
      variables:
        suffix: "123"
  active_profile: "dev"

  variables:
    # Regular variable
    static_value: "static"
    # Variable referencing another global variable
    ref_static: "${static_value}"
    # Variable referencing config
    nested_ref: "test_${config.profiles.dev.variables.suffix}"
    # Complex combination
    combined: "${ref_static}_${nested_ref}"

steps: []
"""

        parser = V2YamlParser()
        test_case = parser.parse_string(yaml_content)

        assert test_case.config.variables['static_value'] == 'static'
        assert test_case.config.variables['ref_static'] == 'static'
        assert test_case.config.variables['nested_ref'] == 'test_123'
        assert test_case.config.variables['combined'] == 'static_test_123'
