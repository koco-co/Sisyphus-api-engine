"""Command Line Interface for Sisyphus API Engine.

This module provides the CLI entry point for running test cases.
Following Google Python Style Guide.
"""

import argparse
import json
import sys
import asyncio
from typing import Optional
from pathlib import Path

from apirun.parser.v2_yaml_parser import V2YamlParser, YamlParseError
from apirun.executor.test_case_executor import TestCaseExecutor
from apirun.core.variable_manager import VariableManager
from apirun.utils.template import render_template
from apirun.data_driven.iterator import DataDrivenIterator
from apirun.cli_help_i18n import get_help_messages, get_validate_help_messages, ARGUMENT_MAPPING


def show_help(parser: argparse.ArgumentParser, lang: str = "en") -> None:
    """Display help message in specified language.

    Args:
        parser: Argument parser object
        lang: Language code ('en' for English, 'zh' for Chinese)
    """
    messages = get_help_messages(lang)

    print(f"\n{messages['description']}\n")
    if lang == "zh":
        print("用法:")
        print("  sisyphus-api-engine --cases <文件> [选项]\n")
        print("参数:")
    else:
        print("Usage:")
        print("  sisyphus-api-engine --cases <file> [options]\n")
        print("Arguments:")

    # Format and display arguments
    for action in parser._actions:
        if action.dest in ['help', '中文帮助']:
            continue

        # Get option strings
        opts = ", ".join(action.option_strings)

        # Get help text from messages based on language
        help_text = ""
        if action.dest in ARGUMENT_MAPPING:
            arg_key = ARGUMENT_MAPPING[action.dest]
            help_text = messages["args"].get(arg_key, "")
        else:
            # Fallback to action's help text (should be English only)
            help_text = action.help or ""

        # Format default values
        if action.default is not None and action.default != "==SUPPRESS==" and action.default != []:
            if action.dest in ['ws_host', 'ws_port', 'allure_dir', 'format']:
                if lang == "zh":
                    if isinstance(action.default, str):
                        help_text += f" (默认: {action.default})"
                    elif isinstance(action.default, int):
                        help_text += f" (默认: {action.default})"
                else:
                    if isinstance(action.default, str):
                        help_text += f" (default: {action.default})"
                    elif isinstance(action.default, int):
                        help_text += f" (default: {action.default})"

        # Display the argument
        if opts:
            print(f"  {opts.ljust(25)} {help_text}")

    print(f"\n{messages['epilog']}")

    # Show additional help options
    if lang == "zh":
        print("帮助选项:")
        print("  -h, --help          显示英文帮助")
        print("  -H, --中文帮助      显示中文帮助")
    else:
        print("Help Options:")
        print("  -h, --help          Show help in English")
        print("  -H, --中文帮助      Show help in Chinese")
    print()


