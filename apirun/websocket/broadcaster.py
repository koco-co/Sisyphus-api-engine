"""Event Broadcaster for WebSocket Real-time Push.

This module implements event broadcasting and subscription management.
Following Google Python Style Guide.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import TYPE_CHECKING

from apirun.websocket.events import EventType, WebSocketEvent

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apirun.websocket.server import WebSocketServer


class EventBroadcaster:
    """Event broadcaster for managing event subscriptions and distribution.

    This broadcaster:
    - Manages event subscriptions
    - Filters events by type
    - Broadcasts events to subscribers
    - Supports async event handlers

    Attributes:
        subscribers: Dictionary of event type to set of subscriber callbacks
        server: WebSocket server instance for broadcasting
    """

    def __init__(self, server: WebSocketServer | None = None):
        """Initialize event broadcaster.

        Args:
            server: Optional WebSocket server for broadcasting to clients
        """
        self.subscribers: dict[EventType, set[Callable]] = {}
        self.server = server
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._broadcast_task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """Start the event broadcaster.

        This starts the background task that processes events from the queue.
        """
        if self._running:
            return

        self._running = True
        self._broadcast_task = asyncio.create_task(self._process_events())
        logger.info('Event broadcaster started')

    async def stop(self):
        """Stop the event broadcaster.

        This stops the background task.
        """
        if not self._running:
            return

        self._running = False

        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            self._broadcast_task = None

        logger.info('Event broadcaster stopped')

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[WebSocketEvent], Awaitable[None]],
    ):
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to
            callback: Async callback function to handle the event
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()

        self.subscribers[event_type].add(callback)
        logger.debug(f'Subscribed to {event_type.value}: {callback.__name__}')

    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[WebSocketEvent], Awaitable[None]],
    ):
        """Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(callback)
            logger.debug(f'Unsubscribed from {event_type.value}: {callback.__name__}')

    async def broadcast(self, event: WebSocketEvent):
        """Broadcast an event to all subscribers.

        Args:
            event: Event to broadcast
        """
        # Put event in queue for processing
        await self._event_queue.put(event)

    async def broadcast_nowait(self, event: WebSocketEvent):
        """Broadcast an event without waiting (non-blocking).

        Args:
            event: Event to broadcast
        """
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning('Event queue is full, dropping event')

    async def _process_events(self):
        """Process events from the queue (background task)."""
        while self._running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Broadcast to WebSocket server clients
                if self.server:
                    await self.server.broadcast(event)

                # Notify subscribers
                if event.type in self.subscribers:
                    subscribers = self.subscribers[event.type]
                    tasks = [
                        self._safe_call(callback, event) for callback in subscribers
                    ]
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)

            except TimeoutError:
                # Continue processing
                continue
            except asyncio.CancelledError:
                logger.info('Event processing task cancelled')
                break
            except Exception as e:
                logger.error(f'Error processing event: {e}', exc_info=True)

    async def _safe_call(
        self, callback: Callable, event: WebSocketEvent
    ) -> Exception | None:
        """Safely call a subscriber callback.

        Args:
            callback: Callback function to call
            event: Event to pass to callback

        Returns:
            Exception if one occurred, None otherwise
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(
                f'Error in subscriber callback {callback.__name__}: {e}', exc_info=True
            )
            return e
        return None

    async def broadcast_test_start(
        self,
        test_name: str,
        total_steps: int,
        description: str = '',
        test_case_id: str | None = None,
    ):
        """Broadcast a test start event.

        Args:
            test_name: Test case name
            total_steps: Total number of steps
            description: Test description
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.TEST_START,
            test_case_id=test_case_id,
            data={
                'test_name': test_name,
                'total_steps': total_steps,
                'description': description,
            },
        )
        await self.broadcast(event)

    async def broadcast_test_complete(
        self,
        test_name: str,
        status: str,
        total_steps: int,
        passed_steps: int,
        failed_steps: int,
        skipped_steps: int,
        duration: float,
        test_case_id: str | None = None,
    ):
        """Broadcast a test complete event.

        Args:
            test_name: Test case name
            status: Final test status
            total_steps: Total number of steps
            passed_steps: Number of passed steps
            failed_steps: Number of failed steps
            skipped_steps: Number of skipped steps
            duration: Total duration in seconds
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.TEST_COMPLETE,
            test_case_id=test_case_id,
            data={
                'test_name': test_name,
                'status': status,
                'total_steps': total_steps,
                'passed_steps': passed_steps,
                'failed_steps': failed_steps,
                'skipped_steps': skipped_steps,
                'duration': duration,
            },
        )
        await self.broadcast(event)

    async def broadcast_step_start(
        self,
        step_name: str,
        step_type: str,
        step_index: int,
        total_steps: int,
        test_case_id: str | None = None,
    ):
        """Broadcast a step start event.

        Args:
            step_name: Step name
            step_type: Step type
            step_index: Step index
            total_steps: Total number of steps
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.STEP_START,
            test_case_id=test_case_id,
            step_name=step_name,
            data={
                'step_name': step_name,
                'step_type': step_type,
                'step_index': step_index,
                'total_steps': total_steps,
            },
        )
        await self.broadcast_nowait(event)

    async def broadcast_step_complete(
        self,
        step_name: str,
        status: str,
        duration: float,
        retry_count: int = 0,
        has_error: bool = False,
        test_case_id: str | None = None,
    ):
        """Broadcast a step complete event.

        Args:
            step_name: Step name
            status: Step status
            duration: Step duration in seconds
            retry_count: Number of retries
            has_error: Whether error occurred
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.STEP_COMPLETE,
            test_case_id=test_case_id,
            step_name=step_name,
            data={
                'step_name': step_name,
                'status': status,
                'duration': duration,
                'retry_count': retry_count,
                'has_error': has_error,
            },
        )
        await self.broadcast_nowait(event)

    async def broadcast_log(
        self,
        level: str,
        message: str,
        context: dict = None,
        test_case_id: str | None = None,
    ):
        """Broadcast a log event.

        Args:
            level: Log level
            message: Log message
            context: Additional context
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.LOG,
            test_case_id=test_case_id,
            data={'level': level, 'message': message, 'context': context or {}},
        )
        await self.broadcast_nowait(event)

    async def broadcast_progress(
        self,
        current_step: int,
        total_steps: int,
        percentage: float,
        passed_steps: int = 0,
        failed_steps: int = 0,
        estimated_remaining: float | None = None,
        test_case_id: str | None = None,
    ):
        """Broadcast a progress event.

        Args:
            current_step: Current step index
            total_steps: Total number of steps
            percentage: Progress percentage
            passed_steps: Number of passed steps
            failed_steps: Number of failed steps
            estimated_remaining: Estimated remaining time in seconds
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.PROGRESS,
            test_case_id=test_case_id,
            data={
                'current_step': current_step,
                'total_steps': total_steps,
                'percentage': round(percentage, 2),
                'passed_steps': passed_steps,
                'failed_steps': failed_steps,
                'estimated_remaining': estimated_remaining,
            },
        )
        await self.broadcast_nowait(event)

    async def broadcast_error(
        self,
        error_type: str,
        error_category: str,
        message: str,
        suggestion: str = '',
        step_name: str | None = None,
        test_case_id: str | None = None,
    ):
        """Broadcast an error event.

        Args:
            error_type: Error type
            error_category: Error category
            message: Error message
            suggestion: Suggested fix
            step_name: Step name where error occurred
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.ERROR,
            test_case_id=test_case_id,
            step_name=step_name,
            data={
                'error_type': error_type,
                'error_category': error_category,
                'message': message,
                'suggestion': suggestion,
                'step_name': step_name,
            },
        )
        await self.broadcast_nowait(event)

    async def broadcast_variable_update(
        self,
        variable_name: str,
        variable_value,
        source: str = 'extracted',
        test_case_id: str | None = None,
    ):
        """Broadcast a variable update event.

        Args:
            variable_name: Variable name
            variable_value: Variable value
            source: Variable source
            test_case_id: Test case identifier
        """
        event = WebSocketEvent(
            type=EventType.VARIABLE_UPDATE,
            test_case_id=test_case_id,
            data={
                'variable_name': variable_name,
                'variable_value': variable_value,
                'source': source,
            },
        )
        await self.broadcast_nowait(event)

    def get_subscriber_count(self, event_type: EventType | None = None) -> int:
        """Get the number of subscribers.

        Args:
            event_type: Optional event type to filter by

        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self.subscribers.get(event_type, set()))
        return sum(len(subs) for subs in self.subscribers.values())
