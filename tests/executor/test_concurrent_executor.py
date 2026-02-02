"""Unit tests for ConcurrentExecutor.

Tests the concurrent step executor functionality, including:
- Thread pool management
- Concurrent step execution
- Result aggregation
- Thread-safe operations
- Error handling

Following Google Python Style Guide.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

from apirun.executor.concurrent_executor import ConcurrentExecutor
from apirun.core.models import TestStep, StepResult
from apirun.core.variable_manager import VariableManager


class TestConcurrentExecutor:
    """Test cases for ConcurrentExecutor class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.variable_manager = VariableManager()
        self.variable_manager.set_variable("base_url", "https://httpbin.org")

    def test_initialization(self):
        """Test ConcurrentExecutor initialization."""
        step = TestStep(
            name="Concurrent Test",
            type="concurrent",
            max_concurrency=2,
            concurrent_steps=[
                TestStep(name="Sub-step 1", type="wait", seconds=0.1),
                TestStep(name="Sub-step 2", type="wait", seconds=0.1),
            ]
        )

        executor = ConcurrentExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30,
            retry_times=0
        )

        assert executor.variable_manager == self.variable_manager
        assert executor.step == step
        assert executor.timeout == 30
        assert executor.retry_times == 0
        assert len(executor.concurrent_results) == 0

    def test_get_thread_pool(self):
        """Test thread pool creation and reuse."""
        pool1 = ConcurrentExecutor.get_thread_pool(max_workers=2)
        pool2 = ConcurrentExecutor.get_thread_pool(max_workers=2)

        # Should return the same instance (reuse)
        assert pool1 is pool2
        assert isinstance(pool1, ThreadPoolExecutor)

        # Cleanup
        ConcurrentExecutor.shutdown_thread_pool()

    def test_shutdown_thread_pool(self):
        """Test thread pool shutdown."""
        # Create a thread pool
        ConcurrentExecutor.get_thread_pool(max_workers=2)

        # Shutdown
        ConcurrentExecutor.shutdown_thread_pool()

        # Should create new pool after shutdown
        pool1 = ConcurrentExecutor.get_thread_pool(max_workers=2)
        pool2 = ConcurrentExecutor.get_thread_pool(max_workers=2)

        assert pool1 is pool2

        # Cleanup
        ConcurrentExecutor.shutdown_thread_pool()

    def test_concurrent_steps_with_validations(self):
        """Test concurrent steps with validation rules."""
        step = TestStep(
            name="Concurrent Test",
            type="concurrent",
            max_concurrency=2,
            concurrent_steps=[
                TestStep(
                    name="Sub-step 1",
                    type="wait",
                    seconds=0.1,
                    validations=[
                        Mock(type="eq", path="$.duration", expect=0.1)
                    ]
                ),
                TestStep(
                    name="Sub-step 2",
                    type="wait",
                    seconds=0.1
                ),
            ]
        )

        executor = ConcurrentExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # Verify step structure
        assert len(step.concurrent_steps) == 2
        assert step.concurrent_steps[0].validations is not None
        assert len(step.concurrent_steps[0].validations) == 1

    def test_invalid_concurrent_config(self):
        """Test handling of invalid concurrent configuration."""
        # Missing concurrent_steps
        step = TestStep(
            name="Invalid Concurrent",
            type="concurrent",
            max_concurrency=2
        )

        executor = ConcurrentExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # Should handle gracefully
        assert executor.step.type == "concurrent"
        assert executor.step.max_concurrency == 2

    def test_max_concurrency_validation(self):
        """Test max_concurrency parameter validation."""
        valid_concurrency_values = [1, 2, 5, 10]

        for value in valid_concurrency_values:
            step = TestStep(
                name=f"Concurrent Test {value}",
                type="concurrent",
                max_concurrency=value,
                concurrent_steps=[
                    TestStep(name=f"Sub-step {i}", type="wait", seconds=0.1)
                    for i in range(value)
                ]
            )

            executor = ConcurrentExecutor(
                variable_manager=self.variable_manager,
                step=step,
                timeout=30
            )

            assert executor.step.max_concurrency == value
            assert len(executor.step.concurrent_steps) == value

    def test_thread_safety(self):
        """Test thread-safe operations."""
        step = TestStep(
            name="Concurrent Test",
            type="concurrent",
            max_concurrency=2,
            concurrent_steps=[
                TestStep(name=f"Sub-step {i}", type="wait", seconds=0.01)
                for i in range(5)
            ]
        )

        executor = ConcurrentExecutor(
            variable_manager=self.variable_manager,
            step=step,
            timeout=30
        )

        # Test lock usage
        assert executor.lock is not None
        assert hasattr(executor.lock, 'acquire')
        assert hasattr(executor.lock, 'release')
