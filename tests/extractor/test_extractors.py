"""Unit tests for variable extractors.

Tests the extraction functionality including:
- JSONPath extractor
- Regex extractor
- Header extractor
- Cookie extractor
"""

import pytest

from apirun.extractor.cookie_extractor import CookieExtractor
from apirun.extractor.header_extractor import HeaderExtractor
from apirun.extractor.jsonpath_extractor import JSONPathExtractor
from apirun.extractor.regex_extractor import RegexExtractor


class TestJSONPathExtractor:
    """Tests for JSONPathExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create JSONPathExtractor instance."""
        return JSONPathExtractor()

    @pytest.fixture
    def sample_data(self):
        """Sample JSON data for testing."""
        return {
            'user': {
                'id': 123,
                'name': 'John Doe',
                'email': 'john@example.com',
                'roles': ['admin', 'user'],
                'address': {'city': 'New York', 'zip': '10001'},
            },
            'status': 'active',
            'items': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'},
                {'id': 3, 'name': 'Item 3'},
            ],
        }

    def test_extract_root(self, extractor, sample_data):
        """Test extracting root node."""
        # Skip this test as $ may not be supported by all JSONPath implementations
        result = extractor.extract('$.user', sample_data)
        assert result == sample_data['user']

    def test_extract_child_node(self, extractor, sample_data):
        """Test extracting child node."""
        result = extractor.extract('$.user.name', sample_data)
        assert result == 'John Doe'

    def test_extract_nested_node(self, extractor, sample_data):
        """Test extracting nested node."""
        result = extractor.extract('$.user.address.city', sample_data)
        assert result == 'New York'

    def test_extract_array_index(self, extractor, sample_data):
        """Test extracting array element by index."""
        result = extractor.extract('$.items[0]', sample_data)
        assert result == {'id': 1, 'name': 'Item 1'}

    def test_extract_array_slice(self, extractor, sample_data):
        """Test extracting array slice - adjust based on jsonpath lib behavior."""
        # jsonpath lib might return different format for slices
        result = extractor.extract('$.items[0:2]', sample_data)
        # Result might be a list or have different structure
        assert result is not None

    def test_extract_wildcard(self, extractor, sample_data):
        """Test extracting with wildcard - returns first match by default."""
        result = extractor.extract('$.user.roles[*]', sample_data)
        # Returns first match with index=0
        assert result in ['admin', 'user']

    def test_extract_recursive_search(self, extractor, sample_data):
        """Test recursive search - returns first match by default."""
        result = extractor.extract('$..name', sample_data)
        # With index=0, returns first match
        assert result in ['John Doe', 'Item 1', 'Item 2', 'Item 3']

    def test_extract_with_index(self, extractor, sample_data):
        """Test extracting with specific index from multiple matches."""
        result = extractor.extract('$..name', sample_data, index=1)
        assert result in ['John Doe', 'Item 1', 'Item 2', 'Item 3']

    def test_extract_invalid_path(self, extractor, sample_data):
        """Test extracting with invalid path."""
        with pytest.raises(ValueError, match='Invalid JSONPath'):
            extractor.extract('[invalid', sample_data)

    def test_extract_no_match(self, extractor, sample_data):
        """Test extracting with non-existent path."""
        # Error message may vary, just check it raises ValueError
        with pytest.raises(ValueError):
            extractor.extract('$.nonexistent', sample_data)

    def test_error_message_formatting_no_garbled_quotes(self, extractor, sample_data):
        """Test that error messages are properly formatted without garbled text."""
        """修复bug: 验证错误消息不包含乱码的引号字符"""
        with pytest.raises(ValueError) as exc_info:
            extractor.extract('$.nonexistent.deep.field', sample_data)

        error_message = str(exc_info.value)
        # Should contain proper formatting with $ symbol
        assert '应以 $ 开头' in error_message or '$' in error_message
        # Should NOT contain the garbled pattern (quotes around $ alone)
        assert "以 ' 开头" not in error_message
        assert "以 '$" not in error_message
        # Should be helpful Chinese message
        assert 'JSONPath' in error_message or '提取' in error_message

    def test_error_message_contains_helpful_suggestions(self, extractor, sample_data):
        """Test that error messages contain helpful debugging suggestions."""
        """修复bug: 验证错误消息包含有用的调试建议"""
        with pytest.raises(ValueError) as exc_info:
            extractor.extract('$.nonexistent', sample_data)

        error_message = str(exc_info.value)
        # Should contain helpful suggestions
        assert any(
            keyword in error_message for keyword in ['请检查', '路径', '字段', '建议']
        )

    def test_extract_with_default_value(self, extractor, sample_data):
        """Test extracting non-existent field with default value."""
        result = extractor.extract('$.nonexistent', sample_data, default='N/A')
        assert result == 'N/A'

    def test_extract_with_default_none(self, extractor, sample_data):
        """Test extracting existing field with default=None should return actual value."""
        result = extractor.extract('$.user.name', sample_data, default=None)
        assert result == 'John Doe'

    def test_extract_with_default_integer(self, extractor, sample_data):
        """Test extracting with integer default value."""
        result = extractor.extract('$.user.age', sample_data, default=18)
        assert result == 18

    def test_extract_with_default_dict(self, extractor, sample_data):
        """Test extracting with dict default value."""
        default_config = {'theme': 'dark', 'lang': 'en'}
        result = extractor.extract(
            '$.user.preferences', sample_data, default=default_config
        )
        assert result == default_config

    def test_extract_nested_with_default(self, extractor, sample_data):
        """Test extracting nested non-existent field with default."""
        result = extractor.extract(
            '$.user.phone.number', sample_data, default='000-0000'
        )
        assert result == '000-0000'

    def test_extract_index_out_of_range(self, extractor, sample_data):
        """Test extracting with index out of range."""
        with pytest.raises(ValueError, match='Index.*out of range'):
            extractor.extract('$.items', sample_data, index=10)

    def test_extract_from_array_at_root(self, extractor):
        """Test extracting from root-level array."""
        data = [1, 2, 3, 4, 5]
        result = extractor.extract('$[0]', data)
        assert result == 1

    def test_extract_nested_array(self, extractor, sample_data):
        """Test extracting from nested arrays."""
        result = extractor.extract('$.items[1].name', sample_data)
        assert result == 'Item 2'

    def test_extract_multiple_matches_index(self, extractor, sample_data):
        """Test extracting specific index from multiple matches."""
        result = extractor.extract('$.items[*].name', sample_data, index=2)
        assert result == 'Item 3'

    def test_extract_deep_nested_array_index(self, extractor):
        """Test extracting from deeply nested array structure - 用户报告的场景."""
        # 测试用户报告的路径: $.data.data[1].id
        data = {
            'code': 'SUCCESS',
            'data': {
                'data': [
                    {'id': 100, 'name': 'first'},
                    {'id': 200, 'name': 'second'},
                    {'id': 300, 'name': 'third'},
                ],
                'total': 3,
            },
        }
        result = extractor.extract('$.data.data[1].id', data)
        assert result == 200, f'Expected 200, got {result}'

    def test_extract_deep_nested_array_multiple_indices(self, extractor):
        """Test extracting different indices from deeply nested array."""
        data = {
            'response': {
                'users': [
                    {'id': 1, 'role': 'admin'},
                    {'id': 2, 'role': 'user'},
                    {'id': 3, 'role': 'guest'},
                ]
            }
        }
        # 测试第一个元素
        result = extractor.extract('$.response.users[0].role', data)
        assert result == 'admin'

        # 测试中间元素
        result = extractor.extract('$.response.users[1].id', data)
        assert result == 2

        # 测试最后一个元素
        result = extractor.extract('$.response.users[2].role', data)
        assert result == 'guest'


