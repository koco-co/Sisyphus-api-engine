"""Unit tests for enhanced VariableManager functionality.

Tests for environment variable integration, variable tracking, and profile overrides.
"""

import os
import pytest
from apirun.core.variable_manager import VariableManager


class TestEnvironmentVariables:
    """Tests for environment variable integration."""

    def test_load_environment_variables_with_prefix(self):
        """Test loading environment variables with prefix."""
        # Set test environment variables
        os.environ["API_TEST_VAR"] = "test_value"
        os.environ["API_BASE_URL"] = "http://example.com"
        os.environ["OTHER_VAR"] = "should_not_load"

        manager = VariableManager(env_vars_prefix="API_")
        loaded = manager.load_environment_variables()

        assert "test_var" in loaded
        assert loaded["test_var"] == "test_value"
        assert "base_url" in loaded
        assert "other_var" not in loaded

        # Cleanup
        del os.environ["API_TEST_VAR"]
        del os.environ["API_BASE_URL"]
        del os.environ["OTHER_VAR"]

    def test_load_environment_variables_without_prefix(self):
        """Test loading all environment variables without prefix."""
        os.environ["TEST_VAR1"] = "value1"
        os.environ["TEST_VAR2"] = "value2"

        manager = VariableManager()
        loaded = manager.load_environment_variables(prefix="")

        assert "test_var1" in loaded
        assert "test_var2" in loaded

        # Cleanup
        del os.environ["TEST_VAR1"]
        del os.environ["TEST_VAR2"]

    def test_environment_variables_priority(self):
        """Test that environment variables have correct priority."""
        os.environ["API_TEST_VAR"] = "env_value"

        manager = VariableManager(env_vars_prefix="API_")
        manager.global_vars = {"test_var": "global_value"}
        # Don't set profile_vars, so env var should be used

        value, source = manager.get_variable_with_source("test_var")

        # Environment variables should be checked after profile but before global
        # Since no profile_var is set, env var should be returned
        assert value == "env_value"
        assert source == "env"

        # Cleanup
        del os.environ["API_TEST_VAR"]

    def test_environment_variable_not_override_existing(self):
        """Test that environment variables don't override profile variables."""
        os.environ["API_TEST_VAR"] = "env_value"

        manager = VariableManager(env_vars_prefix="API_")
        manager.profile_vars = {"test_var": "profile_value"}

        # When profile_var is set, it should take precedence over env var
        value, source = manager.get_variable_with_source("test_var")
        # Should prefer profile_vars over environment variables
        assert value == "profile_value"
        assert source == "profile"

        # Cleanup
        del os.environ["API_TEST_VAR"]


class TestProfileOverrides:
    """Tests for profile override functionality."""

    def test_set_profile_override(self):
        """Test setting a profile override variable."""
        manager = VariableManager()
        manager.set_profile_override("test_var", "override_value")

        assert "test_var" in manager.profile_overrides
        value, source = manager.get_variable_with_source("test_var")
        assert value == "override_value"
        assert source == "override"

    def test_profile_override_priority(self):
        """Test that overrides have highest priority."""
        manager = VariableManager()
        manager.global_vars = {"test_var": "global_value"}
        manager.profile_vars = {"test_var": "profile_value"}
        manager.set_profile_override("test_var", "override_value")

        value, source = manager.get_variable_with_source("test_var")

        assert value == "override_value"
        assert source == "override"

    def test_set_multiple_profile_overrides(self):
        """Test setting multiple profile overrides at once."""
        manager = VariableManager()
        overrides = {"var1": "value1", "var2": "value2", "var3": "value3"}

        manager.set_profile_overrides(overrides)

        assert len(manager.profile_overrides) == 3
        assert manager.profile_overrides["var1"] == "value1"
        assert manager.profile_overrides["var2"] == "value2"
        assert manager.profile_overrides["var3"] == "value3"

    def test_clear_profile_overrides(self):
        """Test clearing all profile overrides."""
        manager = VariableManager()
        manager.set_profile_overrides({"var1": "value1", "var2": "value2"})

        assert len(manager.profile_overrides) == 2

        manager.clear_profile_overrides()

        assert len(manager.profile_overrides) == 0