def show_validate_help(parser: argparse.ArgumentParser, lang: str = "en") -> None:
    """Display validation command help message in specified language.

    Args:
        parser: Argument parser object
        lang: Language code ('en' for English, 'zh' for Chinese)
    """
    messages = get_validate_help_messages(lang)

    print(f"\n{messages['description']}\n")
    if lang == "zh":
        print("用法:")
        print("  sisyphus-api-validate <路径>...\n")
        print("参数:")
    else:
        print("Usage:")
        print("  sisyphus-api-validate <paths>...\n")
        print("Arguments:")

    # Format and display arguments
    for action in parser._actions:
        if action.dest in ['help', '中文帮助']:
            continue

        # Get option strings or positional name
        if action.option_strings:
            opts = ", ".join(action.option_strings)
        else:
            opts = action.dest.upper()

        # Get help text from messages based on language
        help_text = ""
        if action.dest == "paths":
            help_text = messages["args"].get("paths", "")
        else:
            help_text = action.help or ""

        # Display the argument
        print(f"  {opts.ljust(25)} {help_text}")

    print(f"\n{messages['epilog']}")

    # Show additional help options
    if lang == "zh":
        print("帮助选项:")
        print("  -h, --help          显示英文帮助")
        print("  -H, --中文帮助      显示中文帮助")
    else:
        print("Help Options:")
        print("  -h, --help          Show help in English")
        print("  -H, --中文帮助      Show help in Chinese")
    print()


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="Sisyphus API Engine - Enterprise-grade API Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_help_messages("en")["epilog"],
        add_help=False,  # We'll add help manually
    )

    # Add standard help
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message",
    )

    # Add Chinese help
    parser.add_argument(
        "-H", "--中文帮助",
        action="store_true",
        help="Show help in Chinese",
    )

    parser.add_argument(
        "--cases",
        type=str,
        required=True,
        help="Path to YAML test case file or directory",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path for JSON results",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate YAML syntax without execution",
    )

    parser.add_argument(
        "--profile",
        type=str,
        help="Active profile name (overrides config)",
    )

    parser.add_argument(
        "--ws-server",
        action="store_true",
        help="Enable WebSocket server for real-time updates",
    )

    parser.add_argument(
        "--ws-host",
        type=str,
        default="localhost",
        help="WebSocket server host",
    )

    parser.add_argument(
        "--ws-port",
        type=int,
        default=8765,
        help="WebSocket server port",
    )

    parser.add_argument(
        "--env-prefix",
        type=str,
        help="Environment variable prefix to load",
    )

    parser.add_argument(
        "--override",
        type=str,
        action="append",
        help="Configuration overrides in 'key=value' format",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with variable tracking",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "csv", "junit", "html"],
        default="text",
        help="Output format: text/json/csv/junit/html",
    )

    parser.add_argument(
        "--allure",
        action="store_true",
        help="Generate Allure report",
    )

    parser.add_argument(
        "--allure-dir",
        type=str,
        default="allure-results",
        help="Allure results directory",
    )

    # Check for help flags first before parsing required arguments
    import sys
    if "-H" in sys.argv or "--中文帮助" in sys.argv:
        show_help(parser, lang="zh")
        return 0
    elif "-h" in sys.argv or "--help" in sys.argv:
        show_help(parser, lang="en")
        return 0

    # Parse args normally (now --cases is required)
    args = parser.parse_args()

    try:
        if args.validate:
            return validate_yaml(args.cases)

        # Execute test case
        result = execute_test_case(
            args.cases,
            args.verbose,
            args.profile,
            args.ws_server,
            args.ws_host,
            args.ws_port,
            args.env_prefix,
            args.override,
            args.debug,
            args.output,
            args.format,
            args.allure,
            args.allure_dir,
        )

        # Handle output based on format
        if args.format == "json":
            # Determine if we should output compact or full JSON
            # Check verbose flag (from CLI or YAML config)
            use_verbose = args.verbose
            if not use_verbose and result.get("test_case", {}).get("config", {}).get("verbose"):
                use_verbose = True

            if use_verbose:
                # Full JSON output (all information)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                # Ultra-compact JSON output (only response content)
                api_responses = []

                # Extract only response content from steps
                for step in result.get("steps", []):
                    if step.get("response"):
                        response_item = {
                            "step": step["name"],
                            "response": step["response"]
                        }
                        api_responses.append(response_item)

                print(json.dumps(api_responses, ensure_ascii=False, indent=2))

        elif args.format == "csv":
            # CSV output
            from apirun.result.collector import ResultCollector
            from apirun.core.models import TestCaseResult, StepResult, PerformanceMetrics
            from datetime import datetime

            # Reconstruct TestCaseResult from dict
            start_time = datetime.fromisoformat(result["test_case"]["start_time"]) if result["test_case"].get("start_time") else datetime.now()
            end_time = datetime.fromisoformat(result["test_case"]["end_time"]) if result["test_case"].get("end_time") else datetime.now()

            # Reconstruct step results for CSV
            step_results = []
            for step_data in result.get("steps", []):
                step_start = datetime.fromisoformat(step_data["start_time"]) if step_data.get("start_time") else None
                step_end = datetime.fromisoformat(step_data["end_time"]) if step_data.get("end_time") else None

                step_perf = None
                if args.verbose and step_data.get("performance"):
                    perf_data = step_data["performance"]
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get("total_time", 0),
                        dns_time=perf_data.get("dns_time", 0),
                        tcp_time=perf_data.get("tcp_time", 0),
                        tls_time=perf_data.get("tls_time", 0),
                        server_time=perf_data.get("server_time", 0),
                        download_time=perf_data.get("download_time", 0),
                        size=perf_data.get("size", 0),
                    )

                step_result = StepResult(
                    name=step_data["name"],
                    status=step_data["status"],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get("response"),
                    performance=step_perf,
                    error_info=None,
                )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result["test_case"]["name"],
                status=result["test_case"]["status"],
                start_time=start_time,
                end_time=end_time,
                duration=result["test_case"]["duration"],
                total_steps=result["statistics"]["total_steps"],
                passed_steps=result["statistics"]["passed_steps"],
                failed_steps=result["statistics"]["failed_steps"],
                skipped_steps=result["statistics"]["skipped_steps"],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            collector = ResultCollector()
            # Determine if we should use verbose mode
            use_verbose = args.verbose
            if not use_verbose and result.get("test_case", {}).get("config", {}).get("verbose"):
                use_verbose = True

            csv_output = collector.to_csv(test_case_result, verbose=use_verbose)
            print(csv_output, end="")

        elif args.format == "junit":
            # JUnit XML output
            from apirun.result.junit_exporter import JUnitExporter
            from apirun.core.models import TestCaseResult, StepResult, PerformanceMetrics
            from datetime import datetime

            # Reconstruct TestCaseResult with full step results
            start_time = datetime.fromisoformat(result["test_case"]["start_time"]) if result["test_case"].get("start_time") else datetime.now()
            end_time = datetime.fromisoformat(result["test_case"]["end_time"]) if result["test_case"].get("end_time") else datetime.now()

            # Reconstruct step results
            step_results = []
            for step_data in result.get("steps", []):
                step_start = datetime.fromisoformat(step_data["start_time"]) if step_data.get("start_time") else None
                step_end = datetime.fromisoformat(step_data["end_time"]) if step_data.get("end_time") else None
                step_perf = None
                if step_data.get("performance"):
                    perf_data = step_data["performance"]
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get("total_time", 0),
                        dns_time=perf_data.get("dns_time", 0),
                        tcp_time=perf_data.get("tcp_time", 0),
                        tls_time=perf_data.get("tls_time", 0),
                        server_time=perf_data.get("server_time", 0),
                        download_time=perf_data.get("download_time", 0),
                        size=perf_data.get("size", 0),
                    )

                step_result = StepResult(
                    name=step_data["name"],
                    status=step_data["status"],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get("response"),
                    performance=step_perf,
                    error_info=None,  # We'll skip error details in non-verbose mode
                )

                # Only add detailed error info if verbose
                if args.verbose and step_data.get("error_info"):
                    from apirun.core.models import ErrorInfo, ErrorCategory
                    error_data = step_data["error_info"]
                    step_result.error_info = ErrorInfo(
                        type=error_data.get("type", "UNKNOWN"),
                        message=error_data.get("message", ""),
                        category=ErrorCategory(error_data.get("category", "SYSTEM")),
                    )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result["test_case"]["name"],
                status=result["test_case"]["status"],
                start_time=start_time,
                end_time=end_time,
                duration=result["test_case"]["duration"],
                total_steps=result["statistics"]["total_steps"],
                passed_steps=result["statistics"]["passed_steps"],
                failed_steps=result["statistics"]["failed_steps"],
                skipped_steps=result["statistics"]["skipped_steps"],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            exporter = JUnitExporter()
            junit_xml = exporter.to_junit_xml(test_case_result)
            print(junit_xml, end="")

        elif args.format == "html":
            # HTML output
            from apirun.result.html_exporter import HTMLExporter
            from apirun.core.models import TestCaseResult, StepResult, PerformanceMetrics
            from datetime import datetime

            # Reconstruct TestCaseResult with full step results
            start_time = datetime.fromisoformat(result["test_case"]["start_time"]) if result["test_case"].get("start_time") else datetime.now()
            end_time = datetime.fromisoformat(result["test_case"]["end_time"]) if result["test_case"].get("end_time") else datetime.now()

            # Reconstruct step results based on verbose mode
            step_results = []
            for step_data in result.get("steps", []):
                step_start = datetime.fromisoformat(step_data["start_time"]) if step_data.get("start_time") else None
                step_end = datetime.fromisoformat(step_data["end_time"]) if step_data.get("end_time") else None

                step_perf = None
                if args.verbose and step_data.get("performance"):
                    perf_data = step_data["performance"]
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get("total_time", 0),
                        dns_time=perf_data.get("dns_time", 0),
                        tcp_time=perf_data.get("tcp_time", 0),
                        tls_time=perf_data.get("tls_time", 0),
                        server_time=perf_data.get("server_time", 0),
                        download_time=perf_data.get("download_time", 0),
                        size=perf_data.get("size", 0),
                    )

                step_result = StepResult(
                    name=step_data["name"],
                    status=step_data["status"],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get("response") if args.verbose else None,
                    performance=step_perf,
                    error_info=None,
                )

                # Only add detailed error info if verbose
                if args.verbose and step_data.get("error_info"):
                    from apirun.core.models import ErrorInfo, ErrorCategory
                    error_data = step_data["error_info"]
                    step_result.error_info = ErrorInfo(
                        type=error_data.get("type", "UNKNOWN"),
                        message=error_data.get("message", ""),
                        category=ErrorCategory(error_data.get("category", "SYSTEM")),
                    )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result["test_case"]["name"],
                status=result["test_case"]["status"],
                start_time=start_time,
                end_time=end_time,
                duration=result["test_case"]["duration"],
                total_steps=result["statistics"]["total_steps"],
                passed_steps=result["statistics"]["passed_steps"],
                failed_steps=result["statistics"]["failed_steps"],
                skipped_steps=result["statistics"]["skipped_steps"],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            exporter = HTMLExporter()
            html_output = exporter.to_html(test_case_result)
            print(html_output, end="")

        # Save result if output path specified (either in YAML or CLI)
        output_path = args.output
        if not output_path and result.get("test_case", {}).get("config", {}).get("output", {}).get("path"):
            # Use output path from YAML config
            output_path = result["test_case"]["config"]["output"]["path"]

        if output_path:
            save_result(result, output_path)
            # Only print save message in text mode
            if args.format in ["text"] and (args.verbose or result.get("test_case", {}).get("config", {}).get("verbose")):
                print(f"\nResults saved to: {output_path}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except YamlParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def validate_main() -> int:
    """CLI entry point for validation-only mode.

    This is a dedicated command for validating YAML syntax without execution.

    Returns:
        Exit code (0 for valid, non-zero for invalid)
    """
    parser = argparse.ArgumentParser(
        description="Sisyphus API Engine - YAML Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_validate_help_messages("en")["epilog"],
        add_help=False,
    )

    # Add help options
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help message",
    )

    parser.add_argument(
        "-H", "--中文帮助",
        action="store_true",
        help="Show help in Chinese",
    )

    parser.add_argument(
        "paths",
        type=str,
        nargs="+",
        help="Path(s) to YAML file(s) or directory",
    )

    # Check for help flags first
    import sys
    if "-H" in sys.argv or "--中文帮助" in sys.argv:
        show_validate_help(parser, lang="zh")
        return 0
    elif "-h" in sys.argv or "--help" in sys.argv:
        show_validate_help(parser, lang="en")
        return 0

    # Parse args normally
    args = parser.parse_args()

    try:
        all_valid = True
        validator = V2YamlParser()

        for path_str in args.paths:
            path = Path(path_str)

            if not path.exists():
                print(f"Error: Path not found: {path_str}", file=sys.stderr)
                all_valid = False
                continue

            if path.is_file():
                yaml_files = [path]
            elif path.is_dir():
                yaml_files = list(path.glob("**/*.yaml"))
                if not yaml_files:
                    print(f"Warning: No YAML files found in {path_str}")
                    continue
            else:
                print(f"Error: Invalid path: {path_str}", file=sys.stderr)
                all_valid = False
                continue

            for yaml_file in yaml_files:
                print(f"Validating: {yaml_file}")
                errors = validator.validate_yaml(str(yaml_file))

                if errors:
                    all_valid = False
                    print(f"  ❌ Validation failed:")
                    for error in errors:
                        print(f"    - {error}")
                else:
                    print(f"  ✓ Valid")

        if all_valid:
            print("\n✓ All YAML files are valid!")
            return 0
        else:
            print("\n❌ Some YAML files have validation errors.")
            return 1

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def validate_yaml(case_path: str) -> int:
    """Validate YAML file syntax.

    Args:
        case_path: Path to YAML file or directory

    Returns:
        Exit code (0 for valid, non-zero for invalid)
    """
    parser = V2YamlParser()

    path = Path(case_path)
    yaml_files = []

    if path.is_file():
        yaml_files = [path]
    elif path.is_dir():
        yaml_files = list(path.glob("**/*.yaml"))
    else:
        print(f"Error: Path not found: {case_path}", file=sys.stderr)
        return 1

    all_valid = True
    for yaml_file in yaml_files:
        print(f"Validating: {yaml_file}")
        errors = parser.validate_yaml(str(yaml_file))

        if errors:
            all_valid = False
            print(f"  ❌ Validation failed:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ Valid")

    return 0 if all_valid else 1


