"""Command Line Interface for Sisyphus API Engine.

This module provides the CLI entry point for running test cases.
Following Google Python Style Guide.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from apirun.cli_help_i18n import (
    ARGUMENT_MAPPING,
    get_help_messages,
    get_validate_help_messages,
)
from apirun.data_driven.iterator import DataDrivenIterator
from apirun.executor.test_case_executor import TestCaseExecutor
from apirun.parser.v2_yaml_parser import V2YamlParser, YamlParseError


def show_help(parser: argparse.ArgumentParser, lang: str = 'en') -> None:
    """Display help message in specified language.

    Args:
        parser: Argument parser object
        lang: Language code ('en' for English, 'zh' for Chinese)
    """
    messages = get_help_messages(lang)

    print(f'\n{messages["description"]}\n')
    if lang == 'zh':
        print('用法:')
        print('  sisyphus --cases <路径...> [选项]\n')
        print('参数:')
    else:
        print('Usage:')
        print('  sisyphus --cases <paths...> [options]\n')
        print('Arguments:')

    # Format and display arguments
    for action in parser._actions:
        if action.dest in ['help', '中文帮助']:
            continue

        # Get option strings
        opts = ', '.join(action.option_strings)

        # Get help text from messages based on language
        help_text = ''
        if action.dest in ARGUMENT_MAPPING:
            arg_key = ARGUMENT_MAPPING[action.dest]
            help_text = messages['args'].get(arg_key, '')
        else:
            # Fallback to action's help text (should be English only)
            help_text = action.help or ''

        # Format default values
        if (
            action.default is not None
            and action.default != '==SUPPRESS=='
            and action.default != []
        ):
            if action.dest in ['ws_host', 'ws_port', 'allure_dir', 'format']:
                if lang == 'zh':
                    if isinstance(action.default, str):
                        help_text += f' (默认: {action.default})'
                    elif isinstance(action.default, int):
                        help_text += f' (默认: {action.default})'
                else:
                    if isinstance(action.default, str):
                        help_text += f' (default: {action.default})'
                    elif isinstance(action.default, int):
                        help_text += f' (default: {action.default})'

        # Display the argument
        if opts:
            print(f'  {opts.ljust(25)} {help_text}')

    print(f'\n{messages["epilog"]}')

    # Show additional help options
    if lang == 'zh':
        print('帮助选项:')
        print('  -h, --help          显示英文帮助')
        print('  -H, --中文帮助      显示中文帮助')
    else:
        print('Help Options:')
        print('  -h, --help          Show help in English')
        print('  -H, --中文帮助      Show help in Chinese')
    print()


def show_validate_help(parser: argparse.ArgumentParser, lang: str = 'en') -> None:
    """Display validation command help message in specified language.

    Args:
        parser: Argument parser object
        lang: Language code ('en' for English, 'zh' for Chinese)
    """
    messages = get_validate_help_messages(lang)

    print(f'\n{messages["description"]}\n')
    if lang == 'zh':
        print('用法:')
        print('  sisyphus-validate <路径>... [选项]\n')
        print('参数:')
    else:
        print('Usage:')
        print('  sisyphus-validate <paths>... [options]\n')
        print('Arguments:')

    # Format and display arguments
    for action in parser._actions:
        if action.dest in ['help', '中文帮助']:
            continue

        # Get option strings or positional name
        if action.option_strings:
            opts = ', '.join(action.option_strings)
        else:
            opts = action.dest.upper()

        # Get help text from messages based on language
        help_text = ''
        if action.dest == 'paths':
            help_text = messages['args'].get('paths', '')
        elif action.dest == 'quiet':
            help_text = messages['args'].get('-q/--quiet', '')
        else:
            help_text = action.help or ''

        # Display the argument
        print(f'  {opts.ljust(25)} {help_text}')

    print(f'\n{messages["epilog"]}')

    # Show additional help options
    if lang == 'zh':
        print('帮助选项:')
        print('  -h, --help          显示英文帮助')
        print('  -H, --中文帮助      显示中文帮助')
    else:
        print('Help Options:')
        print('  -h, --help          Show help in English')
        print('  -H, --中文帮助      Show help in Chinese')
    print()


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description='Sisyphus API Engine - Enterprise-grade API Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_help_messages('en')['epilog'],
        add_help=False,  # We'll add help manually
    )

    # Add standard help
    parser.add_argument(
        '-h',
        '--help',
        action='store_true',
        help='Show help message',
    )

    # Add Chinese help
    parser.add_argument(
        '-H',
        '--中文帮助',
        action='store_true',
        help='Show help in Chinese',
    )

    parser.add_argument(
        '--cases',
        type=str,
        nargs='+',
        required=True,
        help='Path(s) to YAML test case file(s) or directory/directories',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Output file path for JSON results',
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Enable verbose output',
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Set logging level (debug, info, warning, error)',
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path for detailed execution logs',
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate YAML syntax without execution',
    )

    parser.add_argument(
        '--profile',
        type=str,
        help='Active profile name (overrides config)',
    )

    parser.add_argument(
        '--ws-server',
        action='store_true',
        help='Enable WebSocket server for real-time updates',
    )

    parser.add_argument(
        '--ws-host',
        type=str,
        default='localhost',
        help='WebSocket server host',
    )

    parser.add_argument(
        '--ws-port',
        type=int,
        default=8765,
        help='WebSocket server port',
    )

    parser.add_argument(
        '--env-prefix',
        type=str,
        help='Environment variable prefix to load',
    )

    parser.add_argument(
        '--override',
        type=str,
        action='append',
        help="Configuration overrides in 'key=value' format",
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with variable tracking',
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['text', 'json', 'csv', 'junit', 'html'],
        default='text',
        help='Output format: text/json/csv/junit/html',
    )

    parser.add_argument(
        '--report-lang',
        type=str,
        choices=['en', 'zh'],
        default='en',
        help='Report language: en (English) / zh (中文)',
    )

    parser.add_argument(
        '--lang',
        type=str,
        choices=['en', 'zh'],
        default='zh',
        help='CLI output language: en (English) / zh (中文, default)',
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output',
    )

    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='Disable emoji in output',
    )

    parser.add_argument(
        '--allure',
        action='store_true',
        help='Generate Allure report',
    )

    parser.add_argument(
        '--allure-dir',
        type=str,
        default='allure-results',
        help='Allure results directory',
    )

    parser.add_argument(
        '--allure-clean',
        action='store_true',
        default=True,
        help='Clean Allure results directory before generating (default: True)',
    )

    parser.add_argument(
        '--allure-no-clean',
        action='store_false',
        dest='allure_clean',
        help='Keep previous Allure results (accumulate data)',
    )

    # Check for help flags first before parsing required arguments
    import sys

    if '-H' in sys.argv or '--中文帮助' in sys.argv:
        show_help(parser, lang='zh')
        return 0
    elif '-h' in sys.argv or '--help' in sys.argv:
        show_help(parser, lang='en')
        return 0

    # Parse args normally (now --cases is required)
    args = parser.parse_args()

    try:
        if args.validate:
            # For validation, collect all files and validate them
            yaml_files = collect_yaml_files(args.cases)
            if not yaml_files:
                print('Error: No YAML files found to validate', file=sys.stderr)
                return 1

            all_valid = True
            parser = V2YamlParser()

            for yaml_file in yaml_files:
                print(f'Validating: {yaml_file}')
                errors = parser.validate_yaml(str(yaml_file))

                if errors:
                    all_valid = False
                    print('  ❌ Validation failed:')
                    for error in errors:
                        print(f'    - {error}')
                else:
                    print('  ✓ Valid')

            if all_valid:
                print('\n✓ All YAML files are valid!')
                return 0
            else:
                print('\n❌ Some YAML files have validation errors.')
                return 1

        # For test execution, collect all YAML files
        yaml_files = collect_yaml_files(args.cases)
        if not yaml_files:
            print('Error: No YAML files found', file=sys.stderr)
            return 1

        # Import formatter
        from apirun.utils.console_output import create_formatter

        # Create output formatter
        formatter = create_formatter(
            use_color=not args.no_color,
            use_emoji=not args.no_emoji,
            lang=args.lang,
            verbose=args.verbose,
        )

        found_text = formatter.style.get_text(
            f'找到 {len(yaml_files)} 个测试用例文件',
            f'Found {len(yaml_files)} test case file(s)',
        )
        print(f'\n{formatter.style.info(found_text)}\n')

        # Track overall results
        total_passed = 0
        total_failed = 0
        all_results = []

        # Execute each test case
        for i, yaml_file in enumerate(yaml_files, 1):
            if len(yaml_files) > 1 and i > 1:
                formatter.print_file_separator()

            try:
                # 批量运行时，只在第一个测试用例执行前清理 Allure 目录
                # 当批量运行多个测试用例时，后续用例应该追加结果而不是清理
                current_allure_clean = args.allure_clean and (i == 1)

                # 批量运行时，静默生成 Allure 报告，最后统一输出提示信息
                current_allure_silent = len(yaml_files) > 1

                result = execute_test_case(
                    str(yaml_file),
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
                    current_allure_clean,
                    current_allure_silent,
                    lang=args.lang,
                    use_color=not args.no_color,
                    use_emoji=not args.no_emoji,
                    log_level=args.log_level,
                    log_file=args.log_file,
                )
                all_results.append(result)

                # Track statistics
                if result and result.get('test_case', {}).get('status') == 'passed':
                    total_passed += 1
                else:
                    total_failed += 1

            except Exception as e:
                print(f'Error executing {yaml_file}: {e}', file=sys.stderr)
                total_failed += 1
                if args.verbose:
                    import traceback

                    traceback.print_exc()
                # Add None to maintain list index
                all_results.append(None)

        # Print overall summary if multiple files
        if len(yaml_files) > 1:
            # 使用 formatter 输出总体概览
            formatter.print_overall_summary(
                total_tests=len(yaml_files),
                passed_tests=total_passed,
                failed_tests=total_failed,
            )

            # 如果启用了 Allure，统一输出提示信息
            if args.allure:
                print('\n✓ Allure 报告数据已生成')
                print(f'  结果目录: {args.allure_dir}')
                print(f'  查看报告: allure serve {args.allure_dir}')
                print(
                    f'  或生成 HTML: allure generate {args.allure_dir} --clean -o allure-report'
                )

            # Return non-zero if any test failed
            return 0 if total_failed == 0 else 1

        # Handle output based on format (single file mode)
        result = all_results[0] if all_results else None

        # If result is None (execution failed), return error code
        if result is None:
            return 1

        if args.format == 'json':
            # Determine if we should output compact or full JSON
            # Check verbose flag (from CLI or YAML config)
            use_verbose = args.verbose
            if not use_verbose and result.get('test_case', {}).get('config', {}).get(
                'verbose'
            ):
                use_verbose = True

            if use_verbose:
                # Full JSON output (all information)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                # Ultra-compact JSON output (only response content)
                api_responses = []

                # Extract only response content from steps
                for step in result.get('steps', []):
                    if step.get('response'):
                        response_item = {
                            'step': step['name'],
                            'response': step['response'],
                        }
                        api_responses.append(response_item)

                print(json.dumps(api_responses, ensure_ascii=False, indent=2))

        elif args.format == 'csv':
            # CSV output
            from datetime import datetime

            from apirun.core.models import (
                PerformanceMetrics,
                StepResult,
                TestCaseResult,
            )
            from apirun.result.json_exporter import JSONExporter

            # Reconstruct TestCaseResult from dict
            start_time = (
                datetime.fromisoformat(result['test_case']['start_time'])
                if result['test_case'].get('start_time')
                else datetime.now()
            )
            end_time = (
                datetime.fromisoformat(result['test_case']['end_time'])
                if result['test_case'].get('end_time')
                else datetime.now()
            )

            # Reconstruct step results for CSV
            step_results = []
            for step_data in result.get('steps', []):
                step_start = (
                    datetime.fromisoformat(step_data['start_time'])
                    if step_data.get('start_time')
                    else None
                )
                step_end = (
                    datetime.fromisoformat(step_data['end_time'])
                    if step_data.get('end_time')
                    else None
                )

                step_perf = None
                if args.verbose and step_data.get('performance'):
                    perf_data = step_data['performance']
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get('total_time', 0),
                        dns_time=perf_data.get('dns_time', 0),
                        tcp_time=perf_data.get('tcp_time', 0),
                        tls_time=perf_data.get('tls_time', 0),
                        server_time=perf_data.get('server_time', 0),
                        download_time=perf_data.get('download_time', 0),
                        size=perf_data.get('size', 0),
                    )

                step_result = StepResult(
                    name=step_data['name'],
                    status=step_data['status'],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get('response'),
                    performance=step_perf,
                    error_info=None,
                )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result['test_case']['name'],
                status=result['test_case']['status'],
                start_time=start_time,
                end_time=end_time,
                duration=result['test_case']['duration'],
                total_steps=result['statistics']['total_steps'],
                passed_steps=result['statistics']['passed_steps'],
                failed_steps=result['statistics']['failed_steps'],
                skipped_steps=result['statistics']['skipped_steps'],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            collector = JSONExporter()
            # Determine if we should use verbose mode
            use_verbose = args.verbose
            if not use_verbose and result.get('test_case', {}).get('config', {}).get(
                'verbose'
            ):
                use_verbose = True

            csv_output = collector.to_csv(test_case_result, verbose=use_verbose)
            print(csv_output, end='')

        elif args.format == 'junit':
            # JUnit XML output
            from datetime import datetime

            from apirun.core.models import (
                PerformanceMetrics,
                StepResult,
                TestCaseResult,
            )
            from apirun.result.junit_exporter import JUnitExporter

            # Reconstruct TestCaseResult with full step results
            start_time = (
                datetime.fromisoformat(result['test_case']['start_time'])
                if result['test_case'].get('start_time')
                else datetime.now()
            )
            end_time = (
                datetime.fromisoformat(result['test_case']['end_time'])
                if result['test_case'].get('end_time')
                else datetime.now()
            )

            # Reconstruct step results
            step_results = []
            for step_data in result.get('steps', []):
                step_start = (
                    datetime.fromisoformat(step_data['start_time'])
                    if step_data.get('start_time')
                    else None
                )
                step_end = (
                    datetime.fromisoformat(step_data['end_time'])
                    if step_data.get('end_time')
                    else None
                )
                step_perf = None
                if step_data.get('performance'):
                    perf_data = step_data['performance']
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get('total_time', 0),
                        dns_time=perf_data.get('dns_time', 0),
                        tcp_time=perf_data.get('tcp_time', 0),
                        tls_time=perf_data.get('tls_time', 0),
                        server_time=perf_data.get('server_time', 0),
                        download_time=perf_data.get('download_time', 0),
                        size=perf_data.get('size', 0),
                    )

                step_result = StepResult(
                    name=step_data['name'],
                    status=step_data['status'],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get('response'),
                    performance=step_perf,
                    error_info=None,  # We'll skip error details in non-verbose mode
                )

                # Only add detailed error info if verbose
                if args.verbose and step_data.get('error_info'):
                    from apirun.core.models import ErrorCategory, ErrorInfo

                    error_data = step_data['error_info']
                    step_result.error_info = ErrorInfo(
                        type=error_data.get('type', 'UNKNOWN'),
                        message=error_data.get('message', ''),
                        category=ErrorCategory(error_data.get('category', 'SYSTEM')),
                    )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result['test_case']['name'],
                status=result['test_case']['status'],
                start_time=start_time,
                end_time=end_time,
                duration=result['test_case']['duration'],
                total_steps=result['statistics']['total_steps'],
                passed_steps=result['statistics']['passed_steps'],
                failed_steps=result['statistics']['failed_steps'],
                skipped_steps=result['statistics']['skipped_steps'],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            exporter = JUnitExporter()
            junit_xml = exporter.to_junit_xml(test_case_result)
            print(junit_xml, end='')

        elif args.format == 'html':
            # HTML output
            from datetime import datetime

            from apirun.core.models import (
                PerformanceMetrics,
                StepResult,
                TestCaseResult,
            )
            from apirun.result.html_exporter import HTMLExporter

            # Reconstruct TestCaseResult with full step results
            start_time = (
                datetime.fromisoformat(result['test_case']['start_time'])
                if result['test_case'].get('start_time')
                else datetime.now()
            )
            end_time = (
                datetime.fromisoformat(result['test_case']['end_time'])
                if result['test_case'].get('end_time')
                else datetime.now()
            )

            # Reconstruct step results based on verbose mode
            step_results = []
            for step_data in result.get('steps', []):
                step_start = (
                    datetime.fromisoformat(step_data['start_time'])
                    if step_data.get('start_time')
                    else None
                )
                step_end = (
                    datetime.fromisoformat(step_data['end_time'])
                    if step_data.get('end_time')
                    else None
                )

                step_perf = None
                if args.verbose and step_data.get('performance'):
                    perf_data = step_data['performance']
                    step_perf = PerformanceMetrics(
                        total_time=perf_data.get('total_time', 0),
                        dns_time=perf_data.get('dns_time', 0),
                        tcp_time=perf_data.get('tcp_time', 0),
                        tls_time=perf_data.get('tls_time', 0),
                        server_time=perf_data.get('server_time', 0),
                        download_time=perf_data.get('download_time', 0),
                        size=perf_data.get('size', 0),
                    )

                step_result = StepResult(
                    name=step_data['name'],
                    status=step_data['status'],
                    start_time=step_start,
                    end_time=step_end,
                    response=step_data.get('response') if args.verbose else None,
                    performance=step_perf,
                    error_info=None,
                )

                # Only add detailed error info if verbose
                if args.verbose and step_data.get('error_info'):
                    from apirun.core.models import ErrorCategory, ErrorInfo

                    error_data = step_data['error_info']
                    step_result.error_info = ErrorInfo(
                        type=error_data.get('type', 'UNKNOWN'),
                        message=error_data.get('message', ''),
                        category=ErrorCategory(error_data.get('category', 'SYSTEM')),
                    )

                step_results.append(step_result)

            test_case_result = TestCaseResult(
                name=result['test_case']['name'],
                status=result['test_case']['status'],
                start_time=start_time,
                end_time=end_time,
                duration=result['test_case']['duration'],
                total_steps=result['statistics']['total_steps'],
                passed_steps=result['statistics']['passed_steps'],
                failed_steps=result['statistics']['failed_steps'],
                skipped_steps=result['statistics']['skipped_steps'],
                step_results=step_results,
                final_variables={},
                error_info=None,
            )

            exporter = HTMLExporter(language=args.report_lang)
            html_output = exporter.to_html(test_case_result)
            print(html_output, end='')

        # Save result if output path specified (either in YAML or CLI)
        output_path = args.output

        # Check if result is valid before accessing
        if result is None:
            return 1

        if not output_path and result.get('test_case', {}).get('config', {}).get(
            'output', {}
        ).get('path'):
            # Use output path from YAML config
            output_path = result['test_case']['config']['output']['path']

        if output_path:
            save_result(result, output_path, args.report_lang)
            # Only print save message in text mode
            if args.format in ['text'] and (
                args.verbose
                or result.get('test_case', {}).get('config', {}).get('verbose')
            ):
                print(f'\nResults saved to: {output_path}')

        return 0

    except FileNotFoundError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1
    except YamlParseError as e:
        print(f'Parse Error: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'Unexpected Error: {e}', file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def validate_main() -> int:
    """CLI entry point for validation-only mode.

    This is a dedicated command for validating YAML syntax without execution.
    Uses the enhanced validator with keyword checking and beautiful output.

    Returns:
        Exit code (0 for valid, non-zero for invalid)
    """
    parser = argparse.ArgumentParser(
        description='Sisyphus API Engine - YAML Validator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_validate_help_messages('en')['epilog'],
        add_help=False,
    )

    # Add help options
    parser.add_argument(
        '-h',
        '--help',
        action='store_true',
        help='Show help message',
    )

    parser.add_argument(
        '-H',
        '--中文帮助',
        action='store_true',
        help='Show help in Chinese',
    )

    parser.add_argument(
        'paths',
        type=str,
        nargs='+',
        help='Path(s) to YAML file(s) or directory',
    )

    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='Quiet mode, only show summary',
    )

    # Check for help flags first
    import sys

    if '-H' in sys.argv or '--中文帮助' in sys.argv:
        show_validate_help(parser, lang='zh')
        return 0
    elif '-h' in sys.argv or '--help' in sys.argv:
        show_validate_help(parser, lang='en')
        return 0

    # Parse args normally
    args = parser.parse_args()

    try:
        from apirun.validator.yaml_validator import validate_yaml_files

        show_details = not args.quiet
        exit_code, _ = validate_yaml_files(args.paths, show_details=show_details)

        return exit_code

    except Exception as e:
        print(f'意外错误: {e}', file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def collect_yaml_files(paths: list) -> list:
    """Collect all YAML files from given paths.

    Args:
        paths: List of file or directory paths

    Returns:
        List of Path objects for all YAML files found
    """
    yaml_files = []
    for path_str in paths:
        path = Path(path_str)

        if not path.exists():
            print(f'Warning: Path not found: {path_str}', file=sys.stderr)
            continue

        if path.is_file():
            if path.suffix in ['.yaml', '.yml']:
                yaml_files.append(path)
            else:
                print(f'Warning: Skipping non-YAML file: {path_str}', file=sys.stderr)
        elif path.is_dir():
            found_files = list(path.glob('**/*.yaml')) + list(path.glob('**/*.yml'))
            if found_files:
                yaml_files.extend(found_files)
            else:
                print(f'Warning: No YAML files found in directory: {path_str}')
        else:
            print(f'Warning: Invalid path: {path_str}', file=sys.stderr)

    return sorted(yaml_files)


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
        yaml_files = list(path.glob('**/*.yaml'))
    else:
        print(f'Error: Path not found: {case_path}', file=sys.stderr)
        return 1

    all_valid = True
    for yaml_file in yaml_files:
        print(f'Validating: {yaml_file}')
        errors = parser.validate_yaml(str(yaml_file))

        if errors:
            all_valid = False
            print('  ❌ Validation failed:')
            for error in errors:
                print(f'    - {error}')
        else:
            print('  ✓ Valid')

    return 0 if all_valid else 1


def execute_test_case(
    case_path: str,
    verbose: bool = False,
    profile: str | None = None,
    ws_server: bool = False,
    ws_host: str = 'localhost',
    ws_port: int = 8765,
    env_prefix: str | None = None,
    overrides: list | None = None,
    debug: bool = False,
    output: str | None = None,
    format_type: str = 'text',
    allure: bool = False,
    allure_dir: str = 'allure-results',
    allure_clean: bool = True,
    allure_silent: bool = False,
    lang: str = 'zh',
    use_color: bool = True,
    use_emoji: bool = True,
    log_level: str = 'info',
    log_file: str | None = None,
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
        overrides: Variable overrides from command line
        debug: Enable debug mode
        output: Output file path
        format_type: Output format (text/json/csv/html/junit)
        allure: Generate Allure report
        allure_dir: Allure results directory
        allure_clean: Clean allure directory before execution
        allure_silent: Suppress Allure generation messages
        lang: Output language (zh/en)
        use_color: Use colored output
        use_emoji: Use emoji in output
        log_level: Logging level (debug/info/warning/error)
        log_file: Log file path
        overrides: Configuration overrides (list of "key=value" strings)
        debug: Enable debug mode (overrides YAML config)
        output: Output file path (overrides YAML config)
        format_type: Output format (text/json, overrides YAML config)
        allure: Generate Allure report (overrides YAML config)
        allure_dir: Allure results directory (overrides YAML config)
        allure_clean: Clean Allure results before generating (default: True)
        allure_silent: Suppress Allure output messages (default: False)

    Returns:
        Execution result as dictionary
    """
    # Parse YAML first
    parser = V2YamlParser()
    test_case = parser.parse(case_path)

    # Initialize logging system after parsing
    from apirun.utils.logger import LogConfig, get_logger

    # Determine if we should suppress console logs (for clean text output)
    # Check if output format is text
    is_text_output = not (
        test_case.config
        and test_case.config.output
        and test_case.config.output.get('format') in ['json', 'csv', 'junit', 'html']
    )

    # For text output mode, always use WARNING to suppress INFO/DEBUG logs
    # This ensures only the Rich-formatted output is shown
    # For non-text modes (JSON/CSV/JUnit/HTML), use the specified log level
    if is_text_output:
        effective_log_level = 'warning'
    else:
        effective_log_level = 'debug' if verbose else log_level

    # Setup logger with console_output disabled for text mode
    # This prevents duplicate output (old logs + new Rich format)

    logger_config = LogConfig(
        level=effective_log_level.upper(),
        log_file=log_file,
        console_output=not is_text_output,  # Disable console logs in text mode
        include_timestamps=True,
        include_variable_changes=True,
        include_performance=True,
    )

    # Set global logger with this config
    logger = get_logger(config=logger_config)

    # Only log these messages to file if specified
    if log_file:
        logger.info(f'📋 开始执行测试用例: {case_path}')
        logger.info(f'📄 日志文件: {log_file}')

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
        test_case.config.debug['enabled'] = True

    if env_prefix:
        if test_case.config.env_vars is None:
            test_case.config.env_vars = {}
        test_case.config.env_vars['prefix'] = env_prefix

    if output:
        if test_case.config.output is None:
            test_case.config.output = {}
        test_case.config.output['path'] = output

    # Determine output format configuration
    # Priority: CLI args > YAML config > defaults (text)
    output_format = format_type
    if test_case.config and test_case.config.output:
        yaml_format = test_case.config.output.get('format', 'text')
        # Only use YAML config if CLI is default value
        if format_type == 'text' and yaml_format in [
            'text',
            'json',
            'csv',
            'junit',
            'html',
        ]:
            output_format = yaml_format

    # Store format in config for later use
    if test_case.config.output is None:
        test_case.config.output = {}
    test_case.config.output['format'] = output_format

    # Parse key=value overrides
    override_dict = {}
    if overrides:
        for override in overrides:
            if '=' in override:
                key, value = override.split('=', 1)
                override_dict[key] = value

    # Apply overrides to test case config
    if override_dict and test_case.config:
        for key, value in override_dict.items():
            if hasattr(test_case.config, key):
                setattr(test_case.config, key, value)
            elif test_case.config.active_profile in test_case.config.profiles:
                setattr(
                    test_case.config.profiles[test_case.config.active_profile],
                    key,
                    value,
                )

    # Determine WebSocket configuration
    # Priority: CLI args > YAML config > defaults
    ws_config_enabled = ws_server
    ws_config_host = ws_host
    ws_config_port = ws_port

    # Read from YAML config if available
    if test_case.config and test_case.config.websocket:
        yaml_ws = test_case.config.websocket
        # Only use YAML config if CLI args are not explicitly set
        if not ws_server and yaml_ws.get('enabled', False):
            ws_config_enabled = True
        if ws_host == 'localhost':  # Default value, check if YAML has custom value
            ws_config_host = yaml_ws.get('host', 'localhost')
        if ws_port == 8765:  # Default value, check if YAML has custom value
            ws_config_port = yaml_ws.get('port', 8765)

    # Check if WebSocket server mode is enabled
    if ws_config_enabled:
        return _execute_with_websocket(
            test_case,
            verbose,
            ws_config_host,
            ws_config_port,
            yaml_ws_config=test_case.config.websocket if test_case.config else None,
        )

    # Determine Allure configuration
    # Priority: CLI args > YAML config > defaults (disabled)
    allure_enabled = allure
    allure_output_dir = allure_dir

    # Read from YAML config if available
    if test_case.config and test_case.config.output:
        yaml_output = test_case.config.output
        # Only use YAML config if CLI args are not explicitly set
        if not allure and yaml_output.get('allure', False):
            allure_enabled = True
        if (
            allure_dir == 'allure-results'
        ):  # Default value, check if YAML has custom value
            custom_dir = yaml_output.get('allure_dir')
            if custom_dir:
                allure_output_dir = custom_dir

    # Check if data-driven testing is enabled
    if (
        test_case.config
        and test_case.config.data_iterations
        and test_case.config.data_source
    ):
        result = _execute_data_driven_test(
            test_case, verbose, lang=lang, use_color=use_color, use_emoji=use_emoji
        )
    else:
        result = _execute_single_test(
            test_case, verbose, lang=lang, use_color=use_color, use_emoji=use_emoji
        )

    # Generate Allure report if enabled
    if allure_enabled:
        _generate_allure_report(
            test_case, result, allure_output_dir, allure_clean, silent=allure_silent
        )

    return result


