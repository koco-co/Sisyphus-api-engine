"""Sisyphus API Engine V2 版本 YAML 解析器。

本模块用于解析符合 v2.0 协议规范的 YAML 测试用例文件。
遵循 Google Python 代码风格规范。

主要功能：
- 支持 !include 标签引入外部配置
- 支持多环境配置（profiles）和版本化配置
- 支持变量嵌套引用
- 支持多种步骤类型解析
- 支持验证规则和提取器解析
"""

import os
import pathlib
from typing import Any

from yaml import YAMLError, safe_load
from yaml_include import Constructor

from apirun.core.global_config_manager import GlobalConfigManager
from apirun.core.models import (
    Extractor,
    GlobalConfig,
    ProfileConfig,
    TestCase,
    TestStep,
    ValidationRule,
)


class YamlParseError(Exception):
    """YAML 解析错误异常。

    当 YAML 文件格式错误或解析失败时抛出此异常。
    """

    pass


class V2YamlParser:
    """V2 版本 YAML 测试用例解析器。

    解析 v2.0 格式的 YAML 测试用例文件，支持以下功能：
    - config 配置节（包含 profiles 环境配置）
    - 变量提取和模板渲染
    - 多种步骤类型（request/database/wait/loop/script/poll/concurrent）
    - 验证规则（包含逻辑运算符 and/or/not）
    - 步骤控制（skip_if/only_if/depends_on）
    - Setup/Teardown 钩子

    使用示例：
        parser = V2YamlParser()
        test_case = parser.parse("test_case.yaml")

    属性：
        _current_file: 当前正在解析的文件路径
    """

    def __init__(self):
        """初始化 V2 YAML 解析器。"""
        pass

    def _load_yaml_with_include(self, yaml_file: str) -> dict[str, Any]:
        """加载支持 !include 标签的 YAML 文件。

        使用 yaml_include 库实现 !include 标签支持，
        允许在 YAML 中引入其他 YAML 文件。

        参数：
            yaml_file: YAML 文件路径

        返回：
            解析后的 YAML 数据字典

        示例：
            # test.yaml
            config: !include ../config/global_config.yaml
        """
        import yaml

        # 获取基础目录，用于解析相对路径
        base_dir = os.path.dirname(os.path.abspath(yaml_file))

        # 创建 include 构造器，指定基础目录
        constructor = Constructor(base_dir=base_dir)

        # 将 !include 构造器注册到 yaml.FullLoader
        yaml.add_constructor('!include', constructor, yaml.FullLoader)

        # 使用 FullLoader 加载 YAML 文件
        with pathlib.Path(yaml_file).open(encoding='utf-8') as f:
            return yaml.load(f, yaml.FullLoader)

    def parse(self, yaml_file: str) -> TestCase:
        """解析 YAML 文件为 TestCase 对象。

        这是解析器的主入口方法，完成以下工作：
        1. 检查文件是否存在
        2. 加载 YAML 内容（支持 !include）
        3. 合并全局配置（.sisyphus/config.yaml）
        4. 调用 _parse_test_case 完成最终解析

        参数：
            yaml_file: YAML 文件路径

        返回：
            TestCase 对象

        异常：
            YamlParseError: YAML 解析失败时抛出
            FileNotFoundError: 文件不存在时抛出
        """
        if not pathlib.Path(yaml_file).exists():
            raise FileNotFoundError(f'YAML 文件不存在: {yaml_file}')

        try:
            data = self._load_yaml_with_include(yaml_file)
        except YAMLError as e:
            raise YamlParseError(f'YAML 文件解析失败: {e}')

        if not data:
            raise YamlParseError(f'YAML 文件内容为空: {yaml_file}')

        self._current_file = yaml_file

        # 加载并合并全局配置
        # 配置优先级：测试用例 config > 全局配置 > 默认值
        global_config_manager = GlobalConfigManager(yaml_file)
        if global_config_manager.global_config:
            test_config = data.get('config', {})
            merged_config = global_config_manager.get_merged_config(test_config)
            data['config'] = merged_config

        return self._parse_test_case(data)

    def parse_string(self, yaml_content: str) -> TestCase:
        """解析 YAML 字符串内容为 TestCase 对象。

        用于直接解析 YAML 字符串，不需要文件。
        注意：此方法不支持 !include 标签，因为没有基础目录。

        参数：
            yaml_content: YAML 格式的字符串内容

        返回：
            TestCase 对象

        异常：
            YamlParseError: YAML 解析失败时抛出
        """
        try:
            data = safe_load(yaml_content)
        except YAMLError as e:
            raise YamlParseError(f'YAML 内容解析失败: {e}')

        if not data:
            raise YamlParseError('YAML 内容为空')

        return self._parse_test_case(data)

    def _parse_test_case(self, data: dict[str, Any]) -> TestCase:
        """从 YAML 数据解析测试用例。

        解析顶层结构，包括：
        - name: 用例名称（必填）
        - description: 用例描述
        - config: 全局配置
        - steps: 测试步骤列表（必填）
        - setup/teardown: 测试级钩子
        - tags: 标签列表
        - enabled: 是否启用

        参数：
            data: 已解析的 YAML 数据字典

        返回：
            TestCase 对象
        """
        name = data.get('name', '未命名测试用例')
        description = data.get('description', '')

        # 解析 config 配置节
        config = self._parse_config(data.get('config', {}))

        # 解析测试级 setup/teardown
        setup = data.get('setup')
        teardown = data.get('teardown')

        # 解析标签
        tags = data.get('tags', [])

        # 解析启用标志
        enabled = data.get('enabled', True)

        # 解析测试步骤
        steps_data = data.get('steps', [])
        steps = []
        for step_data in steps_data:
            step = self._parse_step(step_data)
            if step:
                steps.append(step)

        return TestCase(
            name=name,
            description=description,
            config=config,
            steps=steps,
            setup=setup,
            teardown=teardown,
            tags=tags,
            enabled=enabled,
        )

    def _parse_config(self, config_data: dict[str, Any]) -> GlobalConfig | None:
        """解析全局配置节。

        处理 config 部分的所有配置项，包括：
        - profiles: 多环境配置（支持版本化嵌套）
        - active_profile: 当前激活的环境
        - variables: 全局变量（支持模板表达式）
        - timeout: 默认超时时间
        - data_source: 数据驱动配置
        - websocket: WebSocket 配置
        - output: 输出配置

        参数：
            config_data: config 配置节数据

        返回：
            GlobalConfig 对象，如果配置为空则返回 None
        """
        if not config_data:
            return None

        name = config_data.get('name', 'Test Suite')
        description = config_data.get('description', '')

        # 解析 profiles 环境配置
        profiles = {}
        profiles_data = config_data.get('profiles', {})

        # 展平版本化 profiles（如 "v1.dev"、"v2.prod"）
        flattened_profiles = self._flatten_profiles(profiles_data)

        for profile_name, profile_config in flattened_profiles.items():
            profiles[profile_name] = ProfileConfig(
                base_url=profile_config.get('base_url', ''),
                variables=profile_config.get('variables', {}),
                timeout=profile_config.get('timeout', 30),
                verify_ssl=profile_config.get('verify_ssl', True),
                overrides=profile_config.get('overrides', {}),
                priority=profile_config.get('priority', 0),
            )

        active_profile = config_data.get('active_profile')

        # 解析全局变量并渲染模板表达式
        # 支持嵌套引用如 ${config.profiles.dev.variables.xxx}
        variables = config_data.get('variables', {})

        if variables:
            from apirun.core.variable_manager import VariableManager

            vm = VariableManager()

            # 构建配置上下文，用于支持 config 嵌套引用
            # 同时包含展平的 profiles 和嵌套结构
            nested_profiles = self._build_nested_profiles(profiles, flattened_profiles)

            config_context = {
                'profiles': nested_profiles,
                'active_profile': active_profile,
            }

            # 添加展平的 profiles 以保持向后兼容
            # 允许同时使用 profiles.v1.dev 和 profiles.v1.dev 访问方式
            for profile_name, profile_config in profiles.items():
                # 仅添加不与嵌套结构冲突的展平键
                if (
                    '.' not in profile_name
                    or profile_name.split('.')[0] not in nested_profiles
                ):
                    config_context['profiles'][profile_name] = {
                        'base_url': profile_config.base_url,
                        'variables': profile_config.variables,
                        'timeout': profile_config.timeout,
                        'verify_ssl': profile_config.verify_ssl,
                        'overrides': profile_config.overrides,
                        'priority': profile_config.priority,
                    }

            # 设置配置上下文到变量管理器
            vm.set_config_context(config_context)

            # 首先设置原始变量（未渲染的）到变量管理器，支持嵌套引用
            vm.global_vars = variables.copy()

            # 渲染变量中的模板表达式
            rendered_variables = {}
            for key, value in variables.items():
                if isinstance(value, str):
                    rendered_variables[key] = vm.render_string(value)
                else:
                    # 对于非字符串值，尝试将其作为 JSON 字符串渲染
                    import json

                    try:
                        json_str = json.dumps(value)
                        rendered_str = vm.render_string(json_str)
                        rendered_variables[key] = json.loads(rendered_str)
                    except:
                        rendered_variables[key] = value

            # 更新变量管理器中的变量为渲染后的值
            vm.global_vars = rendered_variables
            variables = rendered_variables

        # 解析其他配置选项
        timeout = config_data.get('timeout', 30)
        retry_times = config_data.get('retry_times', 0)
        concurrent = config_data.get('concurrent', False)
        concurrent_threads = config_data.get('concurrent_threads', 3)

        # 解析数据驱动配置
        data_source = config_data.get('data_source')
        data_iterations = config_data.get('data_iterations', False)
        variable_prefix = config_data.get('variable_prefix', '')

        # 解析 WebSocket 配置
        websocket = config_data.get('websocket')

        # 解析输出配置
        output = config_data.get('output')

        # 解析调试配置
        debug = config_data.get('debug')

        # 解析环境变量配置
        env_vars = config_data.get('env_vars')

        # 解析详细输出标志
        verbose = config_data.get('verbose', False)

        return GlobalConfig(
            name=name,
            description=description,
            profiles=profiles,
            active_profile=active_profile,
            variables=variables,
            timeout=timeout,
            retry_times=retry_times,
            concurrent=concurrent,
            concurrent_threads=concurrent_threads,
            data_source=data_source,
            data_iterations=data_iterations,
            variable_prefix=variable_prefix,
            websocket=websocket,
            output=output,
            debug=debug,
            env_vars=env_vars,
            verbose=verbose,
        )

    def _parse_step(self, step_data: dict[str, Any]) -> TestStep | None:
        """解析单个测试步骤。

        支持两种步骤定义格式：
        1. 简写格式（步骤名作为键）：
           - 步骤名称:
               type: request
               url: /api/test

        2. 标准格式：
           - name: 步骤名称
             type: request
             url: /api/test

        参数：
            step_data: 步骤数据字典

        返回：
            TestStep 对象，解析失败返回 None
        """
        # 提取步骤名称（支持简写格式和标准格式）
        if len(step_data) == 1 and isinstance(list(step_data.values())[0], dict):
            # 简写格式：步骤名作为键
            name = list(step_data.keys())[0]
            step_details = step_data[name]
        else:
            # 标准格式：使用 name 字段
            name = step_data.get('name', '未命名步骤')
            step_details = step_data

        # 获取步骤类型，默认为 request
        step_type = step_details.get('type', 'request')

        # 解析 HTTP 请求相关字段
        method = step_details.get('method')
        url = step_details.get('url')
        params = step_details.get('params')
        headers = step_details.get('headers')
        body = step_details.get('body')

        # 解析数据库操作相关字段
        database = step_details.get('database')
        operation = step_details.get('operation')
        sql = step_details.get('sql')

        # 解析等待步骤相关字段
        seconds = step_details.get('seconds')
        condition = step_details.get('condition')
        interval = step_details.get('interval')
        max_wait = step_details.get('max_wait')
        wait_condition = step_details.get('wait_condition')

        # 解析循环步骤相关字段
        loop_type = step_details.get('loop_type')
        loop_count = step_details.get('loop_count')
        loop_condition = step_details.get('loop_condition')
        loop_variable = step_details.get('loop_variable')
        loop_steps = step_details.get('loop_steps')

        # 解析并发步骤相关字段
        max_concurrency = step_details.get('max_concurrency')
        concurrent_steps = step_details.get('concurrent_steps')

        # 解析脚本执行相关字段
        script = step_details.get('script')
        script_file = step_details.get('script_file')
        script_type = step_details.get('script_type', 'python')
        allow_imports = step_details.get('allow_imports', True)
        args = step_details.get('args')
        capture_output = step_details.get('capture_output')

        # 解析轮询步骤相关字段
        poll_config = step_details.get('poll_config')
        on_timeout = step_details.get('on_timeout')

        # 解析验证规则
        validations = []
        validations_data = step_details.get('validations', [])
        for val_data in validations_data:
            validation = self._parse_validation(val_data)
            if validation:
                validations.append(validation)

        # 解析提取器
        extractors = []
        extractors_data = step_details.get('extractors', [])
        for ext_data in extractors_data:
            extractor = self._parse_extractor(ext_data)
            if extractor:
                extractors.append(extractor)

        # 解析步骤控制
        skip_if = step_details.get('skip_if')
        only_if = step_details.get('only_if')
        depends_on = step_details.get('depends_on', [])

        # 解析超时和重试配置
        timeout = step_details.get('timeout')
        retry_times = step_details.get('retry_times')
        retry_policy = step_details.get('retry_policy')

        # 解析步骤级 setup/teardown
        setup = step_details.get('setup')
        teardown = step_details.get('teardown')

        return TestStep(
            name=name,
            type=step_type,
            method=method,
            url=url,
            params=params,
            headers=headers,
            body=body,
            validations=validations,
            extractors=extractors,
            skip_if=skip_if,
            only_if=only_if,
            depends_on=depends_on,
            timeout=timeout,
            retry_times=retry_times,
            setup=setup,
            teardown=teardown,
            database=database,
            operation=operation,
            sql=sql,
            seconds=seconds,
            condition=condition,
            interval=interval,
            max_wait=max_wait,
            wait_condition=wait_condition,
            loop_type=loop_type,
            loop_count=loop_count,
            loop_condition=loop_condition,
            loop_variable=loop_variable,
            loop_steps=loop_steps,
            retry_policy=retry_policy,
            max_concurrency=max_concurrency,
            concurrent_steps=concurrent_steps,
            script=script,
            script_file=script_file,
            script_type=script_type,
            allow_imports=allow_imports,
            args=args,
            capture_output=capture_output,
            poll_config=poll_config,
            on_timeout=on_timeout,
        )

    def _parse_validation(self, val_data: dict[str, Any]) -> ValidationRule | None:
        """解析验证规则。

        支持的验证器类型：
        - 基础验证器：eq/ne/gt/lt/ge/le/contains/type/regex 等
        - 逻辑运算符：and/or/not（支持嵌套子验证）

        参数：
            val_data: 验证规则数据字典

        返回：
            ValidationRule 对象，解析失败返回 None
        """
        if not isinstance(val_data, dict):
            return None

        val_type = val_data.get('type', 'eq')
        path = val_data.get('path', '$')
        expect = val_data.get('expect')
        description = val_data.get('description', '')
        error_message = val_data.get('error_message', '')

        # 解析逻辑运算符（and/or/not）
        if val_type in ('and', 'or', 'not'):
            sub_validations_data = val_data.get('sub_validations', [])
            sub_validations = []

            for sub_val_data in sub_validations_data:
                sub_val = self._parse_validation(sub_val_data)
                if sub_val:
                    sub_validations.append(sub_val)

            return ValidationRule(
                type=val_type,
                path='',
                expect=None,
                description=description,
                logical_operator=val_type,
                sub_validations=sub_validations,
                error_message=error_message,
            )

        return ValidationRule(
            type=val_type,
            path=path,
            expect=expect,
            description=description,
            error_message=error_message,
        )

    def _parse_extractor(self, ext_data: dict[str, Any]) -> Extractor | None:
        """解析变量提取器。

        支持的提取器类型：
        - jsonpath：JSONPath 表达式提取
        - regex：正则表达式提取
        - header：响应头提取
        - cookie：Cookie 提取

        参数：
            ext_data: 提取器数据字典

        返回：
            Extractor 对象，解析失败返回 None
        """
        if not isinstance(ext_data, dict):
            return None

        name = ext_data.get('name')
        ext_type = ext_data.get('type', 'jsonpath')
        description = ext_data.get('description', '')
        default = ext_data.get('default')
        extract_all = ext_data.get('extract_all', False)
        condition = ext_data.get('condition')
        on_failure = ext_data.get('on_failure')

        # 支持不同提取器类型的字段别名
        # regex 提取器：支持 'pattern' 和 'group' 作为 'path' 和 'index' 的别名
        if ext_type == 'regex':
            path = ext_data.get('pattern') or ext_data.get('path', '')
            # 'group' 比 'index' 更语义化，但两者都支持
            index = ext_data.get('group') or ext_data.get('index', 0)
        else:
            path = ext_data.get('path', '')
            index = ext_data.get('index', 0)

        if not name:
            return None

        return Extractor(
            name=name,
            type=ext_type,
            path=path,
            index=index,
            extract_all=extract_all,
            default=default,
            description=description,
            condition=condition,
            on_failure=on_failure,
        )

    def _flatten_profiles(
        self, profiles_data: dict[str, Any], prefix: str = ''
    ) -> dict[str, dict[str, Any]]:
        """展平版本化 profiles 结构。

        将嵌套的 profiles 配置：
        {
          "v1": {"dev": {...}, "prod": {...}},
          "v2": {"dev": {...}, "prod": {...}}
        }

        转换为展平结构：
        {
          "v1.dev": {...},
          "v1.prod": {...},
          "v2.dev": {...},
          "v2.prod": {...}
        }

        参数：
            profiles_data: profiles 配置字典
            prefix: 嵌套键的前缀（递归时内部使用）

        返回：
            展平后的 profiles 字典
        """
        flattened = {}

        for key, value in profiles_data.items():
            full_key = f'{prefix}.{key}' if prefix else key

            # 检查 value 是否为 profile 配置（包含 profile 字段）
            if isinstance(value, dict):
                # 如果包含 profile 特定字段，视为叶子节点 profile
                if any(
                    field in value for field in ['base_url', 'timeout', 'variables']
                ):
                    flattened[full_key] = value
                # 否则，是嵌套的版本文件夹，递归处理
                else:
                    nested = self._flatten_profiles(value, full_key)
                    flattened.update(nested)
            else:
                flattened[full_key] = value

        return flattened

    def _build_nested_profiles(
        self,
        profiles: dict[str, ProfileConfig],
        flattened_profiles: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """构建嵌套 profiles 结构用于模板渲染。

        创建同时支持展平和嵌套访问的结构：
        - profiles.v1.dev -> 可访问
        - profiles.v1.prod -> 可访问
        - profiles.v2.dev -> 可访问

        参数：
            profiles: 展平的 ProfileConfig 对象字典（如 "v1.dev"、"v2.prod"）
            flattened_profiles: 原始展平的 profile 数据

        返回：
            嵌套的 profiles 字典
        """
        nested = {}
        original_data = flattened_profiles

        # 从展平的键构建嵌套结构
        for profile_key, profile_config in profiles.items():
            # 创建嵌套字典路径
            parts = profile_key.split('.')
            current = nested

            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]

            # 设置叶子节点 profile
            leaf_key = parts[-1]
            current[leaf_key] = {
                'base_url': profile_config.base_url,
                'variables': profile_config.variables,
                'timeout': profile_config.timeout,
                'verify_ssl': profile_config.verify_ssl,
                'overrides': profile_config.overrides,
                'priority': profile_config.priority,
            }

        return nested

    def validate_yaml(self, yaml_file: str) -> list[str]:
        """验证 YAML 文件语法（不执行解析）。

        快速检查 YAML 文件的基本结构是否正确，包括：
        - 文件是否存在
        - YAML 语法是否正确
        - 必填字段是否存在

        参数：
            yaml_file: YAML 文件路径

        返回：
            验证错误消息列表（空列表表示验证通过）
        """
        errors = []

        if not pathlib.Path(yaml_file).exists():
            errors.append(f'文件不存在: {yaml_file}')
            return errors

        try:
            # 使用 _load_yaml_with_include 以支持 !include 标签
            data = self._load_yaml_with_include(yaml_file)

            if not data:
                errors.append('YAML 文件内容为空')
                return errors

            # 检查必填字段
            if 'name' not in data:
                errors.append('缺少必填字段: name')

            if 'steps' not in data:
                errors.append('缺少必填字段: steps')
            elif not isinstance(data['steps'], list):
                errors.append("字段 'steps' 必须是列表")
            elif len(data['steps']) == 0:
                errors.append("字段 'steps' 不能为空")

        except YAMLError as e:
            errors.append(f'YAML 语法错误: {e}')
        except Exception as e:
            errors.append(f'验证错误: {e}')

        return errors


def parse_yaml_file(yaml_file: str) -> TestCase:
    """便捷函数：解析 YAML 文件。

    参数：
        yaml_file: YAML 文件路径

    返回：
        TestCase 对象
    """
    parser = V2YamlParser()
    return parser.parse(yaml_file)


def parse_yaml_string(yaml_content: str) -> TestCase:
    """便捷函数：解析 YAML 字符串。

    参数：
        yaml_content: YAML 格式的字符串内容

    返回：
        TestCase 对象
    """
    parser = V2YamlParser()
    return parser.parse_string(yaml_content)
