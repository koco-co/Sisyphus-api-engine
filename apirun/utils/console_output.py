"""Console Output Formatter with Rich Library.

This module provides beautiful console output using Rich library:
- Strict linear flow (Header → Process → Errors → Footer)
- Compact summary footer (no huge panels)
- Dimmed verbose output for better readability
- Progress tracking with step counters
- Detailed HTTP request/response logging in verbose mode

Following Google Python Style Guide.
"""

from dataclasses import dataclass
import json
import os
import sys
from typing import Any

from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


# Color class for backward compatibility
class Color:
    """ANSI color codes for backward compatibility.

    Maps to Rich color styles.
    """

    RESET = 'reset'
    BOLD = 'bold'
    DIM = 'dim'

    # Colors (mapped to Rich styles)
    BLACK = 'black'
    RED = 'red'
    GREEN = 'green'
    YELLOW = 'yellow'
    BLUE = 'blue'
    MAGENTA = 'magenta'
    CYAN = 'cyan'
    WHITE = 'white'

    # Bright colors
    BRIGHT_RED = 'bright_red'
    BRIGHT_GREEN = 'bright_green'
    BRIGHT_YELLOW = 'bright_yellow'
    BRIGHT_BLUE = 'bright_blue'
    BRIGHT_MAGENTA = 'bright_magenta'
    BRIGHT_CYAN = 'bright_cyan'
    BRIGHT_WHITE = 'bright_white'


class Emoji:
    """Emoji symbols for console output."""

    # Status
    SUCCESS = '✅'
    FAILURE = '❌'
    SKIPPED = '⏭️'
    WARNING = '⚠️'
    ERROR = '🚨'
    INFO = 'ℹ️'

    # Test
    ROCKET = '🚀'
    TEST_TUBE = '🧪'
    CHECKLIST = '✅'

    # Performance
    STOPWATCH = '⏱️'
    CHART = '📊'
    SPEED = '⚡'

    # Files
    FILE = '📄'
    FOLDER = '📁'

    # Other
    GEAR = '⚙️'
    STAR = '⭐'
    FIRE = '🔥'
    BULB = '💡'
    TARGET = '🎯'
    PACKAGE = '📦'
    HTTP = '🌐'
    REQUEST = '📤'
    RESPONSE = '📥'


@dataclass
class StepExtraction:
    """Variable extraction information.

    Attributes:
        var_name: Variable name
        value: Extracted value (truncated if too long)
        path: Extraction path (JSONPath, regex, etc.)
    """

    var_name: str
    value: str
    path: str

    def __str__(self) -> str:
        """Format extraction for display."""
        # Truncate value if too long
        display_value = self.value
        if len(display_value) > 50:
            display_value = display_value[:47] + '...'
        return f'{self.var_name} = {display_value} (Source: {self.path})'


@dataclass
class StepError:
    """Step error information.

    Attributes:
        error_type: Type of error (AssertionError, TemplateError, etc.)
        message: Error message
        context: Additional error context (optional)
    """

    error_type: str
    message: str
    context: str | None = None


