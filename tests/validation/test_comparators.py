"""Unit tests for comparators.

Tests for validation comparators in apirun/validation/comparators.py
Following Google Python Style Guide.
"""

import pytest

from apirun.validation.comparators import ComparatorError, Comparators


class TestEqualityComparators:
    """Tests for equality comparators (eq, ne)."""

    def test_compare_eq_equal(self):
        """Test eq comparator with equal values."""
        result = Comparators.eq('value', 'value')
        assert result is True

    def test_compare_eq_not_equal(self):
        """Test eq comparator with different values."""
        result = Comparators.eq('value1', 'value2')
        assert result is False

    def test_compare_ne_equal(self):
        """Test ne comparator with equal values."""
        result = Comparators.ne('value', 'value')
        assert result is False

    def test_compare_ne_not_equal(self):
        """Test ne comparator with different values."""
        result = Comparators.ne('value1', 'value2')
        assert result is True


class TestOrderingComparators:
    """Tests for ordering comparators (gt, lt, ge, le)."""

    def test_compare_gt(self):
        """Test gt comparator."""
        assert Comparators.gt(5, 3) is True
        assert Comparators.gt(3, 5) is False
        assert Comparators.gt(5, 5) is False

    def test_compare_lt(self):
        """Test lt comparator."""
        assert Comparators.lt(3, 5) is True
        assert Comparators.lt(5, 3) is False
        assert Comparators.lt(5, 5) is False

    def test_compare_ge(self):
        """Test ge comparator."""
        assert Comparators.ge(5, 3) is True
        assert Comparators.ge(5, 5) is True
        assert Comparators.ge(3, 5) is False

    def test_compare_le(self):
        """Test le comparator."""
        assert Comparators.le(3, 5) is True
        assert Comparators.le(5, 5) is True
        assert Comparators.le(5, 3) is False

    def test_compare_with_strings(self):
        """Test ordering comparators with string numbers."""
        assert Comparators.gt('5', '3') is True
        assert Comparators.lt('3', '5') is True


class TestContainsComparators:
    """Tests for contains comparators."""

    def test_compare_contains_string(self):
        """Test contains comparator with strings."""
        result = Comparators.contains('Hello World', 'World')
        assert result is True

        result = Comparators.contains('Hello World', 'Python')
        assert result is False

    def test_compare_contains_list(self):
        """Test contains comparator with lists."""
        result = Comparators.contains([1, 2, 3], 2)
        assert result is True

        result = Comparators.contains([1, 2, 3], 4)
        assert result is False

    def test_compare_contains_dict(self):
        """Test contains comparator with dicts."""
        result = Comparators.contains({'key': 'value'}, 'key')
        assert result is True

        result = Comparators.contains({'key': 'value'}, 'other')
        assert result is False

    def test_compare_not_contains(self):
        """Test not_contains comparator."""
        result = Comparators.not_contains('Hello World', 'Python')
        assert result is True

        result = Comparators.not_contains('Hello World', 'World')
        assert result is False

    def test_compare_contains_string_list(self):
        """Test contains comparator with string list - 用户报告的场景."""
        # 测试用户报告的场景：验证数组包含特定字符串
        items = ['apple', 'banana', 'test_param_xxx', 'orange']
        result = Comparators.contains(items, 'test_param_xxx')
        assert result is True, f"Expected True for 'test_param_xxx' in {items}"

        # 测试不存在的字符串
        result = Comparators.contains(items, 'grape')
        assert result is False

    def test_compare_contains_list_with_none(self):
        """Test contains comparator with list containing None values - 边界场景."""
        # 测试包含 None 值的数组
        items = [1, None, 3, 4]
        result = Comparators.contains(items, None)
        assert result is True, 'Expected True for None in list with None values'

        # 测试 None 不在数组中
        items = [1, 2, 3]
        result = Comparators.contains(items, None)
        assert result is False, 'Expected False for None not in list'

    def test_compare_contains_mixed_type_list(self):
        """Test contains comparator with mixed type list."""
        # 测试混合类型数组
        items = ['string', 123, True, None, {'key': 'value'}]
        assert Comparators.contains(items, 'string') is True
        assert Comparators.contains(items, 123) is True
        assert Comparators.contains(items, True) is True
        assert Comparators.contains(items, None) is True
        assert Comparators.contains(items, 'not_exist') is False


