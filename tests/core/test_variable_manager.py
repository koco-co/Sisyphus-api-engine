"""变量管理器单元测试。

本模块包含对 apirun/core/variable_manager.py 中 VariableManager 类的全面单元测试。
遵循 Google Python Style Guide。
"""

import os
import pytest
from unittest.mock import patch

from apirun.core.variable_manager import VariableManager, VariableScope


class TestVariableManagerInit:
    """测试 VariableManager 初始化。"""

    def test_init_default(self):
        """测试默认初始化。"""
        vm = VariableManager()

        assert vm.global_vars == {}
        assert vm.profile_vars == {}
        assert vm.extracted_vars == {}
        assert vm.profile_overrides == {}
        assert vm.env_vars_prefix is None
        assert vm.enable_tracking is False

    def test_init_with_global_vars(self):
        """测试带初始全局变量的初始化。"""
        initial_vars = {"api_key": "test123", "base_url": "https://api.example.com"}
        vm = VariableManager(global_vars=initial_vars)

        assert vm.global_vars == initial_vars
        assert vm.get_variable("api_key") == "test123"

    def test_init_with_env_prefix(self):
        """测试带环境变量前缀的初始化。"""
        vm = VariableManager(env_vars_prefix="API_")

        assert vm.env_vars_prefix == "API_"

    def test_init_with_tracking_enabled(self):
        """测试启用跟踪功能的初始化。"""
        vm = VariableManager(enable_tracking=True)

        assert vm.enable_tracking is True
        assert vm.change_history == []


class TestVariableBasicOperations:
    """测试变量的基本操作。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        return VariableManager()

    def test_set_and_get_variable(self, vm):
        """测试设置和获取变量。"""
        vm.set_variable("user_id", 12345)

        assert vm.get_variable("user_id") == 12345
        assert "user_id" in vm.extracted_vars

    def test_get_variable_not_found_returns_default(self, vm):
        """测试获取不存在的变量返回默认值。"""
        result = vm.get_variable("nonexistent", "default_value")

        assert result == "default_value"

    def test_get_variable_not_found_returns_none(self, vm):
        """测试获取不存在的变量返回 None。"""
        result = vm.get_variable("nonexistent")

        assert result is None

    def test_variable_priority_extracted_over_profile(self, vm):
        """测试提取变量优先于 profile 变量。"""
        vm.profile_vars = {"token": "profile_token"}
        vm.extracted_vars = {"token": "extracted_token"}

        assert vm.get_variable("token") == "extracted_token"

    def test_variable_priority_profile_over_global(self, vm):
        """测试 profile 变量优先于全局变量。"""
        vm.global_vars = {"base_url": "global_url"}
        vm.profile_vars = {"base_url": "profile_url"}

        assert vm.get_variable("base_url") == "profile_url"

    def test_clear_extracted_variables(self, vm):
        """测试清除提取变量。"""
        vm.set_variable("var1", "value1")
        vm.set_variable("var2", "value2")

        vm.clear_extracted()

        assert vm.extracted_vars == {}
        assert vm.get_variable("var1") is None


class TestProfileOperations:
    """测试 Profile 相关操作。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        return VariableManager()

    def test_set_profile(self, vm):
        """测试设置 profile 变量。"""
        profile_vars = {"env": "dev", "debug": True}
        vm.set_profile(profile_vars)

        assert vm.profile_vars == profile_vars
        assert vm.get_variable("env") == "dev"

    def test_set_profile_override(self, vm):
        """测试设置 profile 覆盖变量。"""
        vm.set_profile_override("timeout", 60)

        assert vm.profile_overrides["timeout"] == 60

    def test_set_profile_overrides(self, vm):
        """测试批量设置 profile 覆盖变量。"""
        overrides = {"timeout": 60, "retry": 3}
        vm.set_profile_overrides(overrides)

        assert vm.profile_overrides == overrides

    def test_clear_profile_overrides(self, vm):
        """测试清除 profile 覆盖变量。"""
        vm.set_profile_overrides({"key1": "value1"})
        vm.clear_profile_overrides()

        assert vm.profile_overrides == {}


