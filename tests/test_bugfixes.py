"""Test cases for bug fixes.

Tests for:
1. JSONPath Extractor complex expression support (filter expressions)
2. Variable nested reference rendering
3. Contains validator for arrays
4. Microsecond timestamp support
"""

import pytest
from apirun.utils.enhanced_jsonpath import extract_value
from apirun.core.variable_manager import VariableManager
from apirun.validation.comparators import Comparators
from apirun.core.template_functions import now_us, timestamp_us


class TestJSONPathEnhancements:
    """Test JSONPath enhanced features."""

    def test_filter_expression_not_equal(self):
        """Test filter expression with != operator."""
        data = {
            "data": {
                "data": [
                    {"id": 1, "roleName": "项目所有者"},
                    {"id": 2, "roleName": "开发者"},
                    {"id": 3, "roleName": "测试员"}
                ]
            }
        }

        # Extract all non-owner role IDs
        result = extract_value(
            "$.data.data[?(@.roleName != '项目所有者')].id",
            data,
            index=-1
        )
        assert result == [2, 3], f"Expected [2, 3], got {result}"

    def test_filter_expression_equals(self):
        """Test filter expression with == operator."""
        data = {
            "users": [
                {"name": "Alice", "role": "admin"},
                {"name": "Bob", "role": "user"},
                {"name": "Charlie", "role": "admin"}
            ]
        }

        # Extract admin names
        result = extract_value(
            "$.users[?(@.role == 'admin')].name",
            data,
            index=-1
        )
        assert result == ["Alice", "Charlie"], f"Expected ['Alice', 'Charlie'], got {result}"

    def test_array_index_simple(self):
        """Test simple array indexing."""
        data = {
            "data": {
                "data": [
                    {"id": 1, "name": "first"},
                    {"id": 2, "name": "second"},
                    {"id": 3, "name": "third"}
                ]
            }
        }

        # Extract second element
        result = extract_value("$.data.data[1].id", data)
        assert result == 2, f"Expected 2, got {result}"

    def test_array_wildcard(self):
        """Test wildcard array access."""
        data = {
            "users": [
                {"name": "Alice"},
                {"name": "Bob"}
            ]
        }

        # Extract all names
        result = extract_value("$.users[*].name", data, index=-1)
        assert result == ["Alice", "Bob"], f"Expected ['Alice', 'Bob'], got {result}"

    def test_combined_filter_and_projection(self):
        """Test filter combined with field projection."""
        data = {
            "items": [
                {"id": 1, "price": 100, "active": True},
                {"id": 2, "price": 200, "active": False},
                {"id": 3, "price": 150, "active": True}
            ]
        }

        # Note: jsonpath-ng uses lowercase 'true' in filter expressions
        # Also doesn't support complex AND in single filter, so we do numeric filter only
        # Extract IDs of items with price > 120
        result = extract_value(
            "$.items[?(@.price > 120)].id",
            data,
            index=-1
        )
        assert set(result) == {2, 3}, f"Expected {{2, 3}}, got {set(result)}"

        # Test active filter separately
        result = extract_value(
            "$.items[?(@.active == true)].id",
            data,
            index=-1
        )
        assert result == [1, 3], f"Expected [1, 3], got {result}"

    def test_filter_with_string_comparison(self):
        """Test filter with string comparison."""
        data = {
            "users": [
                {"id": 1, "role": "admin", "name": "Alice"},
                {"id": 2, "role": "user", "name": "Bob"},
                {"id": 3, "role": "admin", "name": "Charlie"}
            ]
        }

        # Extract admin IDs
        result = extract_value(
            "$.users[?(@.role == 'admin')].id",
            data,
            index=-1
        )
        assert result == [1, 3], f"Expected [1, 3], got {result}"


