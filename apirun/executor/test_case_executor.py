"""Test Case Executor for Sisyphus API Engine.

This module implements the main test case execution scheduler.
Following Google Python Style Guide.
"""

import asyncio
from typing import Any, Optional

from apirun.core.models import TestCase, TestStep
from apirun.core.variable_manager import VariableManager
from apirun.executor.api_executor import APIExecutor
from apirun.executor.concurrent_executor import ConcurrentExecutor
from apirun.executor.database_executor import DatabaseExecutor
from apirun.executor.loop_executor import LoopExecutor
from apirun.executor.poll_executor import PollStepExecutor
from apirun.executor.script_executor import ScriptExecutor
from apirun.executor.wait_executor import WaitExecutor
from apirun.result.json_exporter import JSONExporter
from apirun.utils.logger import get_logger


class TestCaseExecutor:
    """Executor for test cases.

    This executor:
    - Initializes variable manager
    - Sets up environment profiles
    - Schedules and executes steps
    - Collects results
    - Handles errors
    - Supports optional WebSocket real-time notifications

    Attributes:
        test_case: Test case to execute
        variable_manager: Variable manager instance
        result_collector: JSON result exporter instance
        notifier: Optional WebSocket notifier for real-time updates
    """

    def __init__(
        self, test_case: TestCase, notifier: Optional['WebSocketNotifier'] = None
    ):
        """Initialize TestCaseExecutor.

        Args:
            test_case: Test case to execute
            notifier: Optional WebSocket notifier for real-time updates
        """
        self.test_case = test_case
        self.variable_manager = VariableManager()
        self.result_collector = JSONExporter()
        self.notifier = notifier
        self.logger = get_logger()

    def execute(self) -> dict:
        """Execute the test case.

        Returns:
            v2.0 compliant JSON result dictionary
        """
        from datetime import datetime

        start_time = datetime.now()

        # Notify test start
        if self.notifier:
            self._run_async(self.notifier.notify_test_start(self.test_case))

        # Initialize global variables
        self._initialize_variables()

        # Set up profile
        self._setup_profile()

        # Execute global setup
        self._execute_global_setup()

        # Execute steps
        step_results = []
        for i, step in enumerate(self.test_case.steps):
            # Notify step start
            if self.notifier:
                self._run_async(
                    self.notifier.notify_step_start(
                        step_name=step.name,
                        step_type=step.type,
                        step_index=i,
                        total_steps=len(self.test_case.steps),
                    )
                )

            # Pass previous step results for dependency checking
            step_result = self._execute_step(step, step_results)
            step_results.append(step_result)

            # Notify step complete
            if self.notifier:
                self._run_async(self.notifier.notify_step_complete(i, step_result))

            # Stop on failure (or continue based on config)
            if step_result.status == 'failure':
                # TODO: Add configuration to control failure behavior
                # For now, continue execution
                pass

        # Execute global teardown
        self._execute_global_teardown()

        # Collect results
        result = self.result_collector.collect(
            self.test_case, step_results, self.variable_manager
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Notify test complete
        if self.notifier:
            self._run_async(
                self.notifier.notify_test_complete(
                    test_case=self.test_case,
                    status=result.status,
                    total_steps=result.total_steps,
                    passed_steps=result.passed_steps,
                    failed_steps=result.failed_steps,
                    skipped_steps=result.skipped_steps,
                    duration=duration,
                )
            )

        return self.result_collector.to_v2_json(result)

    def _run_async(self, coro):
        """Run an async coroutine in the sync context.

        Args:
            coro: Coroutine to run
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create task
                asyncio.create_task(coro)
            else:
                # If loop is not running, run the coroutine
                loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create a new one and run
            asyncio.run(coro)

    def _initialize_variables(self) -> None:
        """Initialize global variables from config."""
        # Add config as a special variable
        if self.test_case.config:
            # Build nested profiles structure for template rendering
            nested_profiles = self._build_nested_profiles_for_rendering()

            self.variable_manager.global_vars = {
                'config': {
                    'name': self.test_case.config.name,
                    'active_profile': self.test_case.config.active_profile,
                    'profiles': nested_profiles,
                    'variables': self.test_case.config.variables or {},
                    'timeout': self.test_case.config.timeout,
                    'retry_times': self.test_case.config.retry_times,
                }
            }

            # Add other global variables
            if self.test_case.config.variables:
                self.variable_manager.global_vars.update(
                    self.test_case.config.variables
                )

    def _build_nested_profiles_for_rendering(self) -> dict[str, Any]:
        """Build nested profiles structure for template rendering.

        Convert flattened profile keys (v1.dev, v2.prod) into nested structure
        that allows template access like ${config.profiles.v2.dev.base_url}.

        Returns:
            Nested profiles dictionary
        """
        if not self.test_case.config.profiles:
            return {}

        nested = {}

        for profile_key, profile in self.test_case.config.profiles.items():
            # Create nested dict path from flattened key
            parts = profile_key.split('.')
            current = nested

            # Navigate/create nested structure
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                # If current[part] is not a dict (edge case), skip
                if not isinstance(current.get(part), dict):
                    current[part] = {}
                current = current[part]

            # Set the leaf profile
            leaf_key = parts[-1]
            current[leaf_key] = {
                'base_url': profile.base_url,
                'variables': profile.variables,
                'timeout': profile.timeout,
                'verify_ssl': profile.verify_ssl,
                'overrides': profile.overrides,
                'priority': profile.priority,
            }

        return nested

        # Apply debug configuration
        if self.test_case.config and self.test_case.config.debug:
            debug_config = self.test_case.config.debug
            if debug_config.get('enabled', False):
                self.variable_manager.enable_tracking = True

        # Apply environment variables configuration
        if self.test_case.config and self.test_case.config.env_vars:
            env_config = self.test_case.config.env_vars
            prefix = env_config.get('prefix')
            if prefix:
                self.variable_manager.env_vars_prefix = prefix

            # Load from OS if enabled
            if env_config.get('load_from_os', False):
                self.variable_manager.load_environment_variables(
                    prefix=prefix, override=False
                )

            # Apply environment variable overrides
            overrides = env_config.get('overrides', {})
            if overrides:
                for key, value in overrides.items():
                    self.variable_manager.set_profile_override(key, value)

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
            # Prepare profile variables dict
            profile_vars = profile.variables.copy() if profile.variables else {}

            # Add base_url as a top-level variable
            if profile.base_url:
                profile_vars['base_url'] = profile.base_url

            # Set profile variables
            self.variable_manager.set_profile(profile_vars)

            # Apply profile overrides
            if profile.overrides:
                for key, value in profile.overrides.items():
                    self.variable_manager.set_profile_override(key, value)

    def _execute_global_setup(self) -> None:
        """Execute global setup hooks."""
        if not self.test_case.setup:
            return

        # Execute setup steps
        setup_data = self.test_case.setup
        if isinstance(setup_data, dict):
            # Single setup step
            setup_steps = [setup_data]
        elif isinstance(setup_data, list):
            # Multiple setup steps
            setup_steps = setup_data
        else:
            self.logger.warning(f'Invalid setup format: {type(setup_data)}')
            return

        # Convert dict to TestStep objects
        for step_data in setup_steps:
            if not isinstance(step_data, dict):
                self.logger.warning(f'Skipping invalid setup step: {type(step_data)}')
                continue

            step = TestStep(**step_data)
            try:
                self._execute_step(step)
                self.logger.debug(f'Setup step completed: {step.name}')
            except Exception as e:
                self.logger.error(f'Setup step failed: {step.name} - {e}')
                raise  # Setup failure should stop test execution

    def _execute_global_teardown(self) -> None:
        """Execute global teardown hooks."""
        if not self.test_case.teardown:
            return

        # Execute teardown steps
        teardown_data = self.test_case.teardown
        if isinstance(teardown_data, dict):
            # Single teardown step
            teardown_steps = [teardown_data]
        elif isinstance(teardown_data, list):
            # Multiple teardown steps
            teardown_steps = teardown_data
        else:
            self.logger.warning(f'Invalid teardown format: {type(teardown_data)}')
            return

        # Convert dict to TestStep objects
        for step_data in teardown_steps:
            if not isinstance(step_data, dict):
                self.logger.warning(
                    f'Skipping invalid teardown step: {type(step_data)}'
                )
                continue

            step = TestStep(**step_data)
            try:
                self._execute_step(step)
                self.logger.debug(f'Teardown step completed: {step.name}')
            except Exception as e:
                # Teardown failures should be logged but not raise
                self.logger.error(f'Teardown step failed: {step.name} - {e}')
                # Continue with remaining teardown steps

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
        if step.type == 'request':
            executor = APIExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'database':
            executor = DatabaseExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'wait':
            executor = WaitExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'loop':
            executor = LoopExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'concurrent':
            executor = ConcurrentExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'script':
            executor = ScriptExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        elif step.type == 'poll':
            executor = PollStepExecutor(
                self.variable_manager, step, timeout, retry_times, previous_results
            )
        else:
            raise ValueError(f'Unsupported step type: {step.type}')

        return executor.execute()
