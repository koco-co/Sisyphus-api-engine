"""Enhanced Logging System for Sisyphus API Engine.

This module provides comprehensive logging capabilities:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- File and console output
- Structured logging for test execution
- Variable change tracking
- Performance metrics logging

Following Google Python Style Guide.
"""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any


@dataclass
class LogConfig:
    """Logging configuration.

    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        include_timestamps: Whether to include timestamps in logs
        include_variable_changes: Whether to log variable changes
        include_performance: Whether to log performance metrics
        format_template: Custom log format template
    """

    level: str = 'INFO'
    log_file: str | None = None
    console_output: bool = True
    include_timestamps: bool = True
    include_variable_changes: bool = True
    include_performance: bool = True
    format_template: str | None = None


class SisyphusLogger:
    """Enhanced logger for Sisyphus API Engine.

    Provides structured logging with:
    - Colored console output
    - File logging with rotation
    - Variable change tracking
    - Performance metrics
    - Detailed error information

    Attributes:
        logger: Python logger instance
        config: Logging configuration
        variable_history: History of variable changes
    """

    # Color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',  # Reset
    }

    def __init__(self, name: str = 'sisyphus', config: LogConfig | None = None):
        """Initialize SisyphusLogger.

        Args:
            name: Logger name
            config: Logging configuration
        """
        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.config.level.upper()))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Variable change history
        self.variable_history: dict[str, list] = {}

        # Setup handlers
        if self.config.console_output:
            self._setup_console_handler()

        if self.config.log_file:
            self._setup_file_handler()

    def _setup_console_handler(self):
        """Setup console handler with colored output."""
        handler = logging.StreamHandler(sys.stdout)

        # Create format
        if self.config.format_template:
            format_str = self.config.format_template
        else:
            if self.config.include_timestamps:
                format_str = '%(asctime)s - %(levelname)s - %(message)s'
            else:
                format_str = '%(levelname)s - %(message)s'

        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')

        # Custom formatter with colors
        class ColoredFormatter(logging.Formatter):
            def __init__(self, fmt, datefmt, colors):
                super().__init__(fmt, datefmt)
                self.colors = colors

            def format(self, record):
                levelname = record.levelname
                if levelname in self.colors:
                    record.levelname = (
                        f'{self.colors[levelname]}{levelname}{self.colors["RESET"]}'
                    )
                return super().format(record)

        colored_formatter = ColoredFormatter(
            formatter._fmt, formatter.datefmt, self.COLORS
        )
        handler.setFormatter(colored_formatter)

        self.logger.addHandler(handler)

    def _setup_file_handler(self):
        """Setup file handler with automatic directory creation."""
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_path, encoding='utf-8')

        # File format (no colors)
        if self.config.format_template:
            format_str = self.config.format_template
        else:
            format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def log_step_start(self, step_name: str, step_type: str, **details):
        """Log step execution start.

        Args:
            step_name: Step name
            step_type: Step type (request, database, etc.)
            **details: Additional step details
        """
        self.info(f'🚀 开始执行步骤: {step_name} ({step_type})')
        if details and self.config.level == 'DEBUG':
            self.debug(f'   详情: {json.dumps(details, ensure_ascii=False, indent=2)}')

    def log_step_end(self, step_name: str, status: str, duration: float, **details):
        """Log step execution end.

        Args:
            step_name: Step name
            status: Execution status (passed, failed, skipped)
            duration: Execution duration in seconds
            **details: Additional details
        """
        emoji = '✅' if status == 'passed' else ('❌' if status == 'failed' else '⏭️')
        self.info(f'{emoji} 步骤完成: {step_name} - 耗时: {duration:.3f}s')

        if details and self.config.level == 'DEBUG':
            self.debug(f'   详情: {json.dumps(details, ensure_ascii=False, indent=2)}')

    def log_variable_change(
        self, var_name: str, old_value: Any, new_value: Any, source: str = 'unknown'
    ):
        """Log variable value change.

        Args:
            var_name: Variable name
            old_value: Previous value
            new_value: New value
            source: Source of change (extraction, validation, etc.)
        """
        if not self.config.include_variable_changes:
            return

        # Track history
        if var_name not in self.variable_history:
            self.variable_history[var_name] = []

        change_record = {
            'timestamp': datetime.now().isoformat(),
            'old_value': old_value,
            'new_value': new_value,
            'source': source,
        }
        self.variable_history[var_name].append(change_record)

        # Log the change
        self.debug(f'📝 变量变更: {var_name} = {new_value} (来源: {source})')

    def log_validation_failure(
        self,
        validation_type: str,
        path: str,
        expected: Any,
        actual: Any,
        error_msg: str,
    ):
        """Log validation failure with detailed comparison.

        Args:
            validation_type: Type of validation (eq, ne, contains, etc.)
            path: JSONPath or field path
            expected: Expected value
            actual: Actual value
            error_msg: Error message
        """
        self.error(f'❌ 验证失败: {validation_type}')
        self.error(f'   路径: {path}')
        self.error(f'   期望值: {expected}')
        self.error(f'   实际值: {actual}')
        self.error(f'   错误信息: {error_msg}')

    def log_extraction_success(self, var_name: str, path: str, value: Any):
        """Log successful variable extraction.

        Args:
            var_name: Variable name
            path: Extraction path
            value: Extracted value
        """
        self.debug(f'✨ 提取成功: {var_name} = {value} (路径: {path})')

    def log_extraction_failure(self, var_name: str, path: str, error: str):
        """Log extraction failure.

        Args:
            var_name: Variable name
            path: Extraction path
            error: Error message
        """
        self.warning(f'⚠️  提取失败: {var_name} (路径: {path})')
        self.warning(f'   错误: {error}')

    def log_retry_attempt(
        self, attempt: int, max_attempts: int, delay: float, error: str
    ):
        """Log retry attempt.

        Args:
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts
            delay: Delay before next attempt
            error: Error that triggered retry
        """
        self.warning(f'🔄 重试 #{attempt}/{max_attempts} (延迟: {delay:.2f}s)')
        self.warning(f'   错误: {error}')

    def log_performance_metrics(self, step_name: str, metrics: dict[str, float]):
        """Log performance metrics.

        Args:
            step_name: Step name
            metrics: Performance metrics dictionary (values in milliseconds)
        """
        if not self.config.include_performance:
            return

        self.debug(f'⚡ 性能指标: {step_name}')
        for metric_name, value in metrics.items():
            # Convert milliseconds to seconds for readability
            value_sec = value / 1000.0
            self.debug(f'   {metric_name}: {value_sec:.3f}s')

    def get_variable_history(self, var_name: str | None = None) -> dict[str, list]:
        """Get variable change history.

        Args:
            var_name: Specific variable name (None = all variables)

        Returns:
            Dictionary of variable change histories
        """
        if var_name:
            return {var_name: self.variable_history.get(var_name, [])}
        return self.variable_history

    def export_history(self, output_file: str):
        """Export variable change history to JSON file.

        Args:
            output_file: Output file path
        """
        with Path(output_file).open('w', encoding='utf-8') as f:
            json.dump(self.variable_history, f, ensure_ascii=False, indent=2)
        self.info(f'📊 变量历史已导出到: {output_file}')


# Global logger instance
_global_logger: SisyphusLogger | None = None


def get_logger(
    name: str = 'sisyphus', config: LogConfig | None = None
) -> SisyphusLogger:
    """Get or create global logger instance.

    Args:
        name: Logger name
        config: Logging configuration

    Returns:
        SisyphusLogger instance
    """
    global _global_logger
    if _global_logger is None or config is not None:
        _global_logger = SisyphusLogger(name, config)
    return _global_logger


def setup_logger_from_args(
    log_level: str, log_file: str | None = None
) -> SisyphusLogger:
    """Setup logger from command-line arguments.

    Args:
        log_level: Log level (debug, info, warning, error)
        log_file: Optional log file path

    Returns:
        Configured SisyphusLogger instance
    """
    config = LogConfig(
        level=log_level.upper(),
        log_file=log_file,
        console_output=True,
        include_timestamps=True,
        include_variable_changes=True,
        include_performance=True,
    )
    return get_logger(config=config)
