"""Variable Manager for Sisyphus API Engine.

This module handles variable management including:
- Global variables
- Profile-specific variables
- Step-extracted variables
- Variable rendering with Jinja2 templates
- Variable tracking and change history
- Environment variable integration

Following Google Python Style Guide.
"""

import re
import copy
import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from jinja2 import Environment, BaseLoader, TemplateError


class VariableManager:
    """Manages test variables across different scopes.

    Variables are organized in layers (from lowest to highest priority):
    1. Global variables
    2. Environment variables (OS environment variables)
    3. Profile variables
    4. Profile overrides (CLI or runtime overrides)
    5. Step-extracted variables

    Attributes:
        global_vars: Global variable dictionary
        profile_vars: Active profile variables
        extracted_vars: Extracted variables from test steps
        profile_overrides: Runtime profile overrides
        env_vars_prefix: Prefix for environment variables to load
        enable_tracking: Whether to track variable changes
        change_history: History of variable changes
        _jinja_env: Jinja2 environment for template rendering
    """

    def __init__(
        self,
        global_vars: Optional[Dict[str, Any]] = None,
        env_vars_prefix: Optional[str] = None,
        enable_tracking: bool = False,
    ):
        """Initialize VariableManager.

        Args:
            global_vars: Initial global variables
            env_vars_prefix: Prefix for environment variables (e.g., "API_")
            enable_tracking: Whether to track variable changes
        """
        self.global_vars = global_vars or {}
        self.profile_vars: Dict[str, Any] = {}
        self.extracted_vars: Dict[str, Any] = {}
        self.profile_overrides: Dict[str, Any] = {}
        self.env_vars_prefix = env_vars_prefix
        self.enable_tracking = enable_tracking

        # Variable change tracking
        self.change_history: List[Dict[str, Any]] = []

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

    def load_environment_variables(
        self, prefix: Optional[str] = None, override: bool = False
    ) -> Dict[str, Any]:
        """Load variables from OS environment.

        Args:
            prefix: Environment variable prefix (e.g., "API_")
                   If None, uses self.env_vars_prefix
            override: Whether to override existing variables

        Returns:
            Dictionary of loaded environment variables
        """
        env_prefix = prefix or self.env_vars_prefix
        loaded_vars = {}

        for key, value in os.environ.items():
            if env_prefix:
                if key.startswith(env_prefix):
                    var_name = key[len(env_prefix):].lower()
                    loaded_vars[var_name] = value
            else:
                # Load all environment variables if no prefix
                loaded_vars[key.lower()] = value

        # Apply to profile_vars or profile_overrides based on override flag
        if override:
            self.profile_overrides.update(loaded_vars)
        else:
            self.profile_vars.update(loaded_vars)

        return loaded_vars

    def set_profile_override(
        self, key: str, value: Any, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set a profile override variable.

        Override variables have higher priority than regular profile variables.

        Args:
            key: Variable name
            value: Variable value
            context: Optional context information for tracking
        """
        old_value = self.get_variable(key)
        self.profile_overrides[key] = value

        if self.enable_tracking:
            self._track_change("override", key, old_value, value, context)

    def set_profile_overrides(self, overrides: Dict[str, Any]) -> None:
        """Set multiple profile override variables.

        Args:
            overrides: Dictionary of override variables
        """
        for key, value in overrides.items():
            self.set_profile_override(key, value)

    def clear_profile_overrides(self) -> None:
        """Clear all profile override variables."""
        self.profile_overrides.clear()

    def get_variable_with_source(self, name: str, default: Any = None) -> tuple:
        """Get variable value along with its source.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Tuple of (value, source) where source is one of:
            - "extracted"
            - "override"
            - "profile"
            - "env"
            - "global"
            - "default"
        """
        # Check in priority order
        if name in self.extracted_vars:
            return self.extracted_vars[name], "extracted"
        if name in self.profile_overrides:
            return self.profile_overrides[name], "override"
        if name in self.profile_vars:
            return self.profile_vars[name], "profile"

        # Check environment variables (after profile)
        env_key = f"{self.env_vars_prefix}{name.upper()}" if self.env_vars_prefix else name.upper()
        if env_key in os.environ:
            return os.environ[env_key], "env"

        if name in self.global_vars:
            return self.global_vars[name], "global"

        return default, "default"

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables merged (extracted > override > profile > env > global).

        Note: Environment variables are not merged into this dict as they are
        checked separately in get_variable_with_source().

        Returns:
            Merged variable dictionary
        """
        merged = copy.deepcopy(self.global_vars)
        merged.update(self.profile_vars)
        merged.update(self.profile_overrides)
        merged.update(self.extracted_vars)

        return merged

    def compute_delta(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Compute variable changes between two states.

        Args:
            before: Variable state before execution
            after: Variable state after execution

        Returns:
            Dictionary with changes in format:
            {
                "added": {"var_name": value},
                "modified": {"var_name": {"old": old_value, "new": new_value}},
                "deleted": {"var_name": old_value}
            }
        """
        delta = {
            "added": {},
            "modified": {},
            "deleted": {}
        }

        # Find added and modified variables
        for key, value in after.items():
            if key not in before:
                delta["added"][key] = value
            elif before[key] != value:
                delta["modified"][key] = {
                    "old": before[key],
                    "new": value
                }

        # Find deleted variables
        for key in before:
            if key not in after:
                delta["deleted"][key] = before[key]

        return delta

    def _track_change(
        self,
        source: str,
        var_name: str,
        old_value: Any,
        new_value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a variable change.

        Args:
            source: Source of change (extract/override/profile/global)
            var_name: Variable name
            old_value: Old variable value
            new_value: New variable value
            context: Additional context (step_name, etc.)
        """
        if not self.enable_tracking:
            return

        change_record = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "variable": var_name,
            "old_value": old_value,
            "new_value": new_value,
            "context": context or {},
        }

        self.change_history.append(change_record)

    def get_change_history(
        self, variable_name: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get variable change history.

        Args:
            variable_name: Filter by variable name (None for all)
            limit: Maximum number of records to return (None for all)

        Returns:
            List of change records
        """
        history = self.change_history

        if variable_name:
            history = [record for record in history if record["variable"] == variable_name]

        if limit:
            history = history[-limit:]

        return history

    def clear_change_history(self) -> None:
        """Clear all change history."""
        self.change_history.clear()

    def get_debug_info(self) -> Dict[str, Any]:
        """Get detailed debug information about all variables.

        Returns:
            Dictionary with variable sources and metadata
        """
        debug_info = {
            "global_vars": self.global_vars.copy(),
            "profile_vars": self.profile_vars.copy(),
            "profile_overrides": self.profile_overrides.copy(),
            "extracted_vars": self.extracted_vars.copy(),
            "env_vars_prefix": self.env_vars_prefix,
            "tracking_enabled": self.enable_tracking,
            "change_history_count": len(self.change_history),
        }

        # Add environment variables if prefix is set
        if self.env_vars_prefix:
            debug_info["environment_variables"] = {}
            for key, value in os.environ.items():
                if key.startswith(self.env_vars_prefix):
                    debug_info["environment_variables"][key] = value

        return debug_info

    def export_variables(
        self, include_source: bool = False, include_env: bool = False
    ) -> Dict[str, Any]:
        """Export all variables in a structured format.

        Args:
            include_source: Whether to include variable source information
            include_env: Whether to include environment variables

        Returns:
            Structured export of all variables
        """
        if include_source:
            exported = {}
            all_vars = self.get_all_variables()
            for var_name in all_vars:
                value, source = self.get_variable_with_source(var_name)
                exported[var_name] = {
                    "value": value,
                    "source": source
                }
            return exported
        else:
            return self.get_all_variables()


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
