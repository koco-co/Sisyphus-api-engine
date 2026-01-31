"""Unit tests for template functions.

Tests for built-in template functions that can be used in variable expressions.
"""

import pytest
import re
from apirun.core.variable_manager import VariableManager


class TestTemplateFunctions:
    """Tests for built-in template functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.vm = VariableManager()

    def test_random_function(self):
        """Test random() function generates integers."""
        result = self.vm.render_string("${random()}")
        assert result.isdigit()
        # Should be between 0 and 1000000
        value = int(result)
        assert 0 <= value <= 1000000

    def test_random_with_range(self):
        """Test random(min, max) function."""
        result = self.vm.render_string("${random(1, 10)}")
        value = int(result)
        assert 1 <= value <= 10

    def test_random_str_function(self):
        """Test random_str() function generates strings."""
        result = self.vm.render_string("${random_str()}")
        assert len(result) == 8
        assert result.isalnum()

    def test_random_str_with_length(self):
        """Test random_str(length) function."""
        result = self.vm.render_string("${random_str(16)}")
        assert len(result) == 16
        assert result.isalnum()

    def test_random_str_with_custom_chars(self):
        """Test random_str(length, chars) function."""
        result = self.vm.render_string("${random_str(4, 'ABC')}")
        assert len(result) == 4
        assert all(c in "ABC" for c in result)

    def test_uuid_function(self):
        """Test uuid() function generates UUID without dashes."""
        result = self.vm.render_string("${uuid()}")
        assert len(result) == 32
        assert result.isalnum()
        assert "-" not in result

    def test_uuid4_function(self):
        """Test uuid4() function generates standard UUID."""
        result = self.vm.render_string("${uuid4()}")
        # Standard UUID format: 8-4-4-4-12
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        )
        assert uuid_pattern.match(result) is not None

    def test_timestamp_function(self):
        """Test timestamp() function generates Unix timestamp."""
        result = self.vm.render_string("${timestamp()}")
        assert result.isdigit()
        value = int(result)
        # Should be recent timestamp (after 2020, before 2100)
        assert 1577836800 <= value <= 4102444800

    def test_timestamp_ms_function(self):
        """Test timestamp_ms() function generates millisecond timestamp."""
        result = self.vm.render_string("${timestamp_ms()}")
        assert result.isdigit()
        value = int(result)
        # Should be recent timestamp in milliseconds
        assert 1577836800000 <= value <= 4102444800000

    def test_timestamp_us_function(self):
        """Test timestamp_us() function generates microsecond timestamp."""
        result = self.vm.render_string("${timestamp_us()}")
        assert result.isdigit()
        value = int(result)
        # Should be recent timestamp in microseconds (16+ digits)
        assert value > 1_000_000_000_000_000
        # Should be 16 digits
        assert len(result) >= 16

    def test_now_us_function(self):
        """Test now_us() function generates formatted microsecond timestamp."""
        result = self.vm.render_string("${now_us()}")
        # Should be exactly 20 digits (YYYYMMDDHHMMSSffffffff)
        assert len(result) == 20
        assert result.isdigit()
        # Should start with current year (202x)
        assert result.startswith("20")

    def test_now_with_microseconds(self):
        """Test now().strftime('%f') supports microsecond precision."""
        result = self.vm.render_string("${now().strftime('%Y%m%d%H%M%S%f')}")
        # Length: 14 (YYYYMMDDHHMMSS) + 6 (microseconds) = 20
        assert len(result) == 20
        assert result.isdigit()

    def test_date_function_default_format(self):
        """Test date() function with default format."""
        result = self.vm.render_string("${date()}")
        # Default format: "%Y-%m-%d %H:%M:%S"
        # Should match pattern like "2026-01-29 13:30:00"
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
        assert date_pattern.match(result) is not None

    def test_date_function_custom_format(self):
        """Test date(format) function with custom format."""
        result = self.vm.render_string("${date('%Y-%m-%d')}")
        # Should match pattern like "2026-01-29"
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        assert date_pattern.match(result) is not None

    def test_now_function(self):
        """Test now() function returns datetime object."""
        result = self.vm.render_string("${now().strftime('%Y%m%d')}")
        # Should match pattern like "20260129"
        date_pattern = re.compile(r'^\d{8}$')
        assert date_pattern.match(result) is not None

    def test_choice_function(self):
        """Test choice() function selects random element."""
        result = self.vm.render_string("${choice(['a', 'b', 'c'])}")
        assert result in ["a", "b", "c"]

    def test_nested_function_calls(self):
        """Test nested function calls like table_${random()}."""
        result = self.vm.render_string("table_${random()}")
        # Should start with "table_" followed by a number
        assert result.startswith("table_")
        number_part = result[6:]
        assert number_part.isdigit()

    def test_multiple_function_calls(self):
        """Test multiple function calls in one string."""
        result = self.vm.render_string("${uuid()}_${timestamp()}")
        parts = result.split("_")
        assert len(parts) == 2
        assert len(parts[0]) == 32  # UUID without dashes
        assert parts[1].isdigit()  # Timestamp

    def test_combined_functions_and_variables(self):
        """Test combining functions with regular variables."""
        self.vm.global_vars = {"name": "test"}
        result = self.vm.render_string("${name}_${random()}")
        parts = result.split("_")
        assert parts[0] == "test"
        assert parts[1].isdigit()

    def test_randint_alias(self):
        """Test randint() as alias for random()."""
        result1 = self.vm.render_string("${randint(1, 100)}")
        result2 = self.vm.render_string("${random(1, 100)}")
        # Both should be numbers
        assert result1.isdigit()
        assert result2.isdigit()


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.vm = VariableManager()

    def test_dynamic_table_name(self):
        """Test generating dynamic table names."""
        result = self.vm.render_string("table_${random()}")
        assert result.startswith("table_")
        table_num = int(result.split("_")[1])
        assert 0 <= table_num <= 1000000

    def test_user_id_with_uuid(self):
        """Test generating user ID with UUID."""
        result = self.vm.render_string("user_${uuid()}")
        parts = result.split("_")
        assert parts[0] == "user"
        assert len(parts[1]) == 32  # UUID without dashes

    def test_complex_filename_generation(self):
        """Test generating complex filename with multiple functions."""
        result = self.vm.render_string("report_${date('%Y%m%d')}_${uuid()}.txt")
        # Should match pattern: report_20260129_<uuid>.txt
        assert result.startswith("report_")
        assert result.endswith(".txt")
        parts = result.split("_")
        assert len(parts) == 3
        assert parts[1].isdigit()  # Date
        assert len(parts[2].removesuffix(".txt")) == 32  # UUID

    def test_request_parameters_with_functions(self):
        """Test using functions in URL parameters."""
        url = self.vm.render_string(
            "https://api.example.com/data?ts=${timestamp()}&id=${uuid()}"
        )
        assert "ts=" in url
        assert "id=" in url
        # Extract and check the values
        import re
        ts_match = re.search(r'ts=(\d+)', url)
        id_match = re.search(r'id=([a-f0-9]{32})', url)
        assert ts_match is not None
        assert id_match is not None

    def test_json_with_functions(self):
        """Test using functions in JSON template."""
        template = '{"user_id": "${random()}", "request_id": "${uuid()}", "timestamp": "${timestamp()}"}'
        result = self.vm.render_string(template)
        # Should be valid JSON
        import json
        data = json.loads(result)
        assert "user_id" in data
        assert "request_id" in data
        assert "timestamp" in data
        # Values will be strings after template rendering
        assert isinstance(data["user_id"], str)
        assert isinstance(data["timestamp"], str)