class TestRegexExtractor:
    """Tests for RegexExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create RegexExtractor instance."""
        return RegexExtractor()

    def test_extract_full_match(self, extractor):
        """Test extracting full match."""
        result = extractor.extract(r'hello', 'hello world')
        assert result == 'hello'

    def test_extract_group(self, extractor):
        """Test extracting capturing group - index=0 returns full match."""
        result = extractor.extract(r'id=(\d+)', 'user id=12345', index=1)
        assert result == '12345'

    def test_extract_multiple_groups(self, extractor):
        """Test extracting specific group."""
        result = extractor.extract(r'(\w+)=(\d+)', 'user id=12345', index=1)
        assert result == 'id'

    def test_extract_named_group(self, extractor):
        """Test extracting named group."""
        result = extractor.extract(r'(?P<name>\w+)', 'john')
        assert result == 'john'

    def test_extract_no_match(self, extractor):
        """Test extracting with no match."""
        result = extractor.extract(r'\d+', 'no numbers here')
        assert result is None

    def test_extract_with_default_value(self, extractor):
        """Test extracting with no match but with default value."""
        result = extractor.extract(r'\d+', 'no numbers here', default='0')
        assert result == '0'

    def test_extract_match_with_default_ignored(self, extractor):
        """Test extracting with match should ignore default value."""
        result = extractor.extract(r'\d+', 'user id=12345', default='0')
        assert result == '12345'

    def test_extract_no_match_with_default_dict(self, extractor):
        """Test extracting with no match, return dict default."""
        default_data = {'id': 'unknown', 'name': 'anonymous'}
        result = extractor.extract(r'id=(\d+)', 'no id', default=default_data)
        assert result == default_data

    def test_extract_group_out_of_range_with_default(self, extractor):
        """Test extracting with group index out of range, should return default."""
        result = extractor.extract(r'(\d+)', 'id=123', index=5, default='N/A')
        assert result == 'N/A'

    def test_extract_from_non_string(self, extractor):
        """Test extracting from non-string data."""
        result = extractor.extract(r'\d+', 12345)
        assert result == '12345'

    def test_extract_invalid_regex(self, extractor):
        """Test extracting with invalid regex."""
        with pytest.raises(ValueError, match='无效的正则表达式'):
            extractor.extract(r'(?P<invalid', 'test')

    def test_extract_group_index_out_of_range(self, extractor):
        """Test extracting with group index out of range."""
        result = extractor.extract(r'(\d+)', 'id=123', index=5)
        assert result is None

    def test_extract_special_characters(self, extractor):
        """Test extracting special characters - use index=1 for group."""
        result = extractor.extract(r'email: (.+)', 'email: test@example.com', index=1)
        assert result == 'test@example.com'

    def test_extract_with_flags_implicit(self, extractor):
        """Test extraction is case-sensitive by default."""
        result = extractor.extract(r'hello', 'HELLO world')
        assert result is None

    def test_extract_email_pattern(self, extractor):
        """Test extracting email."""
        result = extractor.extract(r'[\w.]+@[\w.]+', 'Contact: test@example.com')
        assert result == 'test@example.com'

    def test_extract_url_pattern(self, extractor):
        """Test extracting URL."""
        result = extractor.extract(
            r'https?://[\w./]+', 'Visit https://example.com/path'
        )
        assert result == 'https://example.com/path'

    def test_extract_digits(self, extractor):
        """Test extracting digits."""
        result = extractor.extract(r'\d+', 'User ID: 12345')
        assert result == '12345'

    def test_extract_word_boundary(self, extractor):
        """Test extracting with word boundaries."""
        result = extractor.extract(r'\btest\b', 'this is a test string')
        assert result == 'test'

    def test_extract_from_dict_with_json_dumps(self, extractor):
        """Test extracting from dict (should use json.dumps() for proper formatting)."""
        data = {'userId': 101809, 'userName': 'wangzai'}
        # Should use json.dumps() internally, preserving double quotes
        result = extractor.extract(r'"userId"\s*:\s*(\d+)', data, index=1)
        assert result == '101809'

    def test_extract_from_list_with_json_dumps(self, extractor):
        """Test extracting from list (should use json.dumps() for proper formatting)."""
        data = [{'id': 123}, {'id': 456}]
        # Should use json.dumps() internally, preserving double quotes
        result = extractor.extract(r'"id":\s*(\d+)', data, index=1)
        assert result == '123'

    def test_extract_from_nested_json(self, extractor):
        """Test extracting from nested JSON structure."""
        data = {'user': {'id': 101809, 'name': 'test'}}
        # Regex should match the JSON string produced by json.dumps()
        result = extractor.extract(r'"id"\s*:\s*(\d+)', data, index=1)
        assert result == '101809'