class TestRegexComparator:
    """Tests for regex comparator."""

    def test_compare_regex_match(self):
        """Test regex comparator with matching pattern."""
        result = Comparators.regex('test@example.com', r'^[a-z]+@[a-z]+\.[a-z]+$')
        assert result is True

    def test_compare_regex_no_match(self):
        """Test regex comparator with non-matching pattern."""
        result = Comparators.regex('invalid-email', r'^[a-z]+@[a-z]+\.[a-z]+$')
        assert result is False

    def test_compare_regex_with_digits(self):
        """Test regex comparator with digit pattern."""
        result = Comparators.regex('user123', r'user\d+')
        assert result is True

    def test_compare_regex_non_string(self):
        """Test regex comparator with non-string input (auto-convert to string)."""
        result = Comparators.regex(123, r'\d+')
        assert result is True  # 123 converts to "123", which matches \d+

    def test_compare_regex_integer_exact_match(self):
        """Test regex comparator with integer exact match."""
        result = Comparators.regex(1, r'^1$')
        assert result is True  # 1 converts to "1", which matches ^1$


class TestTypeComparator:
    """Tests for type comparator."""

    def test_compare_type_string(self):
        """Test type comparator with string."""
        result = Comparators.type('hello', 'str')
        assert result is True

    def test_compare_type_integer(self):
        """Test type comparator with integer."""
        result = Comparators.type(123, 'int')
        assert result is True

    def test_compare_type_float(self):
        """Test type comparator with float."""
        result = Comparators.type(3.14, 'float')
        assert result is True

    def test_compare_type_boolean(self):
        """Test type comparator with boolean."""
        result = Comparators.type(True, 'bool')
        assert result is True

    def test_compare_type_list(self):
        """Test type comparator with list."""
        result = Comparators.type([1, 2, 3], 'list')
        assert result is True

    def test_compare_type_dict(self):
        """Test type comparator with dict."""
        result = Comparators.type({'key': 'value'}, 'dict')
        assert result is True

    def test_compare_type_none(self):
        """Test type comparator with None."""
        result = Comparators.type(None, 'null')
        assert result is True

    def test_compare_type_mismatch(self):
        """Test type comparator with mismatched type."""
        result = Comparators.type('hello', 'int')
        assert result is False

    def test_compare_type_invalid_type_string(self):
        """Test type comparator with invalid type string."""
        result = Comparators.type('hello', 'invalid')
        assert result is False


class TestInComparators:
    """Tests for in/not_in comparators."""

    def test_compare_in_list(self):
        """Test in comparator with list."""
        result = Comparators.in_list('apple', ['apple', 'banana', 'orange'])
        assert result is True

        result = Comparators.in_list('grape', ['apple', 'banana', 'orange'])
        assert result is False

    def test_compare_in_tuple(self):
        """Test in comparator with tuple."""
        result = Comparators.in_list('apple', ('apple', 'banana', 'orange'))
        assert result is True

    def test_compare_in_not_list(self):
        """Test in comparator with non-list."""
        result = Comparators.in_list('apple', 'not a list')
        assert result is False

    def test_compare_not_in_list(self):
        """Test not_in comparator with list."""
        result = Comparators.not_in_list('grape', ['apple', 'banana', 'orange'])
        assert result is True

        result = Comparators.not_in_list('apple', ['apple', 'banana', 'orange'])
        assert result is False