def execute_test_case(
    case_path: str,
    verbose: bool = False,
    profile: Optional[str] = None,
    ws_server: bool = False,
    ws_host: str = "localhost",
    ws_port: int = 8765,
    env_prefix: Optional[str] = None,
    overrides: Optional[list] = None,
    debug: bool = False,
    output: Optional[str] = None,
    format_type: str = "text",
    allure: bool = False,
    allure_dir: str = "allure-results",
) -> dict:
    """Execute test case and return results.

    Args:
        case_path: Path to YAML file
        verbose: Enable verbose output (overrides YAML config)
        profile: Active profile name (overrides config)
        ws_server: Enable WebSocket server for real-time updates
        ws_host: WebSocket server host
        ws_port: WebSocket server port
        env_prefix: Environment variable prefix (overrides YAML config)
        overrides: Configuration overrides (list of "key=value" strings)
        debug: Enable debug mode (overrides YAML config)
        output: Output file path (overrides YAML config)
        format_type: Output format (text/json, overrides YAML config)
        allure: Generate Allure report (overrides YAML config)
        allure_dir: Allure results directory (overrides YAML config)

    Returns:
        Execution result as dictionary
    """
    # Parse YAML
    parser = V2YamlParser()
    test_case = parser.parse(case_path)

    # Initialize config if not exists
    if not test_case.config:
        from apirun.core.models import GlobalConfig
        test_case.config = GlobalConfig(name=test_case.name)

    # Apply CLI overrides to config (CLI has higher priority)
    if verbose is not False:  # Only override if explicitly set
        test_case.config.verbose = verbose

    if profile and test_case.config:
        test_case.config.active_profile = profile

    if debug:
        if test_case.config.debug is None:
            test_case.config.debug = {}
        test_case.config.debug["enabled"] = True

    if env_prefix:
        if test_case.config.env_vars is None:
            test_case.config.env_vars = {}
        test_case.config.env_vars["prefix"] = env_prefix

    if output:
        if test_case.config.output is None:
            test_case.config.output = {}
        test_case.config.output["path"] = output

    # Determine output format configuration
    # Priority: CLI args > YAML config > defaults (text)
    output_format = format_type
    if test_case.config and test_case.config.output:
        yaml_format = test_case.config.output.get("format", "text")
        # Only use YAML config if CLI is default value
        if format_type == "text" and yaml_format in ["text", "json", "csv", "junit", "html"]:
            output_format = yaml_format

    # Store format in config for later use
    if test_case.config.output is None:
        test_case.config.output = {}
    test_case.config.output["format"] = output_format

    # Parse key=value overrides
    override_dict = {}
    if overrides:
        for override in overrides:
            if "=" in override:
                key, value = override.split("=", 1)
                override_dict[key] = value

    # Apply overrides to test case config
    if override_dict and test_case.config:
        for key, value in override_dict.items():
            if hasattr(test_case.config, key):
                setattr(test_case.config, key, value)
            elif test_case.config.active_profile in test_case.config.profiles:
                setattr(test_case.config.profiles[test_case.config.active_profile], key, value)

    # Determine WebSocket configuration
    # Priority: CLI args > YAML config > defaults
    ws_config_enabled = ws_server
    ws_config_host = ws_host
    ws_config_port = ws_port

    # Read from YAML config if available
    if test_case.config and test_case.config.websocket:
        yaml_ws = test_case.config.websocket
        # Only use YAML config if CLI args are not explicitly set
        if not ws_server and yaml_ws.get("enabled", False):
            ws_config_enabled = True
        if ws_host == "localhost":  # Default value, check if YAML has custom value
            ws_config_host = yaml_ws.get("host", "localhost")
        if ws_port == 8765:  # Default value, check if YAML has custom value
            ws_config_port = yaml_ws.get("port", 8765)

    # Check if WebSocket server mode is enabled
    if ws_config_enabled:
        return _execute_with_websocket(
            test_case, verbose, ws_config_host, ws_config_port, yaml_ws_config=test_case.config.websocket if test_case.config else None
        )

    # Determine Allure configuration
    # Priority: CLI args > YAML config > defaults (disabled)
    allure_enabled = allure
    allure_output_dir = allure_dir

    # Read from YAML config if available
    if test_case.config and test_case.config.output:
        yaml_output = test_case.config.output
        # Only use YAML config if CLI args are not explicitly set
        if not allure and yaml_output.get("allure", False):
            allure_enabled = True
        if allure_dir == "allure-results":  # Default value, check if YAML has custom value
            custom_dir = yaml_output.get("allure_dir")
            if custom_dir:
                allure_output_dir = custom_dir

    # Check if data-driven testing is enabled
    if (
        test_case.config
        and test_case.config.data_iterations
        and test_case.config.data_source
    ):
        result = _execute_data_driven_test(test_case, verbose)
    else:
        result = _execute_single_test(test_case, verbose)

    # Generate Allure report if enabled
    if allure_enabled:
        _generate_allure_report(test_case, result, allure_output_dir)

    return result


