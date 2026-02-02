"""Poll Executor for Sisyphus API Engine.

This module implements polling mechanism for async operations.
Following Google Python Style Guide.
"""

import time
import json
from typing import Any, Dict, Optional
from datetime import datetime

from apirun.executor.step_executor import StepExecutor
from apirun.executor.api_executor import APIExecutor
from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.extractor.jsonpath_extractor import JSONPathExtractor


class PollStepExecutor(StepExecutor):
    """Executor for polling async operations.

    Supports:
    - JSONPath-based condition checking
    - Status code checking
    - Custom backoff strategies (fixed/exponential)
    - Timeout handling
    - Configurable polling intervals

    Usage:
        - name: "Wait for project ready"
          type: poll
          url: "/api/project/status"
          method: GET
          poll_config:
            condition:
              type: jsonpath
              path: "$.data.status"
              operator: "eq"
              expect: "ACTIVE"
            max_attempts: 30
            interval: 2000
            timeout: 60000
            backoff: "fixed"
          on_timeout:
            behavior: "fail"
            message: "Project initialization timeout"
    """

    def __init__(
        self,
        variable_manager: VariableManager,
        step: TestStep,
        timeout: int = 30,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize PollStepExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds
            retry_times: Default retry count
            previous_results: List of previous step results
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)

    def _execute_step(self, rendered_step: Dict[str, Any]) -> Any:
        """Execute polling until condition is met or timeout.

        Args:
            rendered_step: Rendered step data

        Returns:
            Polling result with final response and attempt count

        Raises:
            TimeoutError: If polling times out
        """
        poll_config = rendered_step.get("poll_config", {})
        on_timeout = rendered_step.get("on_timeout", {})

        # Extract polling configuration
        condition = poll_config.get("condition", {})
        max_attempts = poll_config.get("max_attempts", 30)
        interval_ms = poll_config.get("interval", 2000)
        timeout_ms = poll_config.get("timeout", 60000)
        backoff = poll_config.get("backoff", "fixed")

        # Convert to seconds
        interval = interval_ms / 1000.0
        timeout_seconds = timeout_ms / 1000.0

        # Initialize
        start_time = time.time()
        attempt = 0
        last_response = None
        backoff_delay = interval

        while attempt < max_attempts:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                timeout_msg = on_timeout.get("message", f"Polling timeout after {timeout_seconds}s")
                behavior = on_timeout.get("behavior", "fail")

                if behavior == "continue":
                    return {
                        "success": False,
                        "timed_out": True,
                        "message": timeout_msg,
                        "attempts": attempt,
                        "elapsed_seconds": elapsed,
                        "last_response": last_response,
                    }
                else:
                    raise TimeoutError(timeout_msg)

            attempt += 1

            # Execute request
            try:
                # Use APIExecutor to make the request
                api_executor = APIExecutor(
                    self.variable_manager,
                    self.step,
                    self.timeout,
                    0,  # No retry for individual poll attempts
                    self.previous_results,
                )

                # Execute the request
                result = api_executor._execute_step(rendered_step)
                last_response = result

                # Check if condition is met
                if self._check_condition(result, condition):
                    return {
                        "success": True,
                        "condition_met": True,
                        "attempts": attempt,
                        "elapsed_seconds": time.time() - start_time,
                        "response": result,
                    }

            except Exception as e:
                # Continue polling on error, will timeout if needed
                last_response = {"error": str(e)}

            # Wait before next attempt
            if attempt < max_attempts:
                # Calculate backoff delay
                if backoff == "exponential":
                    backoff_delay = interval * (2 ** (attempt - 1))
                elif backoff == "linear":
                    backoff_delay = interval * attempt
                else:  # fixed
                    backoff_delay = interval

                # Cap the delay to avoid excessive waiting
                backoff_delay = min(backoff_delay, 30.0)

                time.sleep(backoff_delay)

        # Max attempts reached
        timeout_msg = on_timeout.get("message", f"Polling reached max attempts ({max_attempts})")
        behavior = on_timeout.get("behavior", "fail")

        if behavior == "continue":
            return {
                "success": False,
                "max_attempts_reached": True,
                "message": timeout_msg,
                "attempts": attempt,
                "elapsed_seconds": time.time() - start_time,
                "last_response": last_response,
            }
        else:
            raise TimeoutError(timeout_msg)

    def _check_condition(self, response: Any, condition: Dict[str, Any]) -> bool:
        """Check if polling condition is met.

        Args:
            response: Response from the request
            condition: Condition configuration

        Returns:
            True if condition is met, False otherwise
        """
        condition_type = condition.get("type", "jsonpath")

        if condition_type == "jsonpath":
            return self._check_jsonpath_condition(response, condition)
        elif condition_type == "status_code":
            return self._check_status_code_condition(response, condition)
        elif condition_type == "script":
            # Future: support custom script conditions
            return False
        else:
            raise ValueError(f"Unsupported condition type: {condition_type}")

    def _check_jsonpath_condition(self, response: Any, condition: Dict[str, Any]) -> bool:
        """Check JSONPath-based condition.

        Args:
            response: Response from the request
            condition: Condition with path, operator, expect

        Returns:
            True if condition is met
        """
        path = condition.get("path", "$")
        operator = condition.get("operator", "eq")
        expect = condition.get("expect")

        # Extract value using JSONPath
        try:
            extractor = JSONPathExtractor()
            actual = extractor.extract(path, response, index=0)

            # Handle multiple matches
            if isinstance(actual, list):
                if len(actual) == 0:
                    actual = None
                elif len(actual) == 1:
                    actual = actual[0]
                # Keep as list if multiple values

            # Compare based on operator
            return self._compare_values(actual, expect, operator)

        except Exception as e:
            print(f"Warning: Failed to check JSONPath condition: {e}")
            return False

    def _check_status_code_condition(self, response: Any, condition: Dict[str, Any]) -> bool:
        """Check HTTP status code condition.

        Args:
            response: Response from the request
            condition: Condition with operator, expect

        Returns:
            True if condition is met
        """
        operator = condition.get("operator", "eq")
        expect = condition.get("expect")

        # Extract status code
        if hasattr(response, "get"):
            status_code = response.get("status_code")
            if status_code is None and "response" in response:
                status_code = response["response"].get("status_code")
        else:
            return False

        return self._compare_values(status_code, expect, operator)

    def _compare_values(self, actual: Any, expect: Any, operator: str) -> bool:
        """Compare values based on operator.

        Args:
            actual: Actual value
            expect: Expected value
            operator: Comparison operator

        Returns:
            True if comparison succeeds
        """
        if operator == "eq":
            return actual == expect
        elif operator == "ne":
            return actual != expect
        elif operator == "gt":
            try:
                return float(actual) > float(expect)
            except (ValueError, TypeError):
                return False
        elif operator == "lt":
            try:
                return float(actual) < float(expect)
            except (ValueError, TypeError):
                return False
        elif operator == "ge":
            try:
                return float(actual) >= float(expect)
            except (ValueError, TypeError):
                return False
        elif operator == "le":
            try:
                return float(actual) <= float(expect)
            except (ValueError, TypeError):
                return False
        elif operator == "contains":
            if isinstance(actual, (list, tuple, str)):
                return expect in actual
            return False
        elif operator == "exists":
            return actual is not None
        else:
            raise ValueError(f"Unsupported operator: {operator}")