class TestConfigContext:
    """测试配置上下文功能。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        return VariableManager()

    def test_set_config_context(self, vm):
        """测试设置配置上下文。"""
        config = {
            "profiles": {
                "dev": {"base_url": "https://dev.api.example.com"},
                "prod": {"base_url": "https://api.example.com"},
            }
        }
        vm.set_config_context(config)

        assert vm.config_context == config

    def test_config_context_in_all_variables(self, vm):
        """测试配置上下文包含在 get_all_variables 结果中。"""
        config = {"profiles": {"dev": {"key": "value"}}}
        vm.set_config_context(config)

        all_vars = vm.get_all_variables()

        assert "config" in all_vars
        assert all_vars["config"] == config


class TestTemplateRendering:
    """测试模板渲染功能。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        vm = VariableManager()
        vm.global_vars = {"base_url": "https://api.example.com", "version": "v1"}
        return vm

    def test_render_simple_variable(self, vm):
        """测试渲染简单变量。"""
        result = vm.render_string("${base_url}/users")

        assert result == "https://api.example.com/users"

    def test_render_multiple_variables(self, vm):
        """测试渲染多个变量。"""
        result = vm.render_string("${base_url}/${version}/users")

        assert result == "https://api.example.com/v1/users"

    def test_render_no_template_returns_original(self, vm):
        """测试无模板语法时返回原始字符串。"""
        result = vm.render_string("plain text")

        assert result == "plain text"

    def test_render_non_string_returns_as_is(self, vm):
        """测试非字符串输入直接返回。"""
        result = vm.render_string(12345)

        assert result == 12345

    def test_render_dict(self, vm):
        """测试渲染字典。"""
        data = {
            "url": "${base_url}/api",
            "headers": {"Accept": "application/json"},
            "nested": {"path": "${version}"}
        }
        result = vm.render_dict(data)

        assert result["url"] == "https://api.example.com/api"
        assert result["nested"]["path"] == "v1"
        assert result["headers"]["Accept"] == "application/json"

    def test_render_nested_variables(self):
        """测试渲染嵌套变量引用。"""
        vm = VariableManager()
        vm.global_vars = {
            "host": "example.com",
            "base_url": "https://${host}",
        }

        result = vm.render_string("${base_url}/api")

        assert result == "https://example.com/api"


class TestVariableSnapshot:
    """测试变量快照功能。"""

    @pytest.fixture
    def vm(self):
        """创建带数据的 VariableManager 实例。"""
        vm = VariableManager()
        vm.global_vars = {"global_var": "global_value"}
        vm.profile_vars = {"profile_var": "profile_value"}
        vm.extracted_vars = {"extracted_var": "extracted_value"}
        return vm

    def test_snapshot_captures_state(self, vm):
        """测试快照捕获当前状态。"""
        snapshot = vm.snapshot()

        assert snapshot["global"]["global_var"] == "global_value"
        assert snapshot["profile"]["profile_var"] == "profile_value"
        assert snapshot["extracted"]["extracted_var"] == "extracted_value"

    def test_restore_snapshot(self, vm):
        """测试恢复快照。"""
        snapshot = vm.snapshot()

        # 修改变量
        vm.set_variable("new_var", "new_value")
        vm.global_vars["global_var"] = "modified"

        # 恢复快照
        vm.restore_snapshot(snapshot)

        assert vm.global_vars["global_var"] == "global_value"
        assert "new_var" not in vm.extracted_vars


