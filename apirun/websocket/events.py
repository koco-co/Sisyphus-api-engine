"""WebSocket Event Types and Definitions.

This module defines the event types and data structures for WebSocket communication.
Following Google Python Style Guide.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """WebSocket event types.

    Attributes:
        TEST_START: Test execution started
        TEST_COMPLETE: Test execution completed
        STEP_START: Step execution started
        STEP_COMPLETE: Step execution completed
        LOG: Log message
        PROGRESS: Progress update
        ERROR: Error occurred
        VARIABLE_UPDATE: Variable updated
    """

    TEST_START = "test_start"
    TEST_COMPLETE = "test_complete"
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    LOG = "log"
    PROGRESS = "progress"
    ERROR = "error"
    VARIABLE_UPDATE = "variable_update"


class LogLevel(Enum):
    """Log levels for log events.

    Attributes:
        DEBUG: Debug level
        INFO: Info level
        WARNING: Warning level
        ERROR: Error level
        CRITICAL: Critical level
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class WebSocketEvent:
    """WebSocket event message.

    Attributes:
        type: Event type
        timestamp: Event timestamp
        data: Event data (flexible structure based on event type)
        test_case_id: Test case identifier
        step_name: Step name (for step-related events)
    """

    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    test_case_id: Optional[str] = None
    step_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "test_case_id": self.test_case_id,
            "step_name": self.step_name,
        }


@dataclass
class TestStartData:
    """Data for TEST_START event.

    Attributes:
        test_name: Test case name
        total_steps: Total number of steps
        description: Test description
    """

    test_name: str
    total_steps: int
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "test_name": self.test_name,
            "total_steps": self.total_steps,
            "description": self.description,
        }


@dataclass
class TestCompleteData:
    """Data for TEST_COMPLETE event.

    Attributes:
        status: Final test status
        total_steps: Total number of steps
        passed_steps: Number of passed steps
        failed_steps: Number of failed steps
        skipped_steps: Number of skipped steps
        duration: Total duration in seconds
    """

    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    duration: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "status": self.status,
            "total_steps": self.total_steps,
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "duration": self.duration,
        }


@dataclass
class StepStartData:
    """Data for STEP_START event.

    Attributes:
        step_name: Step name
        step_type: Step type (request/database/wait/loop/etc)
        step_index: Step index (0-based)
        total_steps: Total number of steps
    """

    step_name: str
    step_type: str
    step_index: int
    total_steps: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "step_name": self.step_name,
            "step_type": self.step_type,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
        }


@dataclass
class StepCompleteData:
    """Data for STEP_COMPLETE event.

    Attributes:
        step_name: Step name
        status: Step status
        duration: Step duration in seconds
        retry_count: Number of retries performed
        has_error: Whether error occurred
    """

    step_name: str
    status: str
    duration: float
    retry_count: int = 0
    has_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "step_name": self.step_name,
            "status": self.status,
            "duration": self.duration,
            "retry_count": self.retry_count,
            "has_error": self.has_error,
        }


@dataclass
class LogData:
    """Data for LOG event.

    Attributes:
        level: Log level
        message: Log message
        context: Additional context information
    """

    level: LogLevel
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "level": self.level.value,
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ProgressData:
    """Data for PROGRESS event.

    Attributes:
        current_step: Current step index (0-based)
        total_steps: Total number of steps
        percentage: Progress percentage (0-100)
        passed_steps: Number of passed steps
        failed_steps: Number of failed steps
        estimated_remaining: Estimated remaining time in seconds
    """

    current_step: int
    total_steps: int
    percentage: float
    passed_steps: int = 0
    failed_steps: int = 0
    estimated_remaining: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percentage": round(self.percentage, 2),
            "passed_steps": self.passed_steps,
            "failed_steps": self.failed_steps,
            "estimated_remaining": self.estimated_remaining,
        }


@dataclass
class ErrorData:
    """Data for ERROR event.

    Attributes:
        error_type: Error type
        error_category: Error category
        message: Error message
        suggestion: Suggested fix
        step_name: Step name where error occurred
    """

    error_type: str
    error_category: str
    message: str
    suggestion: str = ""
    step_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "error_type": self.error_type,
            "error_category": self.error_category,
            "message": self.message,
            "suggestion": self.suggestion,
            "step_name": self.step_name,
        }


@dataclass
class VariableUpdateData:
    """Data for VARIABLE_UPDATE event.

    Attributes:
        variable_name: Variable name
        variable_value: Variable value
        source: Variable source (extracted/profile/global)
    """

    variable_name: str
    variable_value: Any
    source: str = "extracted"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "variable_name": self.variable_name,
            "variable_value": self.variable_value,
            "source": self.source,
        }
