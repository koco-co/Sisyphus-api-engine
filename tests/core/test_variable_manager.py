"""Unit tests for VariableManager.

Tests for variable management in apirun/core/variable_manager.py
Following Google Python Style Guide.

Includes tests for:
- Basic variable management functionality
- Environment variable integration
- Variable tracking and change history
- Profile override functionality
- Variable delta computation
- Debug information generation
"""

import os
import pytest
from apirun.core.variable_manager import VariableManager, VariableScope


class TestVariableManager:
    """Tests for VariableManager basic functionality."""

    def test_initialization(self):
        """Test VariableManager initialization."""
        vm = VariableManager()
        assert vm.global_vars == {}
        assert vm.profile_vars == {}
        assert vm.extracted_vars == {}

    def test_initialization_with_global_vars(self):
        """Test initialization with global variables."""
        vm = VariableManager(global_vars={"key": "value"})
        assert vm.global_vars == {"key": "value"}

    def test_set_and_get_global_variable(self):
        """Test setting and getting global variables."""
        vm = VariableManager(global_vars={"key": "value"})
        assert vm.get_variable("key") == "value"

    def test_get_variable_with_default(self):
        """Test getting variable with default value."""
        vm = VariableManager()
        assert vm.get_variable("nonexistent", "default") == "default"
        assert vm.get_variable("nonexistent") is None

    def test_set_profile(self):
        """Test setting profile variables."""
        vm = VariableManager()
        profile_vars = {"env": "test", "timeout": 30}
        vm.set_profile(profile_vars)
        assert vm.profile_vars == profile_vars

    def test_variable_priority(self):
        """Test variable priority: extracted > profile > global."""
        vm = VariableManager()
        vm.global_vars = {"key": "global"}
        vm.set_profile({"key": "profile"})
        vm.set_variable("key", "extracted")

        # Extracted should have highest priority
        assert vm.get_variable("key") == "extracted"

        # Clear extracted, profile should be returned
        vm.clear_extracted()
        assert vm.get_variable("key") == "profile"

        # Clear profile, global should be returned
        vm.profile_vars = {}
        assert vm.get_variable("key") == "global"

    def test_get_all_variables(self):
        """Test getting all variables with proper priority."""
        vm = VariableManager(global_vars={"global1": "value1"})
        vm.set_profile({"profile1": "value2"})
        vm.set_variable("extracted1", "value3")

        all_vars = vm.get_all_variables()
        assert all_vars["global1"] == "value1"
        assert all_vars["profile1"] == "value2"
        assert all_vars["extracted1"] == "value3"

    def test_render_string_simple(self):
        """Test rendering simple string with variable."""
        vm = VariableManager(global_vars={"name": "John"})
        rendered = vm.render_string("Hello ${name}")
        assert rendered == "Hello John"

    def test_render_string_nested(self):
        """Test rendering nested variables."""
        vm = VariableManager(global_vars={"config": {"base_url": "http://api.example.com"}})
        rendered = vm.render_string("URL: ${config.base_url}")
        assert rendered == "URL: http://api.example.com"

    def test_render_dict(self):
        """Test rendering dictionary with variables."""
        vm = VariableManager(global_vars={"user": "alice", "base": "http://api.example.com"})

        data = {
            "username": "${user}",
            "email": "test@example.com",
            "nested": {
                "value": "${user}_123",
                "url": "${base}/api"
            },
            "count": 5  # Non-string should remain unchanged
        }

        rendered = vm.render_dict(data)
        assert rendered["username"] == "alice"
        assert rendered["email"] == "test@example.com"
        assert rendered["nested"]["value"] == "alice_123"
        assert rendered["nested"]["url"] == "http://api.example.com/api"
        assert rendered["count"] == 5

    def test_render_list(self):
        """Test rendering list with variables."""
        vm = VariableManager(global_vars={"base": "http://api.example.com"})

        data = ["${base}/api1", "${base}/api2", "static", 123]
        rendered = vm._render_list(data)

        assert rendered[0] == "http://api.example.com/api1"
        assert rendered[1] == "http://api.example.com/api2"
        assert rendered[2] == "static"
        assert rendered[3] == 123

    def test_render_non_string(self):
        """Test rendering non-string value."""
        vm = VariableManager()
        result = vm.render_string(12345)
        assert result == 12345

    def test_render_no_template_syntax(self):
        """Test rendering string without template syntax."""
        vm = VariableManager()
        result = vm.render_string("Plain text")
        assert result == "Plain text"

    def test_snapshot_and_restore(self):
        """Test snapshot and restore functionality."""
        vm = VariableManager(global_vars={"key1": "value1"})
        vm.set_profile({"key2": "value2"})
        vm.set_variable("key3", "value3")

        # Create snapshot
        snapshot = vm.snapshot()
        assert snapshot["global"] == {"key1": "value1"}
        assert snapshot["profile"] == {"key2": "value2"}
        assert snapshot["extracted"] == {"key3": "value3"}

        # Modify variables
        vm.set_variable("key3", "modified")
        vm.profile_vars = {"key2": "modified"}

        # Restore from snapshot
        vm.restore_snapshot(snapshot)
        assert vm.extracted_vars == {"key3": "value3"}
        assert vm.profile_vars == {"key2": "value2"}

    def test_clear_extracted(self):
        """Test clearing extracted variables."""
        vm = VariableManager()
        vm.set_variable("key1", "value1")
        vm.set_variable("key2", "value2")

        assert len(vm.extracted_vars) == 2

        vm.clear_extracted()
        assert len(vm.extracted_vars) == 0

    def test_extract_from_string(self):
        """Test extracting value using regex."""
        vm = VariableManager()
        text = "User ID: 12345"
        pattern = r"User ID: (\d+)"

        result = vm.extract_from_string(pattern, text)
        # index=0 returns the full match
        assert result == "User ID: 12345"

    def test_extract_from_string_with_group(self):
        """Test extracting with specific capture group."""
        vm = VariableManager()
        text = "Name: John, Age: 30"
        pattern = r"Name: (\w+), Age: (\d+)"

        result = vm.extract_from_string(pattern, text, index=1)
        # index=1 returns the first capture group
        assert result == "John"

    def test_extract_from_string_no_match(self):
        """Test extraction when pattern doesn't match."""
        vm = VariableManager()
        text = "No numbers here"
        pattern = r"\d+"

        result = vm.extract_from_string(pattern, text)
        assert result is None

    def test_extract_from_string_invalid_pattern(self):
        """Test extraction with invalid regex pattern."""
        vm = VariableManager()
        with pytest.raises(ValueError):
            vm.extract_from_string("[invalid(", "text")