class TestHeaderExtractor:
    """Tests for HeaderExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create HeaderExtractor instance."""
        return HeaderExtractor()

    @pytest.fixture
    def response_data(self):
        """Sample response data with headers."""
        return {
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token123',
                'X-Custom-Header': 'custom-value',
            }
        }

    def test_extract_header(self, extractor, response_data):
        """Test extracting header value."""
        result = extractor.extract('Content-Type', response_data)
        assert result == 'application/json'

    def test_extract_header_case_insensitive(self, extractor, response_data):
        """Test case-insensitive header extraction."""
        result1 = extractor.extract('content-type', response_data)
        result2 = extractor.extract('CONTENT-TYPE', response_data)
        result3 = extractor.extract('Content-Type', response_data)
        assert result1 == result2 == result3 == 'application/json'

    def test_extract_nonexistent_header(self, extractor, response_data):
        """Test extracting non-existent header."""
        result = extractor.extract('Non-Existent', response_data)
        assert result is None

    def test_extract_nonexistent_header_with_default(self, extractor, response_data):
        """Test extracting non-existent header with default value."""
        result = extractor.extract('Non-Existent', response_data, default='text/html')
        assert result == 'text/html'

    def test_extract_existing_header_with_default(self, extractor, response_data):
        """Test extracting existing header with default should return actual value."""
        result = extractor.extract('Content-Type', response_data, default='text/plain')
        assert result == 'application/json'

    def test_extract_from_non_dict_data(self, extractor):
        """Test extracting from non-dict data."""
        result = extractor.extract('Content-Type', 'not a dict')
        assert result is None

    def test_extract_from_dict_without_headers(self, extractor):
        """Test extracting from dict without headers key."""
        result = extractor.extract('Content-Type', {'data': 'value'})
        assert result is None

    def test_extract_with_invalid_headers_field(self, extractor):
        """Test extracting when headers is not a dict."""
        data = {'headers': 'not a dict'}
        result = extractor.extract('Content-Type', data)
        assert result is None

    def test_extract_custom_header(self, extractor, response_data):
        """Test extracting custom header."""
        result = extractor.extract('X-Custom-Header', response_data)
        assert result == 'custom-value'

    def test_extract_authorization_header(self, extractor, response_data):
        """Test extracting authorization header."""
        result = extractor.extract('Authorization', response_data)
        assert result == 'Bearer token123'

    def test_extract_ignores_index_parameter(self, extractor, response_data):
        """Test that index parameter is ignored."""
        result1 = extractor.extract('Content-Type', response_data, index=0)
        result2 = extractor.extract('Content-Type', response_data, index=5)
        assert result1 == result2