def _execute_with_websocket(
    test_case, verbose: bool = False, ws_host: str = "localhost", ws_port: int = 8765, yaml_ws_config: dict = None
) -> dict:
    """Execute test case with WebSocket server enabled.

    Args:
        test_case: Test case to execute
        verbose: Enable verbose output
        ws_host: WebSocket server host
        ws_port: WebSocket server port
        yaml_ws_config: WebSocket configuration from YAML

    Returns:
        Execution result as dictionary
    """
    from apirun.websocket.server import WebSocketServer
    from apirun.websocket.broadcaster import EventBroadcaster
    from apirun.websocket.notifier import WebSocketNotifier

    # Merge YAML config with defaults (YAML config takes priority)
    ws_settings = yaml_ws_config or {}
    enable_progress = ws_settings.get("send_progress", True)
    enable_logs = ws_settings.get("send_logs", True)
    enable_variables = ws_settings.get("send_variables", False)

    async def run_test_with_ws():
        """Async function to run WebSocket server and test execution."""
        # Create WebSocket server and broadcaster
        server = WebSocketServer(host=ws_host, port=ws_port)
        broadcaster = EventBroadcaster(server=server)

        # Start server and broadcaster
        await server.start()
        await broadcaster.start()

        print(f"WebSocket server started at ws://{ws_host}:{ws_port}")
        print("Connect a WebSocket client to receive real-time updates.")
        print("Press Ctrl+C to stop the server.\n")

        try:
            # Create notifier with config from YAML
            notifier = WebSocketNotifier(
                broadcaster=broadcaster,
                test_case_id=test_case.name,
                enable_progress=enable_progress,
                enable_logs=enable_logs,
                enable_variables=enable_variables,
            )

            # Execute test case with notifier
            result = _execute_single_test(test_case, verbose, notifier=notifier)

            # Wait a bit for final messages to be sent
            await asyncio.sleep(0.5)

            return result

        finally:
            # Stop broadcaster and server
            await broadcaster.stop()
            await server.stop()
            print(f"\nWebSocket server stopped.")

    # Run the async function
    return asyncio.run(run_test_with_ws())


