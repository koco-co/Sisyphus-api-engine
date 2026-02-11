"""Enhanced YAML Validator for Sisyphus API Engine.

This module provides comprehensive YAML validation including:
- Basic syntax validation
- Required fields checking
- Unknown keyword detection
- Detailed Chinese error messages with beautiful terminal output

Following Google Python Style Guide.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from apirun.utils.yaml_loader import load_yaml_with_include


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for beautiful terminal output."""

    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


@dataclass
class ValidationResult:
    """Validation result for a single file.

    Attributes:
        file_path: Path to the validated file
        is_valid: Whether the file is valid
        syntax_errors: List of YAML syntax errors
        missing_fields: List of missing required fields
        unknown_keywords: List of unknown keywords found
        warnings: List of validation warnings
    """

    file_path: str
    is_valid: bool
    syntax_errors: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    unknown_keywords: list[tuple[str, str]] = field(
        default_factory=list
    )  # (keyword, location)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if result has any errors."""
        return bool(self.syntax_errors or self.missing_fields or self.unknown_keywords)

    @property
    def error_count(self) -> int:
        """Get total error count."""
        return (
            len(self.syntax_errors)
            + len(self.missing_fields)
            + len(self.unknown_keywords)
        )


class YamlValidator:
    """Enhanced YAML validator with keyword checking.

    This validator checks:
    1. YAML syntax errors
    2. Required fields (name, steps)
    3. Unknown/unsupported keywords
    4. Structural validity
    """

    # Valid keywords at test case level (top-level)
    VALID_TEST_CASE_KEYWORDS: set[str] = {
        'name',
        'description',
        'config',
        'steps',
        'tags',
        'timeout',
        'enabled',
        'setup',
        'teardown',
    }

    # Valid keywords in config section
    VALID_CONFIG_KEYWORDS: set[str] = {
        'name',
        'timeout',
        'retry_times',
        'retry_policy',
        'variables',
        'profiles',
        'active_profile',
        'data_source',
        'data_iterations',  # Number of data-driven iterations
        'variable_prefix',  # Prefix for data variables
        'websocket',
        'output',
        'base_url',
        'verify_ssl',
        'debug',
        'env_vars',
        'performance',
    }

    # Valid keywords in profile section
    VALID_PROFILE_KEYWORDS: set[str] = {
        'base_url',
        'variables',
        'timeout',
        'verify_ssl',
        'headers',
    }

    # Valid keywords at step level (common to all step types)
    VALID_STEP_KEYWORDS: set[str] = {
        'name',
        'description',
        'type',
        'depends_on',
        'skip_if',
        'only_if',
        'setup',
        'teardown',
        'retry_times',
        'retry_policy',
        'timeout',
        'variables',
        'validations',
        'extractors',
        'validate',
        'mock',
        'performance',
    }

    # Valid keywords for request steps
    VALID_REQUEST_KEYWORDS: set[str] = {
        'method',
        'url',
        'headers',
        'params',
        'body',
        'cookies',
        'auth',
        'proxy',
        'allow_redirects',
        'verify_ssl',
        'timeout',
        'poll_config',
        'on_timeout',
    }

    # Valid keywords for database steps
    VALID_DATABASE_KEYWORDS: set[str] = {
        'connection',
        'query',
        'params',
        'operation',
        'database',  # Database configuration (matches TestStep.database)
        'sql',  # SQL statement (matches TestStep.sql)
        'transaction',  # Transaction configuration
    }

    # Valid keywords for wait steps
    VALID_WAIT_KEYWORDS: set[str] = {
        'duration',
        'seconds',  # Fixed delay in seconds
        'condition',
        'wait_condition',
        'interval',
        'timeout',
        'max_wait',  # Maximum wait time for conditional waits
        'wait_type',
    }

    # Valid keywords for loop steps
    VALID_LOOP_KEYWORDS: set[str] = {
        'loop_type',
        'iterations',
        'loop_count',
        'condition',
        'loop_condition',
        'break_if',
        'continue_if',
        'steps',
        'loop_steps',
        'variables',
        'loop_variable',
    }

    # Valid keywords for script steps
    VALID_SCRIPT_KEYWORDS: set[str] = {
        'language',
        'script_type',
        'script',
        'allow_imports',
        'variables',
        'timeout',
        'capture_output',  # Capture script output
    }

    # Valid keywords for concurrent steps
    VALID_CONCURRENT_KEYWORDS: set[str] = {
        'max_concurrency',
        'concurrent_steps',
        'steps',
    }

    # Valid keywords for poll steps
    VALID_POLL_KEYWORDS: set[str] = {
        'method',
        'url',
        'headers',
        'params',
        'body',
        'cookies',
        'poll_config',
        'on_timeout',
        'timeout',
    }

    # Valid keywords in poll_config
    VALID_POLL_CONFIG_KEYWORDS: set[str] = {
        'condition',
        'max_attempts',
        'interval',
        'timeout',
        'backoff',
        'base_delay',
        'max_delay',
        'backoff_multiplier',
        'jitter',
        'retry_on',
        'stop_on',
    }

    # Valid keywords in validation rules
    VALID_VALIDATION_KEYWORDS: set[str] = {
        'type',
        'path',
        'expect',
        'expected',
        'description',
        'error_message',  # Custom error message (v2.0.1+)
    }

    # Valid keywords in extractors
    VALID_EXTRACTOR_KEYWORDS: set[str] = {
        'name',
        'type',
        'path',
        'from',
        'index',
        'regex',
        'pattern',
        'group',
        'multiple',
        'extract_all',  # Extract all matches (v2.0+)
        'default',  # Default value if extraction fails (v2.0.1+)
        'condition',  # Conditional extraction (v2.0+)
        'on_failure',  # Behavior on extraction failure (v2.0+)
        'description',
    }

    # Valid keywords in retry_policy
    VALID_RETRY_POLICY_KEYWORDS: set[str] = {
        'max_attempts',
        'strategy',
        'base_delay',
        'max_delay',
        'backoff_multiplier',
        'jitter',
        'retry_on',
        'stop_on',
    }

    # Valid keywords in data_source
    VALID_DATA_SOURCE_KEYWORDS: set[str] = {
        'type',  # Data source type: csv, json, database
        'file_path',  # Path to data file
        'data_key',  # Key for JSON data
        'table',  # Database table name
        'query',  # Database query
        'sheet',  # Excel sheet name
        'delimiter',  # CSV delimiter
        'encoding',  # File encoding
        'data',  # Inline data
        'iterations',  # Number of iterations
    }

    # Valid keywords in data_source
    VALID_DATA_SOURCE_KEYWORDS: set[str] = {
        'type',
        'path',
        'table',
        'query',
        'data',
        'variable_names',
        'encoding',
    }

    # Valid keywords in websocket config
    VALID_WEBSOCKET_KEYWORDS: set[str] = {
        'enabled',
        'host',
        'port',
        'server_url',
        'ssl_enabled',
        'heartbeat_interval',
        'reconnect',
        'message_queue',
    }

    # Valid keywords in output config
    VALID_OUTPUT_KEYWORDS: set[str] = {
        'format',
        'formats',
        'path',
        'dir',
        'save_response',
        'save_request',
        'json',
        'allure',
        'junit',
        'html',
        'csv',
    }

    # Valid step types
    VALID_STEP_TYPES: set[str] = {
        'request',
        'database',
        'wait',
        'loop',
        'concurrent',
        'script',
        'poll',
    }

    # Valid validation types
    VALID_VALIDATION_TYPES: set[str] = {
        'status_code',
        'eq',
        'ne',
        'gt',
        'lt',
        'ge',
        'le',
        'contains',
        'not_contains',
        'regex',
        'type',
        'in',
        'not_in',
        'in_list',
        'not_in_list',
        'length_eq',
        'length_gt',
        'length_lt',
        'contains_key',
        'json_path',
        'exists',
        'is_null',
        'is_empty',
        'starts_with',
        'ends_with',
        'between',
    }

    def __init__(self):
        """Initialize YamlValidator."""
        pass

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            ValidationResult object with detailed error information
        """
        result = ValidationResult(file_path=file_path, is_valid=False)

        # Check file existence
        if not Path(file_path).exists():
            result.syntax_errors.append(f'文件不存在: {file_path}')
            return result

        if not Path(file_path).is_file():
            result.syntax_errors.append(f'路径不是文件: {file_path}')
            return result

        try:
            data = load_yaml_with_include(file_path)

            if data is None:
                result.syntax_errors.append('YAML 文件为空')
                return result

            # Validate test case level structure
            self._validate_test_case_level(data, result)

            # If basic structure is valid, validate deeper
            if not result.syntax_errors and not result.missing_fields:
                self._validate_config(data, result)
                self._validate_steps(data, result)

            result.is_valid = not result.has_errors

        except yaml.YAMLError as e:
            result.syntax_errors.append(f'YAML 语法错误: {str(e)}')
        except Exception as e:
            result.syntax_errors.append(f'验证错误: {str(e)}')

        return result

    def _validate_test_case_level(
        self, data: dict[str, Any], result: ValidationResult
    ) -> None:
        """Validate test case level fields.

        Args:
            data: Parsed YAML data
            result: ValidationResult to update
        """
        if not isinstance(data, dict):
            result.syntax_errors.append('YAML 根节点必须是对象/字典类型')
            return

        # Check for unknown keywords at test case level
        for key in data.keys():
            if key not in self.VALID_TEST_CASE_KEYWORDS:
                result.unknown_keywords.append((key, '测试用例顶层'))

        # Check required fields
        if 'name' not in data:
            result.missing_fields.append('缺少必填字段: name (测试用例名称)')
        elif not data.get('name'):
            result.syntax_errors.append('name 字段不能为空')

        if 'steps' not in data:
            result.missing_fields.append('缺少必填字段: steps (测试步骤列表)')
        elif not isinstance(data['steps'], list):
            result.syntax_errors.append('steps 字段必须是列表类型')
        elif len(data['steps']) == 0:
            result.syntax_errors.append('steps 列表不能为空')

    def _validate_config(self, data: dict[str, Any], result: ValidationResult) -> None:
        """Validate config section.

        Args:
            data: Parsed YAML data
            result: ValidationResult to update
        """
        config = data.get('config')
        if config is None:
            return

        if not isinstance(config, dict):
            result.syntax_errors.append('config 字段必须是对象/字典类型')
            return

        # Check for unknown keywords in config
        for key in config.keys():
            if key not in self.VALID_CONFIG_KEYWORDS:
                result.unknown_keywords.append((key, 'config 配置节'))

        # Validate profiles
        profiles = config.get('profiles')
        if profiles is not None:
            if not isinstance(profiles, dict):
                result.syntax_errors.append('profiles 字段必须是对象/字典类型')
            else:
                for profile_name, profile_config in profiles.items():
                    if not isinstance(profile_config, dict):
                        result.syntax_errors.append(
                            f"profile '{profile_name}' 配置必须是对象/字典类型"
                        )
                        continue

                    # Check for unknown keywords in profile
                    # Note: Users can define custom variables at profile level
                    # We only warn about clearly invalid keywords
                    # Common valid keywords: base_url, variables, timeout, verify_ssl, headers
                    # Any other field is treated as a custom variable (allowed)
                    for key in profile_config.keys():
                        if key in self.VALID_PROFILE_KEYWORDS:
                            continue
                        # Allow any other field as custom variable
                        # Don't report as unknown keyword

        # Validate retry_policy
        retry_policy = config.get('retry_policy')
        if retry_policy is not None:
            if not isinstance(retry_policy, dict):
                result.syntax_errors.append('retry_policy 字段必须是对象/字典类型')
            else:
                for key in retry_policy.keys():
                    if key not in self.VALID_RETRY_POLICY_KEYWORDS:
                        result.unknown_keywords.append((key, 'retry_policy'))

        # Validate data_source
        data_source = config.get('data_source')
        if data_source is not None:
            if not isinstance(data_source, dict):
                result.syntax_errors.append('data_source 字段必须是对象/字典类型')
            else:
                for key in data_source.keys():
                    if key not in self.VALID_DATA_SOURCE_KEYWORDS:
                        result.unknown_keywords.append((key, 'data_source'))

        # Validate websocket config
        websocket = config.get('websocket')
        if websocket is not None:
            if not isinstance(websocket, dict):
                result.syntax_errors.append('websocket 字段必须是对象/字典类型')
            else:
                for key in websocket.keys():
                    if key not in self.VALID_WEBSOCKET_KEYWORDS:
                        result.unknown_keywords.append((key, 'websocket'))

        # Validate output config
        output = config.get('output')
        if output is not None:
            if not isinstance(output, dict):
                result.syntax_errors.append('output 字段必须是对象/字典类型')
            else:
                for key in output.keys():
                    if key not in self.VALID_OUTPUT_KEYWORDS:
                        result.unknown_keywords.append((key, 'output'))

    def _validate_steps(self, data: dict[str, Any], result: ValidationResult) -> None:
        """Validate steps section.

        Args:
            data: Parsed YAML data
            result: ValidationResult to update
        """
        steps = data.get('steps', [])
        if not isinstance(steps, list):
            return

        for idx, step in enumerate(steps):
            step_location = f'steps[{idx}]'

            if not isinstance(step, dict):
                result.syntax_errors.append(f'{step_location}: 步骤必须是对象/字典类型')
                continue

            # Support shorthand syntax: step name as key
            # Example: - 步骤1_测试GET请求:
            #            type: request
            if len(step) == 1 and 'type' not in step:
                # Extract the actual step content from the shorthand syntax
                step_name = list(step.keys())[0]
                step_content = step[step_name]

                if not isinstance(step_content, dict):
                    result.syntax_errors.append(
                        f'{step_location}: 步骤内容必须是对象/字典类型'
                    )
                    continue

                # Use step_content as the step for validation
                # Add name to step_content if not present
                if 'name' not in step_content:
                    step_content = dict(step_content, name=step_name)

                step = step_content

            # Check step type
            step_type = step.get('type', 'request')  # Default is request

            if step_type not in self.VALID_STEP_TYPES:
                result.syntax_errors.append(
                    f"{step_location}: 无效的步骤类型 '{step_type}'，"
                    f'支持的类型: {", ".join(sorted(self.VALID_STEP_TYPES))}'
                )

            # Validate common step keywords
            for key in step.keys():
                # Type-specific keywords will be checked below
                if key in self.VALID_STEP_KEYWORDS:
                    continue
                if step_type == 'request' and key in self.VALID_REQUEST_KEYWORDS:
                    continue
                if step_type == 'database' and key in self.VALID_DATABASE_KEYWORDS:
                    continue
                if step_type == 'wait' and key in self.VALID_WAIT_KEYWORDS:
                    continue
                if step_type == 'loop' and key in self.VALID_LOOP_KEYWORDS:
                    continue
                if step_type == 'script' and key in self.VALID_SCRIPT_KEYWORDS:
                    continue
                if step_type == 'poll' and key in self.VALID_POLL_KEYWORDS:
                    continue
                if step_type == 'concurrent' and key in self.VALID_CONCURRENT_KEYWORDS:
                    continue

                # Check if it's a poll_config special case
                if key == 'poll_config':
                    if step_type not in ('request', 'poll'):
                        result.unknown_keywords.append((key, step_location))
                    continue

                result.unknown_keywords.append((key, step_location))

            # Validate poll_config if present
            if 'poll_config' in step:
                poll_config = step['poll_config']
                if isinstance(poll_config, dict):
                    for key in poll_config.keys():
                        if key not in self.VALID_POLL_CONFIG_KEYWORDS:
                            result.unknown_keywords.append((
                                key,
                                f'{step_location}.poll_config',
                            ))

            # Validate validations
            validations = step.get('validations', [])
            if validations:
                if not isinstance(validations, list):
                    result.syntax_errors.append(
                        f'{step_location}.validations: 必须是列表类型'
                    )
                else:
                    for v_idx, validation in enumerate(validations):
                        v_location = f'{step_location}.validations[{v_idx}]'
                        if not isinstance(validation, dict):
                            result.syntax_errors.append(
                                f'{v_location}: 验证规则必须是对象/字典类型'
                            )
                            continue

                        for key in validation.keys():
                            if key not in self.VALID_VALIDATION_KEYWORDS:
                                result.unknown_keywords.append((key, v_location))

                        # Check validation type
                        v_type = validation.get('type')
                        if v_type and v_type not in self.VALID_VALIDATION_TYPES:
                            result.syntax_errors.append(
                                f"{v_location}: 无效的验证类型 '{v_type}'"
                            )

            # Validate extractors
            extractors = step.get('extractors', [])
            if extractors:
                if not isinstance(extractors, list):
                    result.syntax_errors.append(
                        f'{step_location}.extractors: 必须是列表类型'
                    )
                else:
                    for e_idx, extractor in enumerate(extractors):
                        e_location = f'{step_location}.extractors[{e_idx}]'
                        if not isinstance(extractor, dict):
                            result.syntax_errors.append(
                                f'{e_location}: 提取器必须是对象/字典类型'
                            )
                            continue

                        for key in extractor.keys():
                            if key not in self.VALID_EXTRACTOR_KEYWORDS:
                                result.unknown_keywords.append((key, e_location))


class TerminalFormatter:
    """Beautiful terminal output formatter with colors and emojis."""

    @staticmethod
    def success(msg: str) -> str:
        """Format success message."""
        return f'{Colors.GREEN}✓{Colors.RESET} {msg}'

    @staticmethod
    def error(msg: str) -> str:
        """Format error message."""
        return f'{Colors.RED}✗{Colors.RESET} {msg}'

    @staticmethod
    def warning(msg: str) -> str:
        """Format warning message."""
        return f'{Colors.YELLOW}⚠{Colors.RESET} {msg}'

    @staticmethod
    def info(msg: str) -> str:
        """Format info message."""
        return f'{Colors.CYAN}ℹ{Colors.RESET} {msg}'

    @staticmethod
    def bold(msg: str) -> str:
        """Format bold text."""
        return f'{Colors.BOLD}{msg}{Colors.RESET}'

    @staticmethod
    def dim(msg: str) -> str:
        """Format dim text."""
        return f'{Colors.DIM}{msg}{Colors.RESET}'

    @staticmethod
    def keyword(msg: str) -> str:
        """Format keyword."""
        return f'{Colors.CYAN}{msg}{Colors.RESET}'

    @staticmethod
    def location(msg: str) -> str:
        """Format location."""
        return f'{Colors.DIM}{msg}{Colors.RESET}'

    @staticmethod
    def print_header(title: str) -> None:
        """Print formatted header."""
        print(f'\n{Colors.BOLD}{Colors.BLUE}{"=" * 70}{Colors.RESET}')
        print(f'{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.RESET}')
        print(f'{Colors.BOLD}{Colors.BLUE}{"=" * 70}{Colors.RESET}\n')

    @staticmethod
    def print_subheader(title: str) -> None:
        """Print formatted subheader."""
        print(f'\n{Colors.BOLD}{title}{Colors.RESET}')
        print(f'{Colors.DIM}{"-" * len(title)}{Colors.RESET}')

    @staticmethod
    def print_file_result(result: ValidationResult, show_details: bool = True) -> None:
        """Print validation result for a single file.

        Args:
            result: ValidationResult object
            show_details: Whether to show detailed errors/warnings
        """
        filename = Path(result.file_path).name

        if result.is_valid:
            # File passed validation
            status = TerminalFormatter.success(f'{filename}')
            print(f'  {status}')

            if show_details and result.warnings:
                for warning in result.warnings:
                    print(f'    {TerminalFormatter.warning(warning)}')
        else:
            # File failed validation
            status = TerminalFormatter.error(f'{filename}')
            print(f'  {status}')

            if not show_details:
                error_count = result.error_count
                error_word = '个错误' if error_count > 1 else '个错误'
                print(f'    {TerminalFormatter.dim(f"({error_count} {error_word})")}')
                return

            # Print detailed errors
            if result.syntax_errors:
                print()
                for error in result.syntax_errors:
                    print(f'    {TerminalFormatter.error(error)}')

            if result.missing_fields:
                print()
                for field in result.missing_fields:
                    print(f'    {TerminalFormatter.error(field)}')

            if result.unknown_keywords:
                print()
                print(f'    {TerminalFormatter.warning("未定义的关键字:")}')
                for keyword, location in result.unknown_keywords:
                    print(
                        f'      • {TerminalFormatter.keyword(keyword)} '
                        f'在 {TerminalFormatter.location(location)}'
                    )

    @staticmethod
    def print_summary(results: list[ValidationResult]) -> None:
        """Print validation summary.

        Args:
            results: List of ValidationResult objects
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        print()
        print(f'{Colors.BOLD}{"─" * 70}{Colors.RESET}')
        print(f'{Colors.BOLD}验证统计{Colors.RESET}')
        print(f'{Colors.BOLD}{"─" * 70}{Colors.RESET}')

        # Print statistics
        print(f'\n  总计:     {TerminalFormatter.bold(str(total))} 个文件')
        print(f'  通过:     {TerminalFormatter.success(str(valid))} 个文件')
        print(f'  失败:     {TerminalFormatter.error(str(invalid))} 个文件')

        if invalid > 0:
            total_errors = sum(r.error_count for r in results if not r.is_valid)
            print(f'  错误总数: {TerminalFormatter.error(str(total_errors))} 个')

        print()

        # Print final status
        if invalid == 0:
            print(f'  {Colors.GREEN}{Colors.BOLD}所有文件验证通过！{Colors.RESET}')
        else:
            print(f'  {Colors.RED}{Colors.BOLD}部分文件验证失败{Colors.RESET}')

        print(f'\n{Colors.BOLD}{"─" * 70}{Colors.RESET}\n')


