"""Retry Strategy and Management for Sisyphus API Engine.

This module implements enhanced retry mechanism with:
- Multiple retry strategies (fixed, exponential, linear, custom)
- Retry history tracking
- Smart retry condition judgment
- Configurable backoff algorithms

Following Google Python Style Guide.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RetryStrategy(Enum):
    """Retry strategy types."""

    FIXED = 'fixed'  # Fixed delay between retries
    EXPONENTIAL = 'exponential'  # Exponential backoff (2^attempt)
    LINEAR = 'linear'  # Linear increase (attempt * base_delay)
    CUSTOM = 'custom'  # Custom delay function


@dataclass
class RetryAttempt:
    """Single retry attempt record.

    Attributes:
        attempt_number: Attempt number (0-based)
        timestamp: When the attempt was made
        success: Whether the attempt succeeded
        error_type: Type of error if failed
        error_message: Error message if failed
        delay_before: Delay before this attempt in seconds
        duration: Duration of this attempt in seconds
    """

    attempt_number: int
    timestamp: datetime
    success: bool
    error_type: str | None = None
    error_message: str | None = None
    delay_before: float = 0.0
    duration: float = 0.0


@dataclass
class RetryPolicy:
    """Retry policy configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts (excluding initial attempt)
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds (for exponential/linear)
        backoff_multiplier: Multiplier for exponential backoff (default: 2)
        jitter: Whether to add random jitter to delay
        retry_on: List of error types to retry on (empty = all errors)
        stop_on: List of error types to stop retrying on (empty = none)
        custom_delay_func: Custom delay function for CUSTOM strategy
    """

    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = False
    retry_on: list[str] = field(default_factory=list)
    stop_on: list[str] = field(default_factory=list)
    custom_delay_func: Callable[[int], float] | None = None


class RetryManager:
    """Manages retry logic with history tracking.

    This manager:
    - Calculates retry delays based on strategy
    - Tracks retry history
    - Determines if an error is retryable
    - Supports custom retry conditions

    Attributes:
        policy: Retry policy configuration
        attempts: List of retry attempts
    """

    def __init__(self, policy: RetryPolicy | None = None):
        """Initialize RetryManager.

        Args:
            policy: Retry policy configuration
        """
        self.policy = policy or RetryPolicy()
        self.attempts: list[RetryAttempt] = []

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if should retry based on error and attempt count.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)

        Returns:
            True if should retry, False otherwise
        """
        # Check if max attempts reached
        if attempt >= self.policy.max_attempts:
            return False

        # Get error type name
        error_type = type(error).__name__

        # Check stop_on list first
        if self.policy.stop_on and error_type in self.policy.stop_on:
            return False

        # Check retry_on list
        if self.policy.retry_on and error_type not in self.policy.retry_on:
            return False

        # Default: retry all errors
        return True

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        if self.policy.strategy == RetryStrategy.FIXED:
            delay = self.policy.base_delay

        elif self.policy.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.policy.base_delay * (self.policy.backoff_multiplier**attempt)

        elif self.policy.strategy == RetryStrategy.LINEAR:
            delay = self.policy.base_delay * (attempt + 1)

        elif self.policy.strategy == RetryStrategy.CUSTOM:
            if self.policy.custom_delay_func:
                delay = self.policy.custom_delay_func(attempt)
            else:
                delay = self.policy.base_delay
        else:
            # Default to fixed delay
            delay = self.policy.base_delay

        # Apply max_delay cap
        delay = min(delay, self.policy.max_delay)

        # Add jitter if enabled
        if self.policy.jitter:
            import random

            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        # Ensure non-negative
        return max(0.0, delay)

    def record_attempt(
        self,
        attempt_number: int,
        success: bool,
        error: Exception | None = None,
        delay_before: float = 0.0,
        duration: float = 0.0,
    ) -> None:
        """Record a retry attempt.

        Args:
            attempt_number: Attempt number (0-based)
            success: Whether the attempt succeeded
            error: Exception if failed
            delay_before: Delay before this attempt in seconds
            duration: Duration of this attempt in seconds
        """
        attempt = RetryAttempt(
            attempt_number=attempt_number,
            timestamp=datetime.now(),
            success=success,
            error_type=type(error).__name__ if error else None,
            error_message=str(error) if error else None,
            delay_before=delay_before,
            duration=duration,
        )
        self.attempts.append(attempt)

    def get_retry_summary(self) -> dict[str, Any]:
        """Get summary of retry attempts.

        Returns:
            Dictionary with retry statistics
        """
        if not self.attempts:
            return {
                'total_attempts': 0,
                'successful_attempts': 0,
                'failed_attempts': 0,
                'total_delay': 0.0,
                'total_duration': 0.0,
            }

        successful = sum(1 for a in self.attempts if a.success)
        failed = len(self.attempts) - successful
        total_delay = sum(a.delay_before for a in self.attempts)
        total_duration = sum(a.duration for a in self.attempts)

        return {
            'total_attempts': len(self.attempts),
            'successful_attempts': successful,
            'failed_attempts': failed,
            'total_delay': round(total_delay, 3),
            'total_duration': round(total_duration, 3),
            'last_attempt': self.attempts[-1].attempt_number,
        }

    def get_retry_history(self) -> list[dict[str, Any]]:
        """Get detailed retry history.

        Returns:
            List of attempt details
        """
        history = []
        for attempt in self.attempts:
            history.append({
                'attempt_number': attempt.attempt_number,
                'timestamp': attempt.timestamp.isoformat(),
                'success': attempt.success,
                'error_type': attempt.error_type,
                'error_message': attempt.error_message,
                'delay_before': round(attempt.delay_before, 3),
                'duration': round(attempt.duration, 3),
            })
        return history


def create_retry_policy_from_config(config: dict[str, Any]) -> RetryPolicy:
    """Create RetryPolicy from configuration dictionary.

    Args:
        config: Configuration dictionary with keys:
            - max_attempts: int
            - strategy: str (fixed/exponential/linear/custom)
            - base_delay: float
            - max_delay: float
            - backoff_multiplier: float
            - jitter: bool
            - retry_on: List[str]
            - stop_on: List[str]

    Returns:
        RetryPolicy object

    Raises:
        ValueError: If configuration is invalid
    """
    strategy_str = config.get('strategy', 'exponential')

    try:
        strategy = RetryStrategy(strategy_str)
    except ValueError:
        raise ValueError(
            f'Invalid retry strategy: {strategy_str}. '
            f'Must be one of: {[s.value for s in RetryStrategy]}'
        )

    return RetryPolicy(
        max_attempts=config.get('max_attempts', 3),
        strategy=strategy,
        base_delay=config.get('base_delay', 1.0),
        max_delay=config.get('max_delay', 60.0),
        backoff_multiplier=config.get('backoff_multiplier', 2.0),
        jitter=config.get('jitter', False),
        retry_on=config.get('retry_on', []),
        stop_on=config.get('stop_on', []),
    )
