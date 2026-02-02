"""Wait Executor for Sisyphus API Engine.

This module implements the wait step executor, supporting:
- Fixed time wait (seconds)
- Conditional wait with polling (wait until condition is true)
- API conditional wait (wait until API response meets condition)
- Database conditional wait (wait until database query result meets condition)

Following Google Python Style Guide.
"""

import time
from typing import Any, Dict
from datetime import datetime

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.utils.template import render_template


class APIConditionalWait:
    """Handler for API-based conditional wait."""

    def __init__(self, variable_manager: VariableManager):
        """Initialize API conditional wait handler.

        Args:
            variable_manager: Variable manager instance
        """
        self.variable_manager = variable_manager

    def check_condition(
        self, request_config: Dict[str, Any], check_expression: str
    ) -> bool:
        """Execute API request and check if condition is met.

        Args:
            request_config: API request configuration
            check_expression: Condition to check (Jinja2 template)

        Returns:
            True if condition is met, False otherwise
        """
        from apirun.executor.api_executor import APIExecutor

        # Create a temporary TestStep for the API request
        temp_step = TestStep(
            name="conditional_check_api",
            type="request",
            method=request_config.get("method", "GET"),
            url=request_config.get("url"),
            headers=request_config.get("headers"),
            body=request_config.get("body"),
            params=request_config.get("params"),
        )

        # Create API executor and execute request
        api_executor = APIExecutor(
            self.variable_manager, temp_step, timeout=30, retry_times=0
        )

        try:
            result = api_executor.execute()

            # Extract response data for condition check
            # result is StepResult object, access response attribute
            response_data = result.response if result.response else {}

            # Create a temporary variable context with response data
            temp_vars = {
                "status_code": response_data.get("status_code"),
                "body": response_data.get("body", {}),
                "headers": response_data.get("headers", {}),
                "response": response_data,
            }

            # Merge with existing variables
            check_context = {**self.variable_manager.get_all_variables(), **temp_vars}

            # Render and evaluate check expression
            rendered_check = render_template(check_expression, check_context)

            # Check if condition is true
            return self._is_condition_true(rendered_check)

        except Exception:
            return False

    @staticmethod
    def _is_condition_true(rendered_condition: str) -> bool:
        """Check if rendered condition evaluates to true.

        Args:
            rendered_condition: Rendered condition string

        Returns:
            True if condition is true, False otherwise
        """
        if not rendered_condition:
            return False

        condition_lower = rendered_condition.lower().strip()
        true_values = ["true", "1", "yes", "y", "ok", "success"]
        return condition_lower in true_values


class DatabaseConditionalWait:
    """Handler for database-based conditional wait."""

    def __init__(self, variable_manager: VariableManager):
        """Initialize database conditional wait handler.

        Args:
            variable_manager: Variable manager instance
        """
        self.variable_manager = variable_manager

    def check_condition(
        self,
        db_config: Dict[str, Any],
        sql: str,
        params: list,
        check_expression: str,
    ) -> bool:
        """Execute database query and check if condition is met.

        Args:
            db_config: Database configuration
            sql: SQL query
            params: Query parameters
            check_expression: Condition to check (Jinja2 template)

        Returns:
            True if condition is met, False otherwise
        """
        try:
            from apirun.core.template_functions import _execute_db_query

            # Execute query
            result = _execute_db_query(db_config, sql, tuple(params))

            # Create a temporary variable context with query result
            temp_vars = {
                "result": result,
                "rows": result if isinstance(result, list) else [result],
                "row": result if isinstance(result, dict) else {},
            }

            # Merge with existing variables
            check_context = {**self.variable_manager.get_all_variables(), **temp_vars}

            # Render and evaluate check expression
            rendered_check = render_template(check_expression, check_context)

            # Check if condition is true
            return self._is_condition_true(rendered_check)

        except Exception:
            return False

    @staticmethod
    def _is_condition_true(rendered_condition: str) -> bool:
        """Check if rendered condition evaluates to true.

        Args:
            rendered_condition: Rendered condition string

        Returns:
            True if condition is true, False otherwise
        """
        if not rendered_condition:
            return False

        condition_lower = rendered_condition.lower().strip()
        true_values = ["true", "1", "yes", "y", "ok", "success"]
        return condition_lower in true_values


