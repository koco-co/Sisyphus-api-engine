"""Error handling utilities for Sisyphus API Engine.

This module provides enhanced error handling including:
- Error classification and categorization
- Automated error suggestion generation
- Stack trace formatting
- Context extraction

Following Google Python Style Guide.
"""

from datetime import datetime
import traceback
from typing import Any

from apirun.core.models import ErrorCategory, ErrorInfo


class ErrorClassifier:
    """Classify errors into categories and generate suggestions."""

    # Error type to category mapping
    ERROR_CATEGORIES = {
        # Network errors
        'ConnectionError': ErrorCategory.NETWORK,
        'ConnectTimeout': ErrorCategory.TIMEOUT,
        'ReadTimeout': ErrorCategory.TIMEOUT,
        'Timeout': ErrorCategory.TIMEOUT,
        'HTTPError': ErrorCategory.NETWORK,
        'RequestException': ErrorCategory.NETWORK,
        'SSLError': ErrorCategory.NETWORK,
        # Parsing errors
        'JSONDecodeError': ErrorCategory.PARSING,
        'YAMLError': ErrorCategory.PARSING,
        'ValidationError': ErrorCategory.PARSING,
        'TemplateError': ErrorCategory.PARSING,
        # Assertion errors
        'AssertionError': ErrorCategory.ASSERTION,
        'ValidationException': ErrorCategory.ASSERTION,
        # Database errors
        'DatabaseError': ErrorCategory.SYSTEM,
        'OperationalError': ErrorCategory.SYSTEM,
        'ProgrammingError': ErrorCategory.SYSTEM,
        # System errors
        'FileNotFoundError': ErrorCategory.SYSTEM,
        'PermissionError': ErrorCategory.SYSTEM,
        'ValueError': ErrorCategory.BUSINESS,
        'KeyError': ErrorCategory.BUSINESS,
        'AttributeError': ErrorCategory.BUSINESS,
    }

    # Error suggestions based on error type and message
    ERROR_SUGGESTIONS = {
        ErrorCategory.NETWORK: {
            'ConnectionError': [
                '检查网络连接是否正常',
                '确认服务器地址和端口是否正确',
                '检查防火墙设置',
                '验证服务器是否正在运行',
            ],
            'ConnectTimeout': [
                '检查网络延迟',
                '增加超时时间配置',
                '检查服务器负载情况',
                '尝试使用更近的网络节点',
            ],
            'ReadTimeout': [
                '增加读取超时时间',
                '检查服务器响应性能',
                '减少请求数据量',
                '检查服务器日志',
            ],
            'HTTPError': [
                '检查HTTP状态码含义',
                '验证请求参数是否正确',
                '检查API版本兼容性',
                '确认认证信息是否有效',
            ],
        },
        ErrorCategory.TIMEOUT: {
            'default': [
                '增加超时时间配置',
                '检查网络连接稳定性',
                '优化请求以减少处理时间',
                '检查服务器性能',
            ]
        },
        ErrorCategory.PARSING: {
            'JSONDecodeError': [
                '检查响应格式是否为有效JSON',
                '验证响应编码是否正确',
                '检查API文档确认响应格式',
            ],
            'YAMLError': [
                '检查YAML语法是否正确',
                '验证缩进格式（使用空格，不要使用Tab）',
                '检查特殊字符转义',
            ],
            'TemplateError': [
                '检查变量语法是否正确（${variable}）',
                '确认变量名是否存在',
                '验证Jinja2模板语法',
            ],
        },
        ErrorCategory.ASSERTION: {
            'default': [
                '检查验证规则配置',
                '验证预期值是否正确',
                '检查JSONPath表达式',
                '确认实际响应内容',
            ]
        },
        ErrorCategory.BUSINESS: {
            'default': [
                '检查业务逻辑配置',
                '验证数据格式',
                '确认API文档要求',
            ]
        },
        ErrorCategory.SYSTEM: {
            'FileNotFoundError': [
                '检查文件路径是否正确',
                '确认文件是否存在',
                '验证文件权限',
            ],
            'PermissionError': [
                '检查文件或目录权限',
                '确认用户访问权限',
                '检查磁盘空间',
            ],
        },
    }

    @classmethod
    def classify_error(
        cls, exception: Exception, context: dict[str, Any] | None = None
    ) -> ErrorInfo:
        """Classify an exception and create ErrorInfo.

        Args:
            exception: The exception to classify
            context: Additional context information

        Returns:
            ErrorInfo object with classification and suggestions
        """
        exception_type = type(exception).__name__
        exception_module = type(exception).__module__
        full_type = f'{exception_module}.{exception_type}'

        # Determine category
        category = cls._get_error_category(exception_type)

        # Generate suggestions
        suggestions = cls._generate_suggestions(
            category, exception_type, str(exception)
        )

        # Generate error code
        error_code = cls._generate_error_code(category, exception_type)

        # Determine severity
        severity = cls._determine_severity(category, exception)

        # Extract stack trace
        stack_trace = ''.join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

        # Build context
        error_context = context or {}
        error_context.update({
            'exception_type': exception_type,
            'exception_module': exception_module,
        })

        return ErrorInfo(
            type=full_type,
            category=category,
            message=str(exception),
            suggestion='\n'.join(suggestions),
            stack_trace=stack_trace,
            context=error_context,
            timestamp=datetime.now(),
            severity=severity,
            error_code=error_code,
        )

    @classmethod
    def _get_error_category(cls, exception_type: str) -> ErrorCategory:
        """Get error category from exception type.

        Args:
            exception_type: Exception type name

        Returns:
            ErrorCategory enum value
        """
        return cls.ERROR_CATEGORIES.get(exception_type, ErrorCategory.SYSTEM)

    @classmethod
    def _generate_suggestions(
        cls, category: ErrorCategory, exception_type: str, message: str
    ) -> list:
        """Generate error resolution suggestions.

        Args:
            category: Error category
            exception_type: Exception type name
            message: Error message

        Returns:
            List of suggestion strings
        """
        # First, try to generate contextual suggestions from message
        message_lower = message.lower()
        suggestions = []

        if 'connection refused' in message_lower:
            suggestions.extend([
                '检查服务器是否正在运行',
                '验证端口号是否正确',
                '检查防火墙规则',
            ])
        elif 'timeout' in message_lower:
            suggestions.extend([
                '增加超时时间',
                '检查网络连接',
                '验证服务器性能',
            ])
        elif '401' in message_lower or 'unauthorized' in message_lower:
            suggestions.extend([
                '检查认证凭据',
                '验证token是否有效',
                '确认API密钥配置',
            ])
        elif '403' in message_lower or 'forbidden' in message_lower:
            suggestions.extend([
                '检查访问权限',
                '验证用户角色',
                '确认资源访问策略',
            ])
        elif '404' in message_lower or 'not found' in message_lower:
            suggestions.extend([
                '检查URL路径是否正确',
                '验证资源是否存在',
                '确认API版本',
            ])
        elif '500' in message_lower or 'internal' in message_lower:
            suggestions.extend([
                '检查服务器日志',
                '联系系统管理员',
                '稍后重试',
            ])

        # If no contextual suggestions found, try category-specific suggestions
        if not suggestions:
            if category in cls.ERROR_SUGGESTIONS:
                category_suggestions = cls.ERROR_SUGGESTIONS[category]
                if exception_type in category_suggestions:
                    suggestions = category_suggestions[exception_type]
                elif 'default' in category_suggestions:
                    suggestions = category_suggestions['default']

        if not suggestions:
            suggestions.append('请查看详细错误信息和堆栈跟踪')

        return suggestions

    @classmethod
    def _generate_error_code(cls, category: ErrorCategory, exception_type: str) -> str:
        """Generate machine-readable error code.

        Args:
            category: Error category
            exception_type: Exception type name

        Returns:
            Error code string (e.g., "NET_001", "ASSERT_001")
        """
        category_codes = {
            ErrorCategory.NETWORK: 'NET',
            ErrorCategory.TIMEOUT: 'TMO',
            ErrorCategory.PARSING: 'PRS',
            ErrorCategory.ASSERTION: 'AST',
            ErrorCategory.BUSINESS: 'BIZ',
            ErrorCategory.SYSTEM: 'SYS',
        }

        category_code = category_codes.get(category, 'UNK')

        # Simple hash of exception type to generate number
        type_hash = abs(hash(exception_type)) % 1000

        return f'{category_code}_{type_hash:03d}'

    @classmethod
    def _determine_severity(cls, category: ErrorCategory, exception: Exception) -> str:
        """Determine error severity level.

        Args:
            category: Error category
            exception: Exception object

        Returns:
            Severity level (critical/high/medium/low)
        """
        critical_types = {'KeyboardInterrupt', 'SystemExit', 'MemoryError'}

        if type(exception).__name__ in critical_types:
            return 'critical'

        if category in [ErrorCategory.SYSTEM, ErrorCategory.NETWORK]:
            return 'high'

        if category in [ErrorCategory.ASSERTION, ErrorCategory.TIMEOUT]:
            return 'medium'

        return 'low'


