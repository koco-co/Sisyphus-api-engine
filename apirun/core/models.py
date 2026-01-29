"""Data Models for Sisyphus API Engine.

This module defines the core data structures used throughout the test execution process.
Following Google Python Style Guide.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HttpMethod(Enum):
    """HTTP Methods enum."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ErrorCategory(Enum):
    """Error classification categories."""

    ASSERTION = "assertion"
    NETWORK = "network"
    TIMEOUT = "timeout"
    PARSING = "parsing"
    BUSINESS = "business"
    SYSTEM = "system"


@dataclass
class ProfileConfig:
    """Environment profile configuration.

    Attributes:
        base_url: Base URL for the environment
        variables: Environment-specific variables
        timeout: Default timeout for requests
        verify_ssl: Whether to verify SSL certificates
        overrides: Configuration overrides from environment variables or CLI
        priority: Variable priority level (higher values take precedence)
    """

    base_url: str
    variables: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    verify_ssl: bool = True
    overrides: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0


@dataclass
class GlobalConfig:
    """Global test configuration.

    Attributes:
        name: Test suite name
        description: Test suite description
        profiles: Environment profiles (dev, test, prod, etc.)
        active_profile: Currently active profile name
        variables: Global variables accessible to all tests
        timeout: Global timeout for all steps
        retry_times: Default retry count for failed steps
        concurrent: Whether to enable concurrent execution
        concurrent_threads: Number of threads for concurrent execution
        data_source: Data source configuration for data-driven testing
            - type: Data source type (csv/json/database)
            - file_path: File path (for CSV/JSON)
            - delimiter: CSV delimiter (default: ",")
            - encoding: File encoding (default: "utf-8")
            - has_header: Whether CSV has header (default: True)
            - data_key: JSON key to extract data (for JSON)
            - db_type: Database type (for database)
            - connection_config: Database connection config (for database)
            - sql: SQL query (for database)
        data_iterations: Whether to iterate over data source (default: False)
        variable_prefix: Prefix for data variables (default: "")
        websocket: WebSocket configuration for real-time push
            - enabled: Whether to enable WebSocket server
            - host: WebSocket server host (default: "localhost")
            - port: WebSocket server port (default: 8765)
            - send_progress: Whether to send progress events (default: true)
            - send_logs: Whether to send log events (default: true)
            - send_variables: Whether to send variable update events (default: false)
        output: Output configuration for test results
            - path: Output file path (supports variables like ${timestamp})
            - format: Output format (json/html/xml)
            - include_request: Include request details in output
            - include_response: Include response details in output
            - include_performance: Include performance metrics in output
            - include_variables: Include variable snapshots in output
            - sensitive_data_mask: Mask sensitive data (passwords, tokens)
        debug: Debug mode configuration
            - enabled: Enable debug mode
            - variable_tracking: Track variable changes
            - show_request: Show request details
            - show_response: Show response details
            - log_level: Log level (DEBUG/INFO/WARN/ERROR)
        env_vars: Environment variable configuration
            - prefix: Environment variable prefix (e.g., "API_")
            - load_from_os: Whether to load variables from OS environment
            - overrides: Environment variable overrides
        verbose: Enable verbose output (console)
    """

    name: str
    description: str = ""
    profiles: Dict[str, ProfileConfig] = field(default_factory=dict)
    active_profile: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_times: int = 0
    concurrent: bool = False
    concurrent_threads: int = 3
    data_source: Optional[Dict[str, Any]] = None
    data_iterations: bool = False
    variable_prefix: str = ""
    websocket: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    debug: Optional[Dict[str, Any]] = None
    env_vars: Optional[Dict[str, Any]] = None
    verbose: bool = False


