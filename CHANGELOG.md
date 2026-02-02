# 更新日志

本文件记录 Sisyphus API Engine 的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 规范，
项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html) 规范。

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
