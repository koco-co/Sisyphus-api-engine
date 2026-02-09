"""Sisyphus API Engine 变量管理器。

本模块负责变量管理，包括：
- 全局变量管理
- 环境特定变量（Profile）
- 步骤提取变量
- 基于 Jinja2 模板的变量渲染
- 内置模板函数（random、uuid、timestamp 等）
- 变量跟踪和变更历史
- 环境变量集成

遵循 Google Python 代码风格规范。
"""

from datetime import datetime
import os
import re
from typing import Any

from jinja2 import BaseLoader, Environment, TemplateError

from apirun.core.template_functions import get_template_functions


class VariableManager:
    """管理测试过程中不同作用域的变量。

    变量按优先级分层管理（从低到高）：
    1. 全局变量（global_vars）
    2. 环境变量（从操作系统环境读取）
    3. Profile 变量（profile_vars）
    4. Profile 覆盖变量（CLI 或运行时覆盖）
    5. 步骤提取变量（extracted_vars）

    属性：
        global_vars: 全局变量字典
        profile_vars: 当前激活 profile 的变量
        extracted_vars: 从测试步骤中提取的变量
        profile_overrides: 运行时 profile 覆盖变量
        env_vars_prefix: 环境变量前缀
        enable_tracking: 是否启用变量变更跟踪
        change_history: 变量变更历史记录
        config_context: 配置上下文，用于支持嵌套引用
        _jinja_env: Jinja2 渲染环境
        _cache: 合并变量缓存
        _cache_dirty: 缓存是否需要刷新
        _cache_version: 缓存版本号
    """

    def __init__(
        self,
        global_vars: dict[str, Any] | None = None,
        env_vars_prefix: str | None = None,
        enable_tracking: bool = False,
    ):
        """初始化变量管理器。

        参数：
            global_vars: 初始全局变量
            env_vars_prefix: 环境变量前缀（如 "API_"）
            enable_tracking: 是否启用变量变更跟踪
        """
        self.global_vars = global_vars or {}
        self.profile_vars: dict[str, Any] = {}
        self.extracted_vars: dict[str, Any] = {}
        self.profile_overrides: dict[str, Any] = {}
        self.env_vars_prefix = env_vars_prefix
        self.enable_tracking = enable_tracking

        # 配置上下文，用于支持嵌套引用如 ${config.profiles.dev.variables.xxx}
        self.config_context: dict[str, Any] = {}

        # 变量变更跟踪
        self.change_history: list[dict[str, Any]] = []

        # 性能优化：合并变量缓存
        self._cache: dict[str, Any] = {}
        self._cache_dirty: bool = True
        self._cache_version: int = 0

        # 初始化 Jinja2 环境，使用自定义分隔符 ${} 并注册内置函数
        self._jinja_env = Environment(
            loader=BaseLoader(), variable_start_string='${', variable_end_string='}'
        )

        # 注册内置模板函数（传递 self 以支持 db_query）
        template_functions = get_template_functions(self)
        self._jinja_env.globals.update(template_functions)

    def _invalidate_cache(self) -> None:
        """使变量缓存失效。"""
        self._cache_dirty = True
        self._cache_version += 1

    def set_config_context(self, config: dict[str, Any]) -> None:
        """设置配置上下文以支持嵌套引用。

        允许变量引用配置值，例如：
        ${config.profiles.dev.variables.api_key}

        参数：
            config: 包含 profiles、variables 等的配置字典
        """
        self.config_context = config
        self._invalidate_cache()

    def set_profile(self, profile_vars: dict[str, Any]) -> None:
        """设置当前激活 profile 的变量。

        参数：
            profile_vars: Profile 特定变量字典
        """
        self.profile_vars = profile_vars
        self._invalidate_cache()

    def set_variable(self, name: str, value: Any) -> None:
        """设置一个变量。

        变量将被添加到提取变量中，优先级最高。

        参数：
            name: 变量名
            value: 变量值
        """
        self.extracted_vars[name] = value
        self._invalidate_cache()

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值。

        按优先级顺序搜索：extracted_vars > profile_vars > global_vars

        参数：
            name: 变量名
            default: 未找到时的默认值

        返回：
            变量值，如果未找到则返回默认值
        """
        if name in self.extracted_vars:
            return self.extracted_vars[name]
        if name in self.profile_vars:
            return self.profile_vars[name]
        if name in self.global_vars:
            return self.global_vars[name]
        return default

    def get_all_variables(self) -> dict[str, Any]:
        """获取所有合并后的变量。

        合并顺序（优先级从低到高）：
        config_context < global_vars < profile_vars < profile_overrides < extracted_vars

        性能优化：使用缓存避免重复的深拷贝操作。

        返回：
            合并后的变量字典
        """
        # 如果缓存可用且未失效，直接返回缓存
        if not self._cache_dirty and self._cache:
            return self._cache

        # 构建合并字典，使用浅拷贝（比深拷贝更快）
        merged = {}

        # 首先添加配置上下文，用于支持嵌套引用
        if self.config_context:
            merged['config'] = self.config_context

        # 按优先级顺序合并（从低到高）
        merged.update(self.global_vars)
        merged.update(self.profile_vars)
        merged.update(self.profile_overrides)
        merged.update(self.extracted_vars)

        # 缓存结果
        self._cache = merged
        self._cache_dirty = False

        return merged

    def render_string(self, template_str: str, max_iterations: int = 10) -> str:
        """使用当前变量渲染模板字符串。

        支持 Jinja2 语法：${variable_name}
        支持嵌套变量引用（递归渲染）

        参数：
            template_str: 待渲染的模板字符串
            max_iterations: 最大递归渲染次数（默认：10）

        返回：
            渲染后的字符串

        异常：
            TemplateError: 模板渲染失败时抛出
        """
        if not isinstance(template_str, str):
            return template_str

        # 快速检查是否包含模板语法
        if '${' not in template_str and '{%' not in template_str:
            return template_str

        try:
            # 迭代渲染直到没有更多模板引用
            # 支持嵌套变量引用如 "test_${var1}_${var2}"
            result = template_str
            for _ in range(max_iterations):
                template = self._jinja_env.from_string(result)
                rendered = template.render(**self.get_all_variables())

                # 检查渲染是否改变了值
                if rendered == result:
                    # 没有更多变化，完成渲染
                    break
                result = rendered

                # 检查是否还有模板语法
                if '${' not in result and '{%' not in result:
                    break

            return result
        except TemplateError as e:
            raise TemplateError(f"模板渲染失败 '{template_str}': {e}")

    def render_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """递归渲染字典中的所有字符串值。

        参数：
            data: 待渲染的字典

        返回：
            渲染后的字典
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
        """递归渲染列表中的所有字符串值。

        参数：
            data: 待渲染的列表

        返回：
            渲染后的列表
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
    ) -> str | None:
        """使用正则表达式从字符串中提取值。

        参数：
            pattern: 正则表达式模式
            text: 待搜索的文本
            index: 捕获组索引（默认：0 表示完整匹配）

        返回：
            提取的值，如果未找到返回 None
        """
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(index)
        except re.error as e:
            raise ValueError(f"无效的正则表达式模式 '{pattern}': {e}")
        return None

    def clear_extracted(self) -> None:
        """清除所有提取变量。"""
        self.extracted_vars.clear()

    def snapshot(self) -> dict[str, Any]:
        """创建当前变量状态的快照。

        性能优化：使用优化的拷贝策略——大多数情况下使用浅拷贝。

        返回：
            所有变量的拷贝
        """
        return {
            'global': self.global_vars.copy(),
            'profile': self.profile_vars.copy(),
            'extracted': self.extracted_vars.copy(),
            'cache_version': self._cache_version,
        }

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        """从快照恢复变量状态。

        参数：
            snapshot: 来自 snapshot() 方法的快照
        """
        if 'global' in snapshot:
            self.global_vars = snapshot['global'].copy()
        if 'profile' in snapshot:
            self.profile_vars = snapshot['profile'].copy()
        if 'extracted' in snapshot:
            self.extracted_vars = snapshot['extracted'].copy()

        # 变量已更改，使缓存失效
        self._invalidate_cache()

    def load_environment_variables(
        self, prefix: str | None = None, override: bool = False
    ) -> dict[str, Any]:
        """从操作系统环境加载变量。

        参数：
            prefix: 环境变量前缀（如 "API_"）
                   如果为 None，使用 self.env_vars_prefix
            override: 是否覆盖已存在的变量

        返回：
            已加载的环境变量字典
        """
        env_prefix = prefix or self.env_vars_prefix
        loaded_vars = {}

        for key, value in os.environ.items():
            if env_prefix:
                if key.startswith(env_prefix):
                    var_name = key[len(env_prefix) :].lower()
                    loaded_vars[var_name] = value
            else:
                # 如果没有前缀，加载所有环境变量
                loaded_vars[key.lower()] = value

        # 根据 override 标志应用到 profile_vars 或 profile_overrides
        if override:
            self.profile_overrides.update(loaded_vars)
        else:
            self.profile_vars.update(loaded_vars)

        return loaded_vars

    def set_profile_override(
        self, key: str, value: Any, context: dict[str, Any] | None = None
    ) -> None:
        """设置 profile 覆盖变量。

        覆盖变量比普通 profile 变量优先级更高。

        参数：
            key: 变量名
            value: 变量值
            context: 可选的上下文信息（用于跟踪）
        """
        old_value = self.get_variable(key)
        self.profile_overrides[key] = value

        if self.enable_tracking:
            self._track_change('override', key, old_value, value, context)

    def set_profile_overrides(self, overrides: dict[str, Any]) -> None:
        """设置多个 profile 覆盖变量。

        参数：
            overrides: 覆盖变量字典
        """
        for key, value in overrides.items():
            self.set_profile_override(key, value)

    def clear_profile_overrides(self) -> None:
        """清除所有 profile 覆盖变量。"""
        self.profile_overrides.clear()

    def get_variable_with_source(self, name: str, default: Any = None) -> tuple:
        """获取变量值及其来源。

        参数：
            name: 变量名
            default: 未找到时的默认值

        返回：
            元组 (value, source)，其中 source 为以下之一：
            - "extracted": 步骤提取变量
            - "override": profile 覆盖变量
            - "profile": profile 变量
            - "env": 环境变量
            - "global": 全局变量
            - "default": 默认值
        """
        # 按优先级顺序检查
        if name in self.extracted_vars:
            return self.extracted_vars[name], 'extracted'
        if name in self.profile_overrides:
            return self.profile_overrides[name], 'override'
        if name in self.profile_vars:
            return self.profile_vars[name], 'profile'

        # 检查环境变量（在 profile 之后）
        env_key = (
            f'{self.env_vars_prefix}{name.upper()}'
            if self.env_vars_prefix
            else name.upper()
        )
        if env_key in os.environ:
            return os.environ[env_key], 'env'

        if name in self.global_vars:
            return self.global_vars[name], 'global'

        return default, 'default'

    def compute_delta(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> dict[str, Any]:
        """计算两个状态之间的变量变化。

        参数：
            before: 执行前的变量状态
            after: 执行后的变量状态

        返回：
            变化字典，格式如下：
            {
                "added": {"var_name": value},
                "modified": {"var_name": {"old": old_value, "new": new_value}},
                "deleted": {"var_name": old_value}
            }
        """
        delta = {'added': {}, 'modified': {}, 'deleted': {}}

        # 查找新增和修改的变量
        for key, value in after.items():
            if key not in before:
                delta['added'][key] = value
            elif before[key] != value:
                delta['modified'][key] = {'old': before[key], 'new': value}

        # 查找删除的变量
        for key in before:
            if key not in after:
                delta['deleted'][key] = before[key]

        return delta

    def _track_change(
        self,
        source: str,
        var_name: str,
        old_value: Any,
        new_value: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """跟踪变量变更。

        参数：
            source: 变更来源（extract/override/profile/global）
            var_name: 变量名
            old_value: 变更前的值
            new_value: 变更后的值
            context: 附加上下文（step_name 等）
        """
        if not self.enable_tracking:
            return

        change_record = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'variable': var_name,
            'old_value': old_value,
            'new_value': new_value,
            'context': context or {},
        }

        self.change_history.append(change_record)

    def get_change_history(
        self, variable_name: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """获取变量变更历史。

        参数：
            variable_name: 按变量名过滤（None 表示全部）
            limit: 返回的最大记录数（None 表示全部）

        返回：
            变更记录列表
        """
        history = self.change_history

        if variable_name:
            history = [
                record for record in history if record['variable'] == variable_name
            ]

        if limit:
            history = history[-limit:]

        return history

    def clear_change_history(self) -> None:
        """清除所有变更历史。"""
        self.change_history.clear()

    def get_debug_info(self) -> dict[str, Any]:
        """获取详细的调试信息。

        返回：
            包含变量来源和元数据的字典
        """
        debug_info = {
            'global_vars': self.global_vars.copy(),
            'profile_vars': self.profile_vars.copy(),
            'profile_overrides': self.profile_overrides.copy(),
            'extracted_vars': self.extracted_vars.copy(),
            'env_vars_prefix': self.env_vars_prefix,
            'tracking_enabled': self.enable_tracking,
            'change_history_count': len(self.change_history),
        }

        # 如果设置了前缀，添加匹配的环境变量
        if self.env_vars_prefix:
            debug_info['environment_variables'] = {}
            for key, value in os.environ.items():
                if key.startswith(self.env_vars_prefix):
                    debug_info['environment_variables'][key] = value

        return debug_info

    def export_variables(
        self, include_source: bool = False, include_env: bool = False
    ) -> dict[str, Any]:
        """以结构化格式导出所有变量。

        参数：
            include_source: 是否包含变量来源信息
            include_env: 是否包含环境变量

        返回：
            结构化的变量导出
        """
        if include_source:
            exported = {}
            all_vars = self.get_all_variables()
            for var_name in all_vars:
                value, source = self.get_variable_with_source(var_name)
                exported[var_name] = {'value': value, 'source': source}
            return exported
        else:
            return self.get_all_variables()


class VariableScope:
    """变量作用域上下文管理器。

    用于变量作用域隔离，退出上下文时自动恢复变量状态。

    使用示例：
        with VariableScope(manager) as scope:
            # 修改变量
            manager.set_variable("x", 1)
        # 退出后变量自动恢复
    """

    def __init__(self, manager: VariableManager):
        """初始化变量作用域。

        参数：
            manager: VariableManager 实例
        """
        self.manager = manager
        self._snapshot: dict[str, Any] | None = None

    def __enter__(self) -> 'VariableScope':
        """进入上下文并保存当前状态。"""
        self._snapshot = self.manager.snapshot()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文并恢复之前的状态。"""
        if self._snapshot:
            self.manager.restore_snapshot(self._snapshot)
        return False