class TestVariableDelta:
    """测试变量变化计算。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        return VariableManager()

    def test_compute_delta_added(self, vm):
        """测试计算新增变量。"""
        before = {"a": 1}
        after = {"a": 1, "b": 2}

        delta = vm.compute_delta(before, after)

        assert delta["added"] == {"b": 2}
        assert delta["modified"] == {}
        assert delta["deleted"] == {}

    def test_compute_delta_modified(self, vm):
        """测试计算修改的变量。"""
        before = {"a": 1}
        after = {"a": 2}

        delta = vm.compute_delta(before, after)

        assert delta["added"] == {}
        assert delta["modified"] == {"a": {"old": 1, "new": 2}}

    def test_compute_delta_deleted(self, vm):
        """测试计算删除的变量。"""
        before = {"a": 1, "b": 2}
        after = {"a": 1}

        delta = vm.compute_delta(before, after)

        assert delta["deleted"] == {"b": 2}


class TestGetAllVariables:
    """测试 get_all_variables 方法。"""

    def test_merge_priority(self):
        """测试变量合并优先级。"""
        vm = VariableManager()
        vm.global_vars = {"key": "global"}
        vm.profile_vars = {"key": "profile"}
        vm.profile_overrides = {"key": "override"}
        vm.extracted_vars = {"key": "extracted"}

        all_vars = vm.get_all_variables()

        # extracted 优先级最高
        assert all_vars["key"] == "extracted"

    def test_cache_optimization(self):
        """测试缓存优化。"""
        vm = VariableManager()
        vm.global_vars = {"test": "value"}

        # 第一次调用
        result1 = vm.get_all_variables()
        # 第二次调用（应使用缓存）
        result2 = vm.get_all_variables()

        assert result1 == result2
        assert vm._cache_dirty is False

    def test_cache_invalidation_on_change(self):
        """测试变量更改时缓存失效。"""
        vm = VariableManager()
        vm.global_vars = {"test": "value"}
        vm.get_all_variables()  # 填充缓存

        vm.set_variable("new_var", "new_value")

        assert vm._cache_dirty is True


class TestVariableWithSource:
    """测试 get_variable_with_source 方法。"""

    def test_source_extracted(self):
        """测试提取变量来源。"""
        vm = VariableManager()
        vm.extracted_vars = {"var": "value"}

        value, source = vm.get_variable_with_source("var")

        assert value == "value"
        assert source == "extracted"

    def test_source_override(self):
        """测试覆盖变量来源。"""
        vm = VariableManager()
        vm.profile_overrides = {"var": "value"}

        value, source = vm.get_variable_with_source("var")

        assert value == "value"
        assert source == "override"

    def test_source_profile(self):
        """测试 profile 变量来源。"""
        vm = VariableManager()
        vm.profile_vars = {"var": "value"}

        value, source = vm.get_variable_with_source("var")

        assert value == "value"
        assert source == "profile"

    def test_source_global(self):
        """测试全局变量来源。"""
        vm = VariableManager()
        vm.global_vars = {"var": "value"}

        value, source = vm.get_variable_with_source("var")

        assert value == "value"
        assert source == "global"

    def test_source_default(self):
        """测试默认值来源。"""
        vm = VariableManager()

        value, source = vm.get_variable_with_source("var", "default")

        assert value == "default"
        assert source == "default"


class TestEnvironmentVariables:
    """测试环境变量功能。"""

    def test_load_environment_variables_with_prefix(self):
        """测试加载带前缀的环境变量。"""
        vm = VariableManager(env_vars_prefix="TEST_")

        with patch.dict(os.environ, {"TEST_API_KEY": "secret123", "OTHER_VAR": "ignored"}):
            loaded = vm.load_environment_variables()

        assert "api_key" in loaded
        assert loaded["api_key"] == "secret123"
        assert "OTHER_VAR" not in loaded

    def test_load_environment_variables_override(self):
        """测试环境变量覆盖模式。"""
        vm = VariableManager(env_vars_prefix="APP_")

        with patch.dict(os.environ, {"APP_DEBUG": "true"}):
            vm.load_environment_variables(override=True)

        assert "debug" in vm.profile_overrides


class TestVariableTracking:
    """测试变量跟踪功能。"""

    def test_tracking_disabled_by_default(self):
        """测试默认禁用跟踪。"""
        vm = VariableManager()
        vm.set_profile_override("key", "value")

        assert vm.change_history == []

    def test_tracking_enabled(self):
        """测试启用跟踪。"""
        vm = VariableManager(enable_tracking=True)
        vm.set_profile_override("key", "value")

        assert len(vm.change_history) == 1
        assert vm.change_history[0]["variable"] == "key"
        assert vm.change_history[0]["new_value"] == "value"

    def test_get_change_history_filtered(self):
        """测试按变量名过滤变更历史。"""
        vm = VariableManager(enable_tracking=True)
        vm.set_profile_override("a", 1)
        vm.set_profile_override("b", 2)
        vm.set_profile_override("a", 3)

        history = vm.get_change_history(variable_name="a")

        assert len(history) == 2

    def test_clear_change_history(self):
        """测试清除变更历史。"""
        vm = VariableManager(enable_tracking=True)
        vm.set_profile_override("key", "value")
        vm.clear_change_history()

        assert vm.change_history == []


class TestVariableScope:
    """测试 VariableScope 上下文管理器。"""

    def test_scope_isolates_changes(self):
        """测试作用域隔离变量更改。"""
        vm = VariableManager()
        vm.global_vars = {"shared": "original"}

        with VariableScope(vm):
            vm.set_variable("temp", "temporary")
            vm.global_vars["shared"] = "modified"

        # 退出作用域后恢复
        assert vm.global_vars["shared"] == "original"
        assert "temp" not in vm.extracted_vars

    def test_scope_returns_self(self):
        """测试作用域返回自身。"""
        vm = VariableManager()

        with VariableScope(vm) as scope:
            assert isinstance(scope, VariableScope)


class TestDebugInfo:
    """测试调试信息功能。"""

    def test_get_debug_info(self):
        """测试获取调试信息。"""
        vm = VariableManager(enable_tracking=True)
        vm.global_vars = {"g": 1}
        vm.profile_vars = {"p": 2}
        vm.extracted_vars = {"e": 3}

        info = vm.get_debug_info()

        assert info["global_vars"] == {"g": 1}
        assert info["profile_vars"] == {"p": 2}
        assert info["extracted_vars"] == {"e": 3}
        assert info["tracking_enabled"] is True


class TestExportVariables:
    """测试变量导出功能。"""

    def test_export_without_source(self):
        """测试不含来源的导出。"""
        vm = VariableManager()
        vm.global_vars = {"a": 1}

        exported = vm.export_variables()

        assert exported["a"] == 1

    def test_export_with_source(self):
        """测试包含来源的导出。"""
        vm = VariableManager()
        vm.global_vars = {"a": 1}

        exported = vm.export_variables(include_source=True)

        assert exported["a"]["value"] == 1
        assert exported["a"]["source"] == "global"


class TestExtractFromString:
    """测试字符串提取功能。"""

    @pytest.fixture
    def vm(self):
        """创建测试用的 VariableManager 实例。"""
        return VariableManager()

    def test_extract_with_regex(self, vm):
        """测试正则表达式提取。"""
        text = "Token: abc123xyz"
        result = vm.extract_from_string(r"Token: (\w+)", text, 1)

        assert result == "abc123xyz"

    def test_extract_no_match(self, vm):
        """测试无匹配时返回 None。"""
        result = vm.extract_from_string(r"not_found", "some text")

        assert result is None

    def test_extract_invalid_regex(self, vm):
        """测试无效正则表达式抛出异常。"""
        with pytest.raises(ValueError, match="无效的正则表达式模式"):
            vm.extract_from_string(r"[invalid", "text")