def _execute_data_driven_test(test_case, verbose: bool = False) -> dict:
    """Execute data-driven test case.

    Args:
        test_case: Test case with data source configuration
        verbose: Enable verbose output

    Returns:
        Aggregated execution results
    """
    # Create data-driven iterator
    iterator = DataDrivenIterator(
        test_case,
        test_case.config.data_source,
        test_case.config.variable_prefix,
    )

    print(f"Executing: {test_case.name} (Data-Driven)")
    print(f"Description: {test_case.description}")
    print(f"Data iterations: {len(iterator)}")
    print(f"Steps: {len(test_case.steps)}")
    print()

    # Execute for each data row
    all_results = []
    total_passed = 0
    total_failed = 0

    for i, (data_row, augmented_test_case) in enumerate(iterator):
        print(f"\n--- Data Iteration #{i + 1} ---")
        if verbose:
            print(f"Data: {data_row}")

        result = _execute_single_test(augmented_test_case, verbose, notifier=None)
        all_results.append(result)

        # Update statistics
        if result["test_case"]["status"] == "passed":
            total_passed += 1
        else:
            total_failed += 1

    # Aggregate results
    aggregated_result = {
        "test_case": {
            "name": test_case.name,
            "status": "passed" if total_failed == 0 else "failed",
            "total_iterations": len(iterator),
            "passed_iterations": total_passed,
            "failed_iterations": total_failed,
            "pass_rate": (total_passed / len(iterator) * 100) if len(iterator) > 0 else 0,
        },
        "iterations": all_results,
    }

    # Print summary
    print(f"\n{'='*60}")
    print(f"Data-Driven Test Summary")
    print(f"Total Iterations: {len(iterator)}")
    print(f"Passed: {total_passed} ✓")
    print(f"Failed: {total_failed} ✗")
    print(f"Pass Rate: {aggregated_result['test_case']['pass_rate']:.1f}%")
    print(f"{'='*60}")

    return aggregated_result


