"""Unit tests for VariableManager.

Tests for variable management in apirun/core/variable_manager.py
Following Google Python Style Guide.
"""

import pytest
from apirun.core.variable_manager import VariableManager, VariableScope


class TestVariableManager:
    """Tests for VariableManager class."""

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
