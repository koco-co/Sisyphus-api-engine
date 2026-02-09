"""Script Executor for Sisyphus API Engine.

This module implements custom script execution support, allowing users
to execute Python scripts within test cases for advanced logic.

Following Google Python Style Guide.
"""

import ast
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import io
import sys
import traceback
from typing import Any

from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.executor.step_executor import StepExecutor
from apirun.utils.template import render_template


class ScriptSecurityError(Exception):
    """Exception raised for script security violations."""

    pass


class ScriptSandbox:
    """Sandboxed execution environment for Python scripts.

    This sandbox provides a restricted execution environment while
    allowing safe variable access and manipulation.

    Attributes:
        allowed_modules: Set of allowed module names
        global_vars: Global variables to inject into script context
        local_vars: Local variables from script execution
    """

    # Default allowed modules (safe for testing)
    DEFAULT_ALLOWED_MODULES = {
        'json',
        'datetime',
        'time',
        'random',
        'math',
        're',
        'string',
        'collections',
        'itertools',
        'hashlib',
        'base64',
        'uuid',
    }

    # Blocked built-in functions (security sensitive)
    BLOCKED_BUILTINS = {
        'eval',
        'exec',
        'compile',
        'open',
        'file',
    }

    def __init__(self, variable_manager: VariableManager, allow_imports: bool = True):
        """Initialize ScriptSandbox.

        Args:
            variable_manager: Variable manager for variable sharing
            allow_imports: Whether to allow module imports
        """
        self.variable_manager = variable_manager
        self.allow_imports = allow_imports
        self.global_vars: dict[str, Any] = {}
        self.local_vars: dict[str, Any] = {}
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Setup the sandbox execution environment.

        Creates a safe global namespace with limited built-ins and
        optional module imports.
        """
        # Get safe built-ins
        safe_builtins = {
            name: obj
            for name, obj in __builtins__.items()
            if name not in self.BLOCKED_BUILTINS and not name.startswith('_')
        }

        # Add safe __import__ function
        safe_builtins['__import__'] = self._safe_import

        # Start with safe built-ins
        self.global_vars = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',  # Set __name__ for if __name__ == "__main__" checks
            'print': self._safe_print,
            'True': True,
            'False': False,
            'None': None,
        }

        # Add allowed modules
        if self.allow_imports:
            for module_name in self.DEFAULT_ALLOWED_MODULES:
                try:
                    self._import_module(module_name)
                except ImportError:
                    # Module not available, skip it
                    pass

        # Add variable manager functions
        self.global_vars['get_var'] = self._get_var
        self.global_vars['set_var'] = self._set_var
        self.global_vars['get_all_vars'] = self._get_all_vars

    def _safe_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        """Safe import function that only allows whitelisted modules.

        Args:
            name: Module name to import
            globals: Global namespace (unused)
            locals: Local namespace (unused)
            fromlist: List of names to import from module
            level: Import level (0 for absolute, >0 for relative)

        Returns:
            Imported module

        Raises:
            ImportError: If module is not allowed
        """
        # Check if module is allowed
        if name not in self.DEFAULT_ALLOWED_MODULES:
            raise ImportError(
                f"Module '{name}' is not allowed. "
                f'Allowed modules: {", ".join(sorted(self.DEFAULT_ALLOWED_MODULES))}'
            )

        # Use the real __import__
        return __import__(name, globals, locals, fromlist, level)

    def _import_module(self, module_name: str) -> None:
        """Import a module into the sandbox.

        Args:
            module_name: Name of the module to import

        Raises:
            ScriptSecurityError: If module is not allowed
        """
        if module_name not in self.DEFAULT_ALLOWED_MODULES:
            raise ScriptSecurityError(f"Module '{module_name}' is not allowed")

        __import__(module_name)
        module = sys.modules[module_name]
        self.global_vars[module_name] = module

    def _get_var(self, name: str, default: Any = None) -> Any:
        """Get a variable from the variable manager.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self.variable_manager.get_variable(name, default)

    def _set_var(self, name: str, value: Any) -> None:
        """Set a variable in the variable manager.

        Args:
            name: Variable name
            value: Variable value
        """
        self.variable_manager.set_variable(name, value)

    def _get_all_vars(self) -> dict[str, Any]:
        """Get all variables from the variable manager.

        Returns:
            Dictionary of all variables
        """
        return self.variable_manager.get_all_variables()

    def _safe_print(self, *args, **kwargs) -> None:
        """Safe print function that outputs to stdout.

        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments for print
        """
        # Write directly to stdout so it can be captured by redirect_stdout
        import sys

        print(*args, **kwargs, file=sys.stdout)
        # Also store for later retrieval
        output = io.StringIO()
        print(*args, **kwargs, file=output)
        if not hasattr(self, '_print_output'):
            self._print_output = []
        self._print_output.append(output.getvalue())

    def get_print_output(self) -> list[str]:
        """Get captured print output.

        Returns:
            List of printed strings
        """
        return getattr(self, '_print_output', [])

    def inject_args(self, args: dict[str, Any]) -> None:
        """Inject arguments into the sandbox environment.

        Args:
            args: Dictionary of arguments to inject
        """
        if args:
            self.global_vars.update(args)

    def execute(self, script: str, capture_output: bool = True) -> dict[str, Any]:
        """Execute a script in the sandbox.

        Args:
            script: Python script code to execute
            capture_output: Whether to capture stdout/stderr (default: True)

        Returns:
            Execution result dictionary with output and variables

        Raises:
            ScriptSecurityError: If script violates security rules
            Exception: If script execution fails
        """
        # Clear previous output
        self._print_output = []

        # Parse script to check for security violations
        try:
            tree = ast.parse(script)
            self._check_ast_security(tree)
        except SyntaxError as e:
            raise ScriptSecurityError(f'Syntax error in script: {e}')

        # Execute script
        # Use the same dict for globals and locals to allow recursive function calls
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(
                    compile(tree, filename='<script>', mode='exec'),
                    self.global_vars,
                    self.global_vars,
                )

        except Exception as e:
            # Get full traceback
            tb_lines = traceback.format_exc().split('\n')
            # Filter out internal frames
            filtered_tb = []
            for line in tb_lines:
                if '<script>' in line or 'Traceback' in line or line.strip() == '':
                    filtered_tb.append(line)

            error_msg = f'{type(e).__name__}: {str(e)}'
            raise Exception(
                f'Script execution failed: {error_msg}\n{"".join(filtered_tb[-5:])}'
            )

        # Get output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        print_output = self.get_print_output()

        # Extract new/modified variables (non-system, non-private)
        # We track what was added during this execution
        exported_vars = {}
        system_vars = {
            '__builtins__',
            '__name__',
            'print',
            'True',
            'False',
            'None',
            'get_var',
            'set_var',
            'get_all_vars',
        }

        # Get all allowed modules
        for module_name in self.DEFAULT_ALLOWED_MODULES:
            system_vars.add(module_name)

        # Extract variables that were added in this script execution
        for name, value in self.global_vars.items():
            if not name.startswith('_') and name not in system_vars:
                # Only include if it's not a built-in module or function
                import types

                if (
                    not isinstance(value, types.ModuleType)
                    or name not in self.DEFAULT_ALLOWED_MODULES
                ):
                    exported_vars[name] = value

        return {
            'output': stdout_output,
            'errors': stderr_output,
            'print_output': print_output,
            'variables': exported_vars,
            'success': True,
        }

    def _check_ast_security(self, tree: ast.AST) -> None:
        """Check AST for security violations.

        Args:
            tree: AST tree to check

        Raises:
            ScriptSecurityError: If security violation found
        """
        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.DEFAULT_ALLOWED_MODULES:
                        raise ScriptSecurityError(
                            f"Import of module '{alias.name}' is not allowed"
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.DEFAULT_ALLOWED_MODULES:
                    raise ScriptSecurityError(
                        f"Import from module '{node.module}' is not allowed"
                    )

            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_BUILTINS:
                        raise ScriptSecurityError(
                            f"Use of '{node.func.id}' is not allowed"
                        )


class ScriptExecutor(StepExecutor):
    """Executor for script steps.

    Executes Python scripts with access to test variables and
    optional security restrictions.

    Supports:
    - Python script execution
    - Variable access and modification
    - Module imports (restricted)
    - Output capture
    - Error handling

    Attributes:
        variable_manager: Variable manager instance
        step: Test step to execute
        timeout: Step timeout in seconds
        retry_times: Number of retry attempts
        sandbox: Script sandbox instance
    """

    def __init__(
        self,
        variable_manager: VariableManager,
        step: TestStep,
        timeout: int = 30,
        retry_times: int = 0,
        previous_results=None,
    ):
        """Initialize ScriptExecutor.

        Args:
            variable_manager: Variable manager instance
            step: Test step to execute
            timeout: Default timeout in seconds (default: 30 for script steps)
            retry_times: Default retry count
            previous_results: List of previous step results
        """
        super().__init__(variable_manager, step, timeout, retry_times, previous_results)
        self.sandbox = None

    def _execute_step(self, rendered_step: dict[str, Any]) -> dict[str, Any]:
        """Execute the script step.

        Args:
            rendered_step: Rendered step with variables resolved

        Returns:
            Execution result dictionary

        Raises:
            ValueError: If script configuration is invalid
            ScriptSecurityError: If script violates security rules
            Exception: If script execution fails
        """
        start_time = datetime.now()

        # Get script configuration
        script = rendered_step.get('script')
        script_file = rendered_step.get('script_file')
        script_type = rendered_step.get('script_type', 'python')
        allow_imports = rendered_step.get('allow_imports', True)
        args = rendered_step.get('args', {})
        capture_output = rendered_step.get('capture_output', True)

        # Load script from file if specified
        if script_file and not script:
            script = self._load_script_from_file(script_file)

        if not script:
            raise ValueError("Script step must specify 'script' code or 'script_file'")

        if script_type != 'python':
            raise ValueError(
                f"Unsupported script type: {script_type}. Only 'python' is supported."
            )

        # Create sandbox
        self.sandbox = ScriptSandbox(self.variable_manager, allow_imports=allow_imports)

        # Inject arguments into sandbox as 'args' variable
        if args:
            self.sandbox.global_vars['args'] = args

        # Execute script
        try:
            result = self.sandbox.execute(script, capture_output=capture_output)
        except ScriptSecurityError as e:
            raise ScriptSecurityError(f'Security error: {e}')
        except Exception as e:
            raise Exception(f'Script execution failed: {e}')

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Merge exported variables into variable manager (filter non-serializable)
        if result.get('variables'):
            for var_name, var_value in result['variables'].items():
                # Only set serializable variables
                if self._is_serializable(var_value):
                    self.variable_manager.set_variable(var_name, var_value)

        # Return result
        return {
            'response': {
                'script_type': script_type,
                'script_file': script_file,
                'output': result.get('output', ''),
                'print_output': result.get('print_output', []),
                'errors': result.get('errors', ''),
                'exported_variables': list(result.get('variables', {}).keys()),
                'args': args,
            },
            'performance': self._create_performance_metrics(total_time=elapsed * 1000),
            'extracted_vars': result.get('variables', {}),
        }

    def _load_script_from_file(self, script_file: str) -> str:
        """Load script content from external file.

        Args:
            script_file: Path to the script file

        Returns:
            Script content as string

        Raises:
            ValueError: If file cannot be read
            FileNotFoundError: If file doesn't exist
        """
        from pathlib import Path

        file_path = Path(script_file)

        # Check if file exists
        if not file_path.exists():
            # Try relative to current working directory
            if not file_path.is_absolute():
                # Try relative to test file directory
                import os

                test_dir = Path(os.getcwd())
                file_path = test_dir / script_file

                if not file_path.exists():
                    raise FileNotFoundError(f'Script file not found: {script_file}')

        # Read file content
        try:
            with Path(file_path).open('r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read script file '{script_file}': {e}")

    def _render_step(self) -> dict[str, Any]:
        """Render variables in script step definition.

        Returns:
            Rendered step dictionary
        """
        context = self.variable_manager.get_all_variables()

        rendered = {
            'name': self.step.name,
            'type': self.step.type,
        }

        # Render script (inline)
        if self.step.script:
            rendered['script'] = render_template(self.step.script, context)

        # Render script_file (external file path)
        if self.step.script_file:
            rendered['script_file'] = render_template(self.step.script_file, context)

        # Render args (arguments)
        if self.step.args:
            rendered_args = {}
            for key, value in self.step.args.items():
                if isinstance(value, str):
                    rendered_args[key] = render_template(value, context)
                else:
                    rendered_args[key] = value
            rendered['args'] = rendered_args

        # Render script_type
        if self.step.script_type:
            rendered['script_type'] = self.step.script_type

        # Render allow_imports
        if self.step.allow_imports is not None:
            rendered['allow_imports'] = self.step.allow_imports

        # Render capture_output
        if self.step.capture_output is not None:
            rendered['capture_output'] = self.step.capture_output

        return rendered

    def _is_serializable(self, obj: Any) -> bool:
        """Check if an object is serializable (can be deep copied).

        Args:
            obj: Object to check

        Returns:
            True if serializable, False otherwise
        """
        import types

        # Check for non-serializable types
        if isinstance(obj, (types.ModuleType, types.FunctionType, type(lambda: None))):
            return False

        try:
            import copy

            copy.deepcopy(obj)
            return True
        except (TypeError, AttributeError):
            return False