@dataclass
class ValidationRule:
    """Validation rule for assertions.

    Attributes:
        type: Comparator type (eq, ne, gt, lt, contains, regex, etc.)
              or logical operator (and, or, not)
        path: JSONPath expression to extract value
        expect: Expected value
        description: Validation description
        logical_operator: Logical operator (and/or/not) for complex validations
        sub_validations: List of sub-validation rules for logical operators
    """

    type: str
    path: str = ""
    expect: Any = None
    description: str = ""
    logical_operator: Optional[str] = None
    sub_validations: List["ValidationRule"] = field(default_factory=list)


@dataclass
class Extractor:
    """Variable extraction configuration.

    Attributes:
        name: Variable name to store extracted value
        type: Extraction type (jsonpath, regex, header, cookie)
        path: Extraction path or pattern
        index: Index for multiple matches (default: 0)
    """

    name: str
    type: str
    path: str
    index: int = 0


@dataclass
class TestStep:
    """Single test step.

    Attributes:
        name: Step name
        type: Step type (request, database, wait, loop, concurrent, etc.)
        method: HTTP method (for API requests)
        url: Request URL
        params: Query parameters or database query parameters
        headers: Request headers
        body: Request body
        validations: List of validation rules
        extractors: List of variable extractors
        skip_if: Conditional skip expression
        only_if: Conditional execution expression
        depends_on: List of step names this step depends on
        timeout: Step-specific timeout
        retry_times: Step-specific retry count
        setup: Setup hooks (before step execution)
        teardown: Teardown hooks (after step execution)
        database: Database configuration (for database steps)
            - type: Database type (mysql/postgresql/sqlite)
            - host: Database host (for MySQL/PostgreSQL)
            - port: Database port (for MySQL/PostgreSQL)
            - user: Database user (for MySQL/PostgreSQL)
            - password: Database password (for MySQL/PostgreSQL)
            - database: Database name (for MySQL/PostgreSQL)
            - path: Database file path (for SQLite)
        operation: Database operation type (query/exec/executemany/script)
        sql: SQL statement to execute
        seconds: Wait duration in seconds (for wait steps)
        condition: Condition expression to wait for (for wait steps)
        interval: Polling interval in seconds (for conditional wait, default: 1)
        max_wait: Maximum wait time in seconds (for conditional wait, default: 60)
        loop_type: Loop type (for/while, for loop steps)
        loop_count: Loop iteration count (for for loops)
        loop_condition: Loop continuation condition (for while loops)
        loop_variable: Variable name for loop counter (for loops)
        loop_steps: Steps to execute in loop (for loop steps)
        retry_policy: Enhanced retry policy configuration
            - max_attempts: Maximum retry attempts
            - strategy: Retry strategy (fixed/exponential/linear/custom)
            - base_delay: Base delay in seconds
            - max_delay: Maximum delay in seconds
            - backoff_multiplier: Multiplier for exponential backoff
            - jitter: Whether to add random jitter
            - retry_on: List of error types to retry on
            - stop_on: List of error types to stop retrying on
        max_concurrency: Maximum number of concurrent threads (for concurrent steps)
        concurrent_steps: Steps to execute concurrently (for concurrent steps)
        script: Script code to execute (for script steps)
        script_type: Script language type (python/javascript, default: python)
        allow_imports: Whether to allow module imports in scripts (default: true)
    """

    name: str
    type: str
    method: Optional[str] = None
    url: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    validations: List[ValidationRule] = field(default_factory=list)
    extractors: List[Extractor] = field(default_factory=list)
    skip_if: Optional[str] = None
    only_if: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    retry_times: Optional[int] = None
    setup: Optional[Dict[str, Any]] = None
    teardown: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None
    operation: Optional[str] = None
    sql: Optional[str] = None
    # Wait step fields
    seconds: Optional[float] = None
    condition: Optional[str] = None
    interval: Optional[float] = None
    max_wait: Optional[float] = None
    wait_condition: Optional[Dict[str, Any]] = None
    # Loop step fields
    loop_type: Optional[str] = None
    loop_count: Optional[int] = None
    loop_condition: Optional[str] = None
    loop_variable: Optional[str] = None
    loop_steps: Optional[List[Dict[str, Any]]] = None
    # Retry policy fields
    retry_policy: Optional[Dict[str, Any]] = None
    # Concurrent step fields
    max_concurrency: Optional[int] = None
    concurrent_steps: Optional[List[Dict[str, Any]]] = None
    # Script step fields
    script: Optional[str] = None
    script_type: Optional[str] = None
    allow_imports: Optional[bool] = None


