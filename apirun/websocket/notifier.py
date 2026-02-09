"""WebSocket Notifier for Real-time Push.

This module implements the notifier that bridges test execution and WebSocket broadcasts.
Following Google Python Style Guide.
"""

import logging

from apirun.core.models import StepResult, TestCase
from apirun.websocket.broadcaster import EventBroadcaster
from apirun.websocket.progress import ProgressTracker

logger = logging.getLogger(__name__)


class WebSocketNotifier:
    """WebSocket notifier for real-time test execution updates.

    This notifier:
    - Bridges test execution events and WebSocket broadcasts
    - Provides high-level methods for common test events
    - Manages progress tracking
    - Formats and sends events through EventBroadcaster

    Attributes:
        broadcaster: Event broadcaster for sending events
        progress_tracker: Progress tracker for progress updates
        test_case_id: Test case identifier
        enabled: Whether notifications are enabled
    """

    def __init__(
        self,
        broadcaster: EventBroadcaster,
        test_case_id: str | None = None,
        enable_progress: bool = True,
        enable_logs: bool = True,
        enable_variables: bool = False,
    ):
        """Initialize WebSocket notifier.

        Args:
            broadcaster: Event broadcaster for sending events
            test_case_id: Test case identifier
            enable_progress: Whether to enable progress tracking
            enable_logs: Whether to enable log broadcasting
            enable_variables: Whether to enable variable update broadcasting
        """
        self.broadcaster = broadcaster
        self.test_case_id = test_case_id
        self.enable_progress = enable_progress
        self.enable_logs = enable_logs
        self.enable_variables = enable_variables

        # Initialize progress tracker
        self.progress_tracker: ProgressTracker | None = None
        if enable_progress:
            self.progress_tracker = ProgressTracker(broadcaster, test_case_id)

    async def notify_test_start(self, test_case: TestCase):
        """Notify that a test case has started.

        Args:
            test_case: Test case that started
        """
        await self.broadcaster.broadcast_test_start(
            test_name=test_case.name,
            total_steps=len(test_case.steps),
            description=test_case.description,
            test_case_id=self.test_case_id,
        )

        # Start progress tracking
        if self.progress_tracker:
            await self.progress_tracker.start_test(len(test_case.steps))

    async def notify_test_complete(
        self,
        test_case: TestCase,
        status: str,
        total_steps: int,
        passed_steps: int,
        failed_steps: int,
        skipped_steps: int,
        duration: float,
    ):
        """Notify that a test case has completed.

        Args:
            test_case: Test case that completed
            status: Final test status
            total_steps: Total number of steps
            passed_steps: Number of passed steps
            failed_steps: Number of failed steps
            skipped_steps: Number of skipped steps
            duration: Total duration in seconds
        """
        await self.broadcaster.broadcast_test_complete(
            test_name=test_case.name,
            status=status,
            total_steps=total_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            duration=duration,
            test_case_id=self.test_case_id,
        )

    async def notify_step_start(
        self, step_name: str, step_type: str, step_index: int, total_steps: int
    ):
        """Notify that a step has started.

        Args:
            step_name: Step name
            step_type: Step type
            step_index: Step index (0-based)
            total_steps: Total number of steps
        """
        await self.broadcaster.broadcast_step_start(
            step_name=step_name,
            step_type=step_type,
            step_index=step_index,
            total_steps=total_steps,
            test_case_id=self.test_case_id,
        )

        # Update progress
        if self.progress_tracker:
            await self.progress_tracker.update_step_start(step_index)

    async def notify_step_complete(self, step_index: int, step_result: StepResult):
        """Notify that a step has completed.

        Args:
            step_index: Step index (0-based)
            step_result: Step execution result
        """
        # Calculate duration
        duration = 0.0
        if step_result.start_time and step_result.end_time:
            duration = (step_result.end_time - step_result.start_time).total_seconds()

        await self.broadcaster.broadcast_step_complete(
            step_name=step_result.name,
            status=step_result.status,
            duration=duration,
            retry_count=step_result.retry_count,
            has_error=step_result.error_info is not None,
            test_case_id=self.test_case_id,
        )

        # Update progress
        if self.progress_tracker:
            await self.progress_tracker.update_step_complete(step_index, step_result)

        # Log if there's an error
        if step_result.error_info and self.enable_logs:
            await self.notify_error(
                error_type=step_result.error_info.type,
                error_category=step_result.error_info.category.value,
                message=step_result.error_info.message,
                suggestion=step_result.error_info.suggestion,
                step_name=step_result.name,
            )

    async def notify_log(self, level: str, message: str, context: dict = None):
        """Notify a log message.

        Args:
            level: Log level (debug/info/warning/error/critical)
            message: Log message
            context: Additional context information
        """
        if not self.enable_logs:
            return

        await self.broadcaster.broadcast_log(
            level=level,
            message=message,
            context=context or {},
            test_case_id=self.test_case_id,
        )

    async def notify_error(
        self,
        error_type: str,
        error_category: str,
        message: str,
        suggestion: str = '',
        step_name: str | None = None,
    ):
        """Notify an error.

        Args:
            error_type: Error type
            error_category: Error category
            message: Error message
            suggestion: Suggested fix
            step_name: Step name where error occurred
        """
        await self.broadcaster.broadcast_error(
            error_type=error_type,
            error_category=error_category,
            message=message,
            suggestion=suggestion,
            step_name=step_name,
            test_case_id=self.test_case_id,
        )

    async def notify_variable_update(
        self, variable_name: str, variable_value, source: str = 'extracted'
    ):
        """Notify a variable update.

        Args:
            variable_name: Variable name
            variable_value: Variable value
            source: Variable source (extracted/profile/global)
        """
        if not self.enable_variables:
            return

        await self.broadcaster.broadcast_variable_update(
            variable_name=variable_name,
            variable_value=variable_value,
            source=source,
            test_case_id=self.test_case_id,
        )

    def get_progress_summary(self) -> dict | None:
        """Get current progress summary.

        Returns:
            Progress summary dictionary, or None if progress tracking is disabled
        """
        if self.progress_tracker:
            return self.progress_tracker.get_progress_summary()
        return None
