"""Progress Tracker for WebSocket Real-time Push.

This module implements progress tracking for test execution.
Following Google Python Style Guide.
"""

from datetime import datetime
import logging

from apirun.core.models import StepResult
from apirun.websocket.broadcaster import EventBroadcaster

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Progress tracker for test execution.

    This tracker:
    - Monitors test execution progress
    - Calculates progress percentage
    - Estimates remaining time
    - Broadcasts progress updates via EventBroadcaster

    Attributes:
        broadcaster: Event broadcaster for progress updates
        test_case_id: Test case identifier
        total_steps: Total number of steps
        step_durations: List of step execution durations
        start_time: Test execution start time
        current_step: Current step index
    """

    def __init__(
        self,
        broadcaster: EventBroadcaster,
        test_case_id: str | None = None,
    ):
        """Initialize progress tracker.

        Args:
            broadcaster: Event broadcaster for progress updates
            test_case_id: Test case identifier
        """
        self.broadcaster = broadcaster
        self.test_case_id = test_case_id
        self.total_steps = 0
        self.step_durations: list[float] = []
        self.start_time: datetime | None = None
        self.current_step = 0
        self._passed_steps = 0
        self._failed_steps = 0

    async def start_test(self, total_steps: int):
        """Start tracking test execution.

        Args:
            total_steps: Total number of steps in the test
        """
        self.total_steps = total_steps
        self.start_time = datetime.now()
        self.current_step = 0
        self._passed_steps = 0
        self._failed_steps = 0
        self.step_durations = []

        # Broadcast initial progress
        await self._broadcast_progress()

    async def update_step_start(self, step_index: int):
        """Update progress when a step starts.

        Args:
            step_index: Step index (0-based)
        """
        self.current_step = step_index
        await self._broadcast_progress()

    async def update_step_complete(self, step_index: int, step_result: StepResult):
        """Update progress when a step completes.

        Args:
            step_index: Step index (0-based)
            step_result: Step execution result
        """
        self.current_step = step_index + 1

        # Record step duration
        if step_result.start_time and step_result.end_time:
            duration = (step_result.end_time - step_result.start_time).total_seconds()
            self.step_durations.append(duration)

        # Update counts
        if step_result.status == 'success':
            self._passed_steps += 1
        elif step_result.status == 'failure':
            self._failed_steps += 1

        # Broadcast updated progress
        await self._broadcast_progress()

    def _calculate_percentage(self) -> float:
        """Calculate progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.total_steps == 0:
            return 0.0

        return (self.current_step / self.total_steps) * 100

    def _estimate_remaining_time(self) -> float | None:
        """Estimate remaining execution time.

        Returns:
            Estimated remaining time in seconds, or None if cannot estimate
        """
        if not self.step_durations or self.current_step == 0:
            return None

        # Calculate average step duration
        avg_duration = sum(self.step_durations) / len(self.step_durations)

        # Estimate remaining steps
        remaining_steps = self.total_steps - self.current_step

        # Estimate remaining time
        return avg_duration * remaining_steps

    async def _broadcast_progress(self):
        """Broadcast progress update via EventBroadcaster."""
        percentage = self._calculate_percentage()
        estimated_remaining = self._estimate_remaining_time()

        await self.broadcaster.broadcast_progress(
            current_step=self.current_step,
            total_steps=self.total_steps,
            percentage=percentage,
            passed_steps=self._passed_steps,
            failed_steps=self._failed_steps,
            estimated_remaining=estimated_remaining,
            test_case_id=self.test_case_id,
        )

    def get_progress_summary(self) -> dict:
        """Get current progress summary.

        Returns:
            Dictionary containing progress information
        """
        elapsed = None
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'percentage': self._calculate_percentage(),
            'passed_steps': self._passed_steps,
            'failed_steps': self._failed_steps,
            'skipped_steps': self.current_step
            - self._passed_steps
            - self._failed_steps,
            'elapsed_time': elapsed,
            'estimated_remaining': self._estimate_remaining_time(),
            'average_step_duration': (
                sum(self.step_durations) / len(self.step_durations)
                if self.step_durations
                else None
            ),
        }