class TestVariableTracking:
    """Tests for variable change tracking."""

    def test_tracking_disabled_by_default(self):
        """Test that tracking is disabled by default."""
        manager = VariableManager()

        assert manager.enable_tracking is False
        assert len(manager.change_history) == 0

    def test_enable_tracking(self):
        """Test enabling variable tracking."""
        manager = VariableManager(enable_tracking=True)

        assert manager.enable_tracking is True

        manager.set_profile_override("test_var", "new_value")

        assert len(manager.change_history) == 1

    def test_change_record_structure(self):
        """Test that change records have correct structure."""
        manager = VariableManager(enable_tracking=True)
        manager.set_profile_override("test_var", "new_value", context={"step": "step1"})

        assert len(manager.change_history) == 1
        record = manager.change_history[0]

        assert "timestamp" in record
        assert "source" in record
        assert "variable" in record
        assert "old_value" in record
        assert "new_value" in record
        assert "context" in record

        assert record["source"] == "override"
        assert record["variable"] == "test_var"
        assert record["new_value"] == "new_value"

    def test_get_change_history_for_variable(self):
        """Test getting change history for a specific variable."""
        manager = VariableManager(enable_tracking=True)

        manager.set_profile_override("var1", "value1")
        manager.set_profile_override("var2", "value2")
        manager.set_profile_override("var1", "value1_updated")

        var1_history = manager.get_change_history("var1")

        assert len(var1_history) == 2
        assert var1_history[0]["new_value"] == "value1"
        assert var1_history[1]["new_value"] == "value1_updated"

    def test_get_change_history_with_limit(self):
        """Test getting limited change history."""
        manager = VariableManager(enable_tracking=True)

        for i in range(10):
            manager.set_profile_override("var", f"value{i}")

        history = manager.get_change_history(limit=5)

        assert len(history) == 5

    def test_clear_change_history(self):
        """Test clearing change history."""
        manager = VariableManager(enable_tracking=True)

        manager.set_profile_override("var1", "value1")
        manager.set_profile_override("var2", "value2")

        assert len(manager.change_history) == 2

        manager.clear_change_history()

        assert len(manager.change_history) == 0


class TestVariableDelta:
    """Tests for variable delta computation."""

    def test_compute_delta_with_added_variables(self):
        """Test delta computation with added variables."""
        manager = VariableManager()

        before = {"var1": "value1"}
        after = {"var1": "value1", "var2": "value2"}

        delta = manager.compute_delta(before, after)

        assert "var2" in delta["added"]
        assert delta["added"]["var2"] == "value2"
        assert len(delta["modified"]) == 0
        assert len(delta["deleted"]) == 0

    def test_compute_delta_with_modified_variables(self):
        """Test delta computation with modified variables."""
        manager = VariableManager()

        before = {"var1": "old_value"}
        after = {"var1": "new_value"}

        delta = manager.compute_delta(before, after)

        assert "var1" in delta["modified"]
        assert delta["modified"]["var1"]["old"] == "old_value"
        assert delta["modified"]["var1"]["new"] == "new_value"
        assert len(delta["added"]) == 0
        assert len(delta["deleted"]) == 0

    def test_compute_delta_with_deleted_variables(self):
        """Test delta computation with deleted variables."""
        manager = VariableManager()

        before = {"var1": "value1", "var2": "value2"}
        after = {"var1": "value1"}

        delta = manager.compute_delta(before, after)

        assert "var2" in delta["deleted"]
        assert delta["deleted"]["var2"] == "value2"
        assert len(delta["added"]) == 0
        assert len(delta["modified"]) == 0

    def test_compute_delta_complex(self):
        """Test delta computation with multiple changes."""
        manager = VariableManager()

        before = {
            "var1": "value1",
            "var2": "old_value2",
            "var3": "value3",
            "var4": "value4",
        }
        after = {
            "var1": "value1",  # Unchanged
            "var2": "new_value2",  # Modified
            "var3": "value3",  # Unchanged
            "var5": "value5",  # Added
        }

        delta = manager.compute_delta(before, after)

        assert len(delta["added"]) == 1
        assert "var5" in delta["added"]
        assert len(delta["modified"]) == 1
        assert "var2" in delta["modified"]
        assert len(delta["deleted"]) == 1
        assert "var4" in delta["deleted"]