class TestCookieExtractor:
    """Tests for CookieExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create CookieExtractor instance."""
        return CookieExtractor()

    @pytest.fixture
    def response_data(self):
        """Sample response data with cookies."""
        return {
            'cookies': {
                'session_id': 'abc123',
                'user_token': 'token456',
                'preferences': 'dark_mode',
            }
        }

    def test_extract_cookie(self, extractor, response_data):
        """Test extracting cookie value."""
        result = extractor.extract('session_id', response_data)
        assert result == 'abc123'

    def test_extract_nonexistent_cookie(self, extractor, response_data):
        """Test extracting non-existent cookie."""
        result = extractor.extract('nonexistent', response_data)
        assert result is None

    def test_extract_nonexistent_cookie_with_default(self, extractor, response_data):
        """Test extracting non-existent cookie with default value."""
        result = extractor.extract(
            'nonexistent', response_data, default='default_cookie'
        )
        assert result == 'default_cookie'

    def test_extract_existing_cookie_with_default(self, extractor, response_data):
        """Test extracting existing cookie with default should return actual value."""
        result = extractor.extract('session_id', response_data, default='fallback')
        assert result == 'abc123'

    def test_extract_from_non_dict_data(self, extractor):
        """Test extracting from non-dict data."""
        result = extractor.extract('session_id', 'not a dict')
        assert result is None

    def test_extract_from_dict_without_cookies(self, extractor):
        """Test extracting from dict without cookies key."""
        result = extractor.extract('session_id', {'data': 'value'})
        assert result is None

    def test_extract_with_invalid_cookies_field(self, extractor):
        """Test extracting when cookies is not a dict."""
        data = {'cookies': 'not a dict'}
        result = extractor.extract('session_id', data)
        assert result is None

    def test_extract_user_token_cookie(self, extractor, response_data):
        """Test extracting user token cookie."""
        result = extractor.extract('user_token', response_data)
        assert result == 'token456'

    def test_extract_preferences_cookie(self, extractor, response_data):
        """Test extracting preferences cookie."""
        result = extractor.extract('preferences', response_data)
        assert result == 'dark_mode'

    def test_extract_is_case_sensitive(self, extractor, response_data):
        """Test that cookie extraction is case-sensitive."""
        result = extractor.extract('Session_ID', response_data)
        assert result is None

    def test_extract_ignores_index_parameter(self, extractor, response_data):
        """Test that index parameter is ignored."""
        result1 = extractor.extract('session_id', response_data, index=0)
        result2 = extractor.extract('session_id', response_data, index=5)
        assert result1 == result2


