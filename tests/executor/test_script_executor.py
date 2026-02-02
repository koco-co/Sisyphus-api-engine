"""Unit tests for ScriptExecutor.

Tests for script executor in apirun/executor/script_executor.py
Following Google Python Style Guide.
"""

import pytest
from apirun.executor.script_executor import ScriptExecutor, ScriptSandbox, ScriptSecurityError
from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager


class TestScriptSandbox:
    """Tests for ScriptSandbox class."""

    def test_initialization(self):
        """Test ScriptSandbox initialization."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        assert sandbox.variable_manager == var_manager
        assert sandbox.allow_imports is True
        assert isinstance(sandbox.global_vars, dict)
        assert isinstance(sandbox.local_vars, dict)

    def test_initialization_without_imports(self):
        """Test ScriptSandbox initialization without imports."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager, allow_imports=False)

        assert sandbox.allow_imports is False
        assert "json" not in sandbox.global_vars

    def test_execute_simple_script(self):
        """Test executing a simple script."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        script = """
x = 10
y = 20
result = x + y
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        assert result["variables"]["x"] == 10
        assert result["variables"]["y"] == 20
        assert result["variables"]["result"] == 30

    def test_execute_script_with_print(self):
        """Test script with print statements."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        script = """
print("Hello, World!")
print("Test output")
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        assert len(result["print_output"]) == 2
        assert "Hello, World!" in result["print_output"][0]

    def test_execute_script_with_syntax_error(self):
        """Test script with syntax error."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        script = """
x = 10
y = 20
invalid syntax here
"""

        with pytest.raises(Exception) as exc_info:
            sandbox.execute(script)

        assert "Syntax error" in str(exc_info.value)

    def test_execute_script_with_runtime_error(self):
        """Test script with runtime error."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        script = """
x = 10
y = 0
result = x / y
"""

        with pytest.raises(Exception) as exc_info:
            sandbox.execute(script)

        assert "division by zero" in str(exc_info.value) or "ZeroDivisionError" in str(exc_info.value)

    def test_variable_get_var(self):
        """Test get_var function in sandbox."""
        var_manager = VariableManager()
        var_manager.set_variable("test_var", "test_value")

        sandbox = ScriptSandbox(var_manager)

        script = """
value = get_var("test_var")
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        assert result["variables"]["value"] == "test_value"

    def test_variable_set_var(self):
        """Test set_var function in sandbox."""
        var_manager = VariableManager()

        sandbox = ScriptSandbox(var_manager)

        script = """
set_var("new_var", "new_value")
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        assert var_manager.get_variable("new_var") == "new_value"

    def test_variable_get_all_vars(self):
        """Test get_all_vars function in sandbox."""
        var_manager = VariableManager()
        var_manager.set_variable("var1", "value1")
        var_manager.set_variable("var2", "value2")

        sandbox = ScriptSandbox(var_manager)

        script = """
all_vars = get_all_vars()
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        assert "var1" in result["variables"]["all_vars"]
        assert "var2" in result["variables"]["all_vars"]

    def test_safe_import_allowed_module(self):
        """Test importing an allowed module."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager, allow_imports=True)

        script = """
import json
data = json.dumps({"key": "value"})
"""

        result = sandbox.execute(script)

        assert result["success"] is True
        # json module should not be in exported variables (it's a system module)
        assert "json" not in result["variables"]
        # User-created variable should be exported
        assert result["variables"]["data"] == '{"key": "value"}'

    def test_safe_import_blocked_module(self):
        """Test importing a blocked module."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager, allow_imports=True)

        script = """
import os
"""

        with pytest.raises((ImportError, ScriptSecurityError)) as exc_info:
            sandbox.execute(script)

        assert "not allowed" in str(exc_info.value)

    def test_blocked_builtin_functions(self):
        """Test that blocked built-ins are not available."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        # Test eval
        script = """