class TestDebugInfo:
    """Tests for debug information generation."""

    def test_get_debug_info(self):
        """Test getting comprehensive debug information."""
        manager = VariableManager(
            env_vars_prefix="API_", enable_tracking=True
        )
        manager.global_vars = {"global_var": "global_value"}
        manager.profile_vars = {"profile_var": "profile_value"}
        manager.set_profile_override("override_var", "override_value")
        manager.extracted_vars = {"extracted_var": "extracted_value"}

        debug_info = manager.get_debug_info()

        assert "global_vars" in debug_info
        assert "profile_vars" in debug_info
        assert "profile_overrides" in debug_info
        assert "extracted_vars" in debug_info
        assert "env_vars_prefix" in debug_info
        assert "tracking_enabled" in debug_info
        assert "change_history_count" in debug_info

        assert debug_info["global_vars"]["global_var"] == "global_value"
        assert debug_info["profile_vars"]["profile_var"] == "profile_value"
        assert debug_info["profile_overrides"]["override_var"] == "override_value"
        assert debug_info["extracted_vars"]["extracted_var"] == "extracted_value"
        assert debug_info["env_vars_prefix"] == "API_"
        assert debug_info["tracking_enabled"] is True

    def test_export_variables_with_source(self):
        """Test exporting variables with source information."""
        manager = VariableManager()
        manager.global_vars = {"var1": "value1"}
        manager.profile_vars = {"var2": "value2"}
        manager.set_profile_override("var3", "value3")

        exported = manager.export_variables(include_source=True)

        assert "var1" in exported
        assert "var2" in exported
        assert "var3" in exported

        assert exported["var1"]["value"] == "value1"
        assert exported["var1"]["source"] == "global"
        assert exported["var2"]["source"] == "profile"
        assert exported["var3"]["source"] == "override"

    def test_export_variables_without_source(self):
        """Test exporting variables without source information."""
        manager = VariableManager()
        manager.global_vars = {"var1": "value1"}
        manager.profile_vars = {"var2": "value2"}

        exported = manager.export_variables(include_source=False)

        assert exported == {"var1": "value1", "var2": "value2"}
        assert "source" not in exported.get("var1", {})


class TestVariablePriority:
    """Tests for variable priority ordering."""

    def test_full_priority_order(self):
        """Test complete priority order: extracted > override > profile > global."""
        manager = VariableManager()

        manager.global_vars = {"test_var": "global"}
        manager.profile_vars = {"test_var": "profile"}
        manager.set_profile_override("test_var", "override")
        manager.extracted_vars = {"test_var": "extracted"}

        value, source = manager.get_variable_with_source("test_var")

        assert value == "extracted"
        assert source == "extracted"

    def test_priority_without_extracted(self):
        """Test priority without extracted variables."""
        manager = VariableManager()

        manager.global_vars = {"test_var": "global"}
        manager.profile_vars = {"test_var": "profile"}
        manager.set_profile_override("test_var", "override")

        value, source = manager.get_variable_with_source("test_var")

        assert value == "override"
        assert source == "override"

    def test_priority_without_override(self):
        """Test priority without overrides."""
        manager = VariableManager()

        manager.global_vars = {"test_var": "global"}
        manager.profile_vars = {"test_var": "profile"}

        value, source = manager.get_variable_with_source("test_var")

        assert value == "profile"
        assert source == "profile"