def _execute_single_test(test_case, verbose: bool = False, notifier=None) -> dict:
    """Execute single test case.

    Args:
        test_case: Test case to execute
        verbose: Enable verbose output
        notifier: Optional WebSocket notifier for real-time updates

    Returns:
        Execution result as dictionary
    """
    # Check if output format is text (JSON/CSV/JUnit/HTML modes suppress text output)
    is_text_output = not (
        test_case.config
        and test_case.config.output
        and test_case.config.output.get("format") in ["json", "csv", "junit", "html"]
    )

    # Only print in text mode
    if is_text_output:
        # Print test case info
        print(f"Executing: {test_case.name}")
        print(f"Description: {test_case.description}")
        print(f"Steps: {len(test_case.steps)}")

    # Execute test case
    executor = TestCaseExecutor(test_case, notifier=notifier)
    result = executor.execute()

    # Only print summary in text mode
    if is_text_output:
        # Print summary
        print(f"\n{'='*60}")
        print(f"Status: {result['test_case']['status'].upper()}")
        print(f"Duration: {result['test_case']['duration']:.2f}s")
        print(f"Statistics:")
        print(f"  Total:   {result['statistics']['total_steps']}")
        print(f"  Passed:  {result['statistics']['passed_steps']} ✓")
        print(f"  Failed:  {result['statistics']['failed_steps']} ✗")
        print(f"  Skipped: {result['statistics']['skipped_steps']} ⊘")
        print(f"Pass Rate: {result['statistics']['pass_rate']:.1f}%")
        print(f"{'='*60}")

        # Print step results if verbose
        if verbose:
            print(f"\nStep Details:")
            for step in result["steps"]:
                status_icon = {
                    "success": "✓",
                    "failure": "✗",
                    "skipped": "⊘",
                    "error": "⚠",
                }.get(step["status"], "?")

                print(f"\n  {status_icon} {step['name']}")
                print(f"     Status: {step['status']}")

                if step.get("performance"):
                    perf = step["performance"]
                    total_time = perf.get("total_time", 0)
                    print(f"     Total Time: {total_time:.2f}ms")

                    # Display detailed timing breakdown if available
                    dns_time = perf.get("dns_time", 0)
                    tcp_time = perf.get("tcp_time", 0)
                    tls_time = perf.get("tls_time", 0)
                    server_time = perf.get("server_time", 0)
                    download_time = perf.get("download_time", 0)
                    upload_time = perf.get("upload_time", 0)

                    if any([dns_time, tcp_time, tls_time, server_time, download_time, upload_time]):
                        timing_details = []
                        if dns_time > 0:
                            timing_details.append(f"DNS: {dns_time:.2f}ms")
                        if tcp_time > 0:
                            timing_details.append(f"TCP: {tcp_time:.2f}ms")
                        if tls_time > 0:
                            timing_details.append(f"TLS: {tls_time:.2f}ms")
                        if server_time > 0:
                            timing_details.append(f"Server: {server_time:.2f}ms")
                        if download_time > 0:
                            timing_details.append(f"Download: {download_time:.2f}ms")
                        if upload_time > 0:
                            timing_details.append(f"Upload: {upload_time:.2f}ms")

                        print(f"     Breakdown: {' | '.join(timing_details)}")

                    # Display size information
                    size = perf.get("size", 0)
                    if size > 0:
                        size_kb = size / 1024
                        print(f"     Size: {size} bytes ({size_kb:.2f} KB)")

            if step.get("response", {}).get("status_code"):
                print(f"     Status Code: {step['response']['status_code']}")

            if step.get("error_info"):
                print(f"     Error: {step['error_info']['message']}")

    return result