class TestLengthComparators:
    """Tests for length comparators."""

    def test_compare_length_eq(self):
        """Test length_eq comparator."""
        result = Comparators.length_eq([1, 2, 3], 3)
        assert result is True

        result = Comparators.length_eq([1, 2, 3], 4)
        assert result is False

    def test_compare_length_eq_string(self):
        """Test length_eq comparator with string."""
        result = Comparators.length_eq('test', 4)
        assert result is True

    def test_compare_length_eq_dict(self):
        """Test length_eq comparator with dict."""
        result = Comparators.length_eq({'a': 1, 'b': 2}, 2)
        assert result is True

    def test_compare_length_gt(self):
        """Test length_gt comparator."""
        result = Comparators.length_gt([1, 2, 3, 4], 3)
        assert result is True

        result = Comparators.length_gt([1, 2], 3)
        assert result is False

    def test_compare_length_lt(self):
        """Test length_lt comparator."""
        result = Comparators.length_lt([1, 2], 3)
        assert result is True

        result = Comparators.length_lt([1, 2, 3, 4], 3)
        assert result is False

    def test_compare_length_no_len(self):
        """Test length comparator with object without len."""
        result = Comparators.length_eq(123, 3)
        assert result is False


class TestEmptyComparators:
    """Tests for empty/null comparators."""

    def test_compare_is_empty_string(self):
        """Test is_empty comparator with empty string."""
        result = Comparators.is_empty('')
        assert result is True

        result = Comparators.is_empty('value')
        assert result is False

    def test_compare_is_empty_list(self):
        """Test is_empty comparator with empty list."""
        result = Comparators.is_empty([])
        assert result is True

        result = Comparators.is_empty([1, 2, 3])
        assert result is False

    def test_compare_is_empty_dict(self):
        """Test is_empty comparator with empty dict."""
        result = Comparators.is_empty({})
        assert result is True

        result = Comparators.is_empty({'key': 'value'})
        assert result is False

    def test_compare_is_empty_none(self):
        """Test is_empty comparator with None."""
        result = Comparators.is_empty(None)
        assert result is True

    def test_compare_is_null(self):
        """Test is_null comparator."""
        result = Comparators.is_null(None)
        assert result is True

        result = Comparators.is_null('value')
        assert result is False

        result = Comparators.is_null(0)
        assert result is False

        result = Comparators.is_null(False)
        assert result is False


class TestStatusCodeComparator:
    """Tests for status_code comparator."""

    def test_compare_status_code_int(self):
        """Test status_code comparator with integer."""
        result = Comparators.status_code(200, 200)
        assert result is True

    def test_compare_status_code_string(self):
        """Test status_code comparator with string."""
        result = Comparators.status_code('200', 200)
        assert result is True

    def test_compare_status_code_mismatch(self):
        """Test status_code comparator with mismatch."""
        result = Comparators.status_code(404, 200)
        assert result is False

    def test_compare_status_code_range(self):
        """Test status_code comparator with range pattern."""
        result = Comparators.status_code(200, '2xx')
        assert result is True

        result = Comparators.status_code(404, '4xx')
        assert result is True

        result = Comparators.status_code(200, '4xx')
        assert result is False

    def test_compare_status_code_invalid(self):
        """Test status_code comparator with invalid values."""
        result = Comparators.status_code('invalid', 200)
        assert result is False


class TestExistsComparator:
    """Tests for exists comparator."""

    def test_compare_exists_present(self):
        """Test exists comparator with present value."""
        result = Comparators.exists('value')
        assert result is True

    def test_compare_exists_none(self):
        """Test exists comparator with None."""
        result = Comparators.exists(None)
        assert result is False

    def test_compare_exists_empty_string(self):
        """Test exists comparator with empty string."""
        result = Comparators.exists('')
        assert result is False

    def test_compare_exists_empty_list(self):
        """Test exists comparator with empty list."""
        result = Comparators.exists([])
        assert result is False

    def test_compare_exists_zero(self):
        """Test exists comparator with zero."""
        result = Comparators.exists(0)
        assert result is True

    def test_compare_exists_false(self):
        """Test exists comparator with False."""
        result = Comparators.exists(False)
        assert result is True


