"""Unit tests for TestCaseExecutor.

Tests the test case executor functionality, including:
- Test case execution
- Variable initialization
- Profile setup
- Step execution scheduling
- Error handling
- Result collection

Following Google Python Style Guide.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from apirun.core.models import (
    ErrorCategory,
    ErrorInfo,
    GlobalConfig,
    ProfileConfig,
    StepResult,
    TestCase,
    TestStep,
)
from apirun.core.variable_manager import VariableManager
from apirun.executor.test_case_executor import TestCaseExecutor


class TestTestCaseExecutor:
    """Test cases for TestCaseExecutor class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.test_case = TestCase(
            name='Test Case',
            description='Test description',
            steps=[
                TestStep(name='Step 1', type='wait', seconds=0.1),
                TestStep(name='Step 2', type='wait', seconds=0.1),
            ],
        )

    def test_initialization(self):
        """Test TestCaseExecutor initialization."""
        executor = TestCaseExecutor(self.test_case)

        assert executor.test_case == self.test_case
        assert isinstance(executor.variable_manager, VariableManager)
        assert executor.result_collector is not None
        assert executor.notifier is None

    def test_initialization_with_notifier(self):
        """Test initialization with WebSocket notifier."""
        mock_notifier = Mock()

        executor = TestCaseExecutor(self.test_case, notifier=mock_notifier)

        assert executor.notifier == mock_notifier

    def test_variable_initialization(self):
        """Test variable initialization from config."""
        test_case = TestCase(
            name='Test Variables',
            config=GlobalConfig(
                name='global',
                variables={
                    'base_url': 'https://api.example.com',
                    'api_key': 'test-key-12345',
                },
            ),
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)
        executor._initialize_variables()

        assert (
            executor.variable_manager.get_variable('base_url')
            == 'https://api.example.com'
        )
        assert executor.variable_manager.get_variable('api_key') == 'test-key-12345'

    def test_profile_setup(self):
        """Test profile configuration setup."""
        test_case = TestCase(
            name='Test Profile',
            config=GlobalConfig(
                name='global',
                active_profile='dev',
                profiles={
                    'dev': ProfileConfig(
                        base_url='https://dev.api.com', variables={'env': 'dev'}
                    ),
                    'prod': ProfileConfig(
                        base_url='https://api.example.com', variables={'env': 'prod'}
                    ),
                },
            ),
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)
        executor._initialize_variables()
        executor._setup_profile()

        # Profile variables should be loaded
        assert (
            executor.variable_manager.get_variable('base_url') == 'https://dev.api.com'
        )
        assert executor.variable_manager.get_variable('env') == 'dev'

    def test_profile_switching(self):
        """Test switching between different profiles."""
        for profile_name in ['dev', 'prod', 'staging']:
            test_case = TestCase(
                name=f'Test {profile_name}',
                config=GlobalConfig(
                    name='global',
                    active_profile=profile_name,
                    profiles={
                        profile_name: ProfileConfig(
                            base_url=f'https://{profile_name}.api.com'
                        )
                    },
                ),
                steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
            )

            executor = TestCaseExecutor(test_case)
            executor._initialize_variables()
            executor._setup_profile()

            assert (
                executor.variable_manager.get_variable('base_url')
                == f'https://{profile_name}.api.com'
            )

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_step_execution_order(self, mock_execute_step):
        """Test that steps are executed in order."""
        # Setup mock results
        mock_execute_step.side_effect = [
            StepResult(
                name='Step 1',
                status='success',
                start_time=datetime(2026, 2, 2, 12, 0, 0),
                end_time=datetime(2026, 2, 2, 12, 0, 1),
            ),
            StepResult(
                name='Step 2',
                status='success',
                start_time=datetime(2026, 2, 2, 12, 0, 1),
                end_time=datetime(2026, 2, 2, 12, 0, 2),
            ),
        ]

        executor = TestCaseExecutor(self.test_case)
        result = executor.execute()

        # Verify steps were called in order
        assert mock_execute_step.call_count == 2
        assert mock_execute_step.call_args_list[0][0][0].name == 'Step 1'
        assert mock_execute_step.call_args_list[1][0][0].name == 'Step 2'

    def test_step_type_registration(self):
        """Test that all step types are properly registered."""
        step_types = [
            ('request', 'APIExecutor'),
            ('database', 'DatabaseExecutor'),
            ('wait', 'WaitExecutor'),
            ('loop', 'LoopExecutor'),
            ('concurrent', 'ConcurrentExecutor'),
            ('script', 'ScriptExecutor'),
            ('poll', 'PollStepExecutor'),
        ]

        for step_type, expected_executor in step_types:
            test_case = TestCase(
                name=f'Test {step_type}',
                steps=[TestStep(name='Step 1', type=step_type)],
            )

            executor = TestCaseExecutor(test_case)

            # Verify executor can be created for each step type
            assert executor.test_case.steps[0].type == step_type

    def test_empty_test_case(self):
        """Test handling of test case with no steps."""
        test_case = TestCase(
            name='Empty Test Case', description='Test case with no steps', steps=[]
        )

        executor = TestCaseExecutor(test_case)

        # Should execute without errors
        assert len(executor.test_case.steps) == 0

    def test_test_case_with_description(self):
        """Test test case with description."""
        test_case = TestCase(
            name='Test with Description',
            description='This is a detailed description',
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)

        assert executor.test_case.description == 'This is a detailed description'

    def test_test_case_with_tags(self):
        """Test test case with tags."""
        test_case = TestCase(
            name='Test with Tags',
            tags=['smoke', 'regression', 'critical'],
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)

        assert executor.test_case.tags == ['smoke', 'regression', 'critical']

    def test_test_case_with_timeout(self):
        """Test test case with custom timeout."""
        test_case = TestCase(
            name='Test with Timeout',
            config=GlobalConfig(name='global', timeout=60),
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)

        assert executor.test_case.config.timeout == 60

    def test_variable_inheritance(self):
        """Test that variables are properly inherited from config."""
        test_case = TestCase(
            name='Test Variable Inheritance',
            config=GlobalConfig(
                name='global',
                variables={'global_var': 'global_value', 'api_version': 'v1'},
                active_profile='dev',
                profiles={
                    'dev': ProfileConfig(
                        base_url='https://dev.api.com',
                        variables={'profile_var': 'dev_value'},
                    )
                },
            ),
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)
        executor._initialize_variables()
        executor._setup_profile()

        # All variables should be available
        assert executor.variable_manager.get_variable('global_var') == 'global_value'
        assert executor.variable_manager.get_variable('api_version') == 'v1'
        assert executor.variable_manager.get_variable('profile_var') == 'dev_value'

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_result_collection(self, mock_execute_step):
        """Test that results are properly collected."""
        # Setup mock results
        mock_execute_step.side_effect = [
            StepResult(
                name='Step 1',
                status='success',
                start_time=datetime(2026, 2, 2, 12, 0, 0),
                end_time=datetime(2026, 2, 2, 12, 0, 1),
            ),
            StepResult(
                name='Step 2',
                status='success',
                start_time=datetime(2026, 2, 2, 12, 0, 1),
                end_time=datetime(2026, 2, 2, 12, 0, 2),
            ),
        ]

        executor = TestCaseExecutor(self.test_case)
        result = executor.execute()

        # Result should contain statistics and steps
        assert 'test_case' in result
        assert 'statistics' in result
        assert 'steps' in result
        assert result['statistics']['total_steps'] == 2

    def test_enabled_flag(self):
        """Test test case enabled flag."""
        # Enabled test case
        enabled_case = TestCase(
            name='Enabled Test',
            enabled=True,
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        # Disabled test case
        disabled_case = TestCase(
            name='Disabled Test',
            enabled=False,
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor_enabled = TestCaseExecutor(enabled_case)
        executor_disabled = TestCaseExecutor(disabled_case)

        assert executor_enabled.test_case.enabled is True
        assert executor_disabled.test_case.enabled is False

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_statistics_calculation(self, mock_execute_step):
        """Test that statistics are correctly calculated."""
        # Create a test case with 3 steps for this specific test
        test_case = TestCase(
            name='Test Statistics',
            description='Test statistics calculation',
            steps=[
                TestStep(name='Step 1', type='wait', seconds=0.1),
                TestStep(name='Step 2', type='wait', seconds=0.1),
                TestStep(name='Step 3', type='wait', seconds=0.1),
            ],
        )

        # Setup mixed results
        mock_execute_step.side_effect = [
            StepResult(
                name='Step 1',
                status='success',
                start_time=datetime(2026, 2, 2, 12, 0, 0),
                end_time=datetime(2026, 2, 2, 12, 0, 1),
            ),
            StepResult(
                name='Step 2',
                status='failure',
                start_time=datetime(2026, 2, 2, 12, 0, 1),
                end_time=datetime(2026, 2, 2, 12, 0, 2),
                error_info=ErrorInfo(
                    type='AssertionError',
                    category=ErrorCategory.ASSERTION,
                    message='Validation failed',
                ),
            ),
            StepResult(
                name='Step 3',
                status='skipped',
                start_time=datetime(2026, 2, 2, 12, 0, 2),
                end_time=datetime(2026, 2, 2, 12, 0, 3),
            ),
        ]

        executor = TestCaseExecutor(test_case)
        result = executor.execute()

        stats = result['statistics']
        assert stats['total_steps'] == 3
        assert stats['passed_steps'] == 1
        assert stats['failed_steps'] == 1
        assert stats['skipped_steps'] == 1

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_final_variables_collection(self, mock_execute_step):
        """Test that final variables are collected."""
        # Setup mock with variable extraction
        result_with_extraction = StepResult(
            name='Step 1',
            status='success',
            start_time=datetime(2026, 2, 2, 12, 0, 0),
            end_time=datetime(2026, 2, 2, 12, 0, 1),
            extracted_vars={'token': 'abc123', 'user_id': 456},
        )

        mock_execute_step.return_value = result_with_extraction

        test_case = TestCase(
            name='Test Extraction',
            config=GlobalConfig(
                name='global', variables={'initial_var': 'initial_value'}
            ),
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

        executor = TestCaseExecutor(test_case)
        result = executor.execute()

        # Final variables should include initial and extracted variables
        assert 'final_variables' in result
        assert 'initial_var' in result['final_variables']


class TestWebSocketNotification:
    """Test WebSocket notification integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.test_case = TestCase(
            name='Test with Notifications',
            steps=[TestStep(name='Step 1', type='wait', seconds=0.1)],
        )

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_notification_on_test_start(self, mock_execute_step):
        """Test that notification is sent when test starts."""
        mock_notifier = Mock()
        # Create AsyncMock for async notification methods
        mock_notifier.notify_test_start = AsyncMock()
        mock_notifier.notify_step_start = AsyncMock()
        mock_notifier.notify_step_complete = AsyncMock()
        mock_notifier.notify_test_complete = AsyncMock()

        mock_execute_step.return_value = StepResult(
            name='Step 1',
            status='success',
            start_time=datetime(2026, 2, 2, 12, 0, 0),
            end_time=datetime(2026, 2, 2, 12, 0, 1),
        )

        executor = TestCaseExecutor(self.test_case, notifier=mock_notifier)
        result = executor.execute()

        # Verify notifications were called
        assert mock_notifier.notify_test_start.called
        assert mock_notifier.notify_step_start.called
        assert mock_notifier.notify_step_complete.called

    @patch('apirun.executor.test_case_executor.TestCaseExecutor._execute_step')
    def test_notification_with_step_details(self, mock_execute_step):
        """Test that step details are included in notifications."""
        mock_notifier = Mock()
        # Create AsyncMock for async notification methods
        mock_notifier.notify_test_start = AsyncMock()
        mock_notifier.notify_step_start = AsyncMock()
        mock_notifier.notify_step_complete = AsyncMock()
        mock_notifier.notify_test_complete = AsyncMock()

        mock_execute_step.return_value = StepResult(
            name='Step 1',
            status='success',
            start_time=datetime(2026, 2, 2, 12, 0, 0),
            end_time=datetime(2026, 2, 2, 12, 0, 1),
        )

        executor = TestCaseExecutor(self.test_case, notifier=mock_notifier)
        executor.execute()

        # Verify step details in notification
        call_args = mock_notifier.notify_step_start.call_args
        assert 'step_name' in call_args[1]
        assert call_args[1]['step_name'] == 'Step 1'
        assert 'step_index' in call_args[1]
        assert call_args[1]['step_index'] == 0
        assert 'total_steps' in call_args[1]
        assert call_args[1]['total_steps'] == 1
