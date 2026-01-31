"""Console Output Formatter with Colors and Emoji Support.

This module provides beautiful console output with colors, emojis, and i18n support.
Following Google Python Style Guide.
"""

import sys
from typing import Optional
from enum import Enum


class Color(Enum):
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class Emoji(Enum):
    """Emoji symbols for console output."""
    # Status
    SUCCESS = "✅"
    FAILURE = "❌"
    SKIPPED = "⏭️"
    WARNING = "⚠️"
    ERROR = "🚨"
    INFO = "ℹ️"

    # Test
    ROCKET = "🚀"
    TEST_TUBE = "🧪"
    CHECKLIST = "✅"

    # Performance
    STOPWATCH = "⏱️"
    CHART = "📊"
    SPEED = "⚡"

    # Files
    FILE = "📄"
    FOLDER = "📁"

    # Other
    GEAR = "⚙️"
    STAR = "⭐"
    FIRE = "🔥"
    BULB = "💡"
    TARGET = "🎯"


class ConsoleStyle:
    """Console output styling with colors and emojis."""

    def __init__(self, use_color: bool = True, use_emoji: bool = True, lang: str = "zh"):
        """Initialize console style.

        Args:
            use_color: Enable ANSI colors (default: True)
            use_emoji: Enable emoji symbols (default: True)
            lang: Language code ('zh' for Chinese, 'en' for English)
        """
        self.use_color = use_color and self._supports_color()
        self.use_emoji = use_emoji
        self.lang = lang

        # Auto-disable emoji on Windows terminals that don't support it well
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 0x0004)
                # Windows 10+ supports emoji, older versions don't
            except:
                self.use_emoji = False

    def _supports_color(self) -> bool:
        """Check if terminal supports ANSI colors."""
        # Check if we're in a terminal
        if not hasattr(sys.stdout, 'isatty'):
            return False

        if not sys.stdout.isatty():
            return False

        # Check environment variables
        if os.environ.get('NO_COLOR'):
            return False

        if os.environ.get('TERM') == 'dumb':
            return False

        return True

    def colorize(self, text: str, color: Color) -> str:
        """Apply color to text.

        Args:
            text: Text to colorize
            color: Color to apply

        Returns:
            Colorized text (or original text if color disabled)
        """
        if not self.use_color:
            return text
        return f"{color.value}{text}{Color.RESET.value}"

    def success(self, text: str) -> str:
        """Format success message."""
        emoji = Emoji.SUCCESS.value if self.use_emoji else ""
        return self.colorize(f"{emoji} {text}", Color.GREEN)

    def failure(self, text: str) -> str:
        """Format failure message."""
        emoji = Emoji.FAILURE.value if self.use_emoji else ""
        return self.colorize(f"{emoji} {text}", Color.RED)

    def warning(self, text: str) -> str:
        """Format warning message."""
        emoji = Emoji.WARNING.value if self.use_emoji else ""
        return self.colorize(f"{emoji} {text}", Color.YELLOW)

    def info(self, text: str) -> str:
        """Format info message."""
        emoji = Emoji.INFO.value if self.use_emoji else ""
        return self.colorize(f"{emoji}  {text}", Color.CYAN)

    def header(self, text: str) -> str:
        """Format header message."""
        return self.colorize(text, Color.BOLD)

    def dim(self, text: str) -> str:
        """Format dimmed text."""
        return self.colorize(text, Color.DIM)

    def highlight(self, text: str) -> str:
        """Format highlighted text."""
        return self.colorize(text, Color.BRIGHT_YELLOW)

    def get_text(self, zh_text: str, en_text: str) -> str:
        """Get text based on language setting.

        Args:
            zh_text: Chinese text
            en_text: English text

        Returns:
            Text in configured language
        """
        return zh_text if self.lang == "zh" else en_text


# Import for _supports_color
import os