def _execute_with_websocket(
    test_case,
    verbose: bool = False,
    ws_host: str = 'localhost',
    ws_port: int = 8765,
    yaml_ws_config: dict = None,
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
    from apirun.websocket.broadcaster import EventBroadcaster
    from apirun.websocket.notifier import WebSocketNotifier
    from apirun.websocket.server import WebSocketServer

    # Merge YAML config with defaults (YAML config takes priority)
    ws_settings = yaml_ws_config or {}
    enable_progress = ws_settings.get('send_progress', True)
    enable_logs = ws_settings.get('send_logs', True)
    enable_variables = ws_settings.get('send_variables', False)

    async def run_test_with_ws():
        """Async function to run WebSocket server and test execution."""
        # Create WebSocket server and broadcaster
        server = WebSocketServer(host=ws_host, port=ws_port)
        broadcaster = EventBroadcaster(server=server)

        # Start server and broadcaster
        await server.start()
        await broadcaster.start()

        print(f'WebSocket server started at ws://{ws_host}:{ws_port}')
        print('Connect a WebSocket client to receive real-time updates.')
        print('Press Ctrl+C to stop the server.\n')

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
            print('\nWebSocket server stopped.')

    # Run the async function
    return asyncio.run(run_test_with_ws())


def _execute_data_driven_test(
    test_case,
    verbose: bool = False,
    lang: str = 'zh',
    use_color: bool = True,
    use_emoji: bool = True,
) -> dict:
    """Execute data-driven test case.

    Args:
        test_case: Test case with data source configuration
        verbose: Enable verbose output
        lang: Language code ('zh' or 'en')
        use_color: Enable colored output
        use_emoji: Enable emoji

    Returns:
        Aggregated execution results
    """
    # Create data-driven iterator
    iterator = DataDrivenIterator(
        test_case,
        test_case.config.data_source,
        test_case.config.variable_prefix,
    )

    # Import formatter
    from apirun.utils.console_output import Color, Emoji, create_formatter

    # Create output formatter
    formatter = create_formatter(
        use_color=use_color, use_emoji=use_emoji, lang=lang, verbose=verbose
    )

    # Print header
    dd_text = formatter.style.get_text('数据驱动测试', 'Data-Driven Test')
    formatter.print_test_start(
        f'{test_case.name} ({dd_text})',
        test_case.description or '',
        len(test_case.steps),
    )

    data_text = formatter.style.get_text(
        f'数据迭代: {len(iterator)}', f'Data iterations: {len(iterator)}'
    )
    print(f'   {formatter.style.dim(data_text)}')
    print()

    # Execute for each data row
    all_results = []
    total_passed = 0
    total_failed = 0

    for i, (data_row, augmented_test_case) in enumerate(iterator):
        iteration_text = formatter.style.get_text(
            f'数据迭代 #{i + 1}', f'Data Iteration #{i + 1}'
        )
        print(f'\n{formatter.style.header("━" * 70)}')
        print(f'  {formatter.style.header(iteration_text)}')

        if verbose:
            data_str = (
                str(data_row)[:100] + '...'
                if len(str(data_row)) > 100
                else str(data_row)
            )
            print(f'  {formatter.style.dim(data_str)}')

        print()

        result = _execute_single_test(
            augmented_test_case,
            verbose,
            lang=lang,
            use_color=use_color,
            use_emoji=use_emoji,
            notifier=None,
        )
        all_results.append(result)

        # Update statistics
        if result['test_case']['status'] == 'passed':
            total_passed += 1
        else:
            total_failed += 1

    # Aggregate results
    aggregated_result = {
        'test_case': {
            'name': test_case.name,
            'status': 'passed' if total_failed == 0 else 'failed',
            'total_iterations': len(iterator),
            'passed_iterations': total_passed,
            'failed_iterations': total_failed,
            'pass_rate': (total_passed / len(iterator) * 100)
            if len(iterator) > 0
            else 0,
        },
        'iterations': all_results,
    }

    # Print summary
    summary_text = formatter.style.get_text(
        '数据驱动测试摘要', 'Data-Driven Test Summary'
    )
    print(f'\n{formatter.style.header("━" * 70)}')
    print(f'  {formatter.style.header(summary_text)}')

    total_text = formatter.style.get_text('总迭代次数:', 'Total Iterations:')
    print(f'  {total_text} {formatter.style.colorize(str(len(iterator)), Color.CYAN)}')

    passed_text = formatter.style.get_text('通过:', 'Passed:')
    print(
        f'  {passed_text} {formatter.style.colorize(str(total_passed), Color.GREEN)} {Emoji.SUCCESS.value if formatter.style.use_emoji else ""}'
    )

    failed_text = formatter.style.get_text('失败:', 'Failed:')
    print(
        f'  {failed_text} {formatter.style.colorize(str(total_failed), Color.RED)} {Emoji.FAILURE.value if formatter.style.use_emoji else ""}'
    )

    rate_text = formatter.style.get_text('通过率:', 'Pass Rate:')
    rate_color = (
        Color.GREEN
        if total_failed == 0
        else (Color.YELLOW if total_passed > total_failed else Color.RED)
    )
    pass_rate_value = aggregated_result['test_case']['pass_rate']
    print(
        f'  {rate_text} {formatter.style.colorize(f"{pass_rate_value:.1f}%", rate_color)}'
    )
    print(f'{formatter.style.header("━" * 70)}')

    return aggregated_result


def _execute_single_test(
    test_case,
    verbose: bool = False,
    notifier=None,
    lang: str = 'zh',
    use_color: bool = True,
    use_emoji: bool = True,
) -> dict:
    """Execute single test case with real-time step printing.

    Args:
        test_case: Test case to execute
        verbose: Enable verbose output
        notifier: Optional WebSocket notifier for real-time updates
        lang: Language code ('zh' or 'en')
        use_color: Enable colored output
        use_emoji: Enable emoji

    Returns:
        Execution result as dictionary
    """
    # Check if output format is text (JSON/CSV/JUnit/HTML modes suppress text output)
    is_text_output = not (
        test_case.config
        and test_case.config.output
        and test_case.config.output.get('format') in ['json', 'csv', 'junit', 'html']
    )

    # Only print in text mode
    if is_text_output:
        # Import formatter
        from apirun.utils.console_output import (
            StepError,
            StepExtraction,
            create_formatter,
        )

        # Create output formatter
        formatter = create_formatter(
            use_color=use_color, use_emoji=use_emoji, lang=lang, verbose=verbose
        )

        # Print header
        formatter.print_test_start(
            test_case.name, test_case.description or '', len(test_case.steps)
        )

        # Execute test case with real-time printing
        # We'll manually execute steps to print them in real-time
        from datetime import datetime
        import time

        from apirun.core.variable_manager import VariableManager

        # Initialize
        start_time = datetime.now()
        variable_manager = VariableManager()

        # Initialize global variables
        variable_manager.set_variable('config', test_case.config)

        # Set up profile
        if test_case.config and test_case.config.active_profile:
            profile_name = test_case.config.active_profile
            if profile_name in test_case.config.profiles:
                profile = test_case.config.profiles[profile_name]
                variable_manager.set_variable('profile', profile.variables or {})

        # Track results and failed steps
        step_results = []
        failed_steps = []

        # Execute each step with real-time printing
        for i, step in enumerate(test_case.steps, 1):
            step_start_time = time.time()

            # Get the appropriate executor
            from apirun.executor.api_executor import APIExecutor
            from apirun.executor.concurrent_executor import ConcurrentExecutor
            from apirun.executor.database_executor import DatabaseExecutor
            from apirun.executor.loop_executor import LoopExecutor
            from apirun.executor.poll_executor import PollStepExecutor
            from apirun.executor.script_executor import ScriptExecutor
            from apirun.executor.wait_executor import WaitExecutor

            # Create executor based on step type
            if step.type == 'request':
                executor_cls = APIExecutor
            elif step.type == 'database':
                executor_cls = DatabaseExecutor
            elif step.type == 'wait':
                executor_cls = WaitExecutor
            elif step.type == 'loop':
                executor_cls = LoopExecutor
            elif step.type == 'concurrent':
                executor_cls = ConcurrentExecutor
            elif step.type == 'script':
                executor_cls = ScriptExecutor
            elif step.type == 'poll':
                executor_cls = PollStepExecutor
            else:
                # Default to APIExecutor for backward compatibility
                executor_cls = APIExecutor

            # Execute step
            # Get timeout and retry settings from config
            timeout = getattr(test_case.config, 'timeout', 30) or 30
            retry_policy = getattr(test_case.config, 'retry_policy', None)
            retry_times = (
                getattr(retry_policy, 'max_attempts', 0) - 1 if retry_policy else 0
            )

            executor = executor_cls(
                variable_manager,
                step,
                timeout=timeout,
                retry_times=max(0, retry_times),
                previous_results=step_results,
            )

            step_result = executor.execute()
            step_end_time = time.time()

            # Convert to result dict format
            step_dict = {
                'name': step_result.name,
                'status': step_result.status,
                'start_time': (
                    step_result.start_time.isoformat()
                    if step_result.start_time
                    else start_time.isoformat()
                ),
                'end_time': (
                    step_result.end_time.isoformat()
                    if step_result.end_time
                    else datetime.now().isoformat()
                ),
                'response': step_result.response,
                'extracted_vars': step_result.extracted_vars or {},
                'validations': step_result.validation_results or [],
                'performance': step_result.performance,
                'error_info': None,
                'retry_count': (
                    step_result.retry_count
                    if hasattr(step_result, 'retry_count')
                    else 0
                ),
            }

            # Add error info if present
            if step_result.error_info:
                error_info = step_result.error_info
                step_dict['error_info'] = {
                    'type': error_info.type,
                    'message': error_info.message,
                    'category': (
                        error_info.category.value
                        if hasattr(error_info.category, 'value')
                        else str(error_info.category)
                    ),
                    'suggestion': error_info.suggestion,
                }

            step_results.append(step_dict)

            # Print step in real-time
            duration = step_end_time - step_start_time
            perf = step_result.performance
            duration_sec = duration

            # Convert error info
            step_error = None
            if step_dict.get('error_info'):
                error_data = step_dict['error_info']
                step_error = StepError(
                    error_type=error_data.get('type', 'Error'),
                    message=error_data.get('message', ''),
                    context=error_data.get('suggestion'),
                )

            # Convert extraction info
            extraction = None
            if step_result.extracted_vars:
                var_name = list(step_result.extracted_vars.keys())[0]
                var_value = str(step_result.extracted_vars[var_name])
                extraction = StepExtraction(
                    var_name=var_name,
                    value=var_value[:50] + '...' if len(var_value) > 50 else var_value,
                    path='response',
                )

            # Collect failed steps for error section
            is_failed = step_result.status in ['failure', 'failed']
            if is_failed and step_error:
                failed_steps.append({
                    'index': i,
                    'name': step.name,
                    'error': step_error,
                })

            # Prepare request/response data for verbose logging
            request_data = None
            response_data = None

            if step_result.response and isinstance(step_result.response, dict):
                request_data = step_result.response.get('request')
                response_data = step_result.response

            # Print the step
            formatter.print_step(
                index=i,
                total=len(test_case.steps),
                name=step.name,
                status=step_result.status,
                duration=duration_sec,
                extraction=extraction,
                error=step_error,  # Don't print error here
                performance=perf,
                request_data=request_data,
                response_data=response_data,
            )

        # Calculate statistics
        total_steps = len(step_results)
        passed_steps = sum(
            1 for s in step_results if s['status'] in ['success', 'passed']
        )
        failed_steps_count = sum(
            1 for s in step_results if s['status'] in ['failure', 'failed']
        )
        skipped_steps = sum(1 for s in step_results if s['status'] == 'skipped')
        pass_rate = (passed_steps / total_steps * 100) if total_steps > 0 else 0

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Build result dict
        result = {
            'test_case': {
                'name': test_case.name,
                'status': 'passed' if failed_steps_count == 0 else 'failed',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'config': {},  # Empty dict instead of None
            },
            'statistics': {
                'total_steps': total_steps,
                'passed_steps': passed_steps,
                'failed_steps': failed_steps_count,
                'skipped_steps': skipped_steps,
                'pass_rate': pass_rate,
            },
            'steps': step_results,
            'final_variables': variable_manager.get_all_variables(),
            'error_info': None,
        }

        # === LINEAR FLOW ===
        # 1. Print error section (if any failures)
        if failed_steps:
            formatter.print_error_section(failed_steps)

        # 2. Print summary footer
        formatter.print_summary_footer(
            result['test_case']['status'],
            result['test_case']['duration'],
            result['statistics']['total_steps'],
            result['statistics']['passed_steps'],
            result['statistics']['failed_steps'],
            result['statistics']['skipped_steps'],
            result['statistics']['pass_rate'],
        )

        return result

    else:
        # Non-text mode: use original executor
        executor = TestCaseExecutor(test_case, notifier=notifier)
        return executor.execute()


def save_result(result: dict, output_path: str, report_lang: str = 'en') -> None:
    """Save result to file (format based on extension or config).

    Args:
        result: Result dictionary
        output_path: Output file path
        report_lang: Report language (en/zh)
    """
    # Determine format from file extension or config
    format_from_config = 'json'
    if result.get('test_case', {}).get('config', {}).get('output', {}).get('format'):
        format_from_config = result['test_case']['config']['output']['format']

    # Check file extension
    if output_path.endswith('.csv'):
        output_format = 'csv'
    elif output_path.endswith('.json'):
        output_format = 'json'
    elif output_path.endswith('.xml'):
        output_format = 'junit'
    elif output_path.endswith('.html'):
        output_format = 'html'
    else:
        # Use format from config
        output_format = format_from_config

    # Reconstruct TestCaseResult (needed for all formats)
    from datetime import datetime

    from apirun.core.models import (
        ErrorInfo,
        PerformanceMetrics,
        StepResult,
        TestCaseResult,
    )

    start_time = (
        datetime.fromisoformat(result['test_case']['start_time'])
        if result['test_case'].get('start_time')
        else datetime.now()
    )
    end_time = (
        datetime.fromisoformat(result['test_case']['end_time'])
        if result['test_case'].get('end_time')
        else datetime.now()
    )

    # Reconstruct step results for formats that need them
    step_results = []
    for step_data in result.get('steps', []):
        step_result = StepResult(
            name=step_data['name'],
            status=step_data['status'],
            response=step_data.get('response'),
            extracted_vars=step_data.get('extracted_vars', {}),
            validation_results=step_data.get('validations', []),
            performance=None,
            error_info=None,
        )

        # Add performance if available
        if step_data.get('performance'):
            perf_data = step_data['performance']
            step_result.performance = PerformanceMetrics(
                total_time=perf_data.get('total_time', 0),
                dns_time=perf_data.get('dns_time', 0),
                tcp_time=perf_data.get('tcp_time', 0),
                tls_time=perf_data.get('tls_time', 0),
                server_time=perf_data.get('server_time', 0),
                download_time=perf_data.get('download_time', 0),
                upload_time=perf_data.get('upload_time', 0),
                size=perf_data.get('size', 0),
            )

        # Add error info if available
        if step_data.get('error_info'):
            err_data = step_data['error_info']
            from apirun.core.models import ErrorCategory

            category_map = {
                'assertion': ErrorCategory.ASSERTION,
                'network': ErrorCategory.NETWORK,
                'timeout': ErrorCategory.TIMEOUT,
                'parsing': ErrorCategory.PARSING,
                'business': ErrorCategory.BUSINESS,
                'system': ErrorCategory.SYSTEM,
            }
            category = category_map.get(
                err_data.get('category', ''), ErrorCategory.SYSTEM
            )
            step_result.error_info = ErrorInfo(
                type=err_data.get('type', 'UnknownError'),
                category=category,
                message=err_data.get('message', ''),
                suggestion=err_data.get('suggestion', ''),
            )

        # Parse timestamps
        if step_data.get('start_time'):
            step_result.start_time = datetime.fromisoformat(step_data['start_time'])
        if step_data.get('end_time'):
            step_result.end_time = datetime.fromisoformat(step_data['end_time'])

        step_result.retry_count = step_data.get('retry_count', 0)
        step_results.append(step_result)

    test_case_result = TestCaseResult(
        name=result['test_case']['name'],
        status=result['test_case']['status'],
        start_time=start_time,
        end_time=end_time,
        duration=result['test_case']['duration'],
        total_steps=result['statistics']['total_steps'],
        passed_steps=result['statistics']['passed_steps'],
        failed_steps=result['statistics']['failed_steps'],
        skipped_steps=result['statistics']['skipped_steps'],
        step_results=step_results,
        final_variables=result.get('final_variables', {}),
        error_info=None,
    )

    # Save based on format
    if output_format == 'csv':
        from apirun.result.json_exporter import JSONExporter

        collector = JSONExporter()
        collector.save_csv(test_case_result, output_path)

    elif output_format == 'junit':
        from apirun.result.junit_exporter import JUnitExporter

        exporter = JUnitExporter()
        exporter.save_junit_xml(test_case_result, output_path)

    elif output_format == 'html':
        from apirun.result.html_exporter import HTMLExporter

        exporter = HTMLExporter(language=report_lang)
        exporter.save_html(test_case_result, output_path)

    else:
        # Default to JSON
        with Path(output_path).open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)