eval("print('test')")
"""
        with pytest.raises(ScriptSecurityError) as exc_info:
            sandbox.execute(script)
        assert "not allowed" in str(exc_info.value)

    def test_import_from_allowed_module(self):
        """Test importing from allowed module."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager, allow_imports=True)

        script = """
from datetime import datetime
dt = datetime.now()
"""

        result = sandbox.execute(script)

        assert result["success"] is True

    def test_import_from_blocked_module(self):
        """Test importing from blocked module."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager, allow_imports=True)

        script = """
from os import path
"""

        with pytest.raises(ScriptSecurityError) as exc_info:
            sandbox.execute(script)

        assert "not allowed" in str(exc_info.value)

    def test_get_print_output(self):
        """Test getting captured print output."""
        var_manager = VariableManager()
        sandbox = ScriptSandbox(var_manager)

        script = """
print("Line 1")
print("Line 2")
print("Line 3")
"""

        sandbox.execute(script)
        output = sandbox.get_print_output()

        assert len(output) == 3
        assert "Line 1" in output[0]
        assert "Line 2" in output[1]
        assert "Line 3" in output[2]


class TestScriptExecutor:
    """Tests for ScriptExecutor class."""

    def test_initialization(self):
        """Test ScriptExecutor initialization."""
        var_manager = VariableManager()
        step = TestStep(name="script_step", type="script")

        executor = ScriptExecutor(var_manager, step)

        assert executor.variable_manager == var_manager
        assert executor.step == step
        assert executor.sandbox is None

    def test_execute_python_script(self):
        """Test executing Python script."""
        var_manager = VariableManager()

        step = TestStep(
            name="python_script",
            type="script",
            script="""
x = 10
result = x * 2
""",
            script_type="python",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert result.response["script_type"] == "python"
        # Check that variables are in variable manager
        assert var_manager.get_variable("x") == 10
        assert var_manager.get_variable("result") == 20

    def test_execute_script_without_script_code(self):
        """Test script executor without script code."""
        var_manager = VariableManager()

        step = TestStep(
            name="empty_script",
            type="script",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None
        assert "script" in result.error_info.message

    def test_execute_script_with_unsupported_type(self):
        """Test script executor with unsupported script type."""
        var_manager = VariableManager()

        step = TestStep(
            name="invalid_type",
            type="script",
            script="print('test')",
            script_type="javascript",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None
        assert "Only 'python' is supported" in result.error_info.message

    def test_execute_script_with_variable_substitution(self):
        """Test script with variable substitution."""
        var_manager = VariableManager()
        var_manager.set_variable("multiplier", "5")

        step = TestStep(
            name="var_script",
            type="script",
            script="""
result = 10 * ${multiplier}
""",
            script_type="python",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert var_manager.get_variable("result") == 50

    def test_execute_script_with_allow_imports_false(self):
        """Test script with imports disabled."""
        var_manager = VariableManager()

        step = TestStep(
            name="no_imports",
            type="script",
            script="""
x = 10
result = x * 2
""",
            script_type="python",
            allow_imports=False,
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"

    def test_execute_script_with_security_violation(self):
        """Test script with security violation."""
        var_manager = VariableManager()

        step = TestStep(
            name="security_violation",
            type="script",
            script="""
import os
""",
            script_type="python",
            allow_imports=True,
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "failure"
        assert result.error_info is not None

    def test_render_step(self):
        """Test _render_step method."""
        var_manager = VariableManager()
        var_manager.set_variable("value", "42")

        step = TestStep(
            name="render_test",
            type="script",
            script="x = ${value}",
            script_type="python",
            allow_imports=True,
        )

        executor = ScriptExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["script"] == "x = 42"
        assert rendered["script_type"] == "python"
        assert rendered["allow_imports"] is True

    def test_is_serializable(self):
        """Test _is_serializable method."""
        var_manager = VariableManager()
        step = TestStep(name="test", type="script")

        executor = ScriptExecutor(var_manager, step)

        # Serializable objects
        assert executor._is_serializable(10) is True
        assert executor._is_serializable("test") is True
        assert executor._is_serializable([1, 2, 3]) is True
        assert executor._is_serializable({"key": "value"}) is True

        # Non-serializable objects - lambdas and functions are not serializable
        assert executor._is_serializable(lambda x: x) is False


class TestScriptExecutorScenarios:
    """Test real-world script scenarios."""

    def test_data_transformation_script(self):
        """Test script for data transformation."""
        var_manager = VariableManager()
        var_manager.set_variable("raw_data", '{"name": "test", "value": 123}')

        step = TestStep(
            name="transform_data",
            type="script",
            script="""
