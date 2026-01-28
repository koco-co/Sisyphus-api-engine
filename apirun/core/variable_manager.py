"""Variable Manager for Sisyphus API Engine.

This module handles variable management including:
- Global variables
- Profile-specific variables
- Step-extracted variables
- Variable rendering with Jinja2 templates

Following Google Python Style Guide.
"""

import re
import copy
from typing import Any, Dict, Optional
from jinja2 import Environment, BaseLoader, TemplateError


class VariableManager:
    """Manages test variables across different scopes.

    Variables are organized in layers:
    1. Global variables (lowest priority)
    2. Profile variables
    3. Step-extracted variables (highest priority)

    Attributes:
        global_vars: Global variable dictionary
        profile_vars: Active profile variables
        extracted_vars: Extracted variables from test steps
        _jinja_env: Jinja2 environment for template rendering
    """

    def __init__(self, global_vars: Optional[Dict[str, Any]] = None):
        """Initialize VariableManager.

        Args:
            global_vars: Initial global variables
        """
        self.global_vars = global_vars or {}
        self.profile_vars: Dict[str, Any] = {}
        self.extracted_vars: Dict[str, Any] = {}

        # Initialize Jinja2 environment with custom delimiters
        self._jinja_env = Environment(
            loader=BaseLoader(),
            variable_start_string="${",
            variable_end_string="}"
        )

    def set_profile(self, profile_vars: Dict[str, Any]) -> None:
        """Set active profile variables.

        Args:
            profile_vars: Profile-specific variables
        """
        self.profile_vars = profile_vars

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable.

        Args:
            name: Variable name
            value: Variable value
        """
        self.extracted_vars[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value.

        Searches in order: extracted_vars, profile_vars, global_vars.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        if name in self.extracted_vars:
            return self.extracted_vars[name]
        if name in self.profile_vars:
            return self.profile_vars[name]
        if name in self.global_vars:
            return self.global_vars[name]
        return default

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables merged (extracted > profile > global).

        Returns:
            Merged variable dictionary
        """
        merged = copy.deepcopy(self.global_vars)
        merged.update(self.profile_vars)
        merged.update(self.extracted_vars)
        return merged

    def render_string(self, template_str: str) -> str:
        """Render a template string with current variables.

        Supports Jinja2 syntax: ${variable_name}

        Args:
            template_str: Template string to render

        Returns:
            Rendered string

        Raises:
            TemplateError: If template rendering fails
        """
        if not isinstance(template_str, str):
            return template_str

        # Quick check for template syntax
        if "${" not in template_str and "{%" not in template_str:
            return template_str

        try:
            template = self._jinja_env.from_string(template_str)
            return template.render(**self.get_all_variables())
        except TemplateError as e:
            raise TemplateError(f"Failed to render template '{template_str}': {e}")

    def render_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively render all string values in a dictionary.

        Args:
            data: Dictionary to render

        Returns:
            Dictionary with rendered string values
        """
        if not isinstance(data, dict):
            return data

        rendered = {}
        for key, value in data.items():
            if isinstance(value, str):
                rendered[key] = self.render_string(value)
            elif isinstance(value, dict):
                rendered[key] = self.render_dict(value)
            elif isinstance(value, list):
                rendered[key] = self._render_list(value)
            else:
                rendered[key] = value
        return rendered

    def _render_list(self, data: list) -> list:
        """Recursively render all string values in a list.

        Args:
            data: List to render

        Returns:
            List with rendered string values
        """
        rendered = []
        for item in data:
            if isinstance(item, str):
                rendered.append(self.render_string(item))
            elif isinstance(item, dict):
                rendered.append(self.render_dict(item))
            elif isinstance(item, list):
                rendered.append(self._render_list(item))
            else:
                rendered.append(item)
        return rendered

    def extract_from_string(
        self, pattern: str, text: str, index: int = 0
    ) -> Optional[str]:
        """Extract value from string using regex.

        Args:
            pattern: Regular expression pattern
            text: Text to search in
            index: Capture group index (default: 0 for full match)

        Returns:
            Extracted value or None if not found
        """
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(index)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
        return None

    def clear_extracted(self) -> None:
        """Clear all extracted variables."""
        self.extracted_vars.clear()

    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of current variable state.

        Returns:
            Deep copy of all variables
        """
        return {
            "global": copy.deepcopy(self.global_vars),
            "profile": copy.deepcopy(self.profile_vars),
            "extracted": copy.deepcopy(self.extracted_vars),
        }

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore variable state from snapshot.

        Args:
            snapshot: Snapshot from snapshot() method
        """
        if "global" in snapshot:
            self.global_vars = copy.deepcopy(snapshot["global"])
        if "profile" in snapshot:
            self.profile_vars = copy.deepcopy(snapshot["profile"])
        if "extracted" in snapshot:
            self.extracted_vars = copy.deepcopy(snapshot["extracted"])


class VariableScope:
    """Context manager for variable scope isolation.

    Usage:
        with VariableScope(manager) as scope:
            # Modify variables
            manager.set_variable("x", 1)
        # Variables automatically restored after exit
    """

    def __init__(self, manager: VariableManager):
        """Initialize VariableScope.

        Args:
            manager: VariableManager instance
        """
        self.manager = manager
        self._snapshot: Optional[Dict[str, Any]] = None

    def __enter__(self) -> "VariableScope":
        """Enter context and save current state."""
        self._snapshot = self.manager.snapshot()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore previous state."""
        if self._snapshot:
            self.manager.restore_snapshot(self._snapshot)
        return False