def _generate_allure_report(
    test_case, result: dict, allure_dir: str, clean: bool = True, silent: bool = False
):
    """Generate Allure report from test result.

    Args:
        test_case: Test case object
        result: Test execution result dictionary
        allure_dir: Allure results directory
        clean: Whether to clean directory before generating (default: True)
        silent: Whether to suppress output messages (default: False)
    """
    from pathlib import Path
    import shutil

    from apirun.core.models import TestCaseResult
    from apirun.result.allure_exporter import AllureExporter

    # Clear previous Allure results if requested
    if clean:
        allure_path = Path(allure_dir)
        if allure_path.exists():
            # Remove all files in the directory
            for item in allure_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

    # Create Allure collector
    collector = AllureExporter(output_dir=allure_dir)

    # Reconstruct TestCaseResult from dict
    # This is a simplified reconstruction
    from datetime import datetime

    from apirun.core.models import ErrorInfo, PerformanceMetrics, StepResult

    step_results = []
    for step_data in result.get('steps', []):
        # Reconstruct StepResult
        step_result = StepResult(
            name=step_data['name'],
            status=step_data['status'],
            response=step_data.get('response'),
            extracted_vars=step_data.get('extracted_vars', {}),
            validation_results=step_data.get('validations', []),
            performance=None,
            error_info=None,
        )

        # Add performance if available
        if step_data.get('performance'):
            perf_data = step_data['performance']
            step_result.performance = PerformanceMetrics(
                total_time=perf_data.get('total_time', 0),
                dns_time=perf_data.get('dns_time', 0),
                tcp_time=perf_data.get('tcp_time', 0),
                tls_time=perf_data.get('tls_time', 0),
                server_time=perf_data.get('server_time', 0),
                download_time=perf_data.get('download_time', 0),
                upload_time=perf_data.get('upload_time', 0),
                size=perf_data.get('size', 0),
            )

        # Add error info if available
        if step_data.get('error_info'):
            err_data = step_data['error_info']
            from apirun.core.models import ErrorCategory

            # Map category string to enum
            category_map = {
                'assertion': ErrorCategory.ASSERTION,
                'network': ErrorCategory.NETWORK,
                'timeout': ErrorCategory.TIMEOUT,
                'parsing': ErrorCategory.PARSING,
                'business': ErrorCategory.BUSINESS,
                'system': ErrorCategory.SYSTEM,
            }
            category = category_map.get(
                err_data.get('category', ''), ErrorCategory.SYSTEM
            )

            step_result.error_info = ErrorInfo(
                type=err_data.get('type', 'UnknownError'),
                category=category,
                message=err_data.get('message', ''),
                suggestion=err_data.get('suggestion', ''),
            )

        # Parse timestamps
        if step_data.get('start_time'):
            step_result.start_time = datetime.fromisoformat(step_data['start_time'])
        if step_data.get('end_time'):
            step_result.end_time = datetime.fromisoformat(step_data['end_time'])

        step_result.retry_count = step_data.get('retry_count', 0)
        step_results.append(step_result)

    # Reconstruct TestCaseResult
    test_result = TestCaseResult(
        name=result['test_case']['name'],
        status=result['test_case']['status'],
        start_time=datetime.fromisoformat(result['test_case']['start_time']),
        end_time=datetime.fromisoformat(result['test_case']['end_time']),
        duration=result['test_case']['duration'],
        total_steps=result['statistics']['total_steps'],
        passed_steps=result['statistics']['passed_steps'],
        failed_steps=result['statistics']['failed_steps'],
        skipped_steps=result['statistics']['skipped_steps'],
        step_results=step_results,
        final_variables=result.get('final_variables', {}),
        error_info=None,
    )

    # Generate Allure result file
    result_file = collector.collect(test_case, test_result)

    # Generate supporting files
    collector.generate_environment_file()
    collector.generate_categories_file()

    # Print message only if not in silent mode
    if not silent:
        print(f'\n✓ Allure 报告数据已生成: {result_file}')
        print(f'  结果目录: {allure_dir}')
        print(f'  查看报告: allure serve {allure_dir}')
        print(f'  或生成 HTML: allure generate {allure_dir} --clean -o allure-report')


if __name__ == '__main__':
    sys.exit(main())
