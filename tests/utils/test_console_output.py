"""Unit tests for console_output module.

Tests the colored console output formatter with Rich library support.
"""

from apirun.utils.console_output import (
    Color,
    Emoji,
    OutputFormatter,
    StepError,
    StepExtraction,
    create_formatter,
)


class TestColor:
    """Test Rich color codes."""

    def test_color_values(self):
        """Test that all color values are valid Rich styles."""
        assert Color.RESET == 'reset'
        assert Color.BOLD == 'bold'
        assert Color.RED == 'red'
        assert Color.GREEN == 'green'
        assert Color.YELLOW == 'yellow'
        assert Color.CYAN == 'cyan'

    def test_bright_colors(self):
        """Test bright color variants."""
        assert Color.BRIGHT_RED == 'bright_red'
        assert Color.BRIGHT_GREEN == 'bright_green'
        assert Color.BRIGHT_YELLOW == 'bright_yellow'

    def test_background_colors(self):
        """Test that background colors are not defined (using Rich)."""
        # Rich uses different approach for backgrounds
        assert hasattr(Color, 'BLACK')
        assert hasattr(Color, 'RED')


class TestEmoji:
    """Test emoji symbols."""

    def test_status_emojis(self):
        """Test status-related emojis."""
        assert Emoji.SUCCESS == '✅'
        assert Emoji.FAILURE == '❌'
        assert Emoji.SKIPPED == '⏭️'
        assert Emoji.WARNING == '⚠️'
        assert Emoji.ERROR == '🚨'
        assert Emoji.INFO == 'ℹ️'

    def test_performance_emojis(self):
        """Test performance-related emojis."""
        assert Emoji.STOPWATCH == '⏱️'
        assert Emoji.CHART == '📊'
        assert Emoji.SPEED == '⚡'


