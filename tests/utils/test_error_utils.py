"""Unit tests for error handling utilities.

Tests for error classification, suggestion generation, and formatting.
"""

from json.decoder import JSONDecodeError

import pytest
from requests import ConnectionError, HTTPError, Timeout

from apirun.core.models import ErrorCategory
from apirun.utils.error_utils import (
    ErrorClassifier,
    create_error_from_exception,
    format_error_for_display,
)


class TestErrorClassifier:
    """Tests for ErrorClassifier."""

    def test_classify_network_error(self):
        """Test classification of network errors."""
        error = ConnectionError('Connection refused')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.category == ErrorCategory.NETWORK
        assert 'ConnectionError' in error_info.type
        assert error_info.error_code.startswith('NET_')
        assert error_info.severity == 'high'
        assert error_info.timestamp is not None

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        error = Timeout('Request timed out')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.category == ErrorCategory.TIMEOUT
        assert error_info.error_code.startswith('TMO_')

    def test_classify_parsing_error(self):
        """Test classification of parsing errors."""
        error = JSONDecodeError('Expecting value', '{}', 0)
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.category == ErrorCategory.PARSING
        assert error_info.error_code.startswith('PRS_')

    def test_classify_assertion_error(self):
        """Test classification of assertion errors."""
        error = AssertionError('Assertion failed')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.category == ErrorCategory.ASSERTION
        assert error_info.error_code.startswith('AST_')

    def test_suggestion_generation_for_connection_error(self):
        """Test suggestion generation for connection errors."""
        error = ConnectionError('Connection refused')
        error_info = ErrorClassifier.classify_error(error)

        suggestions = error_info.suggestion.split('\n')
        assert len(suggestions) > 0
        assert any('网络' in s or '服务器' in s for s in suggestions)

    def test_suggestion_generation_for_timeout(self):
        """Test suggestion generation for timeout errors."""
        error = Timeout('Read timeout')
        error_info = ErrorClassifier.classify_error(error)

        suggestions = error_info.suggestion.split('\n')
        assert any('超时' in s or 'timeout' in s.lower() for s in suggestions)

    def test_suggestion_generation_for_401_error(self):
        """Test suggestion generation for 401 errors."""
        error = HTTPError('401 Client Error: Unauthorized')
        error_info = ErrorClassifier.classify_error(error)

        suggestions = error_info.suggestion.split('\n')
        assert any('认证' in s or 'token' in s.lower() for s in suggestions)

    def test_suggestion_generation_for_404_error(self):
        """Test suggestion generation for 404 errors."""
        error = HTTPError('404 Client Error: Not Found')
        error_info = ErrorClassifier.classify_error(error)

        suggestions = error_info.suggestion.split('\n')
        assert any('URL' in s or '路径' in s or '资源' in s for s in suggestions)

    def test_error_code_generation(self):
        """Test error code generation."""
        error1 = ConnectionError('Error 1')
        error_info1 = ErrorClassifier.classify_error(error1)

        error2 = ConnectionError('Error 2')
        error_info2 = ErrorClassifier.classify_error(error2)

        # Same error type should generate same error code
        assert error_info1.error_code == error_info2.error_code

    def test_context_preservation(self):
        """Test that context is preserved in error info."""
        error = ValueError('Invalid value')
        context = {'step_name': 'test_step', 'variable': 'test_var'}

        error_info = ErrorClassifier.classify_error(error, context)

        assert error_info.context['step_name'] == 'test_step'
        assert error_info.context['variable'] == 'test_var'


class TestErrorFormatting:
    """Tests for error formatting functions."""

    def test_format_error_basic(self):
        """Test basic error formatting."""
        error = ConnectionError('Test error')
        error_info = ErrorClassifier.classify_error(error)

        formatted = format_error_for_display(error_info, verbose=False)

        assert 'ConnectionError' in formatted
        assert 'network' in formatted.lower()
        assert 'Test error' in formatted
        assert '建议:' in formatted

    def test_format_error_verbose(self):
        """Test verbose error formatting with stack trace."""
        try:
            # Trigger an actual exception to get a real traceback
            1 / 0
        except ZeroDivisionError as e:
            error = e

        error_info = ErrorClassifier.classify_error(error)

        formatted = format_error_for_display(error_info, verbose=True)

        assert 'ZeroDivisionError' in formatted
        assert '堆栈跟踪:' in formatted
        assert 'Traceback' in formatted or 'traceback' in formatted.lower()

    def test_format_error_with_context(self):
        """Test error formatting with context."""
        error = ValueError('Test error')
        context = {'step_name': 'test_step', 'url': 'http://example.com'}
        error_info = ErrorClassifier.classify_error(error, context)

        formatted = format_error_for_display(error_info, verbose=False)

        assert '上下文信息:' in formatted
        assert 'test_step' in formatted
        assert 'http://example.com' in formatted

    def test_create_error_from_exception(self):
        """Test creating ErrorInfo from exception."""
        error = KeyError('test_key')
        error_info = create_error_from_exception(
            error, step_name='test_step', additional_context={'index': 5}
        )

        assert error_info.context['step_name'] == 'test_step'
        assert error_info.context['index'] == 5
        assert 'KeyError' in error_info.type


class TestErrorSeverity:
    """Tests for error severity determination."""

    def test_critical_severity(self):
        """Test critical severity for system errors."""
        error = KeyboardInterrupt()
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.severity == 'critical'

    def test_high_severity_network(self):
        """Test high severity for network errors."""
        error = ConnectionError('Network error')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.severity == 'high'

    def test_medium_severity_assertion(self):
        """Test medium severity for assertion errors."""
        error = AssertionError('Assertion failed')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.severity == 'medium'

    def test_low_severity_business(self):
        """Test low severity for business logic errors."""
        error = ValueError('Invalid value')
        error_info = ErrorClassifier.classify_error(error)

        assert error_info.severity == 'low'


@pytest.mark.parametrize(
    'error_message,expected_keywords',
    [
        ('connection refused', ['服务器', '端口']),
        ('timeout', ['超时', '时间']),
        ('401 unauthorized', ['认证', 'token']),
        ('403 forbidden', ['权限', '访问']),
        ('404 not found', ['URL', '路径', '资源']),
        ('500 internal server error', ['服务器', '日志']),
    ],
)
def test_contextual_suggestions(error_message, expected_keywords):
    """Test contextual suggestion generation based on error message."""
    error = Exception(error_message)
    error_info = ErrorClassifier.classify_error(error)

    suggestions = error_info.suggestion.lower()

    for keyword in expected_keywords:
        # Check if at least one suggestion contains the keyword
        assert keyword in suggestions or any(
            keyword in line for line in error_info.suggestion.split('\n')
        )
