"""Step Executor Base Class for Sisyphus API Engine.

This module defines the abstract base class for all step executors.
Following Google Python Style Guide.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import time
import traceback
from typing import Any

from apirun.core.models import (
    ErrorCategory,
    ErrorInfo,
    PerformanceMetrics,
    StepResult,
    TestStep,
)
from apirun.core.retry import RetryManager, create_retry_policy_from_config
from apirun.core.variable_manager import VariableManager
from apirun.utils.logger import get_logger
from apirun.utils.template import render_template


class StepExecutor(ABC):
    """Abstract base class for step executors.

    All step executors should inherit from this class and implement
    the execute() method.

    Attributes:
        variable_manager: Variable manager instance
        step: Test step to execute
        timeout: Step timeout in seconds
        retry_times: Number of retry attempts (legacy, using retry_policy if available)
        retry_manager: Enhanced retry manager
    """

    def __init__(
        self,
        variable_manager: VariableManager,
        step: TestStep,
        timeout: int = 30,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize StepExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds
            retry_times: Default retry count
            previous_results: List of previous step results for dependency checking
        """
        self.variable_manager = variable_manager
        self.step = step
        self.timeout = step.timeout or timeout
        self.retry_times = step.retry_times or retry_times
        self.previous_results = previous_results or []

        # Get logger instance
        self.logger = get_logger()

        # Initialize retry manager
        self.retry_manager = None
        if step.retry_policy:
            try:
                retry_policy = create_retry_policy_from_config(step.retry_policy)
                self.retry_manager = RetryManager(retry_policy)
            except Exception as e:
                print(
                    f'Warning: Failed to parse retry_policy: {e}. Using legacy retry_times.'
                )
        elif self.retry_times > 0:
            # Use legacy retry_times
            from apirun.core.retry import RetryPolicy, RetryStrategy

            policy = RetryPolicy(
                max_attempts=self.retry_times,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay=1.0,
                max_delay=10.0,
            )
            self.retry_manager = RetryManager(policy)

    def execute(self) -> StepResult:
        """Execute the test step.

        This method handles:
        - Step control (skip_if, only_if, depends_on)
        - Variable rendering
        - Enhanced retry logic with history tracking
        - Performance metrics collection
        - Error handling

        Returns:
            StepResult object
        """
        start_time = datetime.now()
        result = StepResult(
            name=self.step.name,
            status='pending',
            start_time=start_time,
            end_time=None,
            retry_count=0,
            variables_snapshot=self.variable_manager.snapshot(),
        )

        try:
            # Log step start
            self.logger.log_step_start(
                step_name=self.step.name,
                step_type=self.step.type,
                description=getattr(self.step, 'description', ''),
            )

            # Check step control conditions
            if not self._should_execute():
                result.status = 'skipped'
                result.end_time = datetime.now()
                self.logger.log_step_end(self.step.name, 'skipped', 0)
                return result

            # Execute setup hooks
            self._execute_setup()

            # Execute with retry logic
            attempt = 0
            last_error = None

            while True:
                attempt_start = datetime.now()
                delay_before = 0

                # Calculate delay before retry (not on first attempt)
                if attempt > 0 and self.retry_manager:
                    delay_before = self.retry_manager.calculate_delay(attempt - 1)
                    if delay_before > 0:
                        # Log retry attempt
                        self.logger.log_retry_attempt(
                            attempt=attempt + 1,
                            max_attempts=self.retry_manager.policy.max_attempts,
                            delay=delay_before,
                            error=str(last_error) if last_error else 'Unknown error',
                        )
                        time.sleep(delay_before)

                try:
                    # Render step variables
                    rendered_step = self._render_step()

                    # Execute step implementation
                    step_result = self._execute_step(rendered_step)

                    # Calculate duration
                    duration = (datetime.now() - attempt_start).total_seconds()

                    # Record successful attempt
                    if self.retry_manager:
                        self.retry_manager.record_attempt(
                            attempt_number=attempt,
                            success=True,
                            delay_before=delay_before,
                            duration=duration,
                        )

                    # Merge step result into result
                    result.status = 'success'

                    # Handle both dict and object return values
                    if isinstance(step_result, dict):
                        if 'response' in step_result:
                            result.response = step_result['response']
                        if 'extracted_vars' in step_result:
                            result.extracted_vars = step_result['extracted_vars']
                        if 'performance' in step_result:
                            result.performance = step_result['performance']
                        if 'validation_results' in step_result:
                            result.validation_results = step_result[
                                'validation_results'
                            ]
                    else:
                        if hasattr(step_result, 'response'):
                            result.response = step_result.response
                        if hasattr(step_result, 'extracted_vars'):
                            result.extracted_vars = step_result.extracted_vars
                        if hasattr(step_result, 'performance'):
                            result.performance = step_result.performance
                        if hasattr(step_result, 'validation_results'):
                            result.validation_results = step_result.validation_results

                    # Extract variables
                    self._extract_variables(result)

                    # Set retry count and history
                    result.retry_count = attempt
                    if self.retry_manager:
                        result.retry_history = self.retry_manager.get_retry_history()

                    # Set end time on success
                    result.end_time = datetime.now()

                    # Calculate total duration
                    total_duration = (result.end_time - start_time).total_seconds()

                    # Log step completion with performance metrics
                    performance_details = {}
                    if result.performance:
                        performance_details = {
                            'total_time': result.performance.total_time,
                            'dns_time': getattr(result.performance, 'dns_time', None),
                            'tcp_time': getattr(result.performance, 'tcp_time', None),
                            'tls_time': getattr(result.performance, 'tls_time', None),
                            'server_time': getattr(
                                result.performance, 'server_time', None
                            ),
                        }

                    self.logger.log_step_end(
                        step_name=self.step.name,
                        status='passed',
                        duration=total_duration,
                        **performance_details,
                    )

                    # Log performance metrics if available
                    if result.performance:
                        self.logger.log_performance_metrics(
                            self.step.name,
                            {
                                'total_time': result.performance.total_time,
                                'dns_time': getattr(
                                    result.performance, 'dns_time', None
                                ),
                                'tcp_time': getattr(
                                    result.performance, 'tcp_time', None
                                ),
                                'tls_time': getattr(
                                    result.performance, 'tls_time', None
                                ),
                                'server_time': getattr(
                                    result.performance, 'server_time', None
                                ),
                            },
                        )

                    # Success - no need to retry
                    break

                except Exception as e:
                    duration = (datetime.now() - attempt_start).total_seconds()
                    last_error = e

                    # Record failed attempt
                    if self.retry_manager:
                        self.retry_manager.record_attempt(
                            attempt_number=attempt,
                            success=False,
                            error=e,
                            delay_before=delay_before,
                            duration=duration,
                        )

                    # Check if should retry
                    should_retry = False
                    if self.retry_manager:
                        should_retry = self.retry_manager.should_retry(e, attempt)
                    elif attempt < self.retry_times:
                        # Legacy retry logic
                        should_retry = True

                    if should_retry:
                        attempt += 1
                        # Use legacy backoff if no retry manager
                        if not self.retry_manager:
                            time.sleep(min(2**attempt, 10))  # Exponential backoff
                        continue
                    else:
                        # Final attempt failed - but preserve any partial results
                        result.retry_count = attempt
                        if self.retry_manager:
                            result.retry_history = (
                                self.retry_manager.get_retry_history()
                            )

                        # Try to extract response from the exception if available
                        # Some exceptions may contain partial response data
                        if hasattr(e, '__dict__'):
                            for key, value in e.__dict__.items():
                                if key == 'response' and value is not None:
                                    result.response = value
                                    break

                        raise

            # Execute teardown hooks
            self._execute_teardown()

        except Exception as e:
            result.status = 'failure'
            result.error_info = self._create_error_info(e)
            result.end_time = datetime.now()

            # IMPORTANT: Try to preserve response data even on failure
            # Check if exception contains response information
            if hasattr(e, '__dict__') and not result.response:
                for key, value in e.__dict__.items():
                    if key == 'response' and value is not None:
                        result.response = value
                        break

        # Ensure end_time is set
        if result.end_time is None:
            result.end_time = datetime.now()

        return result

    @abstractmethod
    def _execute_step(self, rendered_step: dict[str, Any]) -> Any:
        """Execute the actual step implementation.

        Subclasses must implement this method.

        Args:
            rendered_step: Step with rendered variables

        Returns:
            Execution result with response/performance/validation data

        Raises:
            Exception: If execution fails
        """
        raise NotImplementedError('Subclasses must implement _execute_step()')

    def _should_execute(self) -> bool:
        """Check if step should be executed based on control conditions.

        Returns:
            True if step should execute, False to skip
        """
        # Import condition evaluator
        from apirun.core.condition_evaluator import ConditionEvaluator

        variables = self.variable_manager.get_all_variables()
        evaluator = ConditionEvaluator(variables)

        # Check skip_if condition
        if self.step.skip_if:
            try:
                should_skip = evaluator.evaluate(self.step.skip_if)
                if should_skip:
                    return False
            except Exception as e:
                # If evaluation fails, log warning but don't skip
                import warnings

                warnings.warn(
                    f"Failed to evaluate skip_if condition '{self.step.skip_if}': {e}"
                )

        # Check only_if condition
        if self.step.only_if:
            try:
                should_execute = evaluator.evaluate(self.step.only_if)
                if not should_execute:
                    return False
            except Exception as e:
                # If evaluation fails, log warning but don't execute
                import warnings

                warnings.warn(
                    f"Failed to evaluate only_if condition '{self.step.only_if}': {e}"
                )
                return False

        # Check generic condition field (skip for wait steps where condition is a parameter)
        if self.step.condition and self.step.type != 'wait':
            try:
                condition_met = evaluator.evaluate(self.step.condition)
                if not condition_met:
                    return False
            except Exception as e:
                # If evaluation fails, log warning but don't execute
                import warnings

                warnings.warn(
                    f"Failed to evaluate condition '{self.step.condition}': {e}"
                )
                return False

        # Check depends_on conditions
        if self.step.depends_on:
            # Check if all dependency steps succeeded
            for dep_step_name in self.step.depends_on:
                dep_found = False
                for result in self.previous_results:
                    if result.name == dep_step_name:
                        dep_found = True
                        # Skip if dependency failed
                        if result.status != 'success':
                            return False
                        break
                # Skip if dependency step not found
                if not dep_found:
                    return False

        return True

    def _render_step(self) -> dict[str, Any]:
        """Render variables in step definition.

        Returns:
            Rendered step dictionary
        """
        context = self.variable_manager.get_all_variables()

        rendered = {
            'name': self.step.name,
            'type': self.step.type,
        }

        if self.step.method:
            rendered['method'] = self.step.method

        if self.step.url:
            rendered['url'] = render_template(self.step.url, context)

        if self.step.params:
            rendered['params'] = self.variable_manager.render_dict(self.step.params)

        if self.step.headers:
            rendered['headers'] = self.variable_manager.render_dict(self.step.headers)

        if self.step.body is not None:
            if isinstance(self.step.body, str):
                rendered['body'] = render_template(self.step.body, context)
            elif isinstance(self.step.body, dict):
                rendered['body'] = self.variable_manager.render_dict(self.step.body)
            else:
                rendered['body'] = self.step.body

        # Render database-specific fields
        if self.step.database:
            rendered['database'] = self.variable_manager.render_dict(self.step.database)

        if self.step.sql:
            rendered['sql'] = render_template(self.step.sql, context)

        if self.step.operation:
            rendered['operation'] = self.step.operation

        # Render validations
        if self.step.validations:
            rendered['validations'] = []
            for val in self.step.validations:
                rendered_val = self._render_validation(val, context)
                rendered['validations'].append(rendered_val)

        # Render extractors
        if self.step.extractors:
            rendered['extractors'] = []
            for ext in self.step.extractors:
                rendered['extractors'].append({
                    'name': ext.name,
                    'type': ext.type,
                    'path': ext.path,
                    'index': ext.index,
                })

        return rendered

    def _render_validation(self, val: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Render validation rule with template support.

        Args:
            val: ValidationRule object
            context: Template context

        Returns:
            Rendered validation dictionary
        """
        from apirun.core.models import ValidationRule

        if not isinstance(val, ValidationRule):
            return val

        rendered_val = {
            'type': val.type,
            'path': val.path,
            'expect': render_template(str(val.expect), context)
            if isinstance(val.expect, str)
            else val.expect,
            'description': val.description,
        }

        # Add logical operator support
        if val.logical_operator:
            rendered_val['logical_operator'] = val.logical_operator
            # Recursively render sub_validations
            if val.sub_validations:
                rendered_val['sub_validations'] = []
                for sub_val in val.sub_validations:
                    rendered_sub_val = self._render_validation(sub_val, context)
                    rendered_val['sub_validations'].append(rendered_sub_val)

        return rendered_val

    def _extract_variables(self, result: StepResult) -> None:
        """Extract variables from step result.

        Args:
            result: Step result containing response data
        """
        from apirun.extractor.extractor_factory import ExtractorFactory

        if not self.step.extractors or not result.response:
            return

        extractor_factory = ExtractorFactory()

        # For request steps, extract from response body by default (like validation)
        # This allows users to use $.code instead of $.body.code
        extraction_data = result.response
        if isinstance(result.response, dict) and 'body' in result.response:
            # Check if extractor type is jsonpath - if so, use body as default
            # For other extractors (header, cookie), they work on the full response
            first_extractor_type = (
                self.step.extractors[0].type if self.step.extractors else None
            )
            if first_extractor_type in ['jsonpath', 'regex']:
                extraction_data = result.response.get('body', result.response)

        for extractor_def in self.step.extractors:
            try:
                # Check condition before extraction if specified
                if extractor_def.condition:
                    condition_met = self._evaluate_condition(
                        extractor_def.condition,
                        extraction_data
                        if extractor_def.type in ['jsonpath', 'regex']
                        else result.response,
                    )

                    if not condition_met:
                        # Condition not met, use default value if specified
                        if (
                            extractor_def.on_failure
                            and 'use_default' in extractor_def.on_failure
                        ):
                            default_value = extractor_def.on_failure['use_default']
                            self.variable_manager.set_variable(
                                extractor_def.name, default_value
                            )
                            result.extracted_vars[extractor_def.name] = default_value
                            print(
                                f"ℹ️  条件不满足，使用默认值: '{extractor_def.name}' = {default_value}"
                            )
                        elif extractor_def.default is not None:
                            self.variable_manager.set_variable(
                                extractor_def.name, extractor_def.default
                            )
                            result.extracted_vars[extractor_def.name] = (
                                extractor_def.default
                            )
                            print(
                                f"ℹ️  条件不满足，使用默认值: '{extractor_def.name}' = {extractor_def.default}"
                            )
                        else:
                            print(f"⚠️  条件不满足且无默认值: '{extractor_def.name}'")
                        continue

                extractor = extractor_factory.create_extractor(extractor_def.type)

                # Choose data source based on extractor type
                if extractor_def.type in ['jsonpath', 'regex']:
                    # jsonpath and regex extractors work on body by default
                    # Backward compatibility: if path starts with "$.body.", use full response
                    path = extractor_def.path
                    if isinstance(result.response, dict):
                        if path.startswith('$.body.'):
                            # Old-style path with explicit $.body. prefix
                            data_source = result.response
                        elif path.startswith('$'):
                            # New-style path without $.body. prefix, auto-extract from body
                            data_source = result.response.get('body', result.response)
                        else:
                            # Non-JSONPath path, use body
                            data_source = result.response.get('body', result.response)
                    else:
                        data_source = result.response
                elif extractor_def.type == 'header':
                    # header extractor works on full response (extracts headers internally)
                    data_source = result.response
                elif extractor_def.type == 'cookie':
                    # cookie extractor works on full response (extracts cookies internally)
                    data_source = result.response
                else:
                    # Other extractors use full response
                    data_source = result.response

                # Handle extract_all parameter: if True, use index=-1 to get all matches
                extract_index = -1 if extractor_def.extract_all else extractor_def.index

                value = extractor.extract(
                    extractor_def.path,
                    data_source,
                    extract_index,
                    extractor_def.default,
                )

                if value is not None:
                    old_value = self.variable_manager.get_variable(
                        extractor_def.name, None
                    )
                    self.variable_manager.set_variable(extractor_def.name, value)
                    result.extracted_vars[extractor_def.name] = value

                    # Log successful extraction
                    self.logger.log_extraction_success(
                        extractor_def.name, extractor_def.path, value
                    )

                    # Log variable change
                    self.logger.log_variable_change(
                        extractor_def.name, old_value, value, 'extraction'
                    )
                else:
                    # Extraction returned None - use logger
                    self.logger.log_extraction_failure(
                        extractor_def.name, extractor_def.path, '未找到匹配的数据'
                    )

            except Exception as e:
                # Extraction failed with error - use logger
                self.logger.log_extraction_failure(
                    extractor_def.name, extractor_def.path, str(e)
                )
                print(f'   错误详情: {type(e).__name__}: {e}')

                # Provide specific suggestions based on error type
                if 'JSONPath' in str(e):
                    print('   💡 JSONPath 路径建议:')
                    print("      • 检查路径是否以 '$' 开头")
                    print('      • 验证数组索引: $.data[0].field')
                    print('      • 确认字段名称拼写正确')
                elif 'regex' in str(e).lower() or 'pattern' in str(e).lower():
                    print('   💡 Regex 表达式建议:')
                    print('      • 验证正则表达式语法')
                    print(f'      • 检查捕获组索引 (group: {extractor_def.index})')
                    print('      • 确保模式与响应数据匹配')
                elif 'No value found' in str(e):
                    print('   💡 数据匹配建议:')
                    print('      • 确认响应中包含目标字段')
                    print('      • 检查字段名是否区分大小写')
                    print('      • 尝试使用更通用的路径表达式')
                else:
                    print('   💡 通用建议:')
                    print('      • 使用 -v 参数查看详细响应数据')
                    print('      • 检查 API 响应格式是否符合预期')

    @staticmethod
    def _evaluate_condition(condition: str, data_source: Any) -> bool:
        """Evaluate a condition expression against data source.

        支持的操作符:
        - 比较操作符: ==, !=, >, <, >=, <=
        - 逻辑操作符: and, or
        - 成员操作符: in, not in (用于数组/字符串)
        - 包含操作符: contains (检查字符串/数组是否包含)
        - 存在性检查: 直接使用路径 (如 "$.data" 检查字段是否存在)

        支持括号改变优先级,如: "$.a == 1 and ($.b == 2 or $.c == 3)"

        Args:
            condition: Condition expression (e.g., "$.code == 1 and $.data != null")
            data_source: Data to evaluate condition against

        Returns:
            True if condition is met, False otherwise
        """

        try:
            # 首先处理括号 - 找到最内层的括号并先评估
            while '(' in condition and ')' in condition:
                # 找到第一个匹配的括号对
                start = condition.find('(')
                end = start + 1
                depth = 1
                while end < len(condition) and depth > 0:
                    if condition[end] == '(':
                        depth += 1
                    elif condition[end] == ')':
                        depth -= 1
                    end += 1

                if depth == 0:
                    # 提取括号内的表达式
                    sub_expr = condition[start + 1 : end - 1]
                    # 递归评估子表达式
                    result = StepExecutor._evaluate_condition(sub_expr, data_source)
                    # 将结果替换回表达式
                    condition = (
                        condition[:start]
                        + ('true' if result else 'false')
                        + condition[end:]
                    )
                else:
                    # 括号不匹配,跳过括号处理
                    break

            # 处理 AND 逻辑 (优先级高于 OR)
            if ' and ' in condition.lower():
                parts = StepExecutor._split_by_operators(condition, [' and '])
                results = []
                for part in parts:
                    results.append(
                        StepExecutor._evaluate_condition(part.strip(), data_source)
                    )
                return all(results)

            # 处理 OR 逻辑
            elif ' or ' in condition.lower():
                parts = StepExecutor._split_by_operators(condition, [' or '])
                results = []
                for part in parts:
                    results.append(
                        StepExecutor._evaluate_condition(part.strip(), data_source)
                    )
                return any(results)

            # 处理简单的布尔值
            elif condition.lower().strip() == 'true':
                return True
            elif condition.lower().strip() == 'false':
                return False

            # 处理简单条件
            else:
                return StepExecutor._evaluate_simple_condition(
                    condition.strip(), data_source
                )

        except Exception as e:
            print(f'⚠️  条件评估失败: {condition}')
            print(f'   错误: {e}')
            # If condition evaluation fails, proceed with extraction
            return True

    @staticmethod
    def _split_by_operators(expression: str, operators: list[str]) -> list[str]:
        """Split expression by operators, respecting quoted strings.

        Args:
            expression: Expression to split
            operators: List of operators to split by (in order of priority)

        Returns:
            List of expression parts
        """
        # Split but keep track of quoted strings
        parts = []
        current = []
        in_quotes = False
        quote_char = None
        i = 0

        while i < len(expression):
            char = expression[i]

            # Handle quotes
            if char in '"\'':
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current.append(char)
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                    current.append(char)
                else:
                    current.append(char)
                i += 1
            elif in_quotes:
                current.append(char)
                i += 1
            else:
                # Check for operator matches
                matched = False
                for op in sorted(operators, key=len, reverse=True):
                    if expression[i : i + len(op)].lower() == op.lower():
                        if current:
                            parts.append(''.join(current))
                            current = []
                        i += len(op)
                        matched = True
                        break
                if not matched:
                    current.append(char)
                    i += 1

        if current:
            parts.append(''.join(current))

        return parts

    @staticmethod
    def _evaluate_simple_condition(condition: str, data_source: Any) -> bool:
        """Evaluate a simple condition (no and/or).

        支持的操作符:
        - 比较操作符: ==, !=, >, <, >=, <=
        - 成员操作符: in, not in
        - 包含操作符: contains

        Args:
            condition: Simple condition expression
            data_source: Data to evaluate against

        Returns:
            True if condition is met, False otherwise
        """
        import re

        from apirun.utils.enhanced_jsonpath import EnhancedJSONPath

        # 优先检查多词操作符: in, not in, contains
        # 模式: path in value, path not in value, path contains value
        multi_op_pattern = r'(\$[^\s]+)\s*(in|not in|contains)\s*(.+)'
        multi_match = re.match(multi_op_pattern, condition.strip(), re.IGNORECASE)

        if multi_match:
            path, operator, expected_value = multi_match.groups()
            operator = operator.lower()
            jsonpath = EnhancedJSONPath()

            try:
                # Extract actual value from data source
                actual_value = jsonpath.extract(path, data_source, 0)

                # Convert expected value
                expected_value = StepExecutor._convert_condition_value(
                    expected_value.strip()
                )

                # Perform operation
                if operator == 'in':
                    # Check if value is in array/string
                    if isinstance(actual_value, (list, tuple)):
                        return expected_value in actual_value
                    elif isinstance(actual_value, str):
                        return str(expected_value) in actual_value
                    return False

                elif operator == 'not in':
                    # Check if value is NOT in array/string
                    if isinstance(actual_value, (list, tuple)):
                        return expected_value not in actual_value
                    elif isinstance(actual_value, str):
                        return str(expected_value) not in actual_value
                    return False

                elif operator == 'contains':
                    # Check if array/string contains value
                    if isinstance(actual_value, (list, tuple)):
                        return expected_value in actual_value
                    elif isinstance(actual_value, str):
                        return str(expected_value) in actual_value
                    return False

            except Exception:
                return False

        # 检查标准比较操作符: ==, !=, >, <, >=, <=
        # 模式: "$.path == value"
        match = re.match(r'(\$[^\s]+)\s*(==|!=|>=|<=|>|<)\s*(.+)', condition.strip())
        if match:
            path, operator, expected_value = match.groups()
            jsonpath = EnhancedJSONPath()

            try:
                # Extract value from data source
                actual_value = jsonpath.extract(path, data_source, 0)

                # Convert expected value to appropriate type
                expected_value = StepExecutor._convert_condition_value(
                    expected_value.strip()
                )

                # Perform comparison
                if operator == '==':
                    return actual_value == expected_value
                elif operator == '!=':
                    return actual_value != expected_value
                elif operator == '>':
                    return actual_value is not None and actual_value > expected_value
                elif operator == '<':
                    return actual_value is not None and actual_value < expected_value
                elif operator == '>=':
                    return actual_value is not None and actual_value >= expected_value
                elif operator == '<=':
                    return actual_value is not None and actual_value <= expected_value
                else:
                    return False

            except Exception:
                return False

        # If no match, check if the path exists (existence check)
        elif condition.startswith('$'):
            jsonpath = EnhancedJSONPath()
            try:
                value = jsonpath.extract(condition, data_source, 0)
                return value is not None
            except Exception:
                return False

        return False

    @staticmethod
    def _convert_condition_value(value: str) -> Any:
        """Convert string value to appropriate Python type.

        Args:
            value: String value from condition

        Returns:
            Converted value (bool, int, float, str, None)
        """
        value_lower = value.lower()

        # Boolean values
        if value_lower == 'true':
            return True
        elif value_lower == 'false':
            return False

        # Null value
        elif value_lower == 'null':
            return None

        # Quoted string
        elif (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Numeric values
        else:
            # Try to convert to number
            try:
                # Check for negative number or decimal
                if value.startswith('-') or '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                # Return as string if not a number
                return value

    def _execute_setup(self) -> None:
        """Execute setup hooks.

        Setup hooks are executed before the step.
        """
        if not self.step.setup:
            return

        from apirun.utils.hooks import HookExecutor

        hook_executor = HookExecutor(self.variable_manager)
        hook_executor.execute(self.step.setup)

    def _execute_teardown(self) -> None:
        """Execute teardown hooks.

        Teardown hooks are executed after the step (even on failure).
        """
        if not self.step.teardown:
            return

        from apirun.utils.hooks import HookExecutor

        hook_executor = HookExecutor(self.variable_manager)
        hook_executor.execute(self.step.teardown)

    def _create_error_info(self, exception: Exception) -> ErrorInfo:
        """Create ErrorInfo from exception.

        Args:
            exception: Exception instance

        Returns:
            ErrorInfo object
        """
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()

        # Categorize error
        category = ErrorCategory.SYSTEM
        if 'Assertion' in error_type or 'validation' in error_message.lower():
            category = ErrorCategory.ASSERTION
        elif 'timeout' in error_message.lower():
            category = ErrorCategory.TIMEOUT
        elif (
            'connection' in error_message.lower() or 'network' in error_message.lower()
        ):
            category = ErrorCategory.NETWORK
        elif 'parse' in error_message.lower():
            category = ErrorCategory.PARSING

        # Generate suggestion
        suggestion = self._generate_error_suggestion(category, error_message)

        return ErrorInfo(
            type=error_type,
            category=category,
            message=error_message,
            suggestion=suggestion,
            stack_trace=stack_trace,
        )

    def _generate_error_suggestion(self, category: ErrorCategory, message: str) -> str:
        """Generate error suggestion based on category and message.

        Args:
            category: Error category
            message: Error message

        Returns:
            Suggestion text
        """
        suggestions = {
            ErrorCategory.ASSERTION: '建议检查预期值设置是否正确，或查看实际响应数据',
            ErrorCategory.NETWORK: '建议检查网络连接、URL 地址和端口是否正确',
            ErrorCategory.TIMEOUT: '建议增加超时时间配置或检查服务响应速度',
            ErrorCategory.PARSING: '建议检查响应数据格式是否与预期一致',
            ErrorCategory.BUSINESS: '建议检查业务逻辑配置',
            ErrorCategory.SYSTEM: '建议查看系统日志获取详细信息',
        }

        message_lower = message.lower()
        if category == ErrorCategory.NETWORK and 'dns' in message_lower:
            return '建议检查 DNS 配置或目标域名是否可解析'
        if category == ErrorCategory.TIMEOUT and 'read' in message_lower:
            return '建议增加读取超时，或排查服务端慢查询/慢响应'
        if category == ErrorCategory.PARSING and 'json' in message_lower:
            return '建议检查响应是否为合法 JSON，或调整提取/断言路径'

        return suggestions.get(category, '请联系技术支持获取帮助')

    def _create_performance_metrics(
        self,
        total_time: float = 0.0,
        dns_time: float = 0.0,
        tcp_time: float = 0.0,
        tls_time: float = 0.0,
        server_time: float = 0.0,
        download_time: float = 0.0,
        upload_time: float = 0.0,
        size: int = 0,
    ) -> PerformanceMetrics:
        """Create PerformanceMetrics object.

        Args:
            total_time: Total execution time in milliseconds
            dns_time: DNS lookup time in milliseconds
            tcp_time: TCP connection time in milliseconds
            tls_time: TLS handshake time in milliseconds
            server_time: Server processing time in milliseconds
            download_time: Download time in milliseconds
            upload_time: Upload time in milliseconds
            size: Response size in bytes

        Returns:
            PerformanceMetrics object
        """
        return PerformanceMetrics(
            total_time=total_time,
            dns_time=dns_time,
            tcp_time=tcp_time,
            tls_time=tls_time,
            server_time=server_time,
            download_time=download_time,
            upload_time=upload_time,
            size=size,
        )
