# Sisyphus API Engine

![Sisyphus](https://img.shields.io/badge/Sisyphus-API%20Engine-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.1-orange)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

**企业级 API 自动化测试引擎**

基于 YAML 的声明式测试框架，支持复杂的 API 测试场景

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [示例](#-示例)

---

## 📖 目录

- [功能特性](#-功能特性)
- [安装指南](#-安装指南)
- [快速开始](#-快速开始)
- [核心概念](#-核心概念)
- [示例说明](#-示例说明)
- [配置参考](#-配置参考)
- [文档](#-文档)
- [开发指南](#-开发指南)
- [许可证](#-许可证)

---

## ✨ 功能特性

### 🎯 核心能力

- **YAML 声明式测试** - 使用简洁的 YAML 语法定义测试用例
- **多环境管理** - 支持多环境配置（dev/test/prod），一键切换
- **变量系统** - 强大的变量管理（全局变量、环境变量、动态提取）
- **模板渲染** - 基于 Jinja2 的模板引擎，支持变量引用和计算

### 🔌 HTTP 测试

- **全方法支持** - GET、POST、PUT、DELETE、PATCH、HEAD、OPTIONS
- **请求定制** - 自定义 headers、params、body、cookies
- **响应验证** - 状态码、响应体、响应头验证
- **变量提取** - JSONPath、正则表达式、Header、Cookie 提取

### 🗄️ 数据库集成

- **多数据库支持** - MySQL、PostgreSQL、SQLite
- **多种操作** - 查询、执行、批量操作、脚本执行
- **参数化查询** - 防止 SQL 注入的预编译语句

### 🔧 高级特性

- **重试机制** - 支持固定、指数退避、线性等重试策略
- **步骤控制** - 条件执行（skip_if/only_if）、依赖管理（depends_on）
- **流程控制** - 等待（固定延迟和条件等待）、For 循环、While 循环
- **数据驱动** - 支持 CSV、JSON、数据库作为数据源
- **钩子函数** - 全局和步骤级别的 setup/teardown
- **并发测试** - 支持多线程并发执行和性能测试
- **脚本执行** - 支持 Python 脚本执行（安全沙箱）
- **Mock 服务** - 内置 Mock 服务器，支持接口模拟

### 📊 结果输出

- **多种格式** - JSON、CSV、HTML、JUnit XML、Allure 报告
- **性能指标** - DNS、TCP、TLS、服务器处理时间等详细性能数据
- **错误分类** - 智能错误分类和诊断信息
- **实时推送** - WebSocket 实时推送测试进度和结果
- **变量追踪** - 调试模式下追踪变量变化

---

## 🚀 安装指南

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/koco-co/Sisyphus-api-engine.git
cd Sisyphus-api-engine

# 安装依赖
pip install -e .

# 或使用 pip 直接安装
pip install Sisyphus-api-engine
```

### 验证安装

```bash
# 查看帮助
sisyphus-api-engine --help

# 验证 YAML 文件语法
sisyphus-api-validate examples/22_最佳实践.yaml

# 运行示例测试
sisyphus-api-engine --cases examples/22_最佳实践.yaml
```

---

## 🎬 快速开始

### 1. 创建第一个测试用例

创建 `my_first_test.yaml`：

```yaml
name: "我的第一个测试"
description: "测试 HTTPBIN API"

config:
  profiles:
    prod:
      base_url: "https://httpbin.org"

steps:
  - 测试GET请求:
      type: request
      url: "${config.profiles.prod.base_url}/get"
      method: GET
      validations:
        - type: eq
          path: "$.url"
          expect: "https://httpbin.org/get"
          description: "验证URL正确"
```

### 2. 运行测试

```bash
# 基本运行
sisyphus-api-engine --cases my_first_test.yaml

# 详细输出
sisyphus-api-engine --cases my_first_test.yaml -v

# 保存结果到 JSON
sisyphus-api-engine --cases my_first_test.yaml -o result.json

# 导出为 CSV
sisyphus-api-engine --cases my_first_test.yaml --format csv -o result.csv

# 导出为 HTML
sisyphus-api-engine --cases my_first_test.yaml --format html -o report.html

# 生成 Allure 报告
sisyphus-api-engine --cases my_first_test.yaml --allure

# 查看 Allure 报告（会自动打开浏览器）
allure serve allure-results

# 或者生成静态 HTML 报告
allure generate allure-results --clean -o allure-report
allure open allure-report

# 启用 WebSocket 实时推送
sisyphus-api-engine --cases my_first_test.yaml --ws-server
```

### 3. 查看结果

测试执行后，你将看到：

```
Executing: 我的第一个测试
Description: 测试 HTTPBIN API
Steps: 1

============================================================
Status: PASSED
Duration: 0.85s
Statistics:
  Total:   1
  Passed:  1 ✓
  Failed:  0 ✗
  Skipped: 0 ⊘
Pass Rate: 100.0%
============================================================
```

---

## 🎓 核心概念

### 测试用例结构

```yaml
name: "测试用例名称"          # 必填：用例名称
description: "测试描述"       # 可选：用例描述

config:                       # 可选：全局配置
  profiles: {}               # 环境配置
  variables: {}              # 全局变量
  timeout: 30                # 超时时间

steps: []                     # 必填：测试步骤列表
```

### 步骤类型

| 类型 | 说明 | 适用场景 |
|-----|------|---------|
| `request` | HTTP 请求 | API 测试 |
| `database` | 数据库操作 | 数据验证 |
| `wait` | 等待/延迟 | 异步场景 |
| `loop` | 循环控制 | 批量操作 |
| `concurrent` | 并发执行 | 性能测试 |
| `script` | 脚本执行 | 自定义逻辑 |

### 变量作用域

```
全局变量 (config.variables)
    ↓
环境变量 (config.profiles.{profile}.variables)
    ↓
提取变量 (extractors)  ← 优先级最高
```

---

## 📚 示例说明

项目提供了从入门到精通的完整示例，位于 `examples/` 目录：

### ⭐ 入门级 (1-7)

- **[01_HTTP请求方法.yaml](examples/01_HTTP请求方法.yaml)** - 各种 HTTP 方法（GET/POST/PUT/PATCH/DELETE等）
- **[02_请求参数配置.yaml](examples/02_请求参数配置.yaml)** - 请求参数、headers、body配置
- **[03_变量基础语法.yaml](examples/03_变量基础语法.yaml)** - 变量定义和使用基础
- **[04_内置模板函数.yaml](examples/04_内置模板函数.yaml)** - 内置函数（random_string/uuid/now/base64等）
- **[05_基础断言验证.yaml](examples/05_基础断言验证.yaml)** - 常用验证断言（状态码、相等、包含等）
- **[06_环境配置切换.yaml](examples/06_环境配置切换.yaml)** - 多环境配置（方式一：在用例内定义）
- **[07_使用全局配置.yaml](examples/07_使用全局配置.yaml)** - 全局配置复用（方式二：!include引入）

### ⭐⭐ 中级 (8-13)

- **[08_输出格式配置.yaml](examples/08_输出格式配置.yaml)** - 多种输出格式（JSON/CSV/HTML/JUnit）
- **[09_变量提取器.yaml](examples/09_变量提取器.yaml)** - 从响应中提取变量（JSONPath/正则/Header等）
- **[10_高级断言验证.yaml](examples/10_高级断言验证.yaml)** - 复杂验证逻辑（逻辑运算符/嵌套验证）
- **[11_步骤控制.yaml](examples/11_步骤控制.yaml)** - 条件执行、跳过、依赖关系
- **[12_重试机制.yaml](examples/12_重试机制.yaml)** - 失败重试策略（固定/指数退避）
- **[13_等待机制.yaml](examples/13_等待机制.yaml)** - 等待条件满足（固定延迟/条件等待）

### ⭐⭐⭐ 进阶级 (14-17)

- **[14_循环控制.yaml](examples/14_循环控制.yaml)** - 循环执行（for/while循环）
- **[15_并发执行.yaml](examples/15_并发执行.yaml)** - 并发测试（并发请求）
- **[16_数据驱动测试.yaml](examples/16_数据驱动测试.yaml)** - 数据驱动（CSV/JSON/数据库）
- **[17_脚本执行.yaml](examples/17_脚本执行.yaml)** - 自定义脚本（Python/JavaScript）

### ⭐⭐⭐⭐ 高级 (18-21)

- **[18_完整流程测试.yaml](examples/18_完整流程测试.yaml)** - 完整业务流程测试
- **[19_Mock服务器测试.yaml](examples/19_Mock服务器测试.yaml)** - Mock服务测试
- **[20_WebSocket实时推送.yaml](examples/20_WebSocket实时推送.yaml)** - WebSocket实时推送
- **[21_性能测试.yaml](examples/21_性能测试.yaml)** - 性能测试与压测

### ⭐⭐⭐⭐⭐ 专家级 (22-23)

- **[22_数据库操作.yaml](examples/22_数据库操作.yaml)** - 数据库操作（MySQL/PostgreSQL/SQLite）
- **[23_最佳实践.yaml](examples/23_最佳实践.yaml)** - 综合最佳实践示例

---

## 🌍 环境切换与配置管理

### 为什么需要配置管理?

当项目有大量测试用例时,如果每个用例都单独配置环境信息,会导致:
- ❌ 配置分散,难以维护
- ❌ 修改环境需要改动多个文件
- ❌ 容易出现配置不一致的问题

### 解决方案:全局配置 + 环境切换

**方案一:使用全局配置文件**

创建 `config/global_config.yaml`:

```yaml
# 全局配置文件
profiles:
  dev:
    base_url: "http://dev-api.example.com"
    variables:
      api_key: "dev-key-12345"
  staging:
    base_url: "http://staging-api.example.com"
    variables:
      api_key: "staging-key-67890"
  prod:
    base_url: "https://api.example.com"
    variables:
      api_key: "prod-key-abcde"

active_profile: "dev"
```

在测试用例中引入:

```yaml
name: "我的测试"
config: !include ../config/global_config.yaml

steps:
  - 测试请求:
      type: request
      url: "${config.profiles.${active_profile}.base_url}/api/users"
      headers:
        X-API-Key: "${config.profiles.${active_profile}.variables.api_key}"
```

**方案二:使用 `!include` 分层配置**

创建分层配置文件:

```yaml
# config/environments.yaml (仅环境配置)
profiles:
  dev: {base_url: "http://dev.example.com"}
  prod: {base_url: "https://api.example.com"}
active_profile: "dev"

# 测试用例文件
config: !include config/environments.yaml
```

**一键切换环境:**

```bash
# 开发环境
sisyphus-api-engine --cases test.yaml --profile dev

# 预发布环境
sisyphus-api-engine --cases test.yaml --profile staging

# 生产环境
sisyphus-api-engine --cases test.yaml --profile prod
```

### 优势

✅ **配置集中管理** - 所有环境配置在一个文件中
✅ **一键切换环境** - 通过 `--profile` 参数,无需修改用例
✅ **配置复用** - 多个用例共享同一配置,修改一处全部生效
✅ **分层配置** - 支持全局配置 + 用例特定配置
✅ **敏感信息保护** - 配合环境变量使用,避免硬编码敏感信息

### 示例参考

- **[06_环境配置切换.yaml](examples/06_环境配置切换.yaml)** - 方式一：在测试用例内定义环境配置
- **[07_使用全局配置.yaml](examples/07_使用全局配置.yaml)** - 方式二：使用 !include 引入全局配置

### 📁 目录结构

<details>
<summary>查看完整示例列表和运行方式</summary>

#### 运行 YAML 测试用例

```bash
# 验证所有 YAML 示例
for file in examples/*.yaml; do
    sisyphus-api-validate "$file"
done

# 运行所有 YAML 示例
for file in examples/*.yaml; do
    sisyphus-api-engine --cases "$file"
done
```

#### 学习路径

1. 从 `01_HTTP请求方法.yaml` 开始理解基本结构
2. 学习 `02_请求参数配置.yaml` 掌握请求定制
3. 通过 `03_变量基础语法.yaml` 学习变量系统
4. 实践 `04_内置模板函数.yaml` 掌握模板函数
5. 进阶 `05_变量提取器.yaml` 学习数据提取
6. 掌握 `06_基础断言验证.yaml` 理解验证机制
7. 精通 `07_高级断言验证.yaml` 掌握复杂验证
8. 学习 `08_环境配置切换.yaml` 理解多环境管理
9. 实践 `09_重试机制.yaml` 掌握重试策略
10. 学习 `10_步骤控制.yaml` 理解流程控制
11. 实践 `11_等待机制.yaml` 掌握异步处理
12. 学习 `12_循环控制.yaml` 掌握循环逻辑
13. 实践 `13_并发执行.yaml` 理解并发测试
14. 学习 `14_数据驱动测试.yaml` 掌握数据驱动
15. 实践 `15_数据库操作.yaml` 掌握数据库集成
16. 学习 `16_脚本执行.yaml` 理解脚本扩展
17. 通过 `17_完整流程测试.yaml` 综合运用所学
18. 学习 `18_输出格式配置.yaml` 掌握结果导出
19. 实践 `19_Mock服务器测试.yaml` 理解 Mock 服务
20. 学习 `20_WebSocket实时推送.yaml` 掌握实时推送
21. 通过 `21_性能测试.yaml` 理解性能测试
22. 最后学习 `22_最佳实践.yaml` 掌握生产级实践

</details>

---

## ⚙️ 配置参考

### 环境配置

```yaml
config:
  profiles:
    dev:
      base_url: "http://dev-api.example.com"
      variables:
        api_key: "dev_key"
    prod:
      base_url: "https://api.example.com"
      variables:
        api_key: "prod_key"

  active_profile: "dev"  # 当前激活环境
```

### 重试策略

```yaml
steps:
  - name: "带重试的请求"
    retry_policy:
      max_attempts: 3           # 最大重试次数
      strategy: exponential      # 策略: fixed/exponential/linear
      base_delay: 1.0           # 基础延迟（秒）
      max_delay: 10.0           # 最大延迟（秒）
      backoff_multiplier: 2.0   # 退避倍数
      jitter: true              # 是否添加随机抖动
```

### 数据驱动测试

```yaml
config:
  data_source:
    type: csv
    file_path: "数据驱动测试.csv"
    delimiter: ","
    has_header: true
  data_iterations: true
  variable_prefix: "user_"
```

### 验证器类型

| 类型 | 说明 | 示例 |
|-----|------|------|
| `eq` | 等于 | `- eq: ["$.status", 200]` |
| `ne` | 不等于 | `- ne: ["$.error", null]` |
| `contains` | 包含 | `- contains: ["$.message", "success"]` |
| `regex` | 正则匹配 | `- regex: ["$.email", "^[\\w\\.]+@"]` |
| `type` | 类型检查 | `- type: ["$.count", "number"]` |

更多验证器请参考[输入协议规范](docs/API-Engine输入协议规范.md)。

---

## 📖 文档

### 核心文档

- **[输入协议规范](docs/API-Engine输入协议规范.md)** - 完整的 YAML 语法和配置说明
- **[输出协议规范](docs/API-Engine输出协议规范.md)** - 测试结果输出格式

---

## 🔧 开发指南

### 项目结构

```
Sisyphus-api-engine/
├── apirun/
│   ├── core/           # 核心数据模型
│   ├── parser/         # YAML 解析器
│   ├── executor/       # 测试执行器
│   ├── validation/     # 断言验证引擎
│   ├── extractor/      # 变量提取器
│   ├── data_driven/    # 数据驱动测试
│   ├── result/         # 结果收集器
│   ├── mock/           # Mock 服务器
│   ├── websocket/      # WebSocket 实时推送
│   └── utils/          # 工具函数
├── examples/           # 示例用例
├── docs/               # 项目文档
└── tests/              # 测试文件
```

### 核心架构

```
输入 YAML
    ↓
V2YamlParser → TestCase
    ↓
TestCaseExecutor
    ↓
VariableManager (变量管理)
    ↓
StepExecutor (API/Database/Wait/Loop)
    ↓
ValidationEngine (验证)
    ↓
ResultCollector (结果收集)
    ↓
输出 JSON
```

### 扩展指南

<details>
<summary>添加自定义验证器</summary>

在 `apirun/validation/comparators.py` 中添加：

```python
def custom_comparator(actual: Any, expected: Any) -> bool:
    """自定义比较器"""
    # 实现比较逻辑
    return actual == expected

# 注册比较器
COMPARATORS = {
    # ... 其他比较器
    "custom": custom_comparator,
}
```

</details>

<details>
<summary>添加新的步骤类型</summary>

1. 创建执行器类：

```python
# apirun/executor/my_executor.py
from apirun.executor.step_executor import StepExecutor

class MyExecutor(StepExecutor):
    def _execute_step(self, rendered_step):
        # 实现执行逻辑
        pass
```

2. 在 `TestCaseExecutor` 中注册：

```python
if step.type == "my_type":
    executor = MyExecutor(...)
```

</details>

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

- 遵循 [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- 添加类型注解
- 编写单元测试
- 更新相关文档

---

## ❓ 常见问题

<details>
<summary>如何切换测试环境？</summary>

使用 `--profile` 参数：

```bash
sisyphus-api-engine --cases test.yaml --profile staging
```

或在 YAML 中设置：

```yaml
config:
  active_profile: "staging"
```

</details>

<details>
<summary>如何调试失败的测试？</summary>

使用 `-v` 参数查看详细输出：

```bash
sisyphus-api-engine --cases test.yaml -v
```

这将显示每个步骤的详细信息，包括请求、响应、验证结果等。

</details>

<details>
<summary>如何处理动态数据？</summary>

使用 Jinja2 模板语法：

```yaml
steps:
  - name: "创建用户"
    body:
      username: "user_${now().strftime('%Y%m%d%H%M%S')}"
      email: "${random_string(10)}@example.com"
```

</details>

<details>
<summary>数据驱动测试需要外部文件吗？</summary>

不需要，可以内联数据：

```yaml
config:
  data_source:
    - {username: "user1", age: 25}
    - {username: "user2", age: 30}
  data_iterations: true
```

</details>

---

## 📝 更新日志

### v1.0.0 (2026-01-29)

#### 核心功能
- ✨ YAML 声明式测试语法
- ✨ 多环境配置管理（dev/test/prod）
- ✨ 强大的变量系统（Jinja2 模板）
- ✨ 17 种内置模板函数
- ✨ 多层级变量作用域

#### HTTP 测试
- ✨ HTTP/HTTPS 全方法支持（GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS）
- ✨ 完整的请求定制（headers/params/body/cookies）
- ✨ 17 种验证器（eq/ne/gt/lt/contains/regex/type/len_eq 等）
- ✨ 4 种变量提取器（JSONPath/正则/Header/Cookie）
- ✨ 增强的重试机制（固定/指数退避/线性策略）

#### 数据库集成
- ✨ MySQL/PostgreSQL/SQLite 支持
- ✨ 查询和执行操作
- ✨ 参数化查询防 SQL 注入

#### 高级特性
- ✨ 步骤控制（skip_if/only_if/depends_on）
- ✨ 流程控制（Wait/For 循环/While 循环）
- ✨ 数据驱动测试（CSV/JSON/数据库）
- ✨ 并发测试（多线程并发执行）
- ✨ 脚本执行（Python 安全沙箱）
- ✨ Mock 服务器（接口模拟）
- ✨ WebSocket 实时推送
- ✨ 钩子函数（setup/teardown）

#### 结果输出
- ✨ 多种格式（JSON/CSV/HTML/JUnit XML/Allure）
- ✨ 详细性能指标（DNS/TCP/TLS/服务器处理时间）
- ✨ 智能错误分类和诊断
- ✨ 变量追踪（调试模式）

#### 质量保证
- ✨ 510+ 单元测试，100% 通过
- ✨ 完整的集成测试覆盖
- ✨ 22 个示例测试用例
- ✨ 详细的文档和最佳实践

#### 代码规范
- ✨ Google Python Style Guide
- ✨ 完整的类型注解和文档字符串
- ✨ Black、isort、flake8、mypy、pylint 配置

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 👥 作者

**koco-co**

- GitHub: [https://github.com/koco-co](https://github.com/koco-co)
- 邮箱: kopohub@gmail.com

---

## 🙏 致谢

- [Requests](https://requests.readthedocs.io/) - HTTP 库
- [Jinja2](https://jinja.palletsprojects.com/) - 模板引擎
- [JSONPath](https://github.com/h2non/jsonpath-ng) - JSON 路径表达式
- [PyYAML](https://pyyaml.org/) - YAML 解析器

---

## 📮 联系我们

- **问题反馈**: [GitHub Issues](https://github.com/koco-co/Sisyphus-api-engine/issues)
- **功能建议**: [GitHub Discussions](https://github.com/koco-co/Sisyphus-api-engine/discussions)
- **邮件**: kopohub@gmail.com

---

**如果这个项目对你有帮助，请给个 ⭐️ Star！**

Made with ❤️ by koco-co