def validate_yaml_files(
    paths: list[str], show_details: bool = True
) -> tuple[int, list[ValidationResult]]:
    """Validate multiple YAML files.

    Args:
        paths: List of file or directory paths
        show_details: Whether to show detailed error messages

    Returns:
        Tuple of (exit_code, list of ValidationResult objects)
    """
    validator = YamlValidator()
    results = []

    # Collect YAML files
    yaml_files = []
    for path_str in paths:
        path = Path(path_str)

        if not path.exists():
            print(TerminalFormatter.error(f'路径不存在: {path_str}'))
            continue

        if path.is_file():
            if path.suffix in ('.yaml', '.yml'):
                yaml_files.append(path)
            else:
                print(TerminalFormatter.warning(f'跳过非 YAML 文件: {path_str}'))
        elif path.is_dir():
            found_files = list(path.glob('**/*.yaml')) + list(path.glob('**/*.yml'))
            if found_files:
                yaml_files.extend(found_files)
            else:
                print(TerminalFormatter.warning(f'目录中未找到 YAML 文件: {path_str}'))

    if not yaml_files:
        print(TerminalFormatter.error('未找到任何 YAML 文件'))
        return 1, []

    # Print header
    TerminalFormatter.print_header('Sisyphus YAML 验证器')

    # Validate files
    for yaml_file in sorted(yaml_files):
        result = validator.validate_file(str(yaml_file))
        results.append(result)
        TerminalFormatter.print_file_result(result, show_details=show_details)

    # Print summary
    TerminalFormatter.print_summary(results)

    # Return exit code
    invalid_count = sum(1 for r in results if not r.is_valid)
    return (1 if invalid_count > 0 else 0), results
