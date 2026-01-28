"""Unit tests for mock server models.

Tests for mock server data models including:
- Request matcher
- Mock response
- Mock rule
- Delay and failure configurations
"""

import pytest
import time
from apirun.mock.models import (
    MatchType,
    FailureType,
    DelayConfig,
    FailureConfig,
    MockResponse,
    RequestMatcher,
    MockRule,
    MockServerConfig,
)


class TestDelayConfig:
    """Tests for DelayConfig."""

    def test_fixed_delay(self):
        """Test fixed delay."""
        config = DelayConfig(fixed_delay=1.0)
        delay = config.get_delay()
        assert delay == 1.0

    def test_random_delay_range(self):
        """Test random delay within range."""
        config = DelayConfig(min_delay=0.5, max_delay=1.5)
        delays = [config.get_delay() for _ in range(10)]
        assert all(0.5 <= d <= 1.5 for d in delays)

    def test_delay_with_jitter(self):
        """Test delay with jitter."""
        config = DelayConfig(fixed_delay=1.0, jitter=True)
        delay = config.get_delay()
        assert 1.0 <= delay <= 1.1

    def test_delay_no_negative(self):
        """Test that delay is never negative."""
        config = DelayConfig(min_delay=-1.0, max_delay=0.5)
        delay = config.get_delay()
        assert delay >= 0

    def test_fixed_delay_takes_precedence(self):
        """Test that fixed_delay is used when set."""
        config = DelayConfig(min_delay=0.1, max_delay=0.2, fixed_delay=1.0)
        delay = config.get_delay()
        assert delay == 1.0


class TestFailureConfig:
    """Tests for FailureConfig."""

    def test_should_fail_always(self):
        """Test failure with probability 1.0."""
        config = FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=1.0)
        assert config.should_fail() is True

    def test_should_fail_never(self):
        """Test failure with probability 0.0."""
        config = FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=0.0)
        assert config.should_fail() is False

    def test_should_fail_sometimes(self):
        """Test failure with probability 0.5."""
        config = FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=0.5)
        # Run multiple times to check randomness
        results = [config.should_fail() for _ in range(100)]
        assert True in results and False in results

    def test_failure_types(self):
        """Test all failure types."""
        for failure_type in FailureType:
            config = FailureConfig(failure_type=failure_type)
            assert config.failure_type == failure_type


class TestMockResponse:
    """Tests for MockResponse."""

    def test_basic_response(self):
        """Test basic response."""
        response = MockResponse(status_code=200, body={"key": "value"})
        assert response.status_code == 200
        assert response.body == {"key": "value"}

    def test_response_with_headers(self):
        """Test response with headers."""
        headers = {"Content-Type": "application/json"}
        response = MockResponse(status_code=200, body={}, headers=headers)
        assert response.headers == headers

    def test_response_with_delay(self):
        """Test response with delay config."""
        delay = DelayConfig(fixed_delay=0.1)
        response = MockResponse(status_code=200, body={}, delay=delay)
        assert response.delay == delay

    def test_response_with_failure(self):
        """Test response with failure config."""
        failure = FailureConfig(failure_type=FailureType.HTTP_ERROR)
        response = MockResponse(status_code=200, body={}, failure=failure)
        assert response.failure == failure

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = MockResponse(status_code=200, body={"key": "value"}, headers={"X-Custom": "test"})
        result = response.to_dict()
        assert result == {"status_code": 200, "body": {"key": "value"}, "headers": {"X-Custom": "test"}}


