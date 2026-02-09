"""Data models for mock server.

Following Google Python Style Guide.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any


class MatchType(Enum):
    """Match type for request matching."""

    EXACT = 'exact'  # Exact match
    REGEX = 'regex'  # Regular expression match
    CONTAINS = 'contains'  # Contains substring
    JSON_PATH = 'json_path'  # JSONPath expression for body


class FailureType(Enum):
    """Failure type for failure simulation."""

    TIMEOUT = 'timeout'  # Simulate timeout
    CONNECTION_ERROR = 'connection_error'  # Simulate connection error
    HTTP_ERROR = 'http_error'  # Simulate HTTP error
    EMPTY_RESPONSE = 'empty_response'  # Return empty response
    MALFORMED_JSON = 'malformed_json'  # Return malformed JSON
    LARGE_DELAY = 'large_delay'  # Simulate large delay


@dataclass
class DelayConfig:
    """Configuration for response delay simulation.

    Attributes:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds (for random delay)
        fixed_delay: Fixed delay in seconds (if set, min/max are ignored)
        jitter: Whether to add random jitter to delay
    """

    min_delay: float = 0.0
    max_delay: float = 0.0
    fixed_delay: float | None = None
    jitter: bool = False

    def get_delay(self) -> float:
        """Get actual delay time.

        Returns:
            Delay time in seconds
        """
        import random

        if self.fixed_delay is not None:
            delay = self.fixed_delay
        else:
            delay = random.uniform(self.min_delay, self.max_delay)

        if self.jitter:
            delay += random.uniform(0, 0.1)  # Add up to 100ms jitter

        return max(0, delay)


@dataclass
class FailureConfig:
    """Configuration for failure simulation.

    Attributes:
        failure_type: Type of failure to simulate
        probability: Probability of failure (0.0 to 1.0)
        status_code: HTTP status code for HTTP_ERROR type
        error_message: Error message to return
    """

    failure_type: FailureType
    probability: float = 1.0
    status_code: int = 500
    error_message: str = 'Internal Server Error'

    def should_fail(self) -> bool:
        """Check if failure should occur based on probability.

        Returns:
            True if failure should occur
        """
        import random

        return random.random() < self.probability


@dataclass
class MockResponse:
    """Mock response configuration.

    Attributes:
        status_code: HTTP status code
        body: Response body (can be dict for JSON or str for text)
        headers: Response headers
        delay: Delay configuration
        failure: Failure configuration
    """

    status_code: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    delay: DelayConfig | None = None
    failure: FailureConfig | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            'status_code': self.status_code,
            'body': self.body,
            'headers': self.headers,
        }


@dataclass
class RequestMatcher:
    """Request matching configuration.

    Attributes:
        method: HTTP method (GET/POST/PUT/DELETE/etc.)
        path: Request path pattern
        match_type: Type of path matching (exact/regex/contains)
        query_params: Query parameters to match (exact match)
        headers: Headers to match (exact match)
        body_pattern: Body pattern for matching
        body_match_type: Type of body matching
    """

    method: str
    path: str
    match_type: MatchType = MatchType.EXACT
    query_params: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    body_pattern: str | None = None
    body_match_type: MatchType = MatchType.EXACT

    def __post_init__(self):
        """Compile regex patterns if needed."""
        if self.match_type == MatchType.REGEX:
            try:
                self._path_pattern = re.compile(self.path)
            except re.error as e:
                raise ValueError(f'Invalid regex pattern for path: {e}')

        if self.body_pattern and self.body_match_type == MatchType.REGEX:
            try:
                self._body_pattern = re.compile(self.body_pattern)
            except re.error as e:
                raise ValueError(f'Invalid regex pattern for body: {e}')

    def matches(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> bool:
        """Check if request matches this matcher.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            True if request matches
        """
        # Check method
        if self.method.upper() != method.upper():
            return False

        # Check path
        if self.match_type == MatchType.EXACT:
            if self.path != path:
                return False
        elif self.match_type == MatchType.REGEX:
            if not self._path_pattern.match(path):
                return False
        elif self.match_type == MatchType.CONTAINS:
            if self.path not in path:
                return False

        # Check query params
        if self.query_params:
            if not query_params:
                return False
            for key, value in self.query_params.items():
                if query_params.get(key) != value:
                    return False

        # Check headers
        if self.headers:
            if not headers:
                return False
            for key, value in self.headers.items():
                if headers.get(key) != value:
                    return False

        # Check body
        if self.body_pattern:
            import json

            if body is None:
                return False

            # Convert body to string if it's a dict
            body_str = json.dumps(body) if isinstance(body, dict) else str(body)

            if self.body_match_type == MatchType.EXACT:
                if body_str != self.body_pattern:
                    return False
            elif self.body_match_type == MatchType.REGEX:
                if not self._body_pattern.search(body_str):
                    return False
            elif self.body_match_type == MatchType.CONTAINS:
                if self.body_pattern not in body_str:
                    return False

        return True


@dataclass
class MockRule:
    """Mock rule definition.

    Attributes:
        name: Rule name
        matcher: Request matcher
        response: Mock response configuration
        priority: Rule priority (higher = checked first)
        enabled: Whether the rule is enabled
        description: Rule description
        condition: Optional Jinja2 expression for conditional matching
        else_response: Response to use when condition is false (if condition is set)
    """

    name: str
    matcher: RequestMatcher
    response: MockResponse
    priority: int = 0
    enabled: bool = True
    description: str = ''
    condition: str | None = None
    else_response: MockResponse | None = None

    def matches(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> bool:
        """Check if request matches this rule.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            True if request matches and rule is enabled
        """
        if not self.enabled:
            return False

        return self.matcher.matches(method, path, query_params, headers, body)

    def evaluate_condition(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> bool:
        """Evaluate the condition expression for this rule.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            True if condition evaluates to true or no condition is set
        """
        if not self.condition:
            return True

        from apirun.utils.template import render_template

        # Create context with request data
        context = {
            'request': {
                'method': method,
                'path': path,
                'query_params': query_params or {},
                'headers': headers or {},
                'body': body,
            }
        }

        try:
            rendered = render_template(self.condition, context)
            # Check if rendered result is truthy
            if isinstance(rendered, bool):
                return rendered
            return str(rendered).lower() in ('true', '1', 'yes', 'y')
        except Exception:
            return False

    def get_response(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> MockResponse:
        """Get the appropriate response based on condition evaluation.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            MockResponse to use
        """
        if self.condition:
            condition_met = self.evaluate_condition(
                method, path, query_params, headers, body
            )
            if condition_met:
                return self.response
            elif self.else_response:
                return self.else_response

        return self.response


@dataclass
class MockServerConfig:
    """Mock server configuration.

    Attributes:
        host: Server host
        port: Server port
        rules: List of mock rules
        default_response: Default response when no rule matches
        auto_start: Whether to auto-start server
    """

    host: str = 'localhost'
    port: int = 8888
    rules: list[MockRule] = field(default_factory=list)
    default_response: MockResponse | None = None
    auto_start: bool = False

    def add_rule(self, rule: MockRule) -> None:
        """Add a mock rule.

        Args:
            rule: Mock rule to add
        """
        self.rules.append(rule)
        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a mock rule by name.

        Args:
            rule_name: Name of the rule to remove

        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def get_rule(self, rule_name: str) -> MockRule | None:
        """Get a mock rule by name.

        Args:
            rule_name: Name of the rule

        Returns:
            Mock rule if found, None otherwise
        """
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

    def find_matching_rule(
        self,
        method: str,
        path: str,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> MockRule | None:
        """Find the first matching rule for the request.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            First matching rule or None
        """
        for rule in self.rules:
            if rule.matches(method, path, query_params, headers, body):
                return rule
        return None
