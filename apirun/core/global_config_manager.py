"""全局配置管理器：Sisyphus API Engine 的分层配置加载。

实现配置优先级：
1. 全局配置：.sisyphus/config.yaml
2. 测试用例配置：YAML 文件
3. 默认值作为兜底

遵循 Google Python Style Guide。
"""

from pathlib import Path
from typing import Any

import yaml

from apirun.core.models import GlobalConfig, ProfileConfig


class GlobalConfigManager:
    """全局配置管理器：加载和合并全局配置。

    配置优先级（从高到低）：
    1. 测试用例配置（来自 YAML 文件）
    2. 全局配置（来自 .sisyphus/config.yaml）
    3. 默认值

    属性：
        project_root: 项目根目录
        global_config_path: 全局配置文件路径
        global_config: 已加载的全局配置字典
    """

    # 全局配置文件名
    CONFIG_FILENAME = '.sisyphus'
    CONFIG_FILE = 'config.yaml'
    CONFIG_PATH = str(Path(CONFIG_FILENAME) / CONFIG_FILE)

    def __init__(self, test_file_path: str | None = None):
        """初始化全局配置管理器。

        参数：
            test_file_path: 测试用例 YAML 文件路径（用于定位项目根目录）
        """
        self.project_root = self._find_project_root(test_file_path)
        self.global_config_path = str(Path(self.project_root) / self.CONFIG_PATH)
        self.global_config: dict[str, Any] = {}
        self._load_global_config()

    def _find_project_root(self, test_file_path: str | None = None) -> str:
        """通过搜索配置文件查找项目根目录。

        搜索策略：
        1. 如果提供 test_file_path，从其目录开始
        2. 向上搜索 .sisyphus 目录
        3. 回退到当前目录

        参数：
            test_file_path: 测试用例文件路径

        返回：
            项目根目录路径
        """
        # 从测试文件目录或当前目录开始
        if test_file_path:
            start_dir = str(Path(test_file_path).parent.resolve())
        else:
            start_dir = str(Path.cwd().resolve())

        # 向上搜索 .sisyphus 目录
        current_dir = Path(start_dir)
        while current_dir != current_dir.parent:  # 不是根目录
            config_path = current_dir / self.CONFIG_PATH
            if config_path.exists():
                return str(current_dir)

            current_dir = current_dir.parent

        # 回退到当前目录
        return str(Path.cwd().resolve())

    def _load_global_config(self) -> None:
        """从 .sisyphus/config.yaml 加载全局配置。

        如果配置文件不存在，global_config 保持为空字典。
        """
        config_path = Path(self.global_config_path)
        if not config_path.exists():
            return

        try:
            with config_path.open(encoding='utf-8') as f:
                self.global_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(
                f'警告：从 {self.global_config_path} 加载全局配置失败: {e}'
            )
            self.global_config = {}

    def get_merged_config(
        self, test_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """合并测试用例配置和全局配置。

        优先级：test_config > global_config > 默认值

        参数：
            test_config: 测试用例 YAML 文件中的配置

        返回：
            合并后的配置字典
        """
        # 从全局配置开始
        merged = self.global_config.copy()

        # 应用测试用例配置覆盖
        if test_config:
            merged = self._deep_merge(merged, test_config)

        # 确保必填字段有默认值
        merged.setdefault('profiles', {})
        merged.setdefault('active_profile', 'dev')
        merged.setdefault('timeout', 30)
        merged.setdefault('retry_times', 2)

        # 处理版本化配置（例如 "v1.dev", "v2.prod"）
        if 'variables' in merged and 'active_profile' in merged:
            active_profile = merged['active_profile']
            profile_vars = self._get_profile_variables(merged, active_profile)
            if profile_vars:
                # 将全局变量合并到配置变量中
                # 配置变量优先级更高
                merged['profiles'][active_profile] = merged['profiles'].get(
                    active_profile, {}
                )
                merged['profiles'][active_profile]['variables'] = {
                    **merged.get('variables', {}),
                    **profile_vars,
                }

        return merged

    def _get_profile_variables(
        self, config: dict[str, Any], active_profile: str
    ) -> dict[str, Any]:
        """从活动配置中获取变量，支持版本化配置。

        参数：
            config: 合并后的配置字典
            active_profile: 活动配置名称（例如 "dev" 或 "v1.dev"）

        返回：
            配置中的变量字典
        """
        profiles = config.get('profiles', {})

        # 检查配置是否直接存在（非版本化）
        if active_profile in profiles:
            return profiles[active_profile].get('variables', {})

        # 检查配置是否版本化（例如 "v1.dev"）
        if '.' in active_profile:
            version, env = active_profile.split('.', 1)
            if version in profiles and isinstance(profiles[version], dict):
                version_profiles = profiles[version]
                if env in version_profiles:
                    return version_profiles[env].get('variables', {})

        return {}

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """深度合并两个字典。

        参数：
            base: 基础字典（低优先级）
            override: 覆盖字典（高优先级）

        返回：
            合并后的字典
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def create_global_config_model(
        self, merged_config: dict[str, Any]
    ) -> GlobalConfig | None:
        """从合并后的配置创建 GlobalConfig 模型。

        参数：
            merged_config: 合并后的配置字典

        返回：
            GlobalConfig 对象或 None（创建失败时）
        """
        try:
            # 提取配置
            profiles_data = merged_config.get('profiles', {})
            profiles = {}
            for name, profile_data in profiles_data.items():
                profiles[name] = ProfileConfig(
                    base_url=profile_data.get('base_url'),
                    variables=profile_data.get('variables'),
                    timeout=profile_data.get('timeout'),
                    verify_ssl=profile_data.get('verify_ssl', True),
                    overrides=profile_data.get('overrides'),
                    priority=profile_data.get('priority', 0),
                )

            # 创建 GlobalConfig
            config = GlobalConfig(
                name=merged_config.get('name', 'Global Config'),
                active_profile=merged_config.get('active_profile', 'dev'),
                profiles=profiles or None,
                variables=merged_config.get('variables'),
                timeout=merged_config.get('timeout', 30),
                retry_times=merged_config.get('retry_times', 2),
                retry_policy=merged_config.get('retry_policy'),
                debug=merged_config.get('debug'),
                env_vars=merged_config.get('env_vars'),
                data_source=merged_config.get('data_source'),
                websocket=merged_config.get('websocket'),
                output=merged_config.get('output'),
            )

            return config

        except Exception as e:
            print(f'警告：创建 GlobalConfig 模型失败: {e}')
            return None

    @staticmethod
    def is_global_config_available() -> bool:
        """检查全局配置文件是否存在。

        返回：
            如果 .sisyphus/config.yaml 存在则返回 True
        """
        return Path(GlobalConfigManager.CONFIG_PATH).exists()


# 向后兼容的便捷函数
def load_global_config(test_file_path: str | None = None) -> dict[str, Any]:
    """加载全局配置。

    参数：
        test_file_path: 测试用例文件路径

    返回：
        全局配置字典（未找到时为空）
    """
    manager = GlobalConfigManager(test_file_path)
    return manager.global_config