class TestRequestMatcher:
    """Tests for RequestMatcher."""

    def test_exact_method_match(self):
        """Test exact method matching."""
        matcher = RequestMatcher(method="GET", path="/api/users")
        assert matcher.matches("GET", "/api/users") is True
        assert matcher.matches("POST", "/api/users") is False

    def test_exact_path_match(self):
        """Test exact path matching."""
        matcher = RequestMatcher(method="GET", path="/api/users")
        assert matcher.matches("GET", "/api/users") is True
        assert matcher.matches("GET", "/api/posts") is False

    def test_regex_path_match(self):
        """Test regex path matching."""
        matcher = RequestMatcher(method="GET", path=r"/api/users/\d+", match_type=MatchType.REGEX)
        assert matcher.matches("GET", "/api/users/123") is True
        assert matcher.matches("GET", "/api/users/abc") is False

    def test_contains_path_match(self):
        """Test contains path matching."""
        matcher = RequestMatcher(method="GET", path="/users", match_type=MatchType.CONTAINS)
        assert matcher.matches("GET", "/api/users/123") is True
        assert matcher.matches("GET", "/api/posts/123") is False

    def test_query_params_match(self):
        """Test query parameters matching."""
        matcher = RequestMatcher(method="GET", path="/api/users", query_params={"page": "1"})
        assert matcher.matches("GET", "/api/users", query_params={"page": "1"}) is True
        assert matcher.matches("GET", "/api/users", query_params={"page": "2"}) is False
        assert matcher.matches("GET", "/api/users") is False

    def test_headers_match(self):
        """Test headers matching."""
        matcher = RequestMatcher(method="GET", path="/api/users", headers={"Authorization": "Bearer token"})
        assert matcher.matches("GET", "/api/users", headers={"Authorization": "Bearer token"}) is True
        assert matcher.matches("GET", "/api/users", headers={"Authorization": "Bearer other"}) is False
        assert matcher.matches("GET", "/api/users") is False

    def test_body_exact_match(self):
        """Test exact body matching."""
        matcher = RequestMatcher(
            method="POST", path="/api/users", body_pattern='{"name":"John"}', body_match_type=MatchType.EXACT
        )
        assert matcher.matches("POST", "/api/users", body='{"name":"John"}') is True
        assert matcher.matches("POST", "/api/users", body='{"name":"Jane"}') is False

    def test_body_regex_match(self):
        """Test regex body matching."""
        matcher = RequestMatcher(
            method="POST", path="/api/users", body_pattern=r'{"name":"\w+"}', body_match_type=MatchType.REGEX
        )
        assert matcher.matches("POST", "/api/users", body='{"name":"John"}') is True
        assert matcher.matches("POST", "/api/users", body='{"name":"123"}') is True

    def test_body_contains_match(self):
        """Test contains body matching."""
        matcher = RequestMatcher(
            method="POST", path="/api/users", body_pattern="John", body_match_type=MatchType.CONTAINS
        )
        assert matcher.matches("POST", "/api/users", body='{"name":"John"}') is True
        assert matcher.matches("POST", "/api/users", body='{"name":"Jane"}') is False

    def test_invalid_regex_pattern(self):
        """Test invalid regex pattern raises error."""
        with pytest.raises(ValueError, match="Invalid regex"):
            RequestMatcher(method="GET", path="[invalid", match_type=MatchType.REGEX)


class TestMockRule:
    """Tests for MockRule."""

    def test_rule_matches(self):
        """Test rule matching."""
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule = MockRule(name="Get Users", matcher=matcher, response=response)

        assert rule.matches("GET", "/api/users") is True
        assert rule.matches("POST", "/api/users") is False

    def test_disabled_rule(self):
        """Test disabled rule doesn't match."""
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule = MockRule(name="Get Users", matcher=matcher, response=response, enabled=False)

        assert rule.matches("GET", "/api/users") is False

    def test_rule_priority(self):
        """Test rule priority."""
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule1 = MockRule(name="Rule 1", matcher=matcher, response=response, priority=10)
        rule2 = MockRule(name="Rule 2", matcher=matcher, response=response, priority=5)

        assert rule1.priority > rule2.priority


class TestMockServerConfig:
    """Tests for MockServerConfig."""

    def test_initialization(self):
        """Test config initialization."""
        config = MockServerConfig()
        assert config.host == "localhost"
        assert config.port == 8888
        assert config.rules == []

    def test_custom_host_port(self):
        """Test custom host and port."""
        config = MockServerConfig(host="0.0.0.0", port=9999)
        assert config.host == "0.0.0.0"
        assert config.port == 9999

    def test_add_rule(self):
        """Test adding rules."""
        config = MockServerConfig()
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule1 = MockRule(name="Rule 1", matcher=matcher, response=response, priority=5)
        rule2 = MockRule(name="Rule 2", matcher=matcher, response=response, priority=10)

        config.add_rule(rule1)
        config.add_rule(rule2)

        assert len(config.rules) == 2
        # Rules should be sorted by priority (highest first)
        assert config.rules[0].name == "Rule 2"
        assert config.rules[1].name == "Rule 1"

    def test_remove_rule(self):
        """Test removing rules."""
        config = MockServerConfig()
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule = MockRule(name="Test Rule", matcher=matcher, response=response)

        config.add_rule(rule)
        assert len(config.rules) == 1

        result = config.remove_rule("Test Rule")
        assert result is True
        assert len(config.rules) == 0

    def test_remove_nonexistent_rule(self):
        """Test removing non-existent rule."""
        config = MockServerConfig()
        result = config.remove_rule("Nonexistent")
        assert result is False

    def test_get_rule(self):
        """Test getting rule by name."""
        config = MockServerConfig()
        matcher = RequestMatcher(method="GET", path="/api/users")
        response = MockResponse(status_code=200, body={})
        rule = MockRule(name="Test Rule", matcher=matcher, response=response)

        config.add_rule(rule)
        retrieved = config.get_rule("Test Rule")

        assert retrieved is not None
        assert retrieved.name == "Test Rule"

    def test_get_nonexistent_rule(self):
        """Test getting non-existent rule."""
        config = MockServerConfig()
        retrieved = config.get_rule("Nonexistent")
        assert retrieved is None

    def test_find_matching_rule(self):
        """Test finding matching rule."""
        config = MockServerConfig()
        matcher1 = RequestMatcher(method="GET", path="/api/users")
        response1 = MockResponse(status_code=200, body={"users": []})
        rule1 = MockRule(name="Get Users", matcher=matcher1, response=response1, priority=10)

        matcher2 = RequestMatcher(method="GET", path="/api/posts")
        response2 = MockResponse(status_code=200, body={"posts": []})
        rule2 = MockRule(name="Get Posts", matcher=matcher2, response=response2, priority=5)

        config.add_rule(rule1)
        config.add_rule(rule2)

        # Should match first rule
        matched = config.find_matching_rule("GET", "/api/users")
        assert matched is not None
        assert matched.name == "Get Users"

        # Should match second rule
        matched = config.find_matching_rule("GET", "/api/posts")
        assert matched is not None
        assert matched.name == "Get Posts"

        # Should not match any rule
        matched = config.find_matching_rule("GET", "/api/comments")
        assert matched is None

    def test_priority_ordering(self):
        """Test that higher priority rules are checked first."""
        config = MockServerConfig()

        # Add multiple rules that match the same request
        matcher = RequestMatcher(method="GET", path="/api/test")
        response1 = MockResponse(status_code=200, body={"rule": 1})
        response2 = MockResponse(status_code=200, body={"rule": 2})
        response3 = MockResponse(status_code=200, body={"rule": 3})

        rule1 = MockRule(name="Rule 1", matcher=matcher, response=response1, priority=5)
        rule2 = MockRule(name="Rule 2", matcher=matcher, response=response2, priority=10)
        rule3 = MockRule(name="Rule 3", matcher=matcher, response=response3, priority=1)

        config.add_rule(rule1)
        config.add_rule(rule2)
        config.add_rule(rule3)

        # Should match highest priority rule
        matched = config.find_matching_rule("GET", "/api/test")
        assert matched is not None
        assert matched.name == "Rule 2"
        assert matched.priority == 10


