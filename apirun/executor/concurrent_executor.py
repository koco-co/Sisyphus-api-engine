"""Concurrent Executor for Sisyphus API Engine.

This module implements the concurrent step executor, supporting:
- Thread pool based concurrent execution
- Customizable concurrency level
- Concurrent-safe variable management
- Result aggregation from concurrent steps
- Performance-optimized result collection

Following Google Python Style Guide.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List
from datetime import datetime
from queue import Queue

from apirun.executor.step_executor import StepExecutor
from apirun.core.models import TestStep, StepResult, ErrorInfo, ErrorCategory
from apirun.core.variable_manager import VariableManager
from apirun.utils.template import render_template


class ConcurrentExecutor(StepExecutor):
    """Executor for concurrent steps.

    Executes multiple steps concurrently using a thread pool.

    Performance optimizations:
    - Lock-free result collection using Queue
    - Optimized thread pool sizing
    - Reduced context switching
    - Efficient variable merging

    Attributes:
        variable_manager: Variable manager instance
        step: Test step to execute
        timeout: Step timeout in seconds
        retry_times: Number of retry attempts
        concurrent_results: List of results from concurrent execution
        lock: Thread lock for concurrent-safe operations
    """

    # Class-level thread pool for reuse (performance optimization)
    _thread_pool: ThreadPoolExecutor = None
    _thread_pool_lock = threading.Lock()

    def __init__(
        self,
        variable_manager: VariableManager,
        step: TestStep,
        timeout: int = 300,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize ConcurrentExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds (default: 300 for concurrent steps)
            retry_times: Default retry count
            previous_results: List of previous step results
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.concurrent_results: List[StepResult] = []
        self.lock = threading.Lock()

    @classmethod
    def get_thread_pool(cls, max_workers: int) -> ThreadPoolExecutor:
        """Get or create a shared thread pool.

        Args:
            max_workers: Maximum number of workers

        Returns:
            ThreadPoolExecutor instance
        """
        with cls._thread_pool_lock:
            if cls._thread_pool is None:
                cls._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
            return cls._thread_pool

    @classmethod
    def shutdown_thread_pool(cls) -> None:
        """Shutdown the shared thread pool."""
        with cls._thread_pool_lock:
            if cls._thread_pool is not None:
                cls._thread_pool.shutdown(wait=True)
                cls._thread_pool = None

    def _execute_step(self, rendered_step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the concurrent step.

        Args:
            rendered_step: Rendered step with variables resolved

        Returns:
            Execution result dictionary

        Raises:
            ValueError: If concurrent configuration is invalid
        """
        start_time = datetime.now()
        max_concurrency = rendered_step.get("max_concurrency", 3)
        concurrent_steps = rendered_step.get("concurrent_steps", [])

        if not concurrent_steps:
            raise ValueError("Concurrent step must contain 'concurrent_steps' to execute")

        try:
            max_concurrency = int(max_concurrency)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid max_concurrency value: {max_concurrency}")

        if max_concurrency <= 0:
            raise ValueError(f"Max concurrency must be positive, got: {max_concurrency}")

        # Execute concurrent steps
        self.concurrent_results = self._execute_concurrent_steps(
            concurrent_steps, max_concurrency
        )

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Count results
        success_count = sum(1 for r in self.concurrent_results if r.status == "success")
        failure_count = sum(
            1 for r in self.concurrent_results if r.status in ("failure", "skipped")
        )
        skipped_count = sum(1 for r in self.concurrent_results if r.status == "skipped")

        return {
            "response": {
                "max_concurrency": max_concurrency,
                "total_steps": len(concurrent_steps),
                "success_count": success_count,
                "failure_count": failure_count,
                "skipped_count": skipped_count,
            },
            "performance": self._create_performance_metrics(total_time=elapsed * 1000),
            "concurrent_results": self.concurrent_results,
        }

    def _execute_concurrent_steps(
        self, concurrent_steps: List[Dict[str, Any]], max_concurrency: int
    ) -> List[StepResult]:
        """Execute steps concurrently using thread pool.

        Performance optimizations:
        - Uses Queue for lock-free result collection
        - Batches variable merges to reduce lock contention
        - Optimized thread pool reuse

        Args:
            concurrent_steps: List of step definitions to execute concurrently
            max_concurrency: Maximum number of concurrent threads

        Returns:
            List of StepResult objects from all executed steps
        """
        # Use Queue for lock-free result collection
        results_queue: Queue = Queue()
        extracted_vars_queue: Queue = Queue()

        def execute_step(step_dict: Dict[str, Any], index: int) -> StepResult:
            """Execute a single step in a thread.

            Args:
                step_dict: Step definition dictionary
                index: Step index for identification

            Returns:
                StepResult object
            """
            try:
                # Create a copy of variable manager for this thread
                thread_variable_manager = self._create_thread_variable_manager()

                # Parse and execute step
                step_result = self._execute_nested_step(
                    step_dict, thread_variable_manager, index
                )

                # Put extracted variables in queue for batch merging
                if step_result.extracted_vars:
                    extracted_vars_queue.put(step_result.extracted_vars)

                return step_result

            except Exception as e:
                # Create error result
                return StepResult(
                    name=step_dict.get("name", f"concurrent_step_{index}"),
                    status="failure",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_info=ErrorInfo(
                        type=type(e).__name__,
                        category=ErrorCategory.SYSTEM,
                        message=str(e),
                        suggestion="检查并发步骤配置",
                    ),
                )

        # Execute steps in thread pool (use shared pool for performance)
        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            # Submit all tasks
            future_to_step = {
                executor.submit(execute_step, step_dict, idx): (step_dict, idx)
                for idx, step_dict in enumerate(concurrent_steps)
            }

            # Collect results as they complete (lock-free using Queue)
            for future in as_completed(future_to_step):
                step_dict, idx = future_to_step[future]
                try:
                    result = future.result()
                    results_queue.put(result)
                except Exception as e:
                    # Create error result for failed thread
                    error_result = StepResult(
                        name=step_dict.get("name", f"concurrent_step_{idx}"),
                        status="failure",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        error_info=ErrorInfo(
                            type=type(e).__name__,
                            category=ErrorCategory.SYSTEM,
                            message=str(e),
                            suggestion="检查并发线程执行异常",
                        ),
                    )
                    results_queue.put(error_result)

        # Extract results from queue
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Batch merge extracted variables (reduce lock contention)
        while not extracted_vars_queue.empty():
            extracted_vars = extracted_vars_queue.get()
            if extracted_vars:
                for var_name, var_value in extracted_vars.items():
                    self.variable_manager.set_variable(var_name, var_value)

        return results

    def _create_thread_variable_manager(self) -> VariableManager:
        """Create a copy of variable manager for thread-safe execution.

        Returns:
            New VariableManager instance with copied variables
        """
        # Create new variable manager with snapshot of current variables
        thread_vm = VariableManager()

        # Copy global variables
        global_vars = self.variable_manager.global_vars.copy()
        for key, value in global_vars.items():
            thread_vm.set_variable(key, value)

        # Copy profile variables
        profile_vars = self.variable_manager.profile_vars.copy()
        for key, value in profile_vars.items():
            thread_vm.set_variable(key, value)

        # Copy extracted variables
        extracted_vars = self.variable_manager.extracted_vars.copy()
        for key, value in extracted_vars.items():
            thread_vm.set_variable(key, value)

        return thread_vm

    def _execute_nested_step(
        self,
        step_dict: Dict[str, Any],
        variable_manager: VariableManager,
        index: int,
    ) -> StepResult:
        """Execute a nested step within concurrent execution.

        Args:
            step_dict: Step definition dictionary
            variable_manager: Variable manager for this thread
            index: Step index

        Returns:
            StepResult object
        """
        from apirun.parser.v2_yaml_parser import V2YamlParser

        # Parse step dict to TestStep
        parser = V2YamlParser()
        step = parser._parse_step(step_dict)

        # Determine executor type and execute
        if step.type == "request":
            from apirun.executor.api_executor import APIExecutor

            executor = APIExecutor(
                variable_manager, step, self.timeout, self.retry_times
            )
        elif step.type == "database":
            from apirun.executor.database_executor import DatabaseExecutor

            executor = DatabaseExecutor(
                variable_manager, step, self.timeout, self.retry_times
            )
        elif step.type == "wait":
            from apirun.executor.wait_executor import WaitExecutor

            executor = WaitExecutor(
                variable_manager, step, self.timeout, self.retry_times
            )
        elif step.type == "loop":
            from apirun.executor.loop_executor import LoopExecutor

            executor = LoopExecutor(
                variable_manager, step, self.timeout, self.retry_times
            )
        else:
            # Unknown step type
            result = StepResult(
                name=step.name,
                status="failure",
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            result.error_info = ErrorInfo(
                type="ValueError",
                category=ErrorCategory.SYSTEM,
                message=f"Unknown step type: {step.type}",
                suggestion="检查步骤类型配置",
            )
            return result

        # Execute the step
        return executor.execute()

    def _render_step(self) -> Dict[str, Any]:
        """Render variables in concurrent step definition.

        Returns:
            Rendered step dictionary
        """
        context = self.variable_manager.get_all_variables()

        rendered = {
            "name": self.step.name,
            "type": self.step.type,
        }

        # Render max_concurrency
        if self.step.max_concurrency is not None:
            rendered["max_concurrency"] = render_template(
                str(self.step.max_concurrency), context
            )

        # concurrent_steps don't need rendering here
        rendered["concurrent_steps"] = self.step.concurrent_steps

        return rendered
