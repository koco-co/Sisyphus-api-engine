# 更新日志

本文件记录 Sisyphus API Engine 的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 规范，
项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html) 规范。

## [2.0.3] - 2026-02-03

### 🐛 修复

#### Regex 验证器修复 ⭐ 重大修复
- **修复正则表达式匹配问题** (问题#9)
  - 修复 `'1'` 无法匹配模式 `'^1$'` 的 bug
  - **问题根源**: regex 验证器对非字符串类型（如整数）直接返回 False
  - **解决方案**:
    - 自动将所有类型转换为字符串进行匹配
    - 智能检测完整匹配模式（`^...$`）并使用 `re.fullmatch`
    - 部分匹配模式继续使用 `re.search`
  - **影响范围**: 所有涉及数字、布尔值的正则验证场景
  - **修复效果**: 测试通过率从 50% 提升到 100%

#### 验证器别名支持
- **新增验证器别名映射** (问题#8)
  - 新增 `gte` 别名映射到 `ge` (大于等于)
  - 新增 `lte` 别名映射到 `le` (小于等于)
  - 新增 `in` 别名映射到 `in_list` (多值验证)
  - 新增 `not_in` 别名映射到 `not_in_list` (非多值验证)
  - 提升验证器命名的直观性和易用性

#### 版本号统一
- **统一项目版本号**
  - 修复 `pyproject.toml`、`VERSION`、`apirun/__init__.py` 版本号不一致问题
  - 统一更新至 v2.0.3
  - 确保版本号与 CHANGELOG 保持一致

### ✅ 测试

#### Regex 验证器测试
- 创建 `testcases/scenariotest/__regex验证器测试.yaml`
  - Bug复现测试 - 数字 '1' 匹配 '^1$' - 通过 ✅
  - 完整匹配测试 - 邮箱/手机号/邮编格式 - 通过 ✅
  - 边界情况测试 - 空字符串/特殊字符 - 通过 ✅
  - 复杂模式测试 - 多种格式验证 - 通过 ✅
- **测试通过率**: 4/4 (100%)

#### 验证器测试
- 创建 `testcases/scenariotest/__验证器修复测试.yaml`
  - gte 大于等于验证器测试 - 通过 ✅
  - lte 小于等于验证器测试 - 通过 ✅
  - in 多值验证器测试 - 通过 ✅
  - regex 正则表达式验证器测试 - 通过 ✅
  - starts_with 前缀匹配验证器测试 - 通过 ✅
  - ends_with 后缀匹配验证器测试 - 通过 ✅
  - 综合验证器测试 - 通过 ✅
- **测试通过率**: 7/7 (100%)

### 📝 文档更新

- 更新 `问题跟踪文档/框架改进任务清单.md`
  - 添加验证器别名修复记录
  - 添加 Regex 验证器修复记录
  - 记录测试验证结果
  - 更新文档版本至 v2.1

### 🔧 内部改进

- **Regex 验证器增强**
  - 支持任意类型的正则表达式匹配
  - 智能区分完整匹配和部分匹配
  - 提升正则匹配准确性和可靠性

- **验证器别名映射机制**
  - 统一验证器命名规范
  - 改善用户使用体验
  - 提升验证器命名一致性

---

## [2.0.2] - 2026-02-02

### 🐛 修复

#### 日志系统bug修复
- **修复错误消息格式化问题** (问题#6)
  - 修复JSONPath提取器错误消息中的乱码字符
  - 错误消息现在正确显示 `$` 符号而不是 `'`
  - 提升错误消息可读性和调试体验

- **修复性能指标单位显示错误** (问题#7)
  - 修复性能指标日志将毫秒值直接显示为秒的问题
  - 现在正确转换：1729.428ms → 1.729s
  - 所有性能指标（total_time, dns_time, tcp_time, tls_time, server_time）均正确显示

#### 测试增强
- 新增5个单元测试验证日志bug修复：
  - `test_error_message_formatting_no_garbled_quotes` - 验证错误消息无乱码
  - `test_error_message_contains_helpful_suggestions` - 验证帮助建议
  - `test_performance_metrics_unit_conversion` - 验证性能指标单位转换
  - `test_performance_metrics_conversion_with_small_values` - 验证小数值转换
  - `test_performance_metrics_conversion_with_large_values` - 验证大数值转换

### 📝 质量提升

| 指标 | 改进 |
|------|------|
| 单元测试通过率 | 100% (897/897) |
| 新增单元测试 | +5 |
| Bug修复总数 | 7个 |

### 🔧 内部改进

- 优化错误消息格式化逻辑
- 增强性能指标日志可读性
- 提升用户调试体验

---

## [2.0.1] - 2026-02-02

### 🐛 修复

#### 测试修复
- **修复单元测试失败问题**
  - 修复验证失败错误消息格式测试断言
  - 修复统计计算测试中end_time类型错误
  - 修复final_variables收集逻辑，现在包含配置变量
  - 修复WebSocket通知异步调用测试（使用AsyncMock）
  - 修复统计计算测试步骤数量不匹配问题
  - 所有892个单元测试通过 ✅

#### YAML验证器增强
- **新增关键字支持**
  - `seconds`, `max_wait` - 等待步骤关键字
  - `capture_output` - 脚本步骤输出捕获
  - `default` - 提取器默认值（v2.0.1+）
  - `extract_all`, `condition`, `on_failure` - 提取器增强关键字
  - `error_message` - 验证器自定义错误消息（v2.0.1+）
  - `data_iterations`, `variable_prefix` - 数据驱动配置关键字
  - `file_path`, `data_key` 等 - 数据源配置关键字
- 所有41个YAML示例文件验证通过 ✅

### 📝 文档更新

- 创建 `examples/README.md` - YAML示例索引文档
- 更新 `问题追踪清单.md` - Bug修复详细记录
- 更新 `系统测试任务清单.md` - 完整测试任务规划

### 🔧 内部改进

- 优化 `final_variables` 收集逻辑，包含所有变量类型
- 增强YAML验证器schema定义
- 提升测试通过率从99.44%到100%

---

## [2.0.0] - 2026-02-02

### ✨ 新增

#### 变量嵌套引用增强
- **支持 config 嵌套引用**
  - 可在顶层 `config.variables` 中嵌套引用 `config.profiles.*` 的值
  - 支持引用 `config.active_profile` 动态获取当前环境
  - 支持多级嵌套组合（如 `${config.active_profile}_${config.profiles.dev.variables.env}`）
  - 完全向后兼容，不影响现有变量引用语法

- **示例**：
  ```yaml
  config:
    variables:
      # 引用特定 profile 的变量
      category_name: "test_${config.profiles.dev.variables.test_suffix}"
      # 引用 active_profile
      environment: "${config.active_profile}"
  ```

#### 异步轮询机制
- **新增 `poll` 步骤类型**
  - 支持等待异步操作完成（如项目创建、数据处理等）
  - 支持 JSONPath 和状态码两种条件检查方式
  - 提供 8 种比较运算符（eq/ne/gt/lt/ge/le/contains/exists）

- **多种轮询策略**
  - `fixed` - 固定间隔轮询
  - `exponential` - 指数退避（间隔翻倍：1s, 2s, 4s, 8s...）
  - `linear` - 线性增长（间隔递增：1s, 2s, 3s, 4s...）

- **超时处理**
  - 支持 `fail` 模式：超时后标记步骤失败
  - 支持 `continue` 模式：超时后继续执行后续步骤
  - 可配置超时错误消息

- **可配置参数**
  - `max_attempts` - 最大轮询次数（默认 30）
  - `interval` - 轮询间隔毫秒数（默认 2000）
  - `timeout` - 总超时时间毫秒数（默认 60000）
  - `backoff` - 退避策略（默认 fixed）

- **示例**：
  ```yaml
  - name: "等待项目就绪"
    type: poll
    url: "/api/project/status"
    poll_config:
      condition:
        type: jsonpath
        path: "$.data.status"
        operator: "eq"
        expect: "ACTIVE"
      max_attempts: 30
      interval: 2000
      timeout: 60000
      backoff: "exponential"
    on_timeout:
      behavior: "fail"
      message: "项目初始化超时"
  ```

### 🔧 变更
- **VariableManager 扩展**
  - 添加 `config_context` 属性用于支持 config 嵌套引用
  - 添加 `set_config_context()` 方法设置配置上下文
  - `get_all_variables()` 方法现在包含 config 上下文

- **TestStep 模型扩展**
  - 添加 `poll_config` 字段用于配置轮询参数
  - 添加 `on_timeout` 字段用于配置超时处理

- **V2YamlParser 更新**
  - 解析器现在支持解析 `poll_config` 和 `on_timeout` 字段
  - 在渲染变量前构建 config_context 以支持嵌套引用

### 🐛 修复
- **JSONPath 提取器初始化**
  - 修复 PollStepExecutor 中 JSONPathExtractor 的初始化问题
  - 现在正确传递 path 和 response 参数

- **浮点数精度**
  - 修复线性退避策略中的浮点数比较精度问题
  - 使用近似比较避免浮点数误差

### 📝 文档
- **新增功能文档**（问题跟踪文档/）
  - 任务清单.md - 12个功能的完整进度跟踪
  - 功能实现-变量嵌套引用.md - 变量嵌套引用详细说明
  - 功能实现-异步轮询机制.md - 轮询机制完整文档
  - 功能实现总览.md - 所有功能实现状态总览
  - 完整功能实现与自测报告.md - v2.0.0 测试报告

#### 增强型 YAML 验证器
- **新增验证器模块** (`apirun/validator/`)
  - `YamlValidator` - 核心验证器类，支持完整的 YAML 语法检查
  - `ValidationResult` - 验证结果数据模型
  - `TerminalFormatter` - 美观的终端输出（彩色 + Emoji）
  - `validate_yaml_files()` - 批量验证入口函数

- **验证功能**
  - ✅ YAML 语法完整性检查
  - ✅ 未定义关键字自动检测
  - ✅ 支持检查范围：
    - 测试用例顶层字段（name, description, config, steps, tags, enabled）
    - config 配置节字段
    - profile 环境配置
    - 7种步骤类型关键字（request, database, wait, loop, script, poll, concurrent）
    - 23种验证类型（status_code, eq, ne, gt, lt, contains, regex 等）
    - 提取器配置
    - 重试策略、数据源、输出配置等

- **特殊语法支持**
  - ✅ `!include` 标签支持（使用 yaml_include.Constructor）
  - ✅ 步骤简写语法（步骤名称作为键）
  - ✅ Profile 自定义变量（允许任意字段）
  - ✅ 实验性功能字段（mock, performance, websocket 扩展）

- **用户体验**
  - 🎨 彩色终端输出（ANSI 颜色码）
  - 😊 Emoji 图标（✓ ✗ ⚠ ℹ）
  - 🇨🇳 中文错误提示和位置信息
  - 📊 验证统计汇总

- **使用示例**
  ```bash
  # 验证单个文件
  sisyphus-validate test_case.yaml

  # 验证整个目录
  sisyphus-validate examples/

  # 静默模式（仅显示汇总）
  sisyphus-validate examples/ -q

  # 查看中文帮助
  sisyphus-validate -H
  ```

- **测试覆盖**
  - 新增 `tests/validator/test_yaml_validator.py`
  - 22个单元测试覆盖所有验证功能
  - 所有 27 个示例文件验证通过（100%）

- **协议规范更新**
  - API-Engine输入协议规范.md 更新至 v2.0.0
  - 新增 3.6 Poll 步骤完整文档
  - 新增 4.2 变量嵌套引用详细说明

- **README 更新**
  - 版本号更新至 v2.0.0
  - 新增 v2.0.0 功能亮点章节

### ✅ 测试
- **新增单元测试**
  - `tests/parser/test_nested_variable_reference.py` - 9个集成测试
  - `tests/executor/test_poll_executor.py` - 20个轮询执行器测试
  - `tests/core/test_variable_manager.py` - 新增TestConfigContext类（7个测试）

- **新增YAML示例**
  - `examples/变量嵌套引用示例.yaml` - 5个验证步骤
  - `examples/异步轮询示例.yaml` - 6个轮询场景
  - `examples/综合功能测试.yaml` - 10个功能验证步骤

- **测试覆盖**
  - 总计 363 个测试（36个新增 + 282个现有）
  - 测试通过率：100%
  - 向后兼容：无回归问题

### 🔒 安全
- 无安全相关变更

### ⚠️ 重大变更
- 本次更新为主版本升级（Major Release）
- **完全向后兼容**：所有现有测试用例无需修改即可继续使用
- 新增功能为可选特性，不影响现有配置

---

## [1.0.3] - 2026-01-31

### ✨ 新增
- **彩色命令行输出系统**
  - 支持 ANSI 颜色代码美化输出（自动检测终端支持）
  - 丰富的 Emoji 图标增强可读性
  - 中英文双语界面（`--lang en/zh`，默认中文）
  - 可通过 `--no-color` 和 `--no-emoji` 禁用样式
  - 优化的输出排版（emoji 间距、空行分隔等）

- 微秒级时间戳支持
  - 新增 `timestamp_us()` 函数：返回微秒级 Unix 时间戳
  - 新增 `now_us()` 函数：返回格式化的微秒时间字符串（YYYYMMDDHHMMSS%f）
  - 支持 `now().strftime('%f')` 获取微秒部分（6位数字）

### 🔧 变更
- **依赖升级**：`jsonpath` → `jsonpath-ng>=1.6.0`
  - 完整支持 JSONPath 标准语法
  - 支持过滤表达式、通配符、数组切片等高级功能

- **变量渲染**：`VariableManager.render_string()` 添加递归渲染支持
  - 支持多级嵌套变量引用（如 `${var1_${var2}}`）
  - 最多迭代 10 次（防止循环引用）
  - 自动检测渲染完成状态

- **Contains 验证器**：改进类型处理和边界情况
  - 正确处理 `None` 值
  - 支持列表、字符串、字典类型的包含检查
  - 修复数值类型比较问题

### 🐛 修复
- **JSONPath 复杂表达式支持**
  - 修复过滤表达式不工作的问题（`$.array[?(@.field == 'value')]`）
  - 修复数组索引不稳定的问题（`$.array[1]`）
  - 支持通配符访问（`$.array[*].field`）
  - 支持数值比较过滤（`$.array[?(@.price > 100)]`）
  - 支持布尔值过滤（`$.array[?(@.active == true)]`）

- **变量嵌套引用渲染**
  - 修复嵌套变量引用无法正确展开的问题
  - 支持多级嵌套（如 `${base}.${env}.com`）
  - 添加循环引用保护机制

- **Contains 验证器稳定性**
  - 修复对数组验证时偶尔报告不存在的问题
  - 修复包含 `None` 值的列表验证失败问题
  - 修复字典键检查的类型错误

- **时间戳精度支持**
  - 修复微秒格式 `%f` 不生效的问题
  - 提供专用函数避免快速运行时的重复问题

### 🗑️ 废弃
- 无

### ❌ 移除
- 无

### 🔒 安全
- 无

---

## [1.0.2] - 2026-01-29

### ✨ 新增
- JSONPath 函数支持（20+ 种内置函数）
  - 数组函数：length(), first(), last(), reverse(), sort(), unique(), flatten()
  - 数值函数：sum(), avg(), min(), max()
  - 字符串函数：upper(), lower(), trim(), split(), join()
  - 检查函数：contains(), starts_with(), ends_with(), matches()
  - 对象函数：keys(), values()

- 步骤控制功能
  - `skip_if`：条件为真时跳过步骤
  - `only_if`：条件为真时执行步骤
  - `depends_on`：步骤依赖关系
  - `setup`/`teardown`：步骤前后钩子

- 增强重试机制
  - 支持多种重试策略（fixed/exponential/linear）
  - 可配置重试条件（network/timeout/assertion）
  - 支持延迟和抖动（jitter）

### 🔧 变更
- 改进错误提示信息
- 优化变量渲染性能

### 🐛 修复
- 修复模板函数在某些情况下渲染失败的问题
- 修复验证器路径解析的边界情况

---

## [1.0.0] - 2026-01-27

### ✨ 新增
- 🎉 初始版本发布
- HTTP/HTTPS 请求支持（GET/POST/PUT/DELETE/PATCH）
- 数据库操作（MySQL/PostgreSQL/SQLite）
- 变量提取器（JSONPath/正则表达式/Header/Cookie）
- 断言验证器（20+ 种验证类型）
- 环境配置切换（profiles）
- 数据驱动测试（CSV/JSON/数据库）
- 循环控制（for/while）
- 并发执行
- 脚本执行（Python/JavaScript）
- 等待机制（固定延迟/条件等待）
- Mock 服务器
- WebSocket 实时推送
- 性能测试
- 多种输出格式（JSON/CSV/HTML/JUnit/Allure）

---

## 版本说明

### 版本号规则
- **主版本号（Major）**：不兼容的 API 变更
- **次版本号（Minor）**：向后兼容的功能新增
- **修订号（Patch）**：向后兼容的问题修复

### 变更类型说明
- **✨ 新增**：新功能
- **🔧 变更**：功能变更
- **🗑️ 废弃**：即将废弃的功能
- **❌ 移除**：已移除的功能
- **🐛 修复**：问题修复
- **🔒 安全**：安全相关修复

---

## 相关文档
- [API 输入协议规范](docs/API-Engine输入协议规范.md)
- [API 输出协议规范](docs/API-Engine输出协议规范.md)