class OutputFormatter:
    """Formatter for test execution output."""

    def __init__(self, style: ConsoleStyle):
        """Initialize output formatter.

        Args:
            style: ConsoleStyle instance
        """
        self.style = style

    def print_header(self, title: str, subtitle: str = "") -> None:
        """Print formatted header.

        Args:
            title: Main title
            subtitle: Optional subtitle
        """
        print()
        print(self.style.header("=" * 70))
        print(self.style.header(f"  {title}"))
        if subtitle:
            print(f"  {self.style.dim(subtitle)}")
        print(self.style.header("=" * 70))
        print()

    def print_test_start(self, name: str, description: str = "", step_count: int = 0) -> None:
        """Print test execution start message.

        Args:
            name: Test case name
            description: Test description
            step_count: Number of steps
        """
        emoji = Emoji.ROCKET.value if self.style.use_emoji else ""
        print(f"{emoji} {self.style.header(name)}")

        if description:
            print(f"   {self.style.dim(description)}")

        if step_count > 0:
            steps_text = self.style.get_text(f"步骤数: {step_count}", f"Steps: {step_count}")
            print(f"   {self.style.dim(steps_text)}")

        print()

    def print_summary(
        self,
        status: str,
        duration: float,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        pass_rate: float
    ) -> None:
        """Print test execution summary.

        Args:
            status: Test status (passed/failed/error)
            duration: Duration in seconds
            total: Total steps
            passed: Passed steps
            failed: Failed steps
            skipped: Skipped steps
            pass_rate: Pass rate percentage
        """
        # Status display
        status_upper = status.upper()
        if status == "passed":
            status_display = self.style.success(status_upper)
        elif status == "failed":
            status_display = self.style.failure(status_upper)
        else:
            status_display = self.style.warning(status_upper)

        # Print summary box
        print(self.style.header("━" * 70))

        # Status and duration
        status_text = self.style.get_text("状态", "Status")
        duration_text = self.style.get_text("耗时", "Duration")
        print(f"  {status_text}: {status_display}    {duration_text}: {self.style.highlight(f'{duration:.2f}s')}")

        # Statistics
        print()
        stats_text = self.style.get_text("统计", "Statistics")
        print(f"  {stats_text}:")

        # Total with chart emoji
        total_emoji = Emoji.CHART.value if self.style.use_emoji else ""
        print(f"    {total_emoji} {self.style.get_text('总计:', 'Total:')} {self.style.colorize(str(total), Color.CYAN)}")

        # Passed with success emoji
        success_emoji = Emoji.SUCCESS.value if self.style.use_emoji else ""
        print(f"    {success_emoji} {self.style.get_text('通过:', 'Passed:')} {self.style.colorize(str(passed), Color.GREEN)}")

        # Failed with failure emoji
        failure_emoji = Emoji.FAILURE.value if self.style.use_emoji else ""
        print(f"    {failure_emoji} {self.style.get_text('失败:', 'Failed:')} {self.style.colorize(str(failed), Color.RED)}")

        # Skipped with skipped emoji
        skipped_emoji = Emoji.SKIPPED.value if self.style.use_emoji else ""
        print(f"    {skipped_emoji}  {self.style.get_text('跳过:', 'Skipped:')} {self.style.colorize(str(skipped), Color.YELLOW)}")

        # Pass rate with target emoji
        pass_rate_color = Color.GREEN if pass_rate >= 80 else (Color.YELLOW if pass_rate >= 50 else Color.RED)
        rate_text = self.style.get_text("通过率", "Pass Rate")
        target_emoji = Emoji.TARGET.value if self.style.use_emoji else ""
        print(f"    {target_emoji} {rate_text}: {self.style.colorize(f'{pass_rate:.1f}%', pass_rate_color)}")

        print(self.style.header("━" * 70))
        print()

    def print_step(
        self,
        name: str,
        status: str,
        duration: Optional[float] = None,
        performance: Optional[dict] = None,
        error: Optional[str] = None
    ) -> None:
        """Print step result.

        Args:
            name: Step name
            status: Step status
            duration: Optional duration in ms
            performance: Optional performance metrics
            error: Optional error message
        """
        # Add blank line before each step
        print()

        # Status icon
        status_icons = {
            "success": Emoji.SUCCESS.value,
            "failure": Emoji.FAILURE.value,
            "skipped": Emoji.SKIPPED.value,
            "error": Emoji.ERROR.value,
        }
        icon = status_icons.get(status, "") if self.style.use_emoji else ""

        # Status color
        status_colors = {
            "success": Color.GREEN,
            "failure": Color.RED,
            "skipped": Color.YELLOW,
            "error": Color.BRIGHT_RED,
        }
        color = status_colors.get(status, Color.WHITE)

        # Print step header
        # 某些 emoji（如 ⏭️）显示宽度不同，需要额外空格
        extra_space = " " if status == "skipped" else ""
        print(f"  {self.style.colorize(icon, color)} {extra_space}{self.style.header(name)}")

        # Duration
        if duration is not None:
            duration_text = self.style.get_text(f"耗时: {duration:.2f}ms", f"Duration: {duration:.2f}ms")
            print(f"     {duration_text}")

        # Performance breakdown
        if performance:
            parts = []

            dns = performance.get("dns_time", 0)
            tcp = performance.get("tcp_time", 0)
            tls = performance.get("tls_time", 0)
            server = performance.get("server_time", 0)
            download = performance.get("download_time", 0)
            upload = performance.get("upload_time", 0)

            if dns > 0:
                parts.append(f"DNS: {dns:.2f}ms")
            if tcp > 0:
                parts.append(f"TCP: {tcp:.2f}ms")
            if tls > 0:
                parts.append(f"TLS: {tls:.2f}ms")
            if server > 0:
                parts.append(f"Server: {server:.2f}ms")
            if download > 0:
                parts.append(f"Download: {download:.2f}ms")
            if upload > 0:
                parts.append(f"Upload: {upload:.2f}ms")

            if parts:
                breakdown = self.style.get_text("详情:", "Breakdown:")
                print(f"     {breakdown} {' | '.join(parts)}")

            # Size
            size = performance.get("size", 0)
            if size > 0:
                size_kb = size / 1024
                size_text = self.style.get_text(f"大小: {size} bytes ({size_kb:.2f} KB)",
                                                   f"Size: {size} bytes ({size_kb:.2f} KB)")
                print(f"     {size_text}")

        # Error (no emoji, already shown in header)
        if error:
            error_text = self.style.get_text(f"错误: {error}", f"Error: {error}")
            print(f"     {self.style.colorize(error_text, Color.RED)}")

    def print_overall_summary(
        self,
        total_tests: int,
        passed_tests: int,
        failed_tests: int
    ) -> None:
        """Print overall summary for multiple test files.

        Args:
            total_tests: Total number of test cases
            passed_tests: Number of passed tests
            failed_tests: Number of failed tests
        """
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        self.print_header(
            self.style.get_text("总体概览", "OVERALL SUMMARY"),
            f"{passed_tests}/{total_tests} tests passed"
        )

        # Summary stats
        print(f"  {Emoji.CHART.value if self.style.use_emoji else ''} ", end="")
        print(f"{self.style.get_text('测试用例总数:', 'Total Test Cases:')} {self.style.colorize(str(total_tests), Color.CYAN)}")

        print(f"  {Emoji.SUCCESS.value if self.style.use_emoji else ''} ", end="")
        print(f"{self.style.get_text('通过:', 'Passed:')} {self.style.colorize(str(passed_tests), Color.GREEN)}")

        print(f"  {Emoji.FAILURE.value if self.style.use_emoji else ''} ", end="")
        print(f"{self.style.get_text('失败:', 'Failed:')} {self.style.colorize(str(failed_tests), Color.RED)}")

        rate_color = Color.GREEN if pass_rate == 100 else (Color.YELLOW if pass_rate >= 50 else Color.RED)
        print(f"  {Emoji.TARGET.value if self.style.use_emoji else ''} ", end="")
        print(f"{self.style.get_text('通过率:', 'Pass Rate:')} {self.style.colorize(f'{pass_rate:.1f}%', rate_color)}")

        print()


def create_formatter(
    use_color: Optional[bool] = None,
    use_emoji: Optional[bool] = None,
    lang: str = "zh"
) -> OutputFormatter:
    """Create output formatter with specified settings.

    Args:
        use_color: Enable colors (None for auto-detect)
        use_emoji: Enable emoji (None for auto-detect)
        lang: Language code ('zh' or 'en')

    Returns:
        OutputFormatter instance
    """
    style = ConsoleStyle(
        use_color=use_color if use_color is not None else True,
        use_emoji=use_emoji if use_emoji is not None else True,
        lang=lang
    )
    return OutputFormatter(style)
