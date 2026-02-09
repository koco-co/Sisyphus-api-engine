"""Hook Executor for Sisyphus API Engine.

This module implements hook execution for setup/teardown.
Following Google Python Style Guide.
"""

from io import StringIO
import sys
import traceback
from typing import Any


class HookExecutor:
    """Executor for setup/teardown hooks.

    Supports:
    - Python code execution
    - Variable access and modification
    - Error handling and logging
    - Step-level and global-level hooks

    Usage:
        executor = HookExecutor(variable_manager)
        executor.execute(hook_config)
    """

    def __init__(self, variable_manager):
        """Initialize HookExecutor.

        Args:
            variable_manager: Variable manager instance
        """
        self.variable_manager = variable_manager

    def execute(self, hook_config: dict[str, Any] | None) -> None:
        """Execute hook configuration.

        Args:
            hook_config: Hook configuration dictionary
                - type: Hook type (code/function)
                - code: Python code to execute
                - function: Function name to call
                - args: Function arguments

        Raises:
            Exception: If hook execution fails
        """
        if not hook_config:
            return

        hook_type = hook_config.get('type', 'code')

        if hook_type == 'code':
            self._execute_code(hook_config.get('code', ''))
        elif hook_type == 'function':
            self._execute_function(
                hook_config.get('function', ''), hook_config.get('args', {})
            )
        elif hook_type == 'print':
            # Simple print hook for debugging
            message = hook_config.get('message', '')
            print(f'[Hook] {message}')
        else:
            print(f'Warning: Unsupported hook type: {hook_type}')

    def _execute_code(self, code: str) -> None:
        """Execute Python code hook.

        Args:
            code: Python code string to execute

        Raises:
            Exception: If code execution fails
        """
        if not code:
            return

        # Prepare execution context
        context = {
            'variables': self.variable_manager.get_all_variables(),
            'set_variable': self.variable_manager.set_variable,
            'get_variable': self.variable_manager.get_variable,
            'print': print,
        }

        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            # Execute code
            exec(code, context)

            # Get output
            output = sys.stdout.getvalue()
            if output:
                print(f'[Hook Output] {output.strip()}')

            # Restore stdout
            sys.stdout = old_stdout

        except Exception as e:
            sys.stdout = old_stdout
            print(f'Warning: Hook execution failed: {e}')
            if traceback.format_exc():
                print(traceback.format_exc())

    def _execute_function(self, function_name: str, args: dict[str, Any]) -> None:
        """Execute function hook.

        Args:
            function_name: Fully qualified function name
            args: Function arguments

        Raises:
            Exception: If function execution fails
        """
        if not function_name:
            return

        try:
            # Import module and get function
            module_path, func_name = function_name.rsplit('.', 1)
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)

            # Prepare arguments with variable substitution
            context = self.variable_manager.get_all_variables()
            processed_args = self._render_dict(args, context)

            # Execute function
            result = func(**processed_args)

            # Store result if returned
            if result is not None:
                print(f'[Hook Result] {result}')

        except Exception as e:
            print(f'Warning: Hook function execution failed: {e}')

    def _render_dict(self, data: Any, context: dict[str, Any]) -> Any:
        """Render variables in data structure.

        Args:
            data: Data to render
            context: Variable context

        Returns:
            Rendered data
        """
        from apirun.utils.template import render_template

        if isinstance(data, str):
            return render_template(data, context)
        elif isinstance(data, dict):
            return {k: self._render_dict(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._render_dict(item, context) for item in data]
        else:
            return data
