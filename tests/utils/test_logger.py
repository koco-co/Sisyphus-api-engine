"""Unit tests for the enhanced logging system."""

import logging
import pytest
import tempfile
from pathlib import Path
from apirun.utils.logger import SisyphusLogger, LogConfig, get_logger, setup_logger_from_args


class TestLogConfig:
    """Test LogConfig dataclass."""

    def test_default_config(self):
        """Test default log configuration."""
        config = LogConfig()
        assert config.level == "INFO"
        assert config.log_file is None
        assert config.console_output is True
        assert config.include_timestamps is True
        assert config.include_variable_changes is True
        assert config.include_performance is True

    def test_custom_config(self):
        """Test custom log configuration."""
        config = LogConfig(
            level="DEBUG",
            log_file="test.log",
            console_output=False,
            include_timestamps=False
        )
        assert config.level == "DEBUG"
        assert config.log_file == "test.log"
        assert config.console_output is False
        assert config.include_timestamps is False


class TestSisyphusLogger:
    """Test SisyphusLogger class."""

    def test_logger_creation(self):
        """Test logger instance creation."""
        logger = SisyphusLogger("test_logger")
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) > 0

    def test_debug_level(self):
        """Test setting debug log level."""
        config = LogConfig(level="DEBUG")
        logger = SisyphusLogger("debug_test", config)
        assert logger.logger.level == logging.DEBUG

    def test_warning_level(self):
        """Test setting warning log level."""
        config = LogConfig(level="WARNING")
        logger = SisyphusLogger("warning_test", config)
        assert logger.logger.level == logging.WARNING

    def test_error_level(self):
        """Test setting error log level."""
        config = LogConfig(level="ERROR")
        logger = SisyphusLogger("error_test", config)
        assert logger.logger.level == logging.ERROR

    def test_log_methods(self, caplog):
        """Test various log methods."""
        config = LogConfig(level="DEBUG")
        logger = SisyphusLogger("methods_test", config)
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text

    def test_log_step_start(self):
        """Test logging step start."""
        logger = SisyphusLogger("step_test")
        # Should not raise exception
        logger.log_step_start("Test Step", "request", url="http://example.com")

    def test_log_step_end(self):
        """Test logging step end."""
        logger = SisyphusLogger("step_test")
        # Should not raise exception
        logger.log_step_end("Test Step", "passed", 1.5, response_status=200)

    def test_variable_change_tracking(self):
        """Test variable change tracking."""
        logger = SisyphusLogger("variable_test")
        logger.log_variable_change("test_var", "old_value", "new_value", "extraction")

        assert "test_var" in logger.variable_history
        assert len(logger.variable_history["test_var"]) == 1

        change = logger.variable_history["test_var"][0]
        assert change["old_value"] == "old_value"
        assert change["new_value"] == "new_value"
        assert change["source"] == "extraction"
        assert "timestamp" in change

    def test_variable_change_history_disabled(self):
        """Test variable change tracking when disabled."""
        config = LogConfig(include_variable_changes=False)
        logger = SisyphusLogger("no_history_test", config)

        # When include_variable_changes is False, log_variable_change returns early
        # and doesn't track history
        logger.log_variable_change("test_var", "old", "new", "test")

        # History should be empty since tracking is disabled
        assert len(logger.variable_history) == 0

    def test_validation_failure_logging(self):
        """Test validation failure logging."""
        logger = SisyphusLogger("validation_test")
        # Should not raise exception
        logger.log_validation_failure(
            "eq",
            "$.json.code",
            200,
            404,
            "Expected 200 but got 404"
        )

    def test_extraction_success_logging(self):
        """Test extraction success logging."""
        logger = SisyphusLogger("extraction_test")
        # Should not raise exception
        logger.log_extraction_success("user_id", "$.json.id", 12345)

    def test_extraction_failure_logging(self):
        """Test extraction failure logging."""
        logger = SisyphusLogger("extraction_test")
        # Should not raise exception
        logger.log_extraction_failure("user_id", "$.json.id", "Path not found")

    def test_retry_attempt_logging(self):
        """Test retry attempt logging."""
        logger = SisyphusLogger("retry_test")
        # Should not raise exception
        logger.log_retry_attempt(2, 3, 1.5, "Connection timeout")

    def test_performance_metrics_logging(self):
        """Test performance metrics logging."""
        logger = SisyphusLogger("performance_test")
        metrics = {
            "total_time": 2.5,
            "dns_time": 0.1,
            "tcp_time": 0.2,
            "tls_time": 0.3
        }
        # Should not raise exception
        logger.log_performance_metrics("Test Step", metrics)

    def test_performance_metrics_unit_conversion(self, caplog):
        """Test that performance metrics are converted from milliseconds to seconds."""
        """修复bug: 验证性能指标从毫秒转换为秒"""
        config = LogConfig(level="DEBUG", include_performance=True)
        logger = SisyphusLogger("performance_conversion_test", config)

        with caplog.at_level(logging.DEBUG):
            logger.log_performance_metrics("Test Step", {
                "total_time": 1729.428,  # milliseconds
                "dns_time": 100.500,     # milliseconds
                "tcp_time": 150.250,     # milliseconds
                "tls_time": 200.750      # milliseconds
            })

        log_output = caplog.text
        # Should show seconds, not milliseconds (divided by 1000)
        assert "1.729s" in log_output  # 1729.428ms → 1.729s
        assert "0.101s" in log_output  # 100.500ms → 0.101s
        assert "0.150s" in log_output  # 150.250ms → 0.150s
        assert "0.201s" in log_output  # 200.750ms → 0.201s
        # Should NOT show raw millisecond values as seconds
        assert "1729.428s" not in log_output
        assert "100.500s" not in log_output
        # Should mention performance metrics
        assert "性能指标" in log_output

    def test_performance_metrics_conversion_with_small_values(self, caplog):
        """Test conversion with very small millisecond values."""
        """修复bug: 验证小数值的性能指标转换"""
        config = LogConfig(level="DEBUG", include_performance=True)
        logger = SisyphusLogger("small_values_test", config)

        with caplog.at_level(logging.DEBUG):
            logger.log_performance_metrics("Fast Request", {
                "total_time": 1.5,      # 1.5ms
                "dns_time": 0.5,        # 0.5ms
                "tcp_time": 0.3         # 0.3ms
            })

        log_output = caplog.text
        # Should convert to seconds with proper decimal formatting
        assert "0.002s" in log_output  # 1.5ms → 0.002s
        assert "0.001s" in log_output  # 0.5ms → 0.001s
        assert "0.000s" in log_output  # 0.3ms → 0.000s

    def test_performance_metrics_conversion_with_large_values(self, caplog):
        """Test conversion with large millisecond values."""
        """修复bug: 验证大数值的性能指标转换"""
        config = LogConfig(level="DEBUG", include_performance=True)
        logger = SisyphusLogger("large_values_test", config)

        with caplog.at_level(logging.DEBUG):
            logger.log_performance_metrics("Slow Request", {
                "total_time": 54321.789,  # ~54 seconds
                "server_time": 50000.0    # 50 seconds
            })

        log_output = caplog.text
        # Should convert to seconds properly
        assert "54.322s" in log_output  # 54321.789ms → 54.322s
        assert "50.000s" in log_output  # 50000.0ms → 50.000s

    def test_performance_logging_disabled(self):
        """Test performance logging when disabled."""
        config = LogConfig(include_performance=False)
        logger = SisyphusLogger("no_perf_test", config)
        metrics = {"total_time": 2.5}
        # Should not raise exception
        logger.log_performance_metrics("Test Step", metrics)

    def test_get_variable_history(self):
        """Test getting variable history."""
        logger = SisyphusLogger("history_test")
        logger.log_variable_change("var1", "a", "b", "test1")
        logger.log_variable_change("var2", "x", "y", "test2")

        # Get all history
        all_history = logger.get_variable_history()
        assert "var1" in all_history
        assert "var2" in all_history

        # Get specific variable history
        var1_history = logger.get_variable_history("var1")
        assert "var1" in var1_history
        assert "var2" not in var1_history

    def test_export_history(self):
        """Test exporting variable history to file."""
        logger = SisyphusLogger("export_test")
        logger.log_variable_change("test_var", 1, 2, "test")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name

        try:
            logger.export_history(temp_file)
            assert Path(temp_file).exists()

            # Verify file contents
            import json
            with open(temp_file, 'r') as f:
                data = json.load(f)
            assert "test_var" in data
            assert len(data["test_var"]) == 1
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_file_handler_creation(self):
        """Test file handler is created when log_file is specified."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name

        try:
            config = LogConfig(log_file=temp_file)
            logger = SisyphusLogger("file_test", config)

            # Check that file handler was added
            file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0

            # Verify log file exists after logging
            logger.info("Test message")
            assert Path(temp_file).exists()

            # Verify file contents
            with open(temp_file, 'r') as f:
                content = f.read()
            assert "Test message" in content
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_console_handler_can_be_disabled(self):
        """Test console handler can be disabled."""
        config = LogConfig(console_output=False)
        logger = SisyphusLogger("no_console_test", config)

        stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
        # FileHandler is also a StreamHandler in Python, so we need to check more carefully
        console_handlers = [h for h in stream_handlers if not isinstance(h, logging.FileHandler)]
        assert len(console_handlers) == 0


class TestGlobalLogger:
    """Test global logger functions."""

    def test_get_logger_returns_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2

    def test_get_logger_with_new_config(self):
        """Test get_logger with new config creates new instance."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2", config=LogConfig(level="DEBUG"))
        assert logger1 is not logger2

    def test_setup_logger_from_args(self):
        """Test setup_logger_from_args function."""
        logger = setup_logger_from_args("debug", None)
        assert isinstance(logger, SisyphusLogger)
        assert logger.config.level == "DEBUG"
        assert logger.config.log_file is None

    def test_setup_logger_from_args_with_file(self):
        """Test setup_logger_from_args with log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name

        try:
            logger = setup_logger_from_args("info", temp_file)
            assert logger.config.log_file == temp_file
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestLogLevels:
    """Test different log levels."""

    def test_debug_level_filters_info(self, caplog):
        """Test that ERROR level filters INFO messages."""
        config = LogConfig(level="ERROR")
        logger = SisyphusLogger("level_test", config)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug")
            logger.info("Info")
            logger.warning("Warning")
            logger.error("Error")

        # Only ERROR and CRITICAL should be logged
        assert "Error" in caplog.text
        assert "Warning" not in caplog.text
        assert "Info" not in caplog.text
        assert "Debug" not in caplog.text
