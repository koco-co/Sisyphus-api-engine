"""Unit tests for Retry mechanism.

Tests retry policy configuration, retry manager functionality,
and various retry strategies.
"""

import pytest
import time
from datetime import datetime
from apirun.core.retry import (
    RetryStrategy,
    RetryPolicy,
    RetryManager,
    RetryAttempt,
    create_retry_policy_from_config,
)


class TestRetryPolicy:
    """Test RetryPolicy configuration."""

    def test_default_policy(self):
        """Test default retry policy."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.strategy == RetryStrategy.EXPONENTIAL
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.backoff_multiplier == 2.0
        assert policy.jitter is False

    def test_fixed_strategy_policy(self):
        """Test fixed delay strategy."""
        policy = RetryPolicy(
            max_attempts=5,
            strategy=RetryStrategy.FIXED,
            base_delay=2.0,
        )
        assert policy.strategy == RetryStrategy.FIXED
        assert policy.max_attempts == 5
        assert policy.base_delay == 2.0

    def test_exponential_strategy_policy(self):
        """Test exponential backoff strategy."""
        policy = RetryPolicy(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            backoff_multiplier=3.0,
            max_delay=30.0,
        )
        assert policy.strategy == RetryStrategy.EXPONENTIAL
        assert policy.backoff_multiplier == 3.0
        assert policy.max_delay == 30.0

    def test_linear_strategy_policy(self):
        """Test linear increase strategy."""
        policy = RetryPolicy(
            max_attempts=4,
            strategy=RetryStrategy.LINEAR,
            base_delay=0.5,
        )
        assert policy.strategy == RetryStrategy.LINEAR
        assert policy.base_delay == 0.5

    def test_retry_on_stop_on_filters(self):
        """Test retry_on and stop_on error type filtering."""
        policy = RetryPolicy(
            retry_on=["TimeoutError", "ConnectionError"],
            stop_on=["ValueError", "AssertionError"],
        )
        assert "TimeoutError" in policy.retry_on
        assert "ConnectionError" in policy.retry_on
        assert "ValueError" in policy.stop_on
        assert "AssertionError" in policy.stop_on


class TestRetryManager:
    """Test RetryManager functionality."""

    def test_should_retry_by_default(self):
        """Test should retry all errors by default."""
        policy = RetryPolicy(max_attempts=3)
        manager = RetryManager(policy)

        error = Exception("Test error")
        assert manager.should_retry(error, 0) is True
        assert manager.should_retry(error, 1) is True
        assert manager.should_retry(error, 2) is True  # Still within max attempts
        assert manager.should_retry(error, 3) is False  # Max attempts reached

    def test_should_retry_with_filters(self):
        """Test should retry with error type filters."""
        policy = RetryPolicy(
            max_attempts=5,
            retry_on=["TimeoutError", "ConnectionError"],
        )
        manager = RetryManager(policy)

        timeout_error = TimeoutError("Timeout")
        connection_error = ConnectionError("Connection failed")
        value_error = ValueError("Invalid value")

        assert manager.should_retry(timeout_error, 0) is True
        assert manager.should_retry(connection_error, 0) is True
        assert manager.should_retry(value_error, 0) is False  # Not in retry_on list

    def test_should_retry_stop_on(self):
        """Test should not retry with stop_on filter."""
        policy = RetryPolicy(
            max_attempts=5,
            stop_on=["AssertionError", "ValueError"],
        )
        manager = RetryManager(policy)

        assert_error = AssertionError("Assertion failed")
        assert manager.should_retry(assert_error, 0) is False

    def test_calculate_fixed_delay(self):
        """Test fixed delay calculation."""
        policy = RetryPolicy(
            strategy=RetryStrategy.FIXED,
            base_delay=2.0,
        )
        manager = RetryManager(policy)

        assert manager.calculate_delay(0) == 2.0
        assert manager.calculate_delay(1) == 2.0
        assert manager.calculate_delay(5) == 2.0

    def test_calculate_exponential_delay(self):
        """Test exponential backoff delay calculation."""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            backoff_multiplier=2.0,
        )
        manager = RetryManager(policy)

        assert manager.calculate_delay(0) == 1.0  # 1 * 2^0
        assert manager.calculate_delay(1) == 2.0  # 1 * 2^1
        assert manager.calculate_delay(2) == 4.0  # 1 * 2^2
        assert manager.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_calculate_linear_delay(self):
        """Test linear increase delay calculation."""
        policy = RetryPolicy(
            strategy=RetryStrategy.LINEAR,
            base_delay=1.0,
        )
        manager = RetryManager(policy)

        assert manager.calculate_delay(0) == 1.0  # 1 * (0 + 1)
        assert manager.calculate_delay(1) == 2.0  # 1 * (1 + 1)
        assert manager.calculate_delay(2) == 3.0  # 1 * (2 + 1)
        assert manager.calculate_delay(5) == 6.0  # 1 * (5 + 1)

    def test_max_delay_cap(self):
        """Test max_delay capping."""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=5.0,
        )
        manager = RetryManager(policy)

        assert manager.calculate_delay(0) == 1.0
        assert manager.calculate_delay(1) == 2.0
        assert manager.calculate_delay(2) == 4.0
        assert manager.calculate_delay(3) == 5.0  # Capped at max_delay
        assert manager.calculate_delay(10) == 5.0  # Still capped

    def test_record_attempt(self):
        """Test recording retry attempts."""
        manager = RetryManager()

        manager.record_attempt(
            attempt_number=0,
            success=True,
            delay_before=0.0,
            duration=1.5,
        )

        assert len(manager.attempts) == 1
        assert manager.attempts[0].attempt_number == 0
        assert manager.attempts[0].success is True
        assert manager.attempts[0].delay_before == 0.0
        assert manager.attempts[0].duration == 1.5

    def test_record_failed_attempt(self):
        """Test recording failed retry attempts."""
        manager = RetryManager()

        error = ValueError("Test error")
        manager.record_attempt(
            attempt_number=1,
            success=False,
            error=error,
            delay_before=2.0,
            duration=1.0,
        )

        assert len(manager.attempts) == 1
        assert manager.attempts[0].success is False
        assert manager.attempts[0].error_type == "ValueError"
        assert manager.attempts[0].error_message == "Test error"
        assert manager.attempts[0].delay_before == 2.0

    def test_get_retry_summary(self):
        """Test getting retry summary."""
        policy = RetryPolicy(max_attempts=3)
        manager = RetryManager(policy)

        # Record some attempts
        manager.record_attempt(0, False, error=Exception("Error1"), delay_before=0.0, duration=1.0)
        manager.record_attempt(1, False, error=Exception("Error2"), delay_before=1.0, duration=1.0)
        manager.record_attempt(2, True, delay_before=2.0, duration=1.5)

        summary = manager.get_retry_summary()
        assert summary["total_attempts"] == 3
        assert summary["successful_attempts"] == 1
        assert summary["failed_attempts"] == 2
        assert summary["total_delay"] == 3.0
        assert summary["total_duration"] == 3.5
        assert summary["last_attempt"] == 2

    def test_get_retry_summary_empty(self):
        """Test getting retry summary with no attempts."""
        manager = RetryManager()
        summary = manager.get_retry_summary()

        assert summary["total_attempts"] == 0
        assert summary["successful_attempts"] == 0
        assert summary["failed_attempts"] == 0

    def test_get_retry_history(self):
        """Test getting detailed retry history."""
        manager = RetryManager()

        manager.record_attempt(0, True, delay_before=0.0, duration=1.0)
        manager.record_attempt(1, False, error=Exception("Test"), delay_before=1.0, duration=0.5)

        history = manager.get_retry_history()
        assert len(history) == 2
        assert history[0]["attempt_number"] == 0
        assert history[0]["success"] is True
        assert history[1]["attempt_number"] == 1
        assert history[1]["success"] is False
        assert history[1]["error_type"] == "Exception"
        assert "timestamp" in history[0]
        assert "timestamp" in history[1]


class TestCreateRetryPolicyFromConfig:
    """Test creating RetryPolicy from configuration dictionary."""

    def test_create_from_valid_config(self):
        """Test creating policy from valid configuration."""
        config = {
            "max_attempts": 5,
            "strategy": "exponential",
            "base_delay": 2.0,
            "max_delay": 30.0,
            "backoff_multiplier": 3.0,
            "jitter": True,
        }
        policy = create_retry_policy_from_config(config)

        assert policy.max_attempts == 5
        assert policy.strategy == RetryStrategy.EXPONENTIAL
        assert policy.base_delay == 2.0
        assert policy.max_delay == 30.0
        assert policy.backoff_multiplier == 3.0
        assert policy.jitter is True

    def test_create_from_minimal_config(self):
        """Test creating policy from minimal configuration."""
        config = {"max_attempts": 2}
        policy = create_retry_policy_from_config(config)

        assert policy.max_attempts == 2
        assert policy.strategy == RetryStrategy.EXPONENTIAL  # Default
        assert policy.base_delay == 1.0  # Default
        assert policy.max_delay == 60.0  # Default

    def test_create_from_invalid_strategy(self):
        """Test creating policy with invalid strategy."""
        config = {"strategy": "invalid_strategy"}

        with pytest.raises(ValueError) as exc_info:
            create_retry_policy_from_config(config)

        assert "Invalid retry strategy" in str(exc_info.value)

    def test_create_with_retry_on_stop_on(self):
        """Test creating policy with retry_on and stop_on filters."""
        config = {
            "retry_on": ["TimeoutError", "ConnectionError"],
            "stop_on": ["ValueError"],
        }
        policy = create_retry_policy_from_config(config)

        assert "TimeoutError" in policy.retry_on
        assert "ConnectionError" in policy.retry_on
        assert "ValueError" in policy.stop_on


class TestRetryAttempt:
    """Test RetryAttempt dataclass."""

    def test_retry_attempt_creation(self):
        """Test creating a retry attempt record."""
        attempt = RetryAttempt(
            attempt_number=2,
            timestamp=datetime.now(),
            success=False,
            error_type="ConnectionError",
            error_message="Connection refused",
            delay_before=1.5,
            duration=0.5,
        )

        assert attempt.attempt_number == 2
        assert attempt.success is False
        assert attempt.error_type == "ConnectionError"
        assert attempt.error_message == "Connection refused"
        assert attempt.delay_before == 1.5
        assert attempt.duration == 0.5

    def test_retry_attempt_optional_fields(self):
        """Test retry attempt with optional fields."""
        attempt = RetryAttempt(
            attempt_number=0,
            timestamp=datetime.now(),
            success=True,
        )

        assert attempt.attempt_number == 0
        assert attempt.success is True
        assert attempt.error_type is None
        assert attempt.error_message is None
        assert attempt.delay_before == 0.0
        assert attempt.duration == 0.0


class TestRetryStrategiesIntegration:
    """Integration tests for retry strategies."""

    def test_exponential_backoff_sequence(self):
        """Test exponential backoff produces correct delay sequence."""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=100.0,
        )
        manager = RetryManager(policy)

        delays = [manager.calculate_delay(i) for i in range(10)]
        expected = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 100.0, 100.0, 100.0]

        assert delays == expected

    def test_linear_backoff_sequence(self):
        """Test linear backoff produces correct delay sequence."""
        policy = RetryPolicy(
            strategy=RetryStrategy.LINEAR,
            base_delay=0.5,
            max_delay=100.0,
        )
        manager = RetryManager(policy)

        delays = [manager.calculate_delay(i) for i in range(5)]
        expected = [0.5, 1.0, 1.5, 2.0, 2.5]

        assert delays == expected

    def test_fixed_delay_sequence(self):
        """Test fixed delay produces constant delay."""
        policy = RetryPolicy(
            strategy=RetryStrategy.FIXED,
            base_delay=2.5,
        )
        manager = RetryManager(policy)

        delays = [manager.calculate_delay(i) for i in range(5)]
        expected = [2.5, 2.5, 2.5, 2.5, 2.5]

        assert delays == expected