class TestBetweenComparator:
    """Tests for between comparator."""

    def test_compare_between_in_range(self):
        """Test between comparator with value in range."""
        result = Comparators.between(5, [1, 10])
        assert result is True

    def test_compare_between_lower_bound(self):
        """Test between comparator at lower bound."""
        result = Comparators.between(1, [1, 10])
        assert result is True

    def test_compare_between_upper_bound(self):
        """Test between comparator at upper bound."""
        result = Comparators.between(10, [1, 10])
        assert result is True

    def test_compare_between_below_range(self):
        """Test between comparator below range."""
        result = Comparators.between(0, [1, 10])
        assert result is False

    def test_compare_between_above_range(self):
        """Test between comparator above range."""
        result = Comparators.between(11, [1, 10])
        assert result is False

    def test_compare_between_invalid_format(self):
        """Test between comparator with invalid format."""
        with pytest.raises(ComparatorError):
            Comparators.between(5, 'not a list')


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_compare_with_none_values(self):
        """Test comparators with None values."""
        assert Comparators.eq(None, None) is True
        assert Comparators.ne(None, None) is False
        assert Comparators.is_null(None) is True

    def test_compare_with_boolean_values(self):
        """Test comparators with boolean values."""
        assert Comparators.eq(True, True) is True
        assert Comparators.eq(False, False) is True
        assert Comparators.ne(True, False) is True

    def test_compare_with_float_precision(self):
        """Test comparators with float precision."""
        result = Comparators.gt(3.14159, 3.14)
        assert result is True

    def test_compare_unicode_strings(self):
        """Test comparators with unicode strings."""
        result = Comparators.eq('你好', '你好')
        assert result is True

    def test_compare_nested_data_structures(self):
        """Test comparators with nested structures."""
        data = {'user': {'name': 'Alice', 'age': 30}}
        result = Comparators.type(data, 'dict')
        assert result is True

    def test_compare_with_numeric_strings(self):
        """Test ordering comparators convert strings to numbers."""
        assert Comparators.gt('5.5', '3.2') is True
        assert Comparators.lt('2.1', '10.5') is True

    def test_contains_with_tuple(self):
        """Test contains comparator with tuple."""
        result = Comparators.contains((1, 2, 3), 2)
        assert result is True


class TestStringPrefixSuffixComparators:
    """Tests for string prefix/suffix comparators (starts_with, ends_with)."""

    def test_starts_with_positive(self):
        """Test starts_with comparator with matching prefix."""
        result = Comparators.starts_with('hello world', 'hello')
        assert result is True

    def test_starts_with_negative(self):
        """Test starts_with comparator with non-matching prefix."""
        result = Comparators.starts_with('hello world', 'world')
        assert result is False

    def test_starts_with_empty_prefix(self):
        """Test starts_with comparator with empty prefix."""
        result = Comparators.starts_with('hello world', '')
        assert result is True

    def test_starts_with_none_actual(self):
        """Test starts_with comparator with None actual value."""
        result = Comparators.starts_with(None, 'prefix')
        assert result is False

    def test_starts_with_none_both(self):
        """Test starts_with comparator with None values."""
        result = Comparators.starts_with(None, None)
        assert result is True

    def test_starts_with_numeric_conversion(self):
        """Test starts_with comparator with numeric values."""
        result = Comparators.starts_with(12345, '12')
        assert result is True

    def test_ends_with_positive(self):
        """Test ends_with comparator with matching suffix."""
        result = Comparators.ends_with('hello world', 'world')
        assert result is True

    def test_ends_with_negative(self):
        """Test ends_with comparator with non-matching suffix."""
        result = Comparators.ends_with('hello world', 'hello')
        assert result is False

    def test_ends_with_empty_suffix(self):
        """Test ends_with comparator with empty suffix."""
        result = Comparators.ends_with('hello world', '')
        assert result is True

    def test_ends_with_none_actual(self):
        """Test ends_with comparator with None actual value."""
        result = Comparators.ends_with(None, 'suffix')
        assert result is False

    def test_ends_with_none_both(self):
        """Test ends_with comparator with None values."""
        result = Comparators.ends_with(None, None)
        assert result is True

    def test_ends_with_numeric_conversion(self):
        """Test ends_with comparator with numeric values."""
        result = Comparators.ends_with(12345, '45')
        assert result is True

    def test_starts_with_full_string(self):
        """Test starts_with comparator with full string match."""
        result = Comparators.starts_with('test', 'test')
        assert result is True

    def test_ends_with_full_string(self):
        """Test ends_with comparator with full string match."""
        result = Comparators.ends_with('test', 'test')
        assert result is True
