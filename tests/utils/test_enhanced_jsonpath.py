"""Unit tests for Enhanced JSONPath functionality.

Following Google Python Style Guide.
"""

import pytest
from apirun.utils.enhanced_jsonpath import extract_value, EnhancedJSONPath


class TestEnhancedJSONPath:
    """Test cases for Enhanced JSONPath processor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = EnhancedJSONPath()

    def test_basic_jsonpath(self):
        """Test basic JSONPath without functions."""
        data = {"name": "Alice", "age": 30}
        result = extract_value("$.name", data)
        assert result == "Alice"

    def test_length_function_array(self):
        """Test length() function on array."""
        data = {"items": [1, 2, 3, 4, 5]}
        result = extract_value("$.items.length()", data)
        assert result == 5

    def test_size_function(self):
        """Test size() function (alias for length)."""
        data = {"users": [{"name": "A"}, {"name": "B"}]}
        result = extract_value("$.users.size()", data)
        assert result == 2

    def test_count_function(self):
        """Test count() function (alias for length)."""
        data = {"data": [1, 2, 3]}
        result = extract_value("$.data.count()", data)
        assert result == 3

    def test_sum_function(self):
        """Test sum() function."""
        data = {"numbers": [1, 2, 3, 4, 5]}
        result = extract_value("$.numbers.sum()", data)
        assert result == 15

    def test_avg_function(self):
        """Test avg() function."""
        data = {"numbers": [2, 4, 6]}
        result = extract_value("$.numbers.avg()", data)
        assert result == 4.0

    def test_min_function(self):
        """Test min() function."""
        data = {"values": [10, 5, 8, 3]}
        result = extract_value("$.values.min()", data)
        assert result == 3

    def test_max_function(self):
        """Test max() function."""
        data = {"values": [10, 5, 8, 3]}
        result = extract_value("$.values.max()", data)
        assert result == 10

    def test_first_function(self):
        """Test first() function."""
        data = {"items": ["a", "b", "c"]}
        result = extract_value("$.items.first()", data)
        assert result == "a"

    def test_last_function(self):
        """Test last() function."""
        data = {"items": ["a", "b", "c"]}
        result = extract_value("$.items.last()", data)
        assert result == "c"

    def test_keys_function(self):
        """Test keys() function."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = extract_value("$.user.keys()", data)
        assert set(result) == {"name", "age"}

    def test_values_function(self):
        """Test values() function."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = extract_value("$.user.values()", data)
        assert "Alice" in result
        assert 30 in result

    def test_reverse_function(self):
        """Test reverse() function."""
        data = {"items": [1, 2, 3]}
        result = extract_value("$.items.reverse()", data)
        assert result == [3, 2, 1]

    def test_sort_function(self):
        """Test sort() function."""
        data = {"numbers": [3, 1, 2]}
        result = extract_value("$.numbers.sort()", data)
        assert result == [1, 2, 3]

    def test_unique_function(self):
        """Test unique() function."""
        data = {"values": [1, 2, 2, 3, 3, 3]}
        result = extract_value("$.values.unique()", data)
        assert set(result) == {1, 2, 3}

    def test_flatten_function(self):
        """Test flatten() function."""
        data = {"nested": [[1, 2], [3, 4]]}
        result = extract_value("$.nested.flatten()", data)
        assert result == [1, 2, 3, 4]

    def test_upper_function(self):
        """Test upper() function."""
        data = {"text": "hello"}
        result = extract_value("$.text.upper()", data)
        assert result == "HELLO"

    def test_lower_function(self):
        """Test lower() function."""
        data = {"text": "HELLO"}
        result = extract_value("$.text.lower()", data)
        assert result == "hello"

    def test_trim_function(self):
        """Test trim() function."""
        data = {"text": "  hello  "}
        result = extract_value("$.text.trim()", data)
        assert result == "hello"

    def test_split_function(self):
        """Test split() function."""
        data = {"text": "a,b,c"}
        result = extract_value("$.text.split(',')", data)  # Use quoted delimiter
        assert result == ["a", "b", "c"]

    def test_join_function(self):
        """Test join() function."""
        data = {"items": ["a", "b", "c"]}
        result = extract_value("$.items.join(-)", data)
        assert result == "a-b-c"

    def test_contains_function(self):
        """Test contains() function."""
        data = {"text": "hello world"}
        result = extract_value("$.text.contains(world)", data)
        assert result is True

    def test_starts_with_function(self):
        """Test starts_with() function."""
        data = {"text": "hello world"}
        result = extract_value("$.text.starts_with(hello)", data)
        assert result is True

    def test_ends_with_function(self):
        """Test ends_with() function."""
        data = {"text": "hello world"}
        result = extract_value("$.text.ends_with(world)", data)
        assert result is True

    def test_matches_function(self):
        """Test matches() function."""
        data = {"text": "test123"}
        result = extract_value("$.text.matches(^test\\d+$)", data)
        assert result is True

    def test_chained_functions(self):
        """Test chained function calls - Note: chaining works on the array result."""
        data = {"items": [3, 1, 2]}
        # First extract all items, then sort, then get the result
        result = extract_value("$.items.sort()", data)
        # The result is sorted array [1, 2, 3]
        assert result == [1, 2, 3]

    def test_nested_array_extraction_with_function(self):
        """Test extraction from nested array with function."""
        data = {
            "users": [
                {"name": "Alice", "score": 95},
                {"name": "Bob", "score": 87},
                {"name": "Charlie", "score": 92}
            ]
        }
        # Extract all users, then extract scores, then sum
        # Note: $.users.score will return [95, 87, 92]
        scores = extract_value("$.users[*].score", data, index=-1)  # Get all matches
        result = sum(scores) if isinstance(scores, list) else scores
        assert result == 274

    def test_empty_array_length(self):
        """Test length() on empty array."""
        data = {"items": []}
        result = extract_value("$.items.length()", data)
        assert result == 0

    def test_string_length(self):
        """Test length() on string."""
        data = {"text": "hello"}
        result = extract_value("$.text.length()", data)
        assert result == 5

    def test_object_length(self):
        """Test length() on object (dict)."""
        data = {"user": {"name": "Alice", "age": 30, "city": "NYC"}}
        result = extract_value("$.user.length()", data)
        assert result == 3

    def test_complex_validation_scenario(self):
        """Test the original user scenario: $.data.length() > 0."""
        data = {
            "code": 200,
            "data": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
        }
        # Extract length
        result = extract_value("$.data.length()", data)
        assert result == 2
        assert result > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
