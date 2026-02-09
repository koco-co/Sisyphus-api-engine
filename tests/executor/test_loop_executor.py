"""Unit tests for LoopExecutor.

Tests for loop executor in apirun/executor/loop_executor.py
Following Google Python Style Guide.
"""

from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.executor.loop_executor import LoopExecutor


class TestLoopExecutor:
    """Tests for LoopExecutor class."""

    def test_initialization(self):
        """Test LoopExecutor initialization."""
        var_manager = VariableManager()
        step = TestStep(name='loop_step', type='loop')

        executor = LoopExecutor(var_manager, step)

        assert executor.variable_manager == var_manager
        assert executor.step == step
        assert executor.loop_results == []
        assert executor.timeout == 300  # default for loop steps

    def test_for_loop_basic(self):
        """Test basic for loop execution."""
        var_manager = VariableManager()

        # Simple loop with wait steps (avoiding network calls)
        step = TestStep(
            name='test_for_loop',
            type='loop',
            loop_type='for',
            loop_count=3,
            loop_variable='i',
            loop_steps=[
                {
                    'name': 'wait_step',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['loop_type'] == 'for'
        assert result.response['loop_count'] == 3
        assert result.response['iterations'] == 3
        assert result.response['success_count'] == 3
        assert result.response['failure_count'] == 0

    def test_for_loop_without_loop_count(self):
        """Test for loop without loop_count."""
        var_manager = VariableManager()

        step = TestStep(
            name='invalid_for_loop',
            type='loop',
            loop_type='for',
            loop_steps=[],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'loop_count' in result.error_info.message

    def test_for_loop_invalid_loop_count(self):
        """Test for loop with invalid loop_count."""
        var_manager = VariableManager()

        step = TestStep(
            name='invalid_count',
            type='loop',
            loop_type='for',
            loop_count='invalid',
            loop_steps=[],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None

    def test_for_loop_negative_count(self):
        """Test for loop with negative count."""
        var_manager = VariableManager()

        step = TestStep(
            name='negative_count',
            type='loop',
            loop_type='for',
            loop_count=-1,
            loop_steps=[],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'non-negative' in result.error_info.message

    def test_for_loop_without_steps(self):
        """Test for loop without loop_steps."""
        var_manager = VariableManager()

        step = TestStep(
            name='empty_loop',
            type='loop',
            loop_type='for',
            loop_count=3,
            loop_steps=None,
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'loop_steps' in result.error_info.message

    def test_while_loop_basic(self):
        """Test basic while loop execution."""
        var_manager = VariableManager()
        var_manager.set_variable('continue_loop', 'false')

        step = TestStep(
            name='test_while_loop',
            type='loop',
            loop_type='while',
            loop_condition='${continue_loop}',
            loop_steps=[
                {
                    'name': 'wait_step',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['loop_type'] == 'while'

    def test_while_loop_without_condition(self):
        """Test while loop without loop_condition."""
        var_manager = VariableManager()

        step = TestStep(
            name='invalid_while_loop',
            type='loop',
            loop_type='while',
            loop_steps=None,
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'loop_condition' in result.error_info.message

    def test_loop_without_loop_type(self):
        """Test loop without loop_type."""
        var_manager = VariableManager()

        step = TestStep(
            name='invalid_loop',
            type='loop',
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'loop_type' in result.error_info.message

    def test_loop_with_invalid_loop_type(self):
        """Test loop with invalid loop_type."""
        var_manager = VariableManager()

        step = TestStep(
            name='invalid_type',
            type='loop',
            loop_type='invalid',
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'Unsupported loop type' in result.error_info.message

    def test_for_loop_variable_injection(self):
        """Test for loop variable injection."""
        var_manager = VariableManager()

        step = TestStep(
            name='loop_with_var',
            type='loop',
            loop_type='for',
            loop_count=2,
            loop_variable='index',
            loop_steps=[
                {
                    'name': 'wait_step',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        # Variable should be set to last iteration value
        assert var_manager.get_variable('index') == 1

    def test_while_loop_variable_injection(self):
        """Test while loop variable injection."""
        var_manager = VariableManager()

        step = TestStep(
            name='while_loop_var',
            type='loop',
            loop_type='while',
            loop_condition='false',  # Exit immediately
            loop_variable='iteration',
            loop_steps=[
                {
                    'name': 'wait_step',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'

    def test_is_condition_true(self):
        """Test _is_condition_true method."""
        var_manager = VariableManager()
        step = TestStep(name='test', type='loop')

        executor = LoopExecutor(var_manager, step)

        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'ok', 'success']
        for value in true_values:
            assert executor._is_condition_true(value) is True

        false_values = ['false', 'False', '0', 'no', 'error', '']
        for value in false_values:
            assert executor._is_condition_true(value) is False

    def test_render_step_for_loop(self):
        """Test _render_step for for loop."""
        var_manager = VariableManager()
        var_manager.set_variable('count', '5')

        step = TestStep(
            name='render_for',
            type='loop',
            loop_type='for',
            loop_count='${count}',
            loop_variable='i',
        )

        executor = LoopExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered['loop_type'] == 'for'
        assert rendered['loop_count'] == '5'
        assert rendered['loop_variable'] == 'i'

    def test_render_step_while_loop(self):
        """Test _render_step for while loop."""
        var_manager = VariableManager()
        var_manager.set_variable('condition', 'true')

        step = TestStep(
            name='render_while',
            type='loop',
            loop_type='while',
            loop_condition='${condition}',
            loop_variable='iter',
        )

        executor = LoopExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered['loop_type'] == 'while'
        assert rendered['loop_condition'] == 'true'
        assert rendered['loop_variable'] == 'iter'


class TestLoopExecutorScenarios:
    """Test real-world loop scenarios."""

    def test_loop_over_data_list(self):
        """Test looping over a list of data."""
        var_manager = VariableManager()

        # Loop 3 times, each with a small wait
        step = TestStep(
            name='process_items',
            type='loop',
            loop_type='for',
            loop_count=3,
            loop_variable='item_index',
            loop_steps=[
                {
                    'name': 'process_item',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['success_count'] == 3

    def test_retry_loop_pattern(self):
        """Test using while loop for retry pattern."""
        var_manager = VariableManager()
        var_manager.set_variable('max_retries', '0')  # Exit immediately

        step = TestStep(
            name='retry_until_success',
            type='loop',
            loop_type='while',
            loop_condition='${max_retries}',
            loop_steps=[
                {
                    'name': 'wait_step',
                    'type': 'wait',
                    'seconds': 0.01,
                }
            ],
        )

        executor = LoopExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