class TestIntegration:
    """Integration tests for mock server models."""

    def test_complete_flow(self):
        """Test complete mock rule matching flow."""
        config = MockServerConfig()

        # Add multiple rules
        rule1 = MockRule(
            name="Get Users",
            matcher=RequestMatcher(method="GET", path="/api/users"),
            response=MockResponse(status_code=200, body={"users": []}),
            priority=10,
        )

        rule2 = MockRule(
            name="Get User by ID",
            matcher=RequestMatcher(method="GET", path=r"/api/users/\d+", match_type=MatchType.REGEX),
            response=MockResponse(status_code=200, body={"id": 123, "name": "John"}),
            priority=5,
        )

        rule3 = MockRule(
            name="Create User",
            matcher=RequestMatcher(
                method="POST", path="/api/users", body_pattern="John", body_match_type=MatchType.CONTAINS
            ),
            response=MockResponse(status_code=201, body={"id": 123}),
            priority=1,
        )

        config.add_rule(rule1)
        config.add_rule(rule2)
        config.add_rule(rule3)

        # Test matching
        assert config.find_matching_rule("GET", "/api/users").name == "Get Users"
        assert config.find_matching_rule("GET", "/api/users/123").name == "Get User by ID"
        assert config.find_matching_rule("POST", "/api/users", body='{"name":"John"}').name == "Create User"
        assert config.find_matching_rule("DELETE", "/api/users") is None

    def test_rule_with_all_features(self):
        """Test rule with all features enabled."""
        config = MockServerConfig()

        rule = MockRule(
            name="Complex Rule",
            matcher=RequestMatcher(
                method="POST",
                path="/api/users",
                match_type=MatchType.EXACT,
                query_params={"validate": "true"},
                headers={"Authorization": "Bearer token"},
                body_pattern=r'{"email":"[\w.]+@[\w.]+"}',
                body_match_type=MatchType.REGEX,
            ),
            response=MockResponse(
                status_code=201,
                body={"success": True},
                headers={"Location": "/api/users/123"},
                delay=DelayConfig(fixed_delay=0.1),
                failure=FailureConfig(failure_type=FailureType.HTTP_ERROR, probability=0.0),
            ),
            priority=10,
            enabled=True,
            description="A complex rule with all features",
        )

        config.add_rule(rule)

        # Should match with all conditions
        assert (
            rule.matches(
                "POST",
                "/api/users",
                query_params={"validate": "true"},
                headers={"Authorization": "Bearer token"},
                body='{"email":"test@example.com"}',
            )
            is True
        )

        # Should not match with different query param
        assert (
            rule.matches(
                "POST",
                "/api/users",
                query_params={"validate": "false"},
                headers={"Authorization": "Bearer token"},
                body='{"email":"test@example.com"}',
            )
            is False
        )

        # Should not match with invalid email
        assert (
            rule.matches(
                "POST",
                "/api/users",
                query_params={"validate": "true"},
                headers={"Authorization": "Bearer token"},
                body='{"email":"invalid"}',
            )
            is False
        )
