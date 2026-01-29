"""Mock server implementation for API testing.

Following Google Python Style Guide.
"""

import threading
import time
import json
from typing import Optional, Dict, Any, Tuple
from flask import Flask, request, Response
import logging

from apirun.mock.models import (
    MockServerConfig,
    MockRule,
    MockResponse,
    RequestMatcher,
    MatchType,
    DelayConfig,
    FailureConfig,
    FailureType,
)


class MockServer:
    """Mock HTTP server for API testing.

    Provides a configurable mock server that can simulate various API responses,
    delays, and failures based on configurable rules.

    Attributes:
        config: Mock server configuration
        app: Flask application instance
        server_thread: Background thread for server
        logger: Logger instance
    """

    def __init__(self, config: Optional[MockServerConfig] = None):
        """Initialize mock server.

        Args:
            config: Server configuration (uses default if None)
        """
        self.config = config or MockServerConfig()
        self.app = Flask(__name__)
        self.server_thread: Optional[threading.Thread] = None
        self._running = False

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        @self.app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        def handle_request(path: str = "") -> Response:
            """Handle incoming requests."""
            return self._handle_request(path)

        @self.app.route("/_mock/rules", methods=["GET"])
        def list_rules():
            """List all mock rules."""
            rules_data = [
                {
                    "name": rule.name,
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "description": rule.description,
                    "method": rule.matcher.method,
                    "path": rule.matcher.path,
                }
                for rule in self.config.rules
            ]
            return Response(json.dumps(rules_data, indent=2), mimetype="application/json")

        @self.app.route("/_mock/rules/<rule_name>", methods=["DELETE"])
        def delete_rule(rule_name: str):
            """Delete a mock rule."""
            if self.config.remove_rule(rule_name):
                return Response(json.dumps({"status": "deleted"}), mimetype="application/json")
            return Response(json.dumps({"error": "Rule not found"}, indent=2), status=404, mimetype="application/json")

        @self.app.route("/_mock/rules", methods=["POST"])
        def add_rule():
            """Add a new mock rule."""
            try:
                data = request.get_json()

                # Create request matcher
                matcher = RequestMatcher(
                    method=data["method"],
                    path=data["path"],
                    match_type=MatchType(data.get("match_type", "exact")),
                    query_params=data.get("query_params"),
                    headers=data.get("headers"),
                    body_pattern=data.get("body_pattern"),
                    body_match_type=MatchType(data.get("body_match_type", "exact")),
                )

                # Create delay config
                delay = None
                if "delay" in data:
                    delay_data = data["delay"]
                    delay = DelayConfig(
                        min_delay=delay_data.get("min_delay", 0.0),
                        max_delay=delay_data.get("max_delay", 0.0),
                        fixed_delay=delay_data.get("fixed_delay"),
                        jitter=delay_data.get("jitter", False),
                    )

                # Create failure config
                failure = None
                if "failure" in data:
                    failure_data = data["failure"]
                    failure = FailureConfig(
                        failure_type=FailureType(failure_data["failure_type"]),
                        probability=failure_data.get("probability", 1.0),
                        status_code=failure_data.get("status_code", 500),
                        error_message=failure_data.get("error_message", "Internal Server Error"),
                    )

                # Create mock response
                response = MockResponse(
                    status_code=data.get("status_code", 200),
                    body=data.get("body"),
                    headers=data.get("headers", {}),
                    delay=delay,
                    failure=failure,
                )

                # Create mock rule
                rule = MockRule(
                    name=data["name"],
                    matcher=matcher,
                    response=response,
                    priority=data.get("priority", 0),
                    enabled=data.get("enabled", True),
                    description=data.get("description", ""),
                )

                self.config.add_rule(rule)

                return Response(json.dumps({"status": "added"}), mimetype="application/json")
            except Exception as e:
                self.logger.error(f"Error adding rule: {e}")
                return Response(json.dumps({"error": str(e)}), status=400, mimetype="application/json")

        @self.app.route("/_mock/health", methods=["GET"])
        def health_check():
            """Health check endpoint."""
            return Response(json.dumps({"status": "ok", "running": self._running}), mimetype="application/json")

    def _handle_request(self, path: str) -> Response:
        """Handle incoming request and find matching rule.

        Args:
            path: Request path

        Returns:
            Flask response
        """
        # Get request details
        method = request.method
        full_path = f"/{path}" if path else "/"
        query_params = dict(request.args)
        headers = dict(request.headers)

        # Get body
        body = None
        if request.data:
            try:
                body = request.get_json(silent=True)
                if body is None:
                    body = request.data.decode("utf-8")
            except Exception:
                body = request.data.decode("utf-8", errors="ignore")

        # Log request
        self.logger.info(f"Mock request: {method} {full_path}")

        # Find matching rule
        rule = self.config.find_matching_rule(method, full_path, query_params, headers, body)

        if rule:
            self.logger.debug(f"Matched rule: {rule.name}")

            # Use get_response to evaluate conditions
            mock_response = rule.get_response(method, full_path, query_params, headers, body)

            # Log condition evaluation if applicable
            if rule.condition:
                condition_met = rule.evaluate_condition(method, full_path, query_params, headers, body)
                self.logger.debug(f"Condition evaluation: {condition_met}")

            return self._create_response(mock_response)

        # Use default response if no rule matches
        if self.config.default_response:
            self.logger.debug("Using default response")
            return self._create_response(self.config.default_response)

        # Return 404 if no rule matches
        self.logger.warning(f"No matching rule for {method} {full_path}")
        return Response(
            json.dumps({"error": "No matching mock rule", "method": method, "path": full_path}),
            status=404,
            mimetype="application/json",
        )

    def _create_response(self, mock_response: MockResponse) -> Response:
        """Create Flask response from mock response config.

        Args:
            mock_response: Mock response configuration

        Returns:
            Flask response
        """
        # Check for failure simulation
        if mock_response.failure:
            if mock_response.failure.should_fail():
                self.logger.debug(f"Simulating failure: {mock_response.failure.failure_type.value}")
                return self._create_failure_response(mock_response.failure)

        # Apply delay if configured
        if mock_response.delay:
            delay = mock_response.delay.get_delay()
            if delay > 0:
                self.logger.debug(f"Applying delay: {delay:.2f}s")
                time.sleep(delay)

        # Prepare response body
        body = None
        if mock_response.body is not None:
            if isinstance(mock_response.body, dict):
                body = json.dumps(mock_response.body, indent=2)
            elif isinstance(mock_response.body, (list, str, int, float, bool)):
                body = json.dumps(mock_response.body)
            else:
                body = str(mock_response.body)

        # Create response
        response = Response(
            response=body,
            status=mock_response.status_code,
            mimetype="application/json" if body and self._is_json(body) else "text/plain",
        )

        # Add headers
        for key, value in mock_response.headers.items():
            response.headers[key] = value

        return response

    def _create_failure_response(self, failure: FailureConfig) -> Response:
        """Create failure response based on failure type.

        Args:
            failure: Failure configuration

        Returns:
            Flask response
        """
        if failure.failure_type == FailureType.TIMEOUT:
            # Simulate timeout by waiting a long time
            time.sleep(30)
            return Response(json.dumps({"error": "Timeout"}), status=408, mimetype="application/json")

        elif failure.failure_type == FailureType.CONNECTION_ERROR:
            # Simulate connection error (can't really do this in Flask)
            return Response(json.dumps({"error": "Connection error"}), status=503, mimetype="application/json")

        elif failure.failure_type == FailureType.HTTP_ERROR:
            return Response(
                json.dumps({"error": failure.error_message}),
                status=failure.status_code,
                mimetype="application/json",
            )

        elif failure.failure_type == FailureType.EMPTY_RESPONSE:
            return Response(response="", status=200)

        elif failure.failure_type == FailureType.MALFORMED_JSON:
            return Response(response="{invalid json", status=200, mimetype="application/json")

        elif failure.failure_type == FailureType.LARGE_DELAY:
            # Simulate large delay (10 seconds)
            time.sleep(10)
            return Response(json.dumps({"error": "Large delay"}), status=200, mimetype="application/json")

        else:
            return Response(json.dumps({"error": "Unknown failure type"}), status=500, mimetype="application/json")

    def _is_json(self, text: str) -> bool:
        """Check if text is JSON.

        Args:
            text: Text to check

        Returns:
            True if text is JSON
        """
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def start(self, blocking: bool = False) -> None:
        """Start the mock server.

        Args:
            blocking: Whether to block the calling thread
        """
        if self._running:
            self.logger.warning("Mock server is already running")
            return

        self._running = True

        if blocking:
            self.app.run(host=self.config.host, port=self.config.port, debug=False, use_reloader=False)
        else:
            # Run in background thread
            self.server_thread = threading.Thread(
                target=self.app.run,
                kwargs={"host": self.config.host, "port": self.config.port, "debug": False, "use_reloader": False},
                daemon=True,
            )
            self.server_thread.start()
            self.logger.info(f"Mock server started on http://{self.config.host}:{self.config.port}")

    def stop(self) -> None:
        """Stop the mock server."""
        if not self._running:
            self.logger.warning("Mock server is not running")
            return

        self._running = False

        # Note: Flask doesn't provide a clean way to shutdown from code
        # In production, you might want to use a different approach
        self.logger.info("Mock server stopped")

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if server is running
        """
        return self._running

    def add_rule(self, rule: MockRule) -> None:
        """Add a mock rule.

        Args:
            rule: Mock rule to add
        """
        self.config.add_rule(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a mock rule by name.

        Args:
            rule_name: Name of the rule to remove

        Returns:
            True if rule was removed
        """
        return self.config.remove_rule(rule_name)

    def get_rule(self, rule_name: str) -> Optional[MockRule]:
        """Get a mock rule by name.

        Args:
            rule_name: Name of the rule

        Returns:
            Mock rule if found
        """
        return self.config.get_rule(rule_name)

    def list_rules(self) -> list:
        """List all mock rules.

        Returns:
            List of mock rules
        """
        return self.config.rules


def create_simple_rule(
    name: str,
    method: str,
    path: str,
    status_code: int = 200,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    priority: int = 0,
) -> MockRule:
    """Create a simple mock rule.

    Args:
        name: Rule name
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        body: Response body
        headers: Response headers
        priority: Rule priority

    Returns:
        Mock rule
    """
    matcher = RequestMatcher(method=method, path=path, match_type=MatchType.EXACT)

    response = MockResponse(
        status_code=status_code,
        body=body,
        headers=headers or {},
    )

    return MockRule(name=name, matcher=matcher, response=response, priority=priority)


def create_regex_rule(
    name: str,
    method: str,
    path_pattern: str,
    status_code: int = 200,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
    priority: int = 0,
) -> MockRule:
    """Create a regex-based mock rule.

    Args:
        name: Rule name
        method: HTTP method
        path_pattern: Regex pattern for path
        status_code: HTTP status code
        body: Response body
        headers: Response headers
        priority: Rule priority

    Returns:
        Mock rule
    """
    matcher = RequestMatcher(method=method, path=path_pattern, match_type=MatchType.REGEX)

    response = MockResponse(
        status_code=status_code,
        body=body,
        headers=headers or {},
    )

    return MockRule(name=name, matcher=matcher, response=response, priority=priority)