@dataclass
class TestCase:
    """Test case definition.

    Attributes:
        name: Test case name
        description: Test case description
        config: Global configuration
        steps: List of test steps
        setup: Global setup hooks
        teardown: Global teardown hooks
        tags: Test case tags for filtering
        enabled: Whether the test case is enabled
    """

    name: str
    description: str = ""
    config: Optional[GlobalConfig] = None
    steps: List[TestStep] = field(default_factory=list)
    setup: Optional[Dict[str, Any]] = None
    teardown: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ErrorInfo:
    """Detailed error information.

    Attributes:
        type: Error type (exception class name)
        category: Error category
        message: Error message
        suggestion: Suggested fix for the error
        stack_trace: Full stack trace
        context: Additional context information (variables, step name, etc.)
        timestamp: When the error occurred
        severity: Error severity (critical/high/medium/low)
        error_code: Machine-readable error code
    """

    type: str
    category: ErrorCategory
    message: str
    suggestion: str = ""
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    severity: str = "medium"
    error_code: str = ""


@dataclass
class PerformanceMetrics:
    """Performance metrics for a step.

    Attributes:
        total_time: Total execution time in milliseconds
        dns_time: DNS lookup time in milliseconds
        tcp_time: TCP connection time in milliseconds
        tls_time: TLS handshake time in milliseconds
        server_time: Server processing time in milliseconds
        download_time: Download time in milliseconds
        upload_time: Upload time in milliseconds
        size: Response size in bytes
    """

    total_time: float = 0.0
    dns_time: float = 0.0
    tcp_time: float = 0.0
    tls_time: float = 0.0
    server_time: float = 0.0
    download_time: float = 0.0
    upload_time: float = 0.0
    size: int = 0


@dataclass
class StepResult:
    """Result of a single test step execution.

    Attributes:
        name: Step name
        status: Execution status (success, failure, skipped, error)
        response: HTTP response data
        extracted_vars: Extracted variables
        validation_results: List of validation results
        performance: Performance metrics
        error_info: Error information if failed
        start_time: Step start timestamp
        end_time: Step end timestamp
        retry_count: Number of retries performed
        variables_snapshot: Variable state before execution
        retry_history: Detailed retry attempt history
        variables_delta: Variable changes during execution (before -> after)
        variables_after: Variable state after execution
    """

    name: str
    status: str
    response: Optional[Dict[str, Any]] = None
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    performance: Optional[PerformanceMetrics] = None
    error_info: Optional[ErrorInfo] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    variables_snapshot: Dict[str, Any] = field(default_factory=dict)
    retry_history: List[Dict[str, Any]] = field(default_factory=list)
    variables_delta: Dict[str, Any] = field(default_factory=dict)
    variables_after: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCaseResult:
    """Result of a test case execution.

    Attributes:
        name: Test case name
        status: Overall status (passed, failed, skipped, error)
        start_time: Test case start timestamp
        end_time: Test case end timestamp
        duration: Total duration in seconds
        total_steps: Total number of steps
        passed_steps: Number of passed steps
        failed_steps: Number of failed steps
        skipped_steps: Number of skipped steps
        step_results: List of individual step results
        final_variables: Final state of all variables
        error_info: Error information if failed
    """

    name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration: float
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    step_results: List[StepResult] = field(default_factory=list)
    final_variables: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[ErrorInfo] = None