class TestVariableScope:
    """Tests for VariableScope context manager."""

    def test_variable_scope_context(self):
        """Test VariableScope as context manager."""
        vm = VariableManager(global_vars={"outer": "value"})

        with VariableScope(vm):
            vm.set_variable("inner", "inner_value")
            assert vm.get_variable("inner") == "inner_value"
            assert vm.get_variable("outer") == "value"

        # After context, extracted variables should be restored
        assert vm.get_variable("inner") is None
        assert vm.get_variable("outer") == "value"

    def test_variable_scope_restore_on_exit(self):
        """Test VariableScope restores state on exit."""
        vm = VariableManager(global_vars={"key1": "original"})
        vm.set_profile({"key2": "original_profile"})
        vm.set_variable("key3", "original_extracted")

        with VariableScope(vm) as scope:
            vm.set_variable("key1", "modified1")
            vm.set_profile({"key2": "modified2"})
            vm.set_variable("key3", "modified3")
            assert vm.get_variable("key1") == "modified1"
            assert vm.get_variable("key3") == "modified3"

        # Should restore to original state
        assert vm.get_variable("key1") == "original"
        assert vm.profile_vars == {"key2": "original_profile"}
        assert vm.extracted_vars == {"key3": "original_extracted"}


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


class TestConfigContext:
    """Tests for config context and nested variable references."""

    def test_set_config_context(self):
        """Test setting config context."""
        manager = VariableManager()

        config = {
            "profiles": {
                "dev": {"variables": {"api_key": "dev_key"}},
                "prod": {"variables": {"api_key": "prod_key"}}
            },
            "active_profile": "dev"
        }

        manager.set_config_context(config)

        assert manager.config_context == config
        assert manager.config_context["active_profile"] == "dev"

    def test_get_all_variables_includes_config(self):
        """Test that get_all_variables includes config context."""
        manager = VariableManager()

        config = {
            "profiles": {"dev": {"variables": {"api_key": "123"}}},
            "active_profile": "dev"
        }

        manager.set_config_context(config)
        manager.global_vars = {"global_var": "value"}

        all_vars = manager.get_all_variables()

        assert "config" in all_vars
        assert all_vars["config"]["active_profile"] == "dev"
        assert all_vars["global_var"] == "value"

    def test_render_string_with_config_reference(self):
        """Test rendering string with config reference."""
        manager = VariableManager()

        config = {
            "profiles": {
                "dev": {
                    "variables": {
                        "test_suffix": "0202093000"
                    }
                }
            },
            "active_profile": "dev"
        }

        manager.set_config_context(config)
        manager.global_vars = {"category_name": "test_${config.profiles.dev.variables.test_suffix}"}

        rendered = manager.render_string("${category_name}")

        assert rendered == "test_0202093000"

    def test_render_nested_config_references(self):
        """Test rendering with nested config references."""
        manager = VariableManager()

        config = {
            "profiles": {
                "ci_62": {
                    "variables": {
                        "test_suffix": "0202093000",
                        "env": "ci"
                    }
                }
            },
            "active_profile": "ci_62"
        }

        manager.set_config_context(config)

        # Test nested reference
        template = "${config.profiles.ci_62.variables.test_suffix}_${config.profiles.ci_62.variables.env}"
        rendered = manager.render_string(template)

        assert rendered == "0202093000_ci"

    def test_render_config_with_active_profile(self):
        """Test rendering with active_profile variable."""
        manager = VariableManager()

        config = {
            "profiles": {
                "dev": {"base_url": "http://dev.example.com"},
                "prod": {"base_url": "http://prod.example.com"}
            },
            "active_profile": "dev"
        }

        manager.set_config_context(config)

        # Reference using active_profile
        template = "${config.active_profile}"
        rendered = manager.render_string(template)

        assert rendered == "dev"

    def test_render_complex_nested_reference(self):
        """Test complex nested reference scenario."""
        manager = VariableManager()

        config = {
            "profiles": {
                "test": {
                    "variables": {
                        "suffix": "12345",
                        "prefix": "test"
                    }
                }
            },
            "active_profile": "test"
        }

        manager.set_config_context(config)
        manager.global_vars = {
            "datasource_name": "${config.profiles.test.variables.prefix}_${config.profiles.test.variables.suffix}"
        }

        all_vars = manager.get_all_variables()
        rendered = manager.render_string("${datasource_name}")

        assert rendered == "test_12345"

    def test_config_context_invalidation(self):
        """Test that changing config context invalidates cache."""
        manager = VariableManager()

        config1 = {"profiles": {"dev": {"variables": {"key": "value1"}}}}
        config2 = {"profiles": {"dev": {"variables": {"key": "value2"}}}}

        manager.set_config_context(config1)
        all_vars1 = manager.get_all_variables()

        assert all_vars1["config"]["profiles"]["dev"]["variables"]["key"] == "value1"

        # Change config context
        manager.set_config_context(config2)
        all_vars2 = manager.get_all_variables()

        assert all_vars2["config"]["profiles"]["dev"]["variables"]["key"] == "value2"
