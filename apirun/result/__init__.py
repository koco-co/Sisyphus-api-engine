"""Result export modules."""

from apirun.result.json_exporter import JSONExporter
from apirun.result.allure_exporter import AllureExporter
from apirun.result.junit_exporter import JUnitExporter, MultiTestSuiteJUnitExporter
from apirun.result.html_exporter import HTMLExporter

# Default patterns for identifying sensitive data fields
DEFAULT_SENSITIVE_PATTERNS = [
    "password",
    "pwd",
    "token",
    "secret",
    "key",
    "auth",
]

__all__ = [
    "JSONExporter",
    "AllureExporter",
    "JUnitExporter",
    "MultiTestSuiteJUnitExporter",
    "HTMLExporter",
    "DEFAULT_SENSITIVE_PATTERNS",
]