class OutputFormatter:
    """Formatter for test execution output using Rich library.

    Features:
    - Strict linear flow (Header → Process → Errors → Footer)
    - Compact summary footer (inline text, not panel)
    - Dimmed verbose output
    - Progress tracking
    - Detailed request/response logging
    """

    def __init__(
        self,
        use_color: bool = True,
        use_emoji: bool = True,
        lang: str = 'zh',
        verbose: bool = False,
    ):
        """Initialize output formatter.

        Args:
            use_color: Enable colored output (default: True)
            use_emoji: Enable emoji symbols (default: True)
            lang: Language code ('zh' for Chinese, 'en' for English)
            verbose: Enable verbose mode for detailed output (default: False)
        """
        self._color_enabled = use_color and self._supports_color()
        self._emoji_enabled = use_emoji
        self.lang = lang
        self.verbose = verbose

        # Force emoji disable on older Windows terminals
        if sys.platform == 'win32':
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 0x0004)
            except Exception:
                self._emoji_enabled = False

        # Create Rich console
        self.console = Console(
            force_terminal=self._color_enabled,
            no_color=not self._color_enabled,
            legacy_windows=False,
        )

    def _supports_color(self) -> bool:
        """Check if terminal supports ANSI colors."""
        if not hasattr(sys.stdout, 'isatty'):
            return False

        if not sys.stdout.isatty():
            return False

        if os.environ.get('NO_COLOR'):
            return False

        if os.environ.get('TERM') == 'dumb':
            return False

        return True

    def _emoji(self, emoji_char: str) -> str:
        """Get emoji string if enabled."""
        return emoji_char if self._emoji_enabled else ''

    def _t(self, zh_text: str, en_text: str) -> str:
        """Get text based on language setting.

        Args:
            zh_text: Chinese text
            en_text: English text

        Returns:
            Text in configured language
        """
        return zh_text if self.lang == 'zh' else en_text

    def print_header(self, title: str, subtitle: str = '') -> None:
        """Print formatted header.

        Args:
            title: Main title
            subtitle: Optional subtitle
        """
        self.console.print()
        self.console.print(
            Panel(
                Text(title, style='bold cyan'), title_align='left', border_style='cyan'
            )
        )
        if subtitle:
            self.console.print(f'  [dim]{subtitle}[/]')

    def print_test_start(
        self, name: str, description: str = '', step_count: int = 0
    ) -> None:
        """Print test execution start message.

        Args:
            name: Test case name
            description: Test description
            step_count: Number of steps
        """
        # Test case info (Cleaner look)
        file_label = self._t('测试文件', 'Test File')

        # Using a Rule with title for a cleaner separation header
        self.console.print()
        self.console.print(
            Rule(title=f'[cyan bold]{file_label}: {name}[/]', style='cyan dim')
        )
        self.console.print()

        # Only print in verbose mode
        if description and self.verbose:
            info_emoji = self._emoji(Emoji.INFO)
            desc_label = self._t('用例描述', 'Description')
            self.console.print(f'[dim]{info_emoji} {desc_label}: {description}[/]')

        if step_count > 0:
            steps_text = self._t(f'({step_count} 步骤)', f'({step_count} Steps)')
            self.console.print(f'[dim]   {steps_text}[/]')

        self.console.print()

    def print_file_separator(self) -> None:
        """Print a visual separator between files in batch execution."""
        self.console.print()
        self.console.print(' ' * 80)  # Empty line
        self.console.print()

    def print_step(
        self,
        index: int,
        total: int,
        name: str,
        status: str,
        duration: float,
        extraction: StepExtraction | None = None,
        error: StepError | None = None,
        performance: dict[str, float] | None = None,
        request_data: dict[str, Any] | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Print step result in standard mode.

        Args:
            index: Step index (1-based)
            total: Total number of steps
            name: Step name
            status: Step status (passed/failed/skipped/error)
            duration: Duration in seconds
            extraction: Variable extraction info (if any)
            error: Error info (if failed)
            performance: Performance metrics (verbose mode only)
            request_data: Request data (verbose mode only)
            response_data: Response data (verbose mode only)
        """
        # Determine status icon and color
        is_success = status in ['success', 'passed']
        is_failed = status in ['failure', 'failed']

        if is_success:
            icon = self._emoji(Emoji.SUCCESS)
            color = 'green'
        elif is_failed:
            icon = self._emoji(Emoji.FAILURE)
            color = 'red bold'  # Make failure pop more
        elif status == 'skipped':
            icon = self._emoji(Emoji.SKIPPED)
            color = 'yellow'
        else:
            icon = self._emoji(Emoji.ERROR)
            color = 'red bold'

        # Create a grid for alignment
        grid = Table.grid(padding=(0, 1))
        grid.add_column(justify='left', no_wrap=True)  # Icon
        grid.add_column(justify='right', no_wrap=True)  # Index
        grid.add_column(justify='left')  # Name
        grid.add_column(justify='right', no_wrap=True)  # Duration

        # Format columns
        index_str = f'[{index}/{total}]'

        # Max length for name to ensure alignment, dynamic based on console width could be better
        # but for now we clamp it
        name_trunc = name
        if len(name) > 50:
            name_trunc = name[:47] + '...'

        # Add row
        grid.add_row(
            Text(icon),
            Text(index_str, style='dim'),
            Text(name_trunc, style=color),
            Text(f'{duration:.2f}s', style='dim'),
        )

        self.console.print(grid)

        # Check if we have performance data to show (for tree connector logic)
        has_performance = (
            self.verbose and performance and self._has_performance_data(performance)
        )

        # Print detailed request/response info if verbose
        if self.verbose and request_data and response_data:
            self._print_http_details(request_data, response_data)

        # Print extraction info ONLY in verbose mode
        if self.verbose and extraction:
            package_emoji = self._emoji(Emoji.PACKAGE)
            extract_label = self._t('提取', 'Extracted')
            # Use tree connector: ├─ if performance follows, └─ if last item
            connector = '├─' if has_performance else '└─'
            extraction_text = (
                f'     {connector} {package_emoji} {extract_label}: {extraction}'
            )
            self.console.print(extraction_text, style='blue dim')

        # Print performance details in verbose mode (dimmed and indented)
        if has_performance:
            self._print_performance_details(performance)

    def _print_http_details(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> None:
        """Print detailed HTTP request and response information.

        Args:
            request: Request dictionary
            response: Response dictionary
        """
        # Indent for all details
        indent = '     '
        connector = '│'

        # --- Request Section ---
        method = request.get('method', 'GET')
        url = request.get('url', '')
        headers = request.get('headers', {})
        body = request.get('body')

        req_title = f'{self._emoji(Emoji.REQUEST)} Request: {method} {url}'
        self.console.print(f'{indent}{req_title}', style='bold cyan')

        # Request Headers
        if headers:
            self.console.print(f'{indent}  Headers:', style='dim')
            for k, v in headers.items():
                self.console.print(f'{indent}    {k}: {v}', style='dim')

        # Request Body
        if body:
            self.console.print(f'{indent}  Body:', style='dim')
            self._print_body(body, indent + '    ')

        # --- Divider ---
        self.console.print(f'{indent}{connector}')

        # --- Response Section ---
        status_code = response.get('status_code', 0)
        # Handle status code color
        status_color = 'green' if 200 <= status_code < 300 else 'red'

        resp_title = f'{self._emoji(Emoji.RESPONSE)} Response: Status {status_code}'
        self.console.print(f'{indent}{resp_title}', style=f'bold {status_color}')

        # Response Body (we typically care more about response body than headers in logs)
        resp_body = response.get('body')
        if resp_body:
            self.console.print(f'{indent}  Body:', style='dim')
            self._print_body(resp_body, indent + '    ')

        self.console.print()

    def _print_body(self, body: Any, indent: str) -> None:
        """Print body content with syntax highlighting if possible.

        Args:
            body: Body content (dict, str, etc.)
            indent: Indentation string
        """
        try:
            if isinstance(body, (dict, list)):
                # JSON object
                json_str = json.dumps(body, indent=2, ensure_ascii=False)
                syntax = Syntax(json_str, 'json', theme='monokai', word_wrap=True)
                # Pad the syntax block with indentation
                self.console.print(Padding(syntax, (0, 0, 0, len(indent))))
            elif isinstance(body, str):
                # Try to parse string as JSON
                try:
                    parsed = json.loads(body)
                    json_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                    syntax = Syntax(json_str, 'json', theme='monokai', word_wrap=True)
                    self.console.print(Padding(syntax, (0, 0, 0, len(indent))))
                except json.JSONDecodeError:
                    # Plain text
                    self.console.print(f'{indent}{body}')
            else:
                self.console.print(f'{indent}{body}')
        except Exception:
            # Fallback
            self.console.print(f'{indent}{body}')

    def _has_performance_data(self, performance: Any) -> bool:
        """Check if performance data has any non-zero values.

        Args:
            performance: PerformanceMetrics object or dictionary

        Returns:
            True if there is performance data to display
        """
        if performance is None:
            return False

        if hasattr(performance, 'dns_time'):
            dns = getattr(performance, 'dns_time', 0) or 0
            tcp = getattr(performance, 'tcp_time', 0) or 0
            tls = getattr(performance, 'tls_time', 0) or 0
            ttfb = getattr(performance, 'server_time', 0) or 0
            download = getattr(performance, 'download_time', 0) or 0
        else:
            dns = performance.get('dns_time', 0) if isinstance(performance, dict) else 0
            tcp = performance.get('tcp_time', 0) if isinstance(performance, dict) else 0
            tls = performance.get('tls_time', 0) if isinstance(performance, dict) else 0
            ttfb = (
                performance.get('server_time', 0)
                if isinstance(performance, dict)
                else 0
            )
            download = (
                performance.get('download_time', 0)
                if isinstance(performance, dict)
                else 0
            )

        return any([dns, tcp, tls, ttfb, download])

    def _print_performance_details(self, performance: Any) -> None:
        """Print performance metrics in verbose mode (dimmed).

        Args:
            performance: PerformanceMetrics object or dictionary
        """
        # Handle both PerformanceMetrics object and dictionary
        if performance is None:
            return

        # Check if performance is a PerformanceMetrics object
        if hasattr(performance, 'dns_time'):
            # PerformanceMetrics object
            dns = getattr(performance, 'dns_time', 0) or 0
            tcp = getattr(performance, 'tcp_time', 0) or 0
            tls = getattr(performance, 'tls_time', 0) or 0
            ttfb = getattr(performance, 'server_time', 0) or 0
            download = getattr(performance, 'download_time', 0) or 0
        else:
            # Dictionary (backward compatibility)
            dns = performance.get('dns_time', 0) if isinstance(performance, dict) else 0
            tcp = performance.get('tcp_time', 0) if isinstance(performance, dict) else 0
            tls = performance.get('tls_time', 0) if isinstance(performance, dict) else 0
            ttfb = (
                performance.get('server_time', 0)
                if isinstance(performance, dict)
                else 0
            )
            download = (
                performance.get('download_time', 0)
                if isinstance(performance, dict)
                else 0
            )

        # Only print if we have actual data
        if not any([dns, tcp, tls, ttfb, download]):
            return

        # Format metrics line (all dimmed)
        metrics = []
        if dns > 0:
            metrics.append(f'DNS: {dns:.0f}ms')
        if tcp > 0:
            metrics.append(f'TCP: {tcp:.0f}ms')
        if tls > 0:
            metrics.append(f'TLS: {tls:.0f}ms')
        if ttfb > 0:
            metrics.append(f'TTFB: {ttfb:.0f}ms')
        if download > 0:
            metrics.append(f'Download: {download:.0f}ms')

        if metrics:
            # Use tree connector and dimmed style
            connector = '└─'
            speed_emoji = self._emoji(Emoji.SPEED) if self._emoji_enabled else ''
            metrics_str = ' | '.join(metrics)
            self.console.print(
                f'     {connector} {speed_emoji} {metrics_str}', style='dim'
            )

    def print_error_section(self, failed_steps: list[dict[str, Any]]) -> None:
        """Print error section at the end (before footer).

        Args:
            failed_steps: List of failed step information
        """
        if not failed_steps:
            return

        error_emoji = self._emoji(Emoji.ERROR)
        title = self._t('错误详情', 'Error Details')
        self.console.print()
        self.console.print(
            Rule(title=f'[bold red]{error_emoji} {title}[/]', style='red bold')
        )
        self.console.print()

        for step_info in failed_steps:
            index = step_info['index']
            name = step_info['name']
            error = step_info['error']

            # Error header
            step_label = self._t('步骤', 'Step')
            self.console.print(
                f'[bold red]{step_label} {index}: {name}[/]', highlight=False
            )
            self.console.print(f'[dim]    {error.error_type}[/]', highlight=False)

            # Error message
            reason_label = self._t('原因', 'Reason')
            self.console.print(
                f'[red]    {reason_label}:[/] {error.message}', highlight=False
            )

            # Context if available
            if error.context:
                context_label = self._t('上下文', 'Context')
                self.console.print(
                    f'[dim]    {context_label}: {error.context}[/]', highlight=False
                )

            self.console.print()

    def print_summary_footer(
        self,
        status: str,
        duration: float,
        total: int,
        passed: int,
        failed: int,
        skipped: int,
        pass_rate: float,
    ) -> None:
        """Print compact summary footer (inline text, not panel).

        Args:
            status: Test status (passed/failed/error)
            duration: Duration in seconds
            total: Total steps
            passed: Passed steps
            failed: Failed steps
            skipped: Skipped steps
            pass_rate: Pass rate percentage
        """
        # Determine background color based on status
        if status in ['passed', 'success']:
            bg_style = 'green'
            text_style = 'bold green'
            status_text = 'PASS'
        elif status in ['failed', 'failure']:
            bg_style = 'red'
            text_style = 'bold red'
            status_text = 'FAIL'
        else:
            bg_style = 'yellow'
            text_style = 'bold yellow'
            status_text = 'WARN'

        # Refined compact summary text
        chart_emoji = self._emoji(Emoji.CHART)
        failure_emoji = self._emoji(Emoji.FAILURE)
        stopwatch_emoji = self._emoji(Emoji.STOPWATCH)

        passed_text = self._t('通过', 'Passed')
        failed_text = self._t('失败', 'Failed')
        duration_text = self._t('执行耗时', 'Duration')  # Updated Copy

        # Simple, inline summary
        self.console.print()

        summary_grid = Table.grid(padding=(0, 2))
        summary_grid.add_column(style='dim')
        summary_grid.add_column(style='green')
        summary_grid.add_column(style='red' if failed > 0 else 'dim')
        summary_grid.add_column(style='cyan')
        summary_grid.add_column(style=text_style, justify='right')

        summary_grid.add_row(
            f'{chart_emoji} {self._t("总计", "Total")}: {total}',
            f'{self._emoji(Emoji.SUCCESS)} {passed_text}: {passed}',
            f'{failure_emoji} {failed_text}: {failed}',
            f'{stopwatch_emoji} {duration_text}: {duration:.2f}s',
            f'[{status_text}]',
        )

        # Center the summary if possible, or just print it
        # self.console.print(Align.center(summary_grid))
        # Keep left aligned but indented
        self.console.print(Padding(summary_grid, (0, 0, 0, 0)))
        self.console.print()

    def print_overall_summary(
        self, total_tests: int, passed_tests: int, failed_tests: int
    ) -> None:
        """Print overall summary for multiple test files.

        Args:
            total_tests: Total number of test cases
            passed_tests: Number of passed tests
            failed_tests: Number of failed tests
        """
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        self.console.print()
        self.console.print(
            Rule(title='[bold cyan]Sisyphus Execution Summary[/]', style='cyan bold')
        )
        self.console.print()

        # Create a Summary Table
        table = Table(box=box.ROUNDED, show_header=True, header_style='bold cyan')
        table.add_column(self._t('指标', 'Metric'), justify='left')
        table.add_column(self._t('数值', 'Value'), justify='right')

        chart_emoji = self._emoji(Emoji.CHART)
        total_label = self._t('测试文件总数', 'Total Test Files')
        table.add_row(f'{chart_emoji} {total_label}', str(total_tests), style='cyan')

        success_emoji = self._emoji(Emoji.SUCCESS)
        passed_label = self._t('通过', 'Passed')
        table.add_row(
            f'{success_emoji} {passed_label}', str(passed_tests), style='green'
        )

        failure_emoji = self._emoji(Emoji.FAILURE)
        failed_label = self._t('失败', 'Failed')
        failed_style = 'red bold' if failed_tests > 0 else 'dim'
        table.add_row(
            f'{failure_emoji} {failed_label}', str(failed_tests), style=failed_style
        )

        # Pass rate
        target_emoji = self._emoji(Emoji.TARGET)
        rate_label = self._t('通过率', 'Pass Rate')
        rate_color = (
            'green'
            if pass_rate == 100
            else ('yellow' if pass_rate >= 50 else 'red bold')
        )
        table.add_row(
            f'{target_emoji} {rate_label}', f'[{rate_color}]{pass_rate:.1f}%[/]'
        )

        self.console.print(table)
        self.console.print()

    # Backward compatibility methods (deprecated)
    def print_summary(self, *args, **kwargs) -> None:
        """Deprecated: Use print_summary_footer instead."""
        self.print_summary_footer(*args, **kwargs)

    # Compatibility methods for old API
    def get_text(self, zh_text: str, en_text: str) -> str:
        """Get text based on language setting (backward compatibility)."""
        return self._t(zh_text, en_text)

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text (backward compatibility)."""
        return f'[{color}]{text}[/]'

    def header(self, text: str) -> str:
        """Format header text (backward compatibility)."""
        return f'[bold cyan]{text}[/]'

    def dim(self, text: str) -> str:
        """Format dimmed text (backward compatibility)."""
        return f'[dim]{text}[/]'

    def info(self, text: str) -> str:
        """Format info text (backward compatibility)."""
        return text

    @property
    def style(self):
        """Style property for backward compatibility."""
        return self

    @property
    def use_emoji(self) -> bool:
        """Get emoji usage status (backward compatibility)."""
        return self._emoji_enabled


def create_formatter(
    use_color: bool | None = None,
    use_emoji: bool | None = None,
    lang: str = 'zh',
    verbose: bool = False,
) -> OutputFormatter:
    """Create output formatter with specified settings.

    Args:
        use_color: Enable colors (None for auto-detect)
        use_emoji: Enable emoji (None for auto-detect)
        lang: Language code ('zh' or 'en')
        verbose: Enable verbose mode for detailed output

    Returns:
        OutputFormatter instance
    """
    return OutputFormatter(
        use_color=use_color if use_color is not None else True,
        use_emoji=use_emoji if use_emoji is not None else True,
        lang=lang,
        verbose=verbose,
    )