class TestVariableNestedReference:
    """Test variable nested reference rendering."""

    def test_nested_variable_reference(self):
        """Test nested variable references."""
        vm = VariableManager()

        # Set base variable
        vm.global_vars["test_suffix"] = "0129"

        # Set variable with nested reference
        vm.global_vars["param_name"] = "test_param_${test_suffix}"

        # Render should resolve the nested reference
        result = vm.render_string("${param_name}")

        assert result == "test_param_0129", f"Expected 'test_param_0129', got '{result}'"

    def test_multi_level_nested_reference(self):
        """Test multiple levels of nested references."""
        vm = VariableManager()

        # Set base variables
        vm.global_vars["base"] = "api"
        vm.global_vars["env"] = "dev"
        vm.global_vars["version"] = "v1"

        # Set nested variables
        vm.global_vars["url1"] = "${base}.${env}.com"
        vm.global_vars["url2"] = "${url1}/${version}"

        # Render should resolve all levels
        result = vm.render_string("${url2}")

        assert result == "api.dev.com/v1", f"Expected 'api.dev.com/v1', got '{result}'"

    def test_recursive_rendering_limit(self):
        """Test that recursive rendering has a safe limit."""
        vm = VariableManager()

        # Create a circular reference
        vm.global_vars["var1"] = "${var2}"
        vm.global_vars["var2"] = "${var1}"

        # Should not hang, but return the partially rendered result
        result = vm.render_string("${var1}", max_iterations=5)

        # After iterations, it should have stopped (either var1 or var2)
        assert "${" in result or result == "var2" or result == "var1"


class TestContainsValidator:
    """Test contains validator improvements."""

    def test_contains_in_list(self):
        """Test contains with list."""
        actual = ["apple", "banana", "cherry"]
        expected = "banana"
        assert Comparators.contains(actual, expected) is True

    def test_contains_not_in_list(self):
        """Test contains with value not in list."""
        actual = ["apple", "banana", "cherry"]
        expected = "grape"
        assert Comparators.contains(actual, expected) is False

    def test_contains_in_string(self):
        """Test contains with string."""
        actual = "Hello World"
        expected = "World"
        assert Comparators.contains(actual, expected) is True

    def test_contains_with_none_actual(self):
        """Test contains with None actual value."""
        actual = None
        expected = "test"
        assert Comparators.contains(actual, expected) is False

    def test_contains_with_none_in_list(self):
        """Test contains when list contains None values."""
        actual = ["value1", None, "value2"]
        expected = None
        # None should be found in the list
        assert Comparators.contains(actual, expected) is True

    def test_contains_empty_list(self):
        """Test contains with empty list."""
        actual = []
        expected = "test"
        assert Comparators.contains(actual, expected) is False

    def test_contains_numeric_in_list(self):
        """Test contains with numeric values."""
        actual = [1, 2, 3, 4, 5]
        expected = 3
        assert Comparators.contains(actual, expected) is True

    def test_contains_dict_keys(self):
        """Test contains with dict keys."""
        actual = {"name": "Alice", "age": 30}
        expected = "name"
        assert Comparators.contains(actual, expected) is True


class TestMicrosecondTimestamp:
    """Test microsecond timestamp support."""

    def test_now_us_format(self):
        """Test now_us() returns correct format."""
        result = now_us()
        # Should be 20 characters: YYYYMMDDHHMMSS + 6 digits microseconds
        assert len(result) == 20, f"Expected length 20, got {len(result)}: '{result}'"
        assert result.isdigit(), f"Expected all digits, got: '{result}'"

    def test_timestamp_us_is_integer(self):
        """Test timestamp_us() returns integer."""
        result = timestamp_us()
        assert isinstance(result, int), f"Expected int, got {type(result)}"
        # Should be a large number (microseconds since epoch)
        assert result > 1_000_000_000_000_000, f"Timestamp too small: {result}"

    def test_now_with_microseconds(self):
        """Test that now().strftime('%f') works correctly."""
        from apirun.core.template_functions import now
        dt = now()
        microsecond_str = dt.strftime('%f')
        # Should be 6 digits
        assert len(microsecond_str) == 6, f"Expected 6 digits, got {len(microsecond_str)}: '{microsecond_str}'"
        assert microsecond_str.isdigit(), f"Expected all digits, got: '{microsecond_str}'"

    def test_microsecond_precision(self):
        """Test that microseconds provide additional precision."""
        import time

        # Get two timestamps in quick succession
        ts1 = now_us()
        time.sleep(0.001)  # Sleep 1ms
        ts2 = now_us()

        # They should be different (at least in the last 3 digits representing milliseconds)
        assert ts1 != ts2, "Microsecond timestamps should differ even with small delay"

    def test_render_microsecond_template(self):
        """Test rendering microsecond timestamp in template."""
        vm = VariableManager()
        result = vm.render_string("${now_us()}")
        assert len(result) == 20, f"Expected length 20, got {len(result)}: '{result}'"
        assert result.isdigit(), f"Expected all digits, got: '{result}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