class TestOutputFormatter:
    """Test output formatter functionality."""

    def test_initialization(self):
        """Test formatter initialization."""
        formatter = OutputFormatter(use_color=True, use_emoji=True, lang='zh')
        assert formatter.lang == 'zh'
        assert formatter.use_emoji is True

    def test_initialization_english(self):
        """Test English language initialization."""
        formatter = OutputFormatter(lang='en')
        assert formatter.lang == 'en'

    def test_disable_color(self):
        """Test disabling colors."""
        formatter = OutputFormatter(use_color=False)
        assert formatter._color_enabled is False

    def test_disable_emoji(self):
        """Test disabling emojis."""
        formatter = OutputFormatter(use_emoji=False)
        assert formatter.use_emoji is False

    def test_create_formatter_default(self):
        """Test create_formatter with defaults."""
        formatter = create_formatter()
        assert formatter.lang == 'zh'

    def test_create_formatter_english(self):
        """Test create_formatter with English."""
        formatter = create_formatter(lang='en')
        assert formatter.lang == 'en'

    def test_create_formatter_no_color(self):
        """Test create_formatter without color."""
        formatter = create_formatter(use_color=False)
        assert formatter._color_enabled is False

    def test_create_formatter_no_emoji(self):
        """Test create_formatter without emoji."""
        formatter = create_formatter(use_emoji=False)
        assert formatter.use_emoji is False

    def test_get_text_chinese(self):
        """Test Chinese text selection."""
        formatter = OutputFormatter(lang='zh')
        result = formatter.get_text('中文', 'English')
        assert result == '中文'

    def test_get_text_english(self):
        """Test English text selection."""
        formatter = OutputFormatter(lang='en')
        result = formatter.get_text('中文', 'English')
        assert result == 'English'

    def test_colorize(self):
        """Test text colorization."""
        formatter = OutputFormatter(use_color=True)
        result = formatter.colorize('test', Color.RED)
        assert '[red]' in result
        assert 'test' in result
        assert '[/]' in result

    def test_header_formatting(self):
        """Test header formatting."""
        formatter = OutputFormatter()
        result = formatter.header('标题')
        assert '[bold cyan]' in result
        assert '标题' in result

    def test_dim_formatting(self):
        """Test dimmed text formatting."""
        formatter = OutputFormatter()
        result = formatter.dim('暗淡文本')
        assert '[dim]' in result
        assert '暗淡文本' in result

    def test_style_property(self):
        """Test style property for backward compatibility."""
        formatter = OutputFormatter()
        assert formatter.style is formatter

    def test_print_summary_footer(self, capsys):
        """Test print_summary_footer (replaces print_summary)."""
        formatter = create_formatter(lang='zh')
        formatter.print_summary_footer(
            status='passed',
            duration=1.23,
            total=10,
            passed=8,
            failed=1,
            skipped=1,
            pass_rate=80.0,
        )
        captured = capsys.readouterr()
        # The output uses Rich, so we just check that something was printed
        assert len(captured.out) > 0

    def test_print_overall_summary(self, capsys):
        """Test print_overall_summary."""
        formatter = create_formatter(lang='zh')
        formatter.print_overall_summary(total_tests=10, passed_tests=8, failed_tests=2)
        captured = capsys.readouterr()
        # Check that output was generated
        assert len(captured.out) > 0

    def test_print_test_start(self, capsys):
        """Test print_test_start."""
        formatter = create_formatter(lang='zh')
        formatter.print_test_start(
            name='测试用例1', description='这是一个测试', step_count=5
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_step_success(self, capsys):
        """Test print_step with success status."""
        formatter = create_formatter(lang='en')
        formatter.print_step(
            index=1, total=3, name='Step 1', status='success', duration=123.45
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_step_failure(self, capsys):
        """Test print_step with failure status."""
        formatter = create_formatter(lang='en')
        error = StepError(error_type='AssertionError', message='Test failed')
        formatter.print_step(
            index=2, total=3, name='Step 2', status='failure', duration=100.0, error=error
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_step_skipped(self, capsys):
        """Test print_step with skipped status."""
        formatter = create_formatter(lang='en')
        formatter.print_step(index=3, total=3, name='Step 3', status='skipped', duration=0.0)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_step_with_extraction(self, capsys):
        """Test print_step with variable extraction."""
        formatter = create_formatter(lang='en', verbose=True)
        extraction = StepExtraction(
            var_name='user_id', value='12345', path='$.user.id'
        )
        formatter.print_step(
            index=1,
            total=1,
            name='Extract Step',
            status='success',
            duration=50.0,
            extraction=extraction,
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_step_with_performance(self, capsys):
        """Test print_step with performance breakdown."""
        formatter = create_formatter(lang='en', verbose=True)
        performance = {
            'dns_time': 50.0,
            'tcp_time': 80.0,
            'tls_time': 120.0,
            'server_time': 250.0,
        }
        formatter.print_step(
            index=1,
            total=1,
            name='API Request',
            status='success',
            duration=500.0,
            performance=performance,
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_error_section(self, capsys):
        """Test print_error_section."""
        formatter = create_formatter(lang='zh')
        error = StepError(
            error_type='AssertionError', message='预期失败', context='步骤 1'
        )
        formatter.print_error_section(
            failed_steps=[{'index': 1, 'name': '步骤1', 'error': error}]
        )
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_info_method(self):
        """Test info method (backward compatibility)."""
        formatter = OutputFormatter()
        result = formatter.info('test')
        assert result == 'test'


class TestStepExtraction:
    """Test StepExtraction dataclass."""

    def test_creation(self):
        """Test creating StepExtraction."""
        extraction = StepExtraction(var_name='test', value='123', path='$.test')
        assert extraction.var_name == 'test'
        assert extraction.value == '123'
        assert extraction.path == '$.test'

    def test_string_representation(self):
        """Test __str__ method."""
        extraction = StepExtraction(var_name='user', value='12345', path='$.user.id')
        result = str(extraction)
        assert 'user = 12345' in result
        assert '$.user.id' in result

    def test_long_value_truncation(self):
        """Test that long values are truncated."""
        long_value = 'x' * 100
        extraction = StepExtraction(var_name='test', value=long_value, path='$.test')
        result = str(extraction)
        assert '...' in result
        assert len(result) < len(long_value)


class TestStepError:
    """Test StepError dataclass."""

    def test_creation(self):
        """Test creating StepError."""
        error = StepError(error_type='TestError', message='Test failed')
        assert error.error_type == 'TestError'
        assert error.message == 'Test failed'
        assert error.context is None

    def test_creation_with_context(self):
        """Test creating StepError with context."""
        error = StepError(
            error_type='TestError', message='Test failed', context='Step 1'
        )
        assert error.context == 'Step 1'


class TestInternationalization:
    """Test internationalization features."""

    def test_chinese_internal_text(self):
        """Test Chinese text selection internally."""
        formatter = OutputFormatter(lang='zh')
        assert formatter._t('中文', 'English') == '中文'

    def test_english_internal_text(self):
        """Test English text selection internally."""
        formatter = OutputFormatter(lang='en')
        assert formatter._t('中文', 'English') == 'English'

    def test_emoji_enabled(self):
        """Test emoji when enabled."""
        formatter = OutputFormatter(use_emoji=True)
        assert formatter._emoji('✅') == '✅'

    def test_emoji_disabled(self):
        """Test emoji when disabled."""
        formatter = OutputFormatter(use_emoji=False)
        assert formatter._emoji('✅') == ''

    def test_verbose_mode(self):
        """Test verbose mode setting."""
        formatter = OutputFormatter(verbose=True)
        assert formatter.verbose is True
