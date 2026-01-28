"""Jinja2 Template Rendering Utilities.

This module provides template rendering functions for the test engine.
Following Google Python Style Guide.
"""

from typing import Any, Dict, List, Union
from jinja2 import Environment, BaseLoader, TemplateError, StrictUndefined


class TemplateRenderer:
    """Jinja2 template renderer with custom configuration.

    Features:
    - Strict undefined variable checking
    - Custom filters for test data
    - Safe rendering with error handling

    Attributes:
        env: Jinja2 Environment instance
    """

    def __init__(self, strict: bool = True):
        """Initialize TemplateRenderer.

        Args:
            strict: Whether to raise errors for undefined variables
        """
        self.env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined if strict else None,
            trim_blocks=True,
            lstrip_blocks=True,
            variable_start_string="${",
            variable_end_string="}",
        )
        self._register_custom_filters()

    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with provided context.

        Args:
            template_str: Template string to render
            context: Variable context for rendering

        Returns:
            Rendered string

        Raises:
            TemplateError: If rendering fails
        """
        if not isinstance(template_str, str):
            return template_str

        # Quick return if no template syntax
        if "${" not in template_str and "{%" not in template_str:
            return template_str

        try:
            template = self.env.from_string(template_str)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateError(f"Template rendering failed: {e}")

    def render_safe(
        self, template_str: str, context: Dict[str, Any], default: str = ""
    ) -> str:
        """Render template with fallback on error.

        Args:
            template_str: Template string to render
            context: Variable context for rendering
            default: Default value if rendering fails

        Returns:
            Rendered string or default value
        """
        try:
            return self.render(template_str, context)
        except TemplateError:
            return default

    def _register_custom_filters(self) -> None:
        """Register custom Jinja2 filters."""

        def to_int(value: Any) -> int:
            """Convert value to integer."""
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        def to_float(value: Any) -> float:
            """Convert value to float."""
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        def to_bool(value: Any) -> bool:
            """Convert value to boolean."""
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        def default(value: Any, default_value: Any = "") -> Any:
            """Return default value if input is falsy."""
            if not value:
                return default_value
            return value

        def length(value: Any) -> int:
            """Get length of value."""
            try:
                return len(value)
            except TypeError:
                return 0

        # Register filters
        self.env.filters["int"] = to_int
        self.env.filters["float"] = to_float
        self.env.filters["bool"] = to_bool
        self.env.filters["default"] = default
        self.env.filters["length"] = length

    def render_dict(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively render all string values in a dictionary.

        Args:
            data: Dictionary to render
            context: Variable context for rendering

        Returns:
            Dictionary with rendered string values
        """
        if not isinstance(data, dict):
            return data

        rendered = {}
        for key, value in data.items():
            if isinstance(value, str):
                rendered[key] = self.render(value, context)
            elif isinstance(value, dict):
                rendered[key] = self.render_dict(value, context)
            elif isinstance(value, list):
                rendered[key] = self._render_list(value, context)
            else:
                rendered[key] = value
        return rendered

    def _render_list(self, data: List[Any], context: Dict[str, Any]) -> List[Any]:
        """Recursively render all string values in a list.

        Args:
            data: List to render
            context: Variable context for rendering

        Returns:
            List with rendered string values
        """
        rendered = []
        for item in data:
            if isinstance(item, str):
                rendered.append(self.render(item, context))
            elif isinstance(item, dict):
                rendered.append(self.render_dict(item, context))
            elif isinstance(item, list):
                rendered.append(self._render_list(item, context))
            else:
                rendered.append(item)
        return rendered


# Global template renderer instance
_global_renderer = TemplateRenderer()


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """Render template using global renderer.

    Args:
        template_str: Template string to render
        context: Variable context for rendering

    Returns:
        Rendered string
    """
    return _global_renderer.render(template_str, context)


def render_template_safe(
    template_str: str, context: Dict[str, Any], default: str = ""
) -> str:
    """Render template safely with fallback.

    Args:
        template_str: Template string to render
        context: Variable context for rendering
        default: Default value if rendering fails

    Returns:
        Rendered string or default value
    """
    return _global_renderer.render_safe(template_str, context, default)
