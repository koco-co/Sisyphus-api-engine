"""Loop Executor for Sisyphus API Engine.

This module implements the loop step executor, supporting:
- For loops: Iterate a fixed number of times
- While loops: Iterate while condition is true

Following Google Python Style Guide.
"""

from datetime import datetime
from typing import Any

from apirun.core.models import StepResult, TestStep
from apirun.core.variable_manager import VariableManager
from apirun.executor.step_executor import StepExecutor
from apirun.utils.template import render_template


class LoopExecutor(StepExecutor):
    """Executor for loop steps.

    Supports two loop types:
    1. For loops: Iterate for a specified count
    2. While loops: Iterate while condition is true

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
        """Initialize LoopExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds (default: 300 for loop steps)
            retry_times: Default retry count
            previous_results: List of previous step results
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.loop_results: list[StepResult] = []

    def _execute_step(self, rendered_step: dict[str, Any]) -> dict[str, Any]:
        """Execute the loop step.

        Args:
            rendered_step: Rendered step with variables resolved

        Returns:
            Execution result dictionary

        Raises:
            ValueError: If loop configuration is invalid
        """
        start_time = datetime.now()
        loop_type = rendered_step.get('loop_type')

        if not loop_type:
            raise ValueError("Loop step must specify 'loop_type' (for/while)")

        if loop_type == 'for':
            return self._execute_for_loop(rendered_step, start_time)
        elif loop_type == 'while':
            return self._execute_while_loop(rendered_step, start_time)
        else:
            raise ValueError(f'Unsupported loop type: {loop_type}')

    def _execute_for_loop(
        self, rendered_step: dict[str, Any], start_time: datetime
    ) -> dict[str, Any]:
        """Execute for loop.

        Iterates a fixed number of times, with optional loop variable.

        Args:
            rendered_step: Rendered step with variables resolved
            start_time: Loop start time

        Returns:
            Execution result dictionary
        """
        loop_count = rendered_step.get('loop_count')
        loop_variable = rendered_step.get('loop_variable', 'index')
        loop_steps = rendered_step.get('loop_steps', [])

        if loop_count is None:
            raise ValueError("For loop must specify 'loop_count'")

        try:
            loop_count = int(loop_count)
        except (ValueError, TypeError):
            raise ValueError(f'Invalid loop_count value: {loop_count}')

        if loop_count < 0:
            raise ValueError(f'Loop count must be non-negative, got: {loop_count}')

        if not loop_steps:
            raise ValueError("Loop must contain 'loop_steps' to execute")

        # Execute loop
        iteration_results = []

        for i in range(loop_count):
            # Set loop variable
            if loop_variable:
                self.variable_manager.set_variable(loop_variable, i)

            # Execute loop steps
            for step_dict in loop_steps:
                # Import here to avoid circular dependency

                # Create a mini executor for this step
                # We'll execute the steps directly
                step_result = self._execute_nested_step(step_dict, i)
                iteration_results.append(step_result)

                # Stop if step failed
                if step_result.status == 'failure':
                    break

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Count results
        success_count = sum(1 for r in iteration_results if r.status == 'success')
        failure_count = sum(1 for r in iteration_results if r.status == 'failure')

        return {
            'response': {
                'loop_type': 'for',
                'loop_count': loop_count,
                'loop_variable': loop_variable,
                'iterations': success_count + failure_count,
                'success_count': success_count,
                'failure_count': failure_count,
            },
            'performance': self._create_performance_metrics(total_time=elapsed * 1000),
            'iteration_results': iteration_results,
        }

    def _execute_while_loop(
        self, rendered_step: dict[str, Any], start_time: datetime
    ) -> dict[str, Any]:
        """Execute while loop.

        Iterates while condition is true.

        Args:
            rendered_step: Rendered step with variables resolved
            start_time: Loop start time

        Returns:
            Execution result dictionary

        Raises:
            TimeoutError: If loop exceeds timeout
        """
        loop_condition = rendered_step.get('loop_condition')
        loop_variable = rendered_step.get('loop_variable', 'index')
        loop_steps = rendered_step.get('loop_steps', [])

        if not loop_condition:
            raise ValueError("While loop must specify 'loop_condition'")

        if not loop_steps:
            raise ValueError("Loop must contain 'loop_steps' to execute")

        iteration_results = []
        iteration = 0
        max_iterations = 1000  # Safety limit

        # Execute while loop
        while iteration < max_iterations:
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > self.timeout:
                raise TimeoutError(
                    f'While loop exceeded timeout of {self.timeout}s '
                    f'(iterations: {iteration})'
                )

            # Check loop condition
            try:
                rendered_condition = render_template(
                    loop_condition, self.variable_manager.get_all_variables()
                )
            except Exception as e:
                raise ValueError(f'Failed to evaluate loop condition: {e}')

            # Break if condition is false
            if not self._is_condition_true(rendered_condition):
                break

            # Set loop variable
            if loop_variable:
                self.variable_manager.set_variable(loop_variable, iteration)

            # Execute loop steps
            for step_dict in loop_steps:
                step_result = self._execute_nested_step(step_dict, iteration)
                iteration_results.append(step_result)

                # Stop if step failed
                if step_result.status == 'failure':
                    break

            iteration += 1

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Count results
        success_count = sum(1 for r in iteration_results if r.status == 'success')
        failure_count = sum(1 for r in iteration_results if r.status == 'failure')

        return {
            'response': {
                'loop_type': 'while',
                'loop_condition': loop_condition,
                'loop_variable': loop_variable,
                'iterations': iteration,
                'success_count': success_count,
                'failure_count': failure_count,
            },
            'performance': self._create_performance_metrics(total_time=elapsed * 1000),
            'iteration_results': iteration_results,
        }

    def _execute_nested_step(
        self, step_dict: dict[str, Any], iteration: int
    ) -> StepResult:
        """Execute a nested step within the loop.

        Args:
            step_dict: Step definition dictionary
            iteration: Current iteration number

        Returns:
            StepResult object
        """
        _ = iteration  # Reserved for nested-step debugging context.

        from apirun.parser.v2_yaml_parser import V2YamlParser

        # Parse step dict to TestStep
        parser = V2YamlParser()
        step = parser._parse_step(step_dict)

        # Determine executor type and execute
        if step.type == 'request':
            from apirun.executor.api_executor import APIExecutor

            executor = APIExecutor(
                self.variable_manager, step, self.timeout, self.retry_times
            )
        elif step.type == 'database':
            from apirun.executor.database_executor import DatabaseExecutor

            executor = DatabaseExecutor(
                self.variable_manager, step, self.timeout, self.retry_times
            )
        elif step.type == 'wait':
            from apirun.executor.wait_executor import WaitExecutor

            executor = WaitExecutor(
                self.variable_manager, step, self.timeout, self.retry_times
            )
        else:
            # Unknown step type
            result = StepResult(
                name=step.name,
                status='failure',
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            from apirun.core.models import ErrorCategory, ErrorInfo

            result.error_info = ErrorInfo(
                type='ValueError',
                category=ErrorCategory.SYSTEM,
                message=f'Unknown step type: {step.type}',
                suggestion='Check step type configuration',
            )
            return result

        # Execute the step
        return executor.execute()

    def _is_condition_true(self, rendered_condition: str) -> bool:
        """Check if rendered condition evaluates to true.

        Args:
            rendered_condition: Rendered condition string

        Returns:
            True if condition is true, False otherwise
        """
        if not rendered_condition:
            return False

        condition_lower = rendered_condition.lower().strip()
        true_values = ['true', '1', 'yes', 'y', 'ok', 'success']
        return condition_lower in true_values

    def _render_step(self) -> dict[str, Any]:
        """Render variables in loop step definition.

        Returns:
            Rendered step dictionary
        """
        context = self.variable_manager.get_all_variables()

        rendered = {
            'name': self.step.name,
            'type': self.step.type,
        }

        # Render loop_type
        if self.step.loop_type:
            rendered['loop_type'] = self.step.loop_type

        # Render loop_count
        if self.step.loop_count is not None:
            rendered['loop_count'] = render_template(str(self.step.loop_count), context)

        # Render loop_condition
        if self.step.loop_condition:
            rendered['loop_condition'] = render_template(
                self.step.loop_condition, context
            )

        # Render loop_variable
        if self.step.loop_variable:
            rendered['loop_variable'] = self.step.loop_variable

        # loop_steps don't need rendering here
        rendered['loop_steps'] = self.step.loop_steps

        return rendered