import json
data = json.loads('${raw_data}')
transformed = {"item_name": data["name"], "item_value": data["value"] * 2}
""",
            script_type="python",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        # Variables are set in the variable manager
        transformed = var_manager.get_variable("transformed")
        assert transformed["item_name"] == "test"
        assert transformed["item_value"] == 246

    def test_custom_validation_script(self):
        """Test script for custom validation."""
        var_manager = VariableManager()
        var_manager.set_variable("response_code", "200")
        var_manager.set_variable("response_body", '{"status": "ok"}')

        step = TestStep(
            name="custom_validation",
            type="script",
            script="""
import json
code = ${response_code}
body = json.loads('${response_body}')
is_valid = (code == 200 and body.get("status") == "ok")
""",
            script_type="python",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert var_manager.get_variable("is_valid") is True


class TestScriptExecutorEnhancements:
    """Test enhanced script features: external files, arguments, output capture."""

    def test_execute_script_with_args(self):
        """Test script execution with arguments."""
        var_manager = VariableManager()

        step = TestStep(
            name="test_args",
            type="script",
            script="""
api_url = args.get("api_url", "default")
config_name = args.get("config_name", "default")
result = {"url": api_url, "config": config_name}
""",
            script_type="python",
            args={"api_url": "https://api.example.com", "config_name": "test_config"},
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        result_data = var_manager.get_variable("result")
        assert result_data["url"] == "https://api.example.com"
        assert result_data["config"] == "test_config"

    def test_execute_script_with_file(self, tmp_path):
        """Test script execution from external file."""
        import os

        # Create a temporary script file
        script_file = tmp_path / "test_script.py"
        script_file.write_text("""
# Simple test script
def multiply(a, b):
    return a * b

result = multiply(5, 3)
print(f"Multiplication result: {result}")
""")

        var_manager = VariableManager()

        step = TestStep(
            name="test_file",
            type="script",
            script_file=str(script_file),
            script_type="python",
            allow_imports=True,
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert var_manager.get_variable("result") == 15

    def test_execute_script_with_recursive_function(self):
        """Test script with recursive function calls."""
        var_manager = VariableManager()

        step = TestStep(
            name="test_recursive",
            type="script",
            script="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
""",
            script_type="python",
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        assert var_manager.get_variable("result") == 55

    def test_execute_script_output_capture(self):
        """Test script output capture."""
        var_manager = VariableManager()

        step = TestStep(
            name="test_capture",
            type="script",
            script="""
print("Line 1")
print("Line 2")
result = "test"
""",
            script_type="python",
            capture_output=True,
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        # Check that output was captured
        assert "Line 1" in result.response["output"]
        assert "Line 2" in result.response["output"]
        assert var_manager.get_variable("result") == "test"

    def test_execute_script_without_output_capture(self):
        """Test script execution without output capture."""
        var_manager = VariableManager()

        step = TestStep(
            name="test_no_capture",
            type="script",
            script="""
print("This should not be captured")
result = "test"
""",
            script_type="python",
            capture_output=False,
        )

        executor = ScriptExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == "success"
        # Result should still have output but capture_output=False doesn't prevent execution
        assert var_manager.get_variable("result") == "test"

    def test_render_step_with_new_fields(self):
        """Test rendering steps with new script fields."""
        var_manager = VariableManager()
        var_manager.set_variable("base_path", "/scripts")

        step = TestStep(
            name="test_render",
            type="script",
            script_file="${base_path}/test.py",
            args={"param1": "${base_path}"},
            script_type="python",
            allow_imports=True,
            capture_output=True,
        )

        executor = ScriptExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered["script_file"] == "/scripts/test.py"
        assert rendered["args"]["param1"] == "/scripts"
        assert rendered["script_type"] == "python"
        assert rendered["allow_imports"] is True
        assert rendered["capture_output"] is True

