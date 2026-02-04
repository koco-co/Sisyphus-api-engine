"""Global Configuration Manager for Sisyphus API Engine.

This module implements hierarchical configuration loading:
1. Global config from .sisyphus/config.yaml
2. Test case config from YAML file
3. Default values as fallback

Following Google Python Style Guide.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from typing import Union

import yaml

from apirun.core.models import GlobalConfig, ProfileConfig


class GlobalConfigManager:
    """Manager for loading and merging global configurations.

    Configuration priority (highest to lowest):
    1. Test case config (from YAML file)
    2. Global config (from .sisyphus/config.yaml)
    3. Default values

    Attributes:
        project_root: Project root directory
        global_config_path: Path to global config file
        global_config: Loaded global configuration dict
    """

    # Global config filename
    CONFIG_FILENAME = ".sisyphus"
    CONFIG_FILE = "config.yaml"
    CONFIG_PATH = os.path.join(CONFIG_FILENAME, CONFIG_FILE)

    def __init__(self, test_file_path: Optional[str] = None):
        """Initialize GlobalConfigManager.

        Args:
            test_file_path: Path to test case YAML file (used to locate project root)
        """
        self.project_root = self._find_project_root(test_file_path)
        self.global_config_path = os.path.join(self.project_root, self.CONFIG_PATH)
        self.global_config: Dict[str, Any] = {}
        self._load_global_config()

    def _find_project_root(self, test_file_path: Optional[str] = None) -> str:
        """Find project root directory by searching for config file.

        Search strategy:
        1. If test_file_path provided, start from its directory
        2. Search upward for .sisyphus directory
        3. Fall back to current directory

        Args:
            test_file_path: Path to test case file

        Returns:
            Project root directory path
        """
        # Start from test file directory or current directory
        if test_file_path:
            start_dir = os.path.abspath(os.path.dirname(test_file_path))
        else:
            start_dir = os.path.abspath(".")

        # Search upward for .sisyphus directory
        current_dir = start_dir
        while current_dir != "/":
            config_path = os.path.join(current_dir, self.CONFIG_PATH)
            if os.path.exists(config_path):
                return current_dir

            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir

        # Fall back to current directory
        return os.path.abspath(".")

    def _load_global_config(self) -> None:
        """Load global configuration from .sisyphus/config.yaml.

        If config file doesn't exist, global_config remains empty dict.
        """
        if not os.path.exists(self.global_config_path):
            return

        try:
            with open(self.global_config_path, "r", encoding="utf-8") as f:
                self.global_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load global config from {self.global_config_path}: {e}")
            self.global_config = {}

    def get_merged_config(self, test_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge test case config with global config.

        Priority: test_config > global_config > defaults

        Args:
            test_config: Configuration from test case YAML file

        Returns:
            Merged configuration dictionary
        """
        # Start with global config
        merged = self.global_config.copy()

        # Apply test config overrides
        if test_config:
            merged = self._deep_merge(merged, test_config)

        # Ensure required fields have defaults
        merged.setdefault("profiles", {})
        merged.setdefault("active_profile", "dev")
        merged.setdefault("timeout", 30)
        merged.setdefault("retry_times", 2)

        # Handle versioned profiles (e.g., "v1.dev", "v2.prod")
        if "variables" in merged and "active_profile" in merged:
            active_profile = merged["active_profile"]
            profile_vars = self._get_profile_variables(merged, active_profile)
            if profile_vars:
                # Merge global variables into profile variables
                # Profile variables have higher priority
                merged["profiles"][active_profile] = merged["profiles"].get(active_profile, {})
                merged["profiles"][active_profile]["variables"] = {
                    **merged.get("variables", {}),
                    **profile_vars
                }

        return merged

    def _get_profile_variables(self, config: Dict[str, Any], active_profile: str) -> Dict[str, Any]:
        """Get variables from active profile, supporting versioned profiles.

        Args:
            config: Merged configuration dictionary
            active_profile: Active profile name (e.g., "dev" or "v1.dev")

        Returns:
            Variables dictionary from the profile
        """
        profiles = config.get("profiles", {})

        # Check if profile exists directly (non-versioned)
        if active_profile in profiles:
            return profiles[active_profile].get("variables", {})

        # Check if profile is versioned (e.g., "v1.dev")
        if "." in active_profile:
            version, env = active_profile.split(".", 1)
            if version in profiles and isinstance(profiles[version], dict):
                version_profiles = profiles[version]
                if env in version_profiles:
                    return version_profiles[env].get("variables", {})

        return {}

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary (lower priority)
            override: Override dictionary (higher priority)

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def create_global_config_model(self, merged_config: Dict[str, Any]) -> Optional[GlobalConfig]:
        """Create GlobalConfig model from merged configuration.

        Args:
            merged_config: Merged configuration dictionary

        Returns:
            GlobalConfig object or None if creation fails
        """
        try:
            # Extract profiles
            profiles_data = merged_config.get("profiles", {})
            profiles = {}
            for name, profile_data in profiles_data.items():
                profiles[name] = ProfileConfig(
                    base_url=profile_data.get("base_url"),
                    variables=profile_data.get("variables"),
                    timeout=profile_data.get("timeout"),
                    verify_ssl=profile_data.get("verify_ssl", True),
                    overrides=profile_data.get("overrides"),
                    priority=profile_data.get("priority", 0),
                )

            # Create GlobalConfig
            config = GlobalConfig(
                name=merged_config.get("name", "Global Config"),
                active_profile=merged_config.get("active_profile", "dev"),
                profiles=profiles or None,
                variables=merged_config.get("variables"),
                timeout=merged_config.get("timeout", 30),
                retry_times=merged_config.get("retry_times", 2),
                retry_policy=merged_config.get("retry_policy"),
                debug=merged_config.get("debug"),
                env_vars=merged_config.get("env_vars"),
                data_source=merged_config.get("data_source"),
                websocket=merged_config.get("websocket"),
                output=merged_config.get("output"),
            )

            return config

        except Exception as e:
            print(f"Warning: Failed to create GlobalConfig model: {e}")
            return None

    @staticmethod
    def is_global_config_available() -> bool:
        """Check if global config file exists.

        Returns:
            True if .sisyphus/config.yaml exists
        """
        return os.path.exists(GlobalConfigManager.CONFIG_PATH)


# Convenience function for backward compatibility
def load_global_config(test_file_path: Optional[str] = None) -> Dict[str, Any]:
    """Load global configuration.

    Args:
        test_file_path: Path to test case file

    Returns:
        Global configuration dictionary (empty if not found)
    """
    manager = GlobalConfigManager(test_file_path)
    return manager.global_config