def save_result(result: dict, output_path: str) -> None:
    """Save result to file (format based on extension or config).

    Args:
        result: Result dictionary
        output_path: Output file path
    """
    # Determine format from file extension or config
    format_from_config = "json"
    if result.get("test_case", {}).get("config", {}).get("output", {}).get("format"):
        format_from_config = result["test_case"]["config"]["output"]["format"]

    # Check file extension
    if output_path.endswith(".csv"):
        output_format = "csv"
    elif output_path.endswith(".json"):
        output_format = "json"
    elif output_path.endswith(".xml"):
        output_format = "junit"
    elif output_path.endswith(".html"):
        output_format = "html"
    else:
        # Use format from config
        output_format = format_from_config

    # Reconstruct TestCaseResult (needed for all formats)
    from apirun.core.models import TestCaseResult, StepResult, PerformanceMetrics, ErrorInfo
    from datetime import datetime

    start_time = datetime.fromisoformat(result["test_case"]["start_time"]) if result["test_case"].get("start_time") else datetime.now()
    end_time = datetime.fromisoformat(result["test_case"]["end_time"]) if result["test_case"].get("end_time") else datetime.now()

    # Reconstruct step results for formats that need them
    step_results = []
    for step_data in result.get("steps", []):
        step_result = StepResult(
            name=step_data["name"],
            status=step_data["status"],
            response=step_data.get("response"),
            extracted_vars=step_data.get("extracted_vars", {}),
            validation_results=step_data.get("validations", []),
            performance=None,
            error_info=None,
        )

        # Add performance if available
        if step_data.get("performance"):
            perf_data = step_data["performance"]
            step_result.performance = PerformanceMetrics(
                total_time=perf_data.get("total_time", 0),
                dns_time=perf_data.get("dns_time", 0),
                tcp_time=perf_data.get("tcp_time", 0),
                tls_time=perf_data.get("tls_time", 0),
                server_time=perf_data.get("server_time", 0),
                download_time=perf_data.get("download_time", 0),
                upload_time=perf_data.get("upload_time", 0),
                size=perf_data.get("size", 0),
            )

        # Add error info if available
        if step_data.get("error_info"):
            err_data = step_data["error_info"]
            from apirun.core.models import ErrorCategory
            category_map = {
                "assertion": ErrorCategory.ASSERTION,
                "network": ErrorCategory.NETWORK,
                "timeout": ErrorCategory.TIMEOUT,
                "parsing": ErrorCategory.PARSING,
                "business": ErrorCategory.BUSINESS,
                "system": ErrorCategory.SYSTEM,
            }
            category = category_map.get(err_data.get("category", ""), ErrorCategory.SYSTEM)
            step_result.error_info = ErrorInfo(
                type=err_data.get("type", "UnknownError"),
                category=category,
                message=err_data.get("message", ""),
                suggestion=err_data.get("suggestion", ""),
            )

        # Parse timestamps
        if step_data.get("start_time"):
            step_result.start_time = datetime.fromisoformat(step_data["start_time"])
        if step_data.get("end_time"):
            step_result.end_time = datetime.fromisoformat(step_data["end_time"])

        step_result.retry_count = step_data.get("retry_count", 0)
        step_results.append(step_result)

    test_case_result = TestCaseResult(
        name=result["test_case"]["name"],
        status=result["test_case"]["status"],
        start_time=start_time,
        end_time=end_time,
        duration=result["test_case"]["duration"],
        total_steps=result["statistics"]["total_steps"],
        passed_steps=result["statistics"]["passed_steps"],
        failed_steps=result["statistics"]["failed_steps"],
        skipped_steps=result["statistics"]["skipped_steps"],
        step_results=step_results,
        final_variables=result.get("final_variables", {}),
        error_info=None,
    )

    # Save based on format
    if output_format == "csv":
        from apirun.result.collector import ResultCollector
        collector = ResultCollector()
        collector.save_csv(test_case_result, output_path)

    elif output_format == "junit":
        from apirun.result.junit_exporter import JUnitExporter
        exporter = JUnitExporter()
        exporter.save_junit_xml(test_case_result, output_path)

    elif output_format == "html":
        from apirun.result.html_exporter import HTMLExporter
        exporter = HTMLExporter()
        exporter.save_html(test_case_result, output_path)

    else:
        # Default to JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


