"""Test Case Executor for Sisyphus API Engine.

This module implements the main test case execution scheduler.
Following Google Python Style Guide.
"""

from typing import Optional

from apirun.core.models import TestCase, TestStep, GlobalConfig, ProfileConfig
from apirun.core.variable_manager import VariableManager
from apirun.executor.api_executor import APIExecutor
from apirun.executor.database_executor import DatabaseExecutor
from apirun.executor.wait_executor import WaitExecutor
from apirun.executor.loop_executor import LoopExecutor
from apirun.result.collector import ResultCollector


class TestCaseExecutor:
    """Executor for test cases.

    This executor:
    - Initializes variable manager
    - Sets up environment profiles
    - Schedules and executes steps
    - Collects results
    - Handles errors

    Attributes:
        test_case: Test case to execute
        variable_manager: Variable manager instance
        result_collector: Result collector instance
    """

    def __init__(self, test_case: TestCase):
        """Initialize TestCaseExecutor.

        Args:
            test_case: Test case to execute
        """
        self.test_case = test_case
        self.variable_manager = VariableManager()
        self.result_collector = ResultCollector()

    def execute(self) -> dict:
        """Execute the test case.

        Returns:
            v2.0 compliant JSON result dictionary
        """
        # Initialize global variables
        self._initialize_variables()

        # Set up profile
        self._setup_profile()

        # Execute global setup
        self._execute_global_setup()

        # Execute steps
        step_results = []
        for i, step in enumerate(self.test_case.steps):
            # Pass previous step results for dependency checking
            step_result = self._execute_step(step, step_results)
            step_results.append(step_result)

            # Stop on failure (or continue based on config)
            if step_result.status == "failure":
                # TODO: Add configuration to control failure behavior
                # For now, continue execution
                pass

        # Execute global teardown
        self._execute_global_teardown()

        # Collect results
        result = self.result_collector.collect(self.test_case, step_results)

        return self.result_collector.to_v2_json(result)

    def _initialize_variables(self) -> None:
        """Initialize global variables from config."""
        # Add config as a special variable
        if self.test_case.config:
            self.variable_manager.global_vars = {
                "config": {
                    "name": self.test_case.config.name,
                    "active_profile": self.test_case.config.active_profile,
                    "profiles": {},
                    "variables": self.test_case.config.variables or {},
                    "timeout": self.test_case.config.timeout,
                    "retry_times": self.test_case.config.retry_times,
                }
            }

            # Add profiles
            if self.test_case.config.profiles:
                for name, profile in self.test_case.config.profiles.items():
                    self.variable_manager.global_vars["config"]["profiles"][name] = {
                        "base_url": profile.base_url,
                        "variables": profile.variables,
                        "timeout": profile.timeout,
                        "verify_ssl": profile.verify_ssl,
                    }

            # Add other global variables
            if self.test_case.config.variables:
                self.variable_manager.global_vars.update(
                    self.test_case.config.variables
                )

    def _setup_profile(self) -> None:
        """Set up active profile variables."""
        if (
            not self.test_case.config
            or not self.test_case.config.active_profile
            or not self.test_case.config.profiles
        ):
            return

        profile_name = self.test_case.config.active_profile
        profile = self.test_case.config.profiles.get(profile_name)

        if profile:
            self.variable_manager.set_profile(profile.variables)

    def _execute_global_setup(self) -> None:
        """Execute global setup hooks."""
        if not self.test_case.setup:
            return

        # TODO: Implement hook execution
        pass

    def _execute_global_teardown(self) -> None:
        """Execute global teardown hooks."""
        if not self.test_case.teardown:
            return

        # TODO: Implement hook execution
        pass

    def _execute_step(self, step: TestStep, previous_results=None):
        """Execute a single test step.

        Args:
            step: Test step to execute
            previous_results: List of previous step results for dependency checking

        Returns:
            StepResult object

        Raises:
            ValueError: If step type is not supported
        """
        # Get timeout and retry from config
        timeout = 30
        retry_times = 0

        if self.test_case.config:
            timeout = self.test_case.config.timeout
            retry_times = self.test_case.config.retry_times

        # Create executor based on step type
        if step.type == "request":
            executor = APIExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == "database":
            executor = DatabaseExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == "wait":
            executor = WaitExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == "loop":
            executor = LoopExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        else:
            raise ValueError(f"Unsupported step type: {step.type}")

        return executor.execute()
