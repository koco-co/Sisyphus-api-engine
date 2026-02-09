"""Unit tests for console_output module.

Tests the colored console output formatter with internationalization support.
"""

from apirun.utils.console_output import (
    Color,
    ConsoleStyle,
    Emoji,
    OutputFormatter,
    create_formatter,
)


class TestColor:
    """Test ANSI color codes."""

    def test_color_values(self):
        """Test that all color values are valid ANSI codes."""
        assert Color.RESET.value == '\033[0m'
        assert Color.BOLD.value == '\033[1m'
        assert Color.RED.value == '\033[31m'
        assert Color.GREEN.value == '\033[32m'
        assert Color.YELLOW.value == '\033[33m'
        assert Color.CYAN.value == '\033[36m'

    def test_bright_colors(self):
        """Test bright color variants."""
        assert Color.BRIGHT_RED.value == '\033[91m'
        assert Color.BRIGHT_GREEN.value == '\033[92m'
        assert Color.BRIGHT_YELLOW.value == '\033[93m'

    def test_background_colors(self):
        """Test background color codes."""
        assert Color.BG_RED.value == '\033[41m'
        assert Color.BG_GREEN.value == '\033[42m'


class TestEmoji:
    """Test emoji symbols."""

    def test_status_emojis(self):
        """Test status-related emojis."""
        assert Emoji.SUCCESS.value == '✅'
        assert Emoji.FAILURE.value == '❌'
        assert Emoji.SKIPPED.value == '⏭️'
        assert Emoji.WARNING.value == '⚠️'
        assert Emoji.ERROR.value == '🚨'
        assert Emoji.INFO.value == 'ℹ️'

    def test_performance_emojis(self):
        """Test performance-related emojis."""
        assert Emoji.STOPWATCH.value == '⏱️'
        assert Emoji.CHART.value == '📊'
        assert Emoji.SPEED.value == '⚡'


