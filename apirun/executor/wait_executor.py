"""Wait Executor for Sisyphus API Engine.

This module implements the wait step executor, supporting:
- Fixed time wait (seconds)
- Conditional wait with polling (wait until condition is true)

Following Google Python Style Guide.
"""

import time
from typing import Any, Dict
from datetime import datetime

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.utils.template import render_template


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

        # Check if it's a conditional wait
        if rendered_step.get("condition"):
            return self._conditional_wait(rendered_step, start_time)
        elif rendered_step.get("seconds"):
            return self._fixed_wait(rendered_step, start_time)
        else:
            raise ValueError("Wait step must have either 'seconds' or 'condition'")

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

        return rendered