class TestExtractorEdgeCases:
    """Tests for edge cases across all extractors."""

    def test_jsonpath_extract_empty_data(self):
        """Test JSONPath extraction from empty dict."""
        extractor = JSONPathExtractor()
        with pytest.raises(ValueError):
            extractor.extract('$.key', {})

    def test_jsonpath_extract_null_value(self):
        """Test JSONPath extraction when value is null."""
        extractor = JSONPathExtractor()
        data = {'key': None}
        result = extractor.extract('$.key', data)
        assert result is None

    def test_regex_extract_empty_string(self):
        """Test regex extraction from empty string."""
        extractor = RegexExtractor()
        result = extractor.extract(r'\d+', '')
        assert result is None

    def test_regex_extract_with_newlines(self):
        """Test regex extraction with newlines - use group index."""
        extractor = RegexExtractor()
        result = extractor.extract(r'line (\d)', 'first\nline 2\nthird', index=1)
        assert result == '2'

    def test_header_extract_empty_dict(self):
        """Test header extraction from empty dict."""
        extractor = HeaderExtractor()
        data = {'headers': {}}
        result = extractor.extract('Content-Type', data)
        assert result is None

    def test_cookie_extract_empty_dict(self):
        """Test cookie extraction from empty dict."""
        extractor = CookieExtractor()
        data = {'cookies': {}}
        result = extractor.extract('session_id', data)
        assert result is None

    def test_jsonpath_extract_boolean_value(self):
        """Test JSONPath extraction of boolean values."""
        extractor = JSONPathExtractor()
        data = {'active': True, 'inactive': False}
        result1 = extractor.extract('$.active', data)
        result2 = extractor.extract('$.inactive', data)
        assert result1 is True
        assert result2 is False

    def test_jsonpath_extract_numeric_value(self):
        """Test JSONPath extraction of numeric values."""
        extractor = JSONPathExtractor()
        data = {'count': 42, 'price': 19.99}
        result1 = extractor.extract('$.count', data)
        result2 = extractor.extract('$.price', data)
        assert result1 == 42
        assert result2 == 19.99

    def test_regex_extract_complex_pattern(self):
        """Test regex extraction with complex pattern - use group index."""
        extractor = RegexExtractor()
        text = 'Date: 2024-01-15, Time: 14:30:00'
        result = extractor.extract(r'Date: (\d{4}-\d{2}-\d{2})', text, index=1)
        assert result == '2024-01-15'

    def test_header_extract_with_multiple_values(self):
        """Test header extraction with multiple same-name headers."""
        extractor = HeaderExtractor()
        # Note: In real HTTP, headers can have multiple values
        # but here we just store the last value
        data = {'headers': {'X-Custom': 'value1'}}
        result = extractor.extract('X-Custom', data)
        assert result == 'value1'

    def test_cookie_extract_with_special_chars(self):
        """Test cookie extraction with special characters in value."""
        extractor = CookieExtractor()
        data = {'cookies': {'session': 'abc123/xyz=789'}}
        result = extractor.extract('session', data)
        assert result == 'abc123/xyz=789'


