"""Result collection modules."""

from apirun.result.collector import ResultCollector
from apirun.result.allure_collector import AllureResultCollector
from apirun.result.junit_exporter import JUnitExporter, MultiTestSuiteJUnitExporter
from apirun.result.html_exporter import HTMLExporter

__all__ = [
    "ResultCollector",
    "AllureResultCollector",
    "JUnitExporter",
    "MultiTestSuiteJUnitExporter",
    "HTMLExporter",
]
