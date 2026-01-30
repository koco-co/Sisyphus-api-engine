"""Sisyphus API Engine - Enterprise-grade API Automation Testing Engine.

This package provides the core functionality for executing YAML-based API tests.
"""

__version__ = "1.0.2"
__author__ = "koco-co"

from apirun.core.models import (
    TestCase,
    TestStep,
    GlobalConfig,
    ProfileConfig,
    ValidationRule,
    Extractor,
    StepResult,
    TestCaseResult,
    ErrorInfo,
    PerformanceMetrics,
    HttpMethod,
    ErrorCategory,
)

from apirun.core.variable_manager import VariableManager, VariableScope
from apirun.parser.v2_yaml_parser import V2YamlParser, parse_yaml_file, parse_yaml_string
from apirun.executor.test_case_executor import TestCaseExecutor
from apirun.executor.api_executor import APIExecutor
from apirun.validation.engine import ValidationEngine
from apirun.result.json_exporter import JSONExporter

__all__ = [
    # Models
    "TestCase",
    "TestStep",
    "GlobalConfig",
    "ProfileConfig",
    "ValidationRule",
    "Extractor",
    "StepResult",
    "TestCaseResult",
    "ErrorInfo",
    "PerformanceMetrics",
    "HttpMethod",
    "ErrorCategory",
    # Core
    "VariableManager",
    "VariableScope",
    # Parser
    "V2YamlParser",
    "parse_yaml_file",
    "parse_yaml_string",
    # Executor
    "TestCaseExecutor",
    "APIExecutor",
    # Validation
    "ValidationEngine",
    # Result
    "JSONExporter",
]