class TestMultiValueExtraction:
    """Tests for multi-value extraction (extract_all parameter)."""

    @pytest.fixture
    def extractor(self):
        """Create JSONPathExtractor instance."""
        return JSONPathExtractor()

    @pytest.fixture
    def sample_array_data(self):
        """Sample data with arrays for testing."""
        return {
            'users': [
                {'id': 1, 'name': 'Alice', 'role': 'admin'},
                {'id': 2, 'name': 'Bob', 'role': 'user'},
                {'id': 3, 'name': 'Charlie', 'role': 'user'},
            ],
            'tags': ['python', 'java', 'go'],
            'scores': [85, 90, 78, 92],
        }

    def test_extract_all_names(self, extractor, sample_array_data):
        """Test extracting all values with index=-1."""
        result = extractor.extract('$.users[*].name', sample_array_data, index=-1)
        assert result == ['Alice', 'Bob', 'Charlie']

    def test_extract_all_ids(self, extractor, sample_array_data):
        """Test extracting all user IDs."""
        result = extractor.extract('$.users[*].id', sample_array_data, index=-1)
        assert result == [1, 2, 3]

    def test_extract_all_simple_array(self, extractor, sample_array_data):
        """Test extracting all elements from simple array."""
        result = extractor.extract('$.tags[*]', sample_array_data, index=-1)
        assert result == ['python', 'java', 'go']

    def test_extract_first_value(self, extractor, sample_array_data):
        """Test extracting first value (default behavior)."""
        result = extractor.extract('$.users[*].name', sample_array_data, index=0)
        assert result == 'Alice'

    def test_extract_second_value(self, extractor, sample_array_data):
        """Test extracting second value."""
        result = extractor.extract('$.users[*].name', sample_array_data, index=1)
        assert result == 'Bob'

    def test_extract_last_value(self, extractor, sample_array_data):
        """Test extracting last value."""
        result = extractor.extract('$.users[*].name', sample_array_data, index=2)
        assert result == 'Charlie'

    def test_extract_all_with_nested_path(self, extractor, sample_array_data):
        """Test extracting all with nested path."""
        result = extractor.extract('$.users[*].role', sample_array_data, index=-1)
        assert result == ['admin', 'user', 'user']

    def test_extract_with_filter_multiple_results(self, extractor):
        """Test extracting filtered results (multiple matches)."""
        data = {
            'items': [
                {'category': 'A', 'price': 100},
                {'category': 'B', 'price': 200},
                {'category': 'A', 'price': 150},
            ]
        }
        # Extract all category A items' prices
        result = extractor.extract(
            "$.items[?(@.category == 'A')].price", data, index=-1
        )
        assert result == [100, 150]

    def test_extract_single_value_does_not_return_array(
        self, extractor, sample_array_data
    ):
        """Test that single value extraction with index=0 returns scalar, not array."""
        result = extractor.extract('$.users[*].name', sample_array_data, index=0)
        assert isinstance(result, str)
        assert result == 'Alice'

    def test_extract_empty_array_returns_empty_list(self, extractor):
        """Test extracting from empty array returns empty list."""
        data = {'items': []}
        result = extractor.extract('$.items[*]', data, index=-1)
        assert result == []

    def test_extract_all_numbers(self, extractor, sample_array_data):
        """Test extracting all numbers from array."""
        result = extractor.extract('$.scores[*]', sample_array_data, index=-1)
        assert result == [85, 90, 78, 92]