def _generate_allure_report(test_case, result: dict, allure_dir: str):
    """Generate Allure report from test result.

    Args:
        test_case: Test case object
        result: Test execution result dictionary
        allure_dir: Allure results directory
    """
    from apirun.result.allure_collector import AllureResultCollector
    from apirun.result.collector import ResultCollector
    from apirun.core.models import TestCaseResult

    # Create Allure collector
    collector = AllureResultCollector(output_dir=allure_dir)

    # Reconstruct TestCaseResult from dict
    # This is a simplified reconstruction
    from datetime import datetime
    from apirun.core.models import StepResult, PerformanceMetrics, ErrorInfo

    step_results = []
    for step_data in result.get("steps", []):
        # Reconstruct StepResult
        step_result = StepResult(
            name=step_data["name"],
            status=step_data["status"],
            response=step_data.get("response"),
            extracted_vars=step_data.get("extracted_vars", {}),
            validation_results=step_data.get("validations", []),
            performance=None,
            error_info=None,
        )

        # Add performance if available
        if step_data.get("performance"):
            perf_data = step_data["performance"]
            step_result.performance = PerformanceMetrics(
                total_time=perf_data.get("total_time", 0),
                dns_time=perf_data.get("dns_time", 0),
                tcp_time=perf_data.get("tcp_time", 0),
                tls_time=perf_data.get("tls_time", 0),
                server_time=perf_data.get("server_time", 0),
                download_time=perf_data.get("download_time", 0),
                upload_time=perf_data.get("upload_time", 0),
                size=perf_data.get("size", 0),
            )

        # Add error info if available
        if step_data.get("error_info"):
            err_data = step_data["error_info"]
            from apirun.core.models import ErrorCategory
            # Map category string to enum
            category_map = {
                "assertion": ErrorCategory.ASSERTION,
                "network": ErrorCategory.NETWORK,
                "timeout": ErrorCategory.TIMEOUT,
                "parsing": ErrorCategory.PARSING,
                "business": ErrorCategory.BUSINESS,
                "system": ErrorCategory.SYSTEM,
            }
            category = category_map.get(err_data.get("category", ""), ErrorCategory.SYSTEM)

            step_result.error_info = ErrorInfo(
                type=err_data.get("type", "UnknownError"),
                category=category,
                message=err_data.get("message", ""),
                suggestion=err_data.get("suggestion", ""),
            )

        # Parse timestamps
        if step_data.get("start_time"):
            step_result.start_time = datetime.fromisoformat(step_data["start_time"])
        if step_data.get("end_time"):
            step_result.end_time = datetime.fromisoformat(step_data["end_time"])

        step_result.retry_count = step_data.get("retry_count", 0)
        step_results.append(step_result)

    # Reconstruct TestCaseResult
    test_result = TestCaseResult(
        name=result["test_case"]["name"],
        status=result["test_case"]["status"],
        start_time=datetime.fromisoformat(result["test_case"]["start_time"]),
        end_time=datetime.fromisoformat(result["test_case"]["end_time"]),
        duration=result["test_case"]["duration"],
        total_steps=result["statistics"]["total_steps"],
        passed_steps=result["statistics"]["passed_steps"],
        failed_steps=result["statistics"]["failed_steps"],
        skipped_steps=result["statistics"]["skipped_steps"],
        step_results=step_results,
        final_variables=result.get("final_variables", {}),
        error_info=None,
    )

    # Generate Allure result file
    result_file = collector.collect(test_case, test_result)

    # Generate supporting files
    collector.generate_environment_file()
    collector.generate_categories_file()

    # Print message
    print(f"\n✓ Allure report generated: {result_file}")
    print(f"  Results directory: {allure_dir}")
    print(f"  View report: allure open {allure_dir}")


if __name__ == "__main__":
    sys.exit(main())
