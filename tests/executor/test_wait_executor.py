"""Unit tests for WaitExecutor.

Tests for wait executor in apirun/executor/wait_executor.py
Following Google Python Style Guide.
"""

from apirun.core.models import TestStep
from apirun.core.variable_manager import VariableManager
from apirun.executor.wait_executor import WaitExecutor


class TestWaitExecutor:
    """Tests for WaitExecutor class."""

    def test_initialization(self):
        """Test WaitExecutor initialization."""
        var_manager = VariableManager()
        step = TestStep(name='wait_step', type='wait', seconds=1)

        executor = WaitExecutor(var_manager, step)

        assert executor.variable_manager == var_manager
        assert executor.step == step
        assert executor.timeout == 300  # default for wait steps

    def test_fixed_wait_execution(self):
        """Test fixed time wait execution."""
        var_manager = VariableManager()
        step = TestStep(
            name='wait_1s', type='wait', seconds=0.1
        )  # Small wait for testing

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['wait_type'] == 'fixed'
        assert result.response['wait_seconds'] == 0.1
        assert (
            0.08 <= result.response['actual_wait_seconds'] <= 0.15
        )  # Allow small variance

    def test_fixed_wait_with_variable(self):
        """Test fixed wait with variable substitution."""
        var_manager = VariableManager()
        var_manager.set_variable('wait_time', '0.1')

        step = TestStep(name='wait_var', type='wait', seconds='${wait_time}')

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['wait_type'] == 'fixed'

    def test_fixed_wait_invalid_value(self):
        """Test fixed wait with invalid value."""
        var_manager = VariableManager()
        step = TestStep(name='wait_invalid', type='wait', seconds='invalid')

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'Invalid wait seconds' in result.error_info.message

    def test_fixed_wait_negative_value(self):
        """Test fixed wait with negative value."""
        var_manager = VariableManager()
        step = TestStep(name='wait_negative', type='wait', seconds=-1)

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'non-negative' in result.error_info.message

    def test_fixed_wait_exceeds_timeout(self):
        """Test fixed wait exceeds timeout."""
        var_manager = VariableManager()
        step = TestStep(name='wait_long', type='wait', seconds=10, timeout=5)

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'exceeds timeout' in result.error_info.message

    def test_conditional_wait_success(self):
        """Test conditional wait that succeeds."""
        var_manager = VariableManager()
        var_manager.set_variable('ready', 'true')

        step = TestStep(
            name='wait_condition',
            type='wait',
            condition='${ready}',
            interval=0.05,
            max_wait=0.2,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['wait_type'] == 'conditional'
        assert result.response['result'] is True

    def test_conditional_wait_timeout(self):
        """Test conditional wait that times out."""
        var_manager = VariableManager()
        var_manager.set_variable('ready', 'false')

        step = TestStep(
            name='wait_condition_timeout',
            type='wait',
            condition='${ready}',
            interval=0.05,
            max_wait=0.15,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'did not become true' in result.error_info.message

    def test_conditional_wait_invalid_interval(self):
        """Test conditional wait with invalid interval."""
        var_manager = VariableManager()
        var_manager.set_variable('ready', 'false')
        step = TestStep(
            name='wait_invalid_interval',
            type='wait',
            condition='${ready}',
            interval=-1,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'positive' in result.error_info.message

    def test_conditional_wait_invalid_max_wait(self):
        """Test conditional wait with invalid max_wait."""
        var_manager = VariableManager()
        var_manager.set_variable('ready', 'false')
        step = TestStep(
            name='wait_invalid_max',
            type='wait',
            condition='${ready}',
            max_wait=0,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'positive' in result.error_info.message

    def test_conditional_wait_max_wait_exceeds_timeout(self):
        """Test conditional wait where max_wait exceeds timeout."""
        var_manager = VariableManager()
        var_manager.set_variable('ready', 'false')
        step = TestStep(
            name='wait_max_timeout',
            type='wait',
            condition='${ready}',
            max_wait=10,
            timeout=5,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert 'exceeds timeout' in result.error_info.message

    def test_wait_without_seconds_or_condition(self):
        """Test wait without seconds or condition."""
        var_manager = VariableManager()
        step = TestStep(name='wait_empty', type='wait')

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'failure'
        assert result.error_info is not None
        assert "must have either 'seconds' or 'condition'" in result.error_info.message

    def test_is_condition_true_true_values(self):
        """Test _is_condition_true with true values."""
        var_manager = VariableManager()
        step = TestStep(name='wait_test', type='wait')

        executor = WaitExecutor(var_manager, step)

        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'y', 'ok', 'success']

        for value in true_values:
            assert executor._is_condition_true(value) is True, f'Failed for: {value}'

    def test_is_condition_true_false_values(self):
        """Test _is_condition_true with false values."""
        var_manager = VariableManager()
        step = TestStep(name='wait_test', type='wait')

        executor = WaitExecutor(var_manager, step)

        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'n', '', 'error']

        for value in false_values:
            assert executor._is_condition_true(value) is False, f'Failed for: {value}'

    def test_render_step_with_seconds(self):
        """Test _render_step with seconds."""
        var_manager = VariableManager()
        var_manager.set_variable('delay', '1.5')

        step = TestStep(name='wait_render', type='wait', seconds='${delay}')

        executor = WaitExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered['seconds'] == '1.5'

    def test_render_step_with_condition(self):
        """Test _render_step with condition."""
        var_manager = VariableManager()
        var_manager.set_variable('flag', 'true')

        step = TestStep(name='wait_render', type='wait', condition='${flag}')

        executor = WaitExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered['condition'] == 'true'

    def test_render_step_with_interval_and_max_wait(self):
        """Test _render_step with interval and max_wait."""
        var_manager = VariableManager()
        var_manager.set_variable('poll_interval', '0.5')
        var_manager.set_variable('max_time', '10')
        var_manager.set_variable('ready', 'false')

        step = TestStep(
            name='wait_render',
            type='wait',
            condition='${ready}',
            interval='${poll_interval}',
            max_wait='${max_time}',
        )

        executor = WaitExecutor(var_manager, step)
        rendered = executor._render_step()

        assert rendered['interval'] == '0.5'
        assert rendered['max_wait'] == '10'


class TestWaitExecutorScenarios:
    """Test real-world wait scenarios."""

    def test_wait_for_api_ready(self):
        """Test waiting for API to become ready."""
        var_manager = VariableManager()
        var_manager.set_variable('api_ready', 'true')

        step = TestStep(
            name='wait_for_api',
            type='wait',
            condition='${api_ready}',
            interval=0.1,
            max_wait=0.3,
        )

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['result'] is True

    def test_short_wait_between_steps(self):
        """Test short wait between steps."""
        var_manager = VariableManager()

        step = TestStep(name='short_wait', type='wait', seconds=0.05)

        executor = WaitExecutor(var_manager, step)
        result = executor.execute()

        assert result.status == 'success'
        assert result.response['wait_type'] == 'fixed'