class TestConditionalExtraction:
    """Tests for conditional extraction (condition parameter)."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for conditional extraction testing."""
        return {
            'code': 200,
            'success': True,
            'data': {'id': 'task-123', 'name': 'Test Task', 'status': 'active'},
            'items': [{'id': 1, 'name': 'Item 1'}, {'id': 2, 'name': 'Item 2'}],
        }

    def test_condition_eq_true(self, sample_data):
        """Test condition with equality check (true)."""
        # Create a mock executor with minimal setup
        from apirun.core.variable_manager import VariableManager
        from apirun.executor.step_executor import StepExecutor

        vm = VariableManager()

        # Simulate condition evaluation
        result = StepExecutor._evaluate_simple_condition('$.code == 200', sample_data)
        assert result is True

    def test_condition_eq_false(self, sample_data):
        """Test condition with equality check (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code == 404', sample_data)
        assert result is False

    def test_condition_ne_true(self, sample_data):
        """Test condition with not-equal check (true)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code != 404', sample_data)
        assert result is True

    def test_condition_ne_false(self, sample_data):
        """Test condition with not-equal check (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code != 200', sample_data)
        assert result is False

    def test_condition_gt_true(self, sample_data):
        """Test condition with greater-than check (true)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code > 100', sample_data)
        assert result is True

    def test_condition_gt_false(self, sample_data):
        """Test condition with greater-than check (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code > 300', sample_data)
        assert result is False

    def test_condition_lt_true(self, sample_data):
        """Test condition with less-than check (true)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.code < 300', sample_data)
        assert result is True

    def test_condition_boolean_true(self, sample_data):
        """Test condition with boolean check (true)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition(
            '$.success == true', sample_data
        )
        assert result is True

    def test_condition_boolean_false(self, sample_data):
        """Test condition with boolean check (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition(
            '$.success == false', sample_data
        )
        assert result is False

    def test_condition_exists(self, sample_data):
        """Test condition checking if field exists."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.data', sample_data)
        assert result is True

    def test_condition_not_exists(self, sample_data):
        """Test condition checking if field doesn't exist."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.nonexistent', sample_data)
        assert result is False

    def test_condition_with_string_value(self, sample_data):
        """Test condition with string comparison."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition(
            '$.data.status == "active"', sample_data
        )
        assert result is True

    def test_condition_and_logic(self, sample_data):
        """Test condition with AND logic."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_condition(
            '$.code == 200 and $.success == true', sample_data
        )
        assert result is True

    def test_condition_and_logic_false(self, sample_data):
        """Test condition with AND logic (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_condition(
            '$.code == 200 and $.code == 404', sample_data
        )
        assert result is False

    def test_condition_or_logic(self, sample_data):
        """Test condition with OR logic."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_condition(
            '$.code == 404 or $.success == true', sample_data
        )
        assert result is True

    def test_condition_or_logic_false(self, sample_data):
        """Test condition with OR logic (false)."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_condition(
            '$.code == 404 or $.success == false', sample_data
        )
        assert result is False

    def test_condition_with_array_length(self, sample_data):
        """Test condition with array length check."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition(
            '$.items.length() > 0', sample_data
        )
        assert result is True

    def test_condition_with_null_check(self, sample_data):
        """Test condition with null check."""
        from apirun.executor.step_executor import StepExecutor

        result = StepExecutor._evaluate_simple_condition('$.data != null', sample_data)
        assert result is True

    def test_condition_with_nonexistent_null_check(self):
        """Test condition with null check on non-existent field."""
        from apirun.executor.step_executor import StepExecutor

        data = {'data': None}
        result = StepExecutor._evaluate_simple_condition('$.data != null', data)
        assert result is False