class TestConsoleStyle:
    """Test console styling functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        style = ConsoleStyle()
        assert style.lang == 'zh'
        assert isinstance(style.use_color, bool)
        assert isinstance(style.use_emoji, bool)

    def test_initialization_english(self):
        """Test English language initialization."""
        style = ConsoleStyle(lang='en')
        assert style.lang == 'en'

    def test_disable_color(self):
        """Test disabling colors."""
        style = ConsoleStyle(use_color=False)
        assert not style.use_color

    def test_disable_emoji(self):
        """Test disabling emojis."""
        style = ConsoleStyle(use_emoji=False)
        assert not style.use_emoji

    def test_colorize_with_color(self):
        """Test text colorization when enabled."""
        style = ConsoleStyle(use_color=True, use_emoji=False)
        # Force enable color for testing (in case terminal doesn't support it)
        style.use_color = True
        result = style.colorize('test', Color.RED)
        # Check ANSI escape sequence (may be \x1b or \033)
        assert '\x1b[31m' in result or '\033[31m' in result
        assert 'test' in result
        assert '\x1b[0m' in result or '\033[0m' in result

    def test_colorize_without_color(self):
        """Test text colorization when disabled."""
        style = ConsoleStyle(use_color=False)
        result = style.colorize('test', Color.RED)
        assert result == 'test'

    def test_success_formatting(self):
        """Test success message formatting."""
        style = ConsoleStyle()
        result = style.success('操作成功')
        assert '操作成功' in result

    def test_failure_formatting(self):
        """Test failure message formatting."""
        style = ConsoleStyle()
        result = style.failure('操作失败')
        assert '操作失败' in result

    def test_warning_formatting(self):
        """Test warning message formatting."""
        style = ConsoleStyle()
        result = style.warning('警告信息')
        assert '警告信息' in result

    def test_info_formatting(self):
        """Test info message formatting."""
        style = ConsoleStyle()
        result = style.info('信息提示')
        assert '信息提示' in result

    def test_info_spacing(self):
        """Test that info emoji has 2 spaces after it."""
        style = ConsoleStyle(use_emoji=True)
        result = style.info('test')
        # ℹ️ + 2 spaces + text
        assert result.startswith('ℹ️  ')

    def test_get_text_chinese(self):
        """Test Chinese text selection."""
        style = ConsoleStyle(lang='zh')
        result = style.get_text('中文', 'English')
        assert result == '中文'

    def test_get_text_english(self):
        """Test English text selection."""
        style = ConsoleStyle(lang='en')
        result = style.get_text('中文', 'English')
        assert result == 'English'

    def test_header_formatting(self):
        """Test header formatting."""
        style = ConsoleStyle()
        result = style.header('标题')
        assert '标题' in result

    def test_dim_formatting(self):
        """Test dimmed text formatting."""
        style = ConsoleStyle()
        result = style.dim('暗淡文本')
        assert '暗淡文本' in result

    def test_highlight_formatting(self):
        """Test highlighted text formatting."""
        style = ConsoleStyle()
        result = style.highlight('高亮文本')
        assert '高亮文本' in result


class TestOutputFormatter:
    """Test output formatter functionality."""

    def test_initialization(self):
        """Test formatter initialization."""
        style = ConsoleStyle()
        formatter = OutputFormatter(style)
        assert formatter.style == style

    def test_create_formatter_default(self):
        """Test create_formatter with defaults."""
        formatter = create_formatter()
        assert formatter.style.lang == 'zh'

    def test_create_formatter_english(self):
        """Test create_formatter with English."""
        formatter = create_formatter(lang='en')
        assert formatter.style.lang == 'en'

    def test_create_formatter_no_color(self):
        """Test create_formatter without color."""
        formatter = create_formatter(use_color=False)
        assert not formatter.style.use_color

    def test_create_formatter_no_emoji(self):
        """Test create_formatter without emoji."""
        formatter = create_formatter(use_emoji=False)
        assert not formatter.style.use_emoji

    def test_print_summary_chinese(self, capsys):
        """Test print_summary in Chinese."""
        formatter = create_formatter(lang='zh')
        formatter.print_summary(
            status='passed',
            duration=1.23,
            total=10,
            passed=8,
            failed=1,
            skipped=1,
            pass_rate=80.0,
        )
        captured = capsys.readouterr()
        assert '状态' in captured.out
        assert '通过' in captured.out
        assert '失败' in captured.out
        assert '跳过' in captured.out
        assert '通过率' in captured.out

    def test_print_summary_english(self, capsys):
        """Test print_summary in English."""
        formatter = create_formatter(lang='en')
        formatter.print_summary(
            status='passed',
            duration=1.23,
            total=10,
            passed=8,
            failed=1,
            skipped=1,
            pass_rate=80.0,
        )
        captured = capsys.readouterr()
        assert 'Status' in captured.out
        assert 'Passed' in captured.out
        assert 'Failed' in captured.out
        assert 'Skipped' in captured.out
        assert 'Pass Rate' in captured.out

    def test_print_summary_passed_status(self, capsys):
        """Test summary with passed status."""
        formatter = create_formatter(lang='en')
        formatter.print_summary(
            status='passed',
            duration=1.0,
            total=5,
            passed=5,
            failed=0,
            skipped=0,
            pass_rate=100.0,
        )
        captured = capsys.readouterr()
        assert 'PASSED' in captured.out

    def test_print_summary_failed_status(self, capsys):
        """Test summary with failed status."""
        formatter = create_formatter(lang='en')
        formatter.print_summary(
            status='failed',
            duration=1.0,
            total=5,
            passed=3,
            failed=2,
            skipped=0,
            pass_rate=60.0,
        )
        captured = capsys.readouterr()
        assert 'FAILED' in captured.out

    def test_print_test_start_chinese(self, capsys):
        """Test print_test_start in Chinese."""
        formatter = create_formatter(lang='zh')
        formatter.print_test_start(
            name='测试用例1', description='这是一个测试', step_count=5
        )
        captured = capsys.readouterr()
        assert '测试用例1' in captured.out
        assert '这是一个测试' in captured.out
        assert '步骤数: 5' in captured.out

    def test_print_test_start_english(self, capsys):
        """Test print_test_start in English."""
        formatter = create_formatter(lang='en')
        formatter.print_test_start(
            name='Test Case 1', description='This is a test', step_count=5
        )
        captured = capsys.readouterr()
        assert 'Test Case 1' in captured.out
        assert 'This is a test' in captured.out
        assert 'Steps: 5' in captured.out

    def test_print_step_success(self, capsys):
        """Test print_step with success status."""
        formatter = create_formatter(lang='en')
        formatter.print_step(name='Step 1', status='success', duration=123.45)
        captured = capsys.readouterr()
        assert 'Step 1' in captured.out
        assert '123.45ms' in captured.out

    def test_print_step_failure(self, capsys):
        """Test print_step with failure status."""
        formatter = create_formatter(lang='en')
        formatter.print_step(name='Step 2', status='failure', error='Assertion failed')
        captured = capsys.readouterr()
        assert 'Step 2' in captured.out
        assert 'Error: Assertion failed' in captured.out

    def test_print_step_skipped(self, capsys):
        """Test print_step with skipped status."""
        formatter = create_formatter(lang='en')
        formatter.print_step(name='Step 3', status='skipped')
        captured = capsys.readouterr()
        assert 'Step 3' in captured.out

    def test_print_step_with_performance(self, capsys):
        """Test print_step with performance breakdown."""
        formatter = create_formatter(lang='en')
        formatter.print_step(
            name='API Request',
            status='success',
            duration=500.0,
            performance={
                'dns_time': 50.0,
                'tcp_time': 80.0,
                'tls_time': 120.0,
                'server_time': 250.0,
            },
        )
        captured = capsys.readouterr()
        assert 'API Request' in captured.out
        assert 'DNS: 50.00ms' in captured.out
        assert 'TCP: 80.00ms' in captured.out
        assert 'TLS: 120.00ms' in captured.out
        assert 'Server: 250.00ms' in captured.out

    def test_print_overall_summary(self, capsys):
        """Test print_overall_summary."""
        formatter = create_formatter(lang='zh')
        formatter.print_overall_summary(total_tests=10, passed_tests=8, failed_tests=2)
        captured = capsys.readouterr()
        assert '总体概览' in captured.out or 'OVERALL SUMMARY' in captured.out
        assert '8/10' in captured.out


class TestEmojiSpacing:
    """Test emoji spacing consistency."""

    def test_step_success_spacing(self, capsys):
        """Test that success emoji has 1 space after it in steps."""
        formatter = create_formatter(lang='en', use_emoji=True)
        formatter.print_step(name='Test Step', status='success')
        captured = capsys.readouterr()
        # Should be: ✅ Test Step (1 space)
        assert '✅ Test Step' in captured.out

    def test_step_failure_spacing(self, capsys):
        """Test that failure emoji has 1 space after it in steps."""
        formatter = create_formatter(lang='en', use_emoji=True)
        formatter.print_step(name='Failed Step', status='failure')
        captured = capsys.readouterr()
        # Should be: ❌ Failed Step (1 space)
        assert '❌ Failed Step' in captured.out

    def test_step_skipped_spacing(self, capsys):
        """Test that skipped emoji has proper spacing in steps."""
        formatter = create_formatter(lang='en', use_emoji=True)
        formatter.print_step(name='Skipped Step', status='skipped')
        captured = capsys.readouterr()
        # ⏭️ is a wide character, needs extra space
        assert '⏭️' in captured.out
        assert 'Skipped Step' in captured.out

    def test_summary_stats_spacing(self, capsys):
        """Test emoji spacing in summary statistics."""
        formatter = create_formatter(lang='zh', use_emoji=True)
        formatter.print_summary(
            status='passed',
            duration=1.0,
            total=10,
            passed=8,
            failed=2,
            skipped=0,
            pass_rate=80.0,
        )
        captured = capsys.readouterr()
        # Statistics should have emoji before label
        # ⏭️ has 2 spaces after it in summary
        assert '⏭️  跳过:' in captured.out


class TestInternationalization:
    """Test internationalization features."""

    def test_chinese_output(self, capsys):
        """Test Chinese language output."""
        formatter = create_formatter(lang='zh')
        formatter.print_summary(
            status='passed',
            duration=1.0,
            total=1,
            passed=1,
            failed=0,
            skipped=0,
            pass_rate=100.0,
        )
        captured = capsys.readouterr()
        assert '状态' in captured.out
        assert '耗时' in captured.out
        assert '统计' in captured.out

    def test_english_output(self, capsys):
        """Test English language output."""
        formatter = create_formatter(lang='en')
        formatter.print_summary(
            status='passed',
            duration=1.0,
            total=1,
            passed=1,
            failed=0,
            skipped=0,
            pass_rate=100.0,
        )
        captured = capsys.readouterr()
        assert 'Status' in captured.out
        assert 'Duration' in captured.out
        assert 'Statistics' in captured.out