class WaitExecutor(StepExecutor):
    """Executor for wait steps.

    Supports two wait modes:
    1. Fixed time wait: Wait for specified seconds
    2. Conditional wait: Poll and wait until condition becomes true

    Attributes:
        variable_manager: Variable manager instance
        step: Test step to execute
        timeout: Step timeout in seconds
        retry_times: Number of retry attempts
    """

    def __init__(
        self,
        variable_manager: VariableManager,
        step: TestStep,
        timeout: int = 300,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize WaitExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds (default: 300 for wait steps)
            retry_times: Default retry count
            previous_results: List of previous step results
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.timeout = step.timeout or timeout

    def _execute_step(self, rendered_step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the wait step.

        Args:
            rendered_step: Rendered step with variables resolved

        Returns:
            Execution result dictionary

        Raises:
            ValueError: If wait configuration is invalid
            TimeoutError: If conditional wait exceeds max_wait time
        """
        start_time = datetime.now()

        # Check for wait_condition (API or Database conditional wait)
        wait_condition = rendered_step.get("wait_condition")
        if wait_condition:
            return self._conditional_wait_check(rendered_step, start_time)

        # Check if it's a conditional wait
        if rendered_step.get("condition"):
            return self._conditional_wait(rendered_step, start_time)
        elif rendered_step.get("seconds"):
            return self._fixed_wait(rendered_step, start_time)
        else:
            raise ValueError("Wait step must have either 'seconds' or 'condition' or 'wait_condition'")

    def _fixed_wait(self, rendered_step: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Execute fixed time wait.

        Args:
            rendered_step: Rendered step with variables resolved
            start_time: Wait start time

        Returns:
            Execution result dictionary
        """
        seconds = rendered_step["seconds"]

        # Ensure seconds is a float
        try:
            wait_seconds = float(seconds)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid wait seconds value: {seconds}")

        if wait_seconds < 0:
            raise ValueError(f"Wait seconds must be non-negative, got: {wait_seconds}")

        # Check timeout
        if wait_seconds > self.timeout:
            raise ValueError(
                f"Wait time ({wait_seconds}s) exceeds timeout ({self.timeout}s)"
            )

        # Perform wait
        time.sleep(wait_seconds)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        return {
            "response": {
                "wait_type": "fixed",
                "wait_seconds": wait_seconds,
                "actual_wait_seconds": elapsed,
            },
            "performance": self._create_performance_metrics(total_time=elapsed * 1000),
        }

    def _conditional_wait(
        self, rendered_step: Dict[str, Any], start_time: datetime
    ) -> Dict[str, Any]:
        """Execute conditional wait with polling.

        Waits until the condition becomes true or max_wait is exceeded.

        Args:
            rendered_step: Rendered step with variables resolved
            start_time: Wait start time

        Returns:
            Execution result dictionary

        Raises:
            TimeoutError: If condition does not become true within max_wait time
            ValueError: If condition expression is invalid
        """
        condition = rendered_step["condition"]
        interval = rendered_step.get("interval", 1.0)
        max_wait = rendered_step.get("max_wait", 60.0)

        # Validate parameters
        try:
            interval = float(interval)
            max_wait = float(max_wait)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid interval or max_wait value: {e}")

        if interval <= 0:
            raise ValueError(f"Polling interval must be positive, got: {interval}")

        if max_wait <= 0:
            raise ValueError(f"Maximum wait time must be positive, got: {max_wait}")

        if max_wait > self.timeout:
            raise ValueError(
                f"Max wait time ({max_wait}s) exceeds timeout ({self.timeout}s)"
            )

        elapsed = 0.0
        poll_count = 0

        # Poll loop
        while elapsed < max_wait:
            # Evaluate condition
            try:
                rendered_condition = render_template(
                    condition, self.variable_manager.get_all_variables()
                )

                # Check if condition is true
                if self._is_condition_true(rendered_condition):
                    end_time = datetime.now()
                    elapsed = (end_time - start_time).total_seconds()

                    return {
                        "response": {
                            "wait_type": "conditional",
                            "condition": condition,
                            "result": True,
                            "elapsed_seconds": elapsed,
                            "poll_count": poll_count + 1,
                        },
                        "performance": self._create_performance_metrics(
                            total_time=elapsed * 1000
                        ),
                    }
            except Exception as e:
                raise ValueError(f"Failed to evaluate condition '{condition}': {e}")

            # Wait before next poll
            time.sleep(interval)
            elapsed += interval
            poll_count += 1

        # Condition did not become true within max_wait
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        raise TimeoutError(
            f"Condition '{condition}' did not become true within {max_wait}s "
            f"(elapsed: {elapsed:.2f}s, polls: {poll_count})"
        )

    def _conditional_wait_check(
        self, rendered_step: Dict[str, Any], start_time: datetime
    ) -> Dict[str, Any]:
        """Execute API or Database conditional wait with polling.

        Waits until the API response or database query result meets the condition.

        Args:
            rendered_step: Rendered step with variables resolved
            start_time: Wait start time

        Returns:
            Execution result dictionary

        Raises:
            TimeoutError: If condition does not become true within max_wait time
            ValueError: If wait_condition configuration is invalid
        """
        wait_condition = rendered_step["wait_condition"]
        condition_type = wait_condition.get("type")
        interval = wait_condition.get("interval", 2.0)
        max_wait = wait_condition.get("timeout", 30.0)

        # Validate parameters
        try:
            interval = float(interval)
            max_wait = float(max_wait)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid interval or timeout value: {e}")

        if interval <= 0:
            raise ValueError(f"Polling interval must be positive, got: {interval}")

        if max_wait <= 0:
            raise ValueError(f"Maximum wait time must be positive, got: {max_wait}")

        if max_wait > self.timeout:
            raise ValueError(
                f"Max wait time ({max_wait}s) exceeds timeout ({self.timeout}s)"
            )

        elapsed = 0.0
        poll_count = 0

        # Poll loop
        while elapsed < max_wait:
            # Check condition based on type
            try:
                if condition_type == "api":
                    # API conditional wait
                    request_config = wait_condition.get("request", {})
                    check_expression = wait_condition.get("check", "")

                    api_wait = APIConditionalWait(self.variable_manager)
                    condition_met = api_wait.check_condition(request_config, check_expression)

                elif condition_type == "database":
                    # Database conditional wait
                    db_config = wait_condition.get("database", {})
                    sql = wait_condition.get("sql", "")
                    params = wait_condition.get("params", [])
                    check_expression = wait_condition.get("check", "")

                    db_wait = DatabaseConditionalWait(self.variable_manager)
                    condition_met = db_wait.check_condition(db_config, sql, params, check_expression)

                else:
                    raise ValueError(f"Unsupported wait_condition type: {condition_type}")

                # Check if condition is met
                if condition_met:
                    end_time = datetime.now()
                    elapsed = (end_time - start_time).total_seconds()

                    return {
                        "response": {
                            "wait_type": "conditional_check",
                            "condition_type": condition_type,
                            "result": True,
                            "elapsed_seconds": elapsed,
                            "poll_count": poll_count + 1,
                        },
                        "performance": self._create_performance_metrics(
                            total_time=elapsed * 1000
                        ),
                    }

            except Exception as e:
                raise ValueError(f"Failed to check {condition_type} condition: {e}")

            # Wait before next poll
            time.sleep(interval)
            elapsed += interval
            poll_count += 1

        # Condition did not become true within max_wait
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        raise TimeoutError(
            f"{condition_type.capitalize()} condition did not become true within {max_wait}s "
            f"(elapsed: {elapsed:.2f}s, polls: {poll_count})"
        )

    def _is_condition_true(self, rendered_condition: str) -> bool:
        """Check if rendered condition evaluates to true.

        Args:
            rendered_condition: Rendered condition string

        Returns:
            True if condition is true, False otherwise
        """
        if not rendered_condition:
            return False

        # Convert to lowercase for comparison
        condition_lower = rendered_condition.lower().strip()

        # Check for boolean-like values
        true_values = ["true", "1", "yes", "y", "ok", "success"]
        return condition_lower in true_values

    def _render_step(self) -> Dict[str, Any]:
        """Render variables in wait step definition.

        Returns:
            Rendered step dictionary
        """
        context = self.variable_manager.get_all_variables()

        rendered = {
            "name": self.step.name,
            "type": self.step.type,
        }

        # Render seconds
        if self.step.seconds is not None:
            rendered["seconds"] = render_template(
                str(self.step.seconds), context
            )

        # Render condition
        if self.step.condition:
            rendered["condition"] = render_template(self.step.condition, context)

        # Render interval
        if self.step.interval is not None:
            rendered["interval"] = render_template(
                str(self.step.interval), context
            )

        # Render max_wait
        if self.step.max_wait is not None:
            rendered["max_wait"] = render_template(
                str(self.step.max_wait), context
            )

        # Render wait_condition
        if self.step.wait_condition is not None:
            rendered["wait_condition"] = self.step.wait_condition

        return rendered