def format_error_for_display(error_info: ErrorInfo, verbose: bool = False) -> str:
    """Format error information for display.

    Args:
        error_info: ErrorInfo object
        verbose: Whether to include verbose details

    Returns:
            Formatted error message string
    """
    lines = []
    lines.append(f'错误类型: {error_info.type}')
    lines.append(f'错误分类: {error_info.category.value}')
    lines.append(f'错误代码: {error_info.error_code}')
    lines.append(f'严重程度: {error_info.severity}')

    if error_info.timestamp:
        lines.append(f'发生时间: {error_info.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

    lines.append('\n错误信息:')
    lines.append(f'  {error_info.message}')

    if error_info.context:
        lines.append('\n上下文信息:')
        for key, value in error_info.context.items():
            if key not in ['exception_type', 'exception_module']:
                lines.append(f'  {key}: {value}')

    if error_info.suggestion:
        lines.append('\n建议:')
        for suggestion in error_info.suggestion.split('\n'):
            lines.append(f'  • {suggestion}')

    if verbose and error_info.stack_trace:
        lines.append('\n堆栈跟踪:')
        lines.append('  ' + '\n  '.join(error_info.stack_trace.split('\n')))

    return '\n'.join(lines)


def create_error_from_exception(
    exception: Exception,
    step_name: str | None = None,
    additional_context: dict[str, Any] | None = None,
) -> ErrorInfo:
    """Create ErrorInfo from exception with enhanced context.

    Args:
        exception: Exception object
        step_name: Name of the step where error occurred
        additional_context: Additional context information

    Returns:
        Enhanced ErrorInfo object
    """
    context = additional_context or {}
    if step_name:
        context['step_name'] = step_name

    error_info = ErrorClassifier.classify_error(exception, context)

    return error_info
