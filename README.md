# Sisyphus API Engine

<div align="center">

![Sisyphus](https://img.shields.io/badge/Sisyphus-API%20Engine-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-orange)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

**企业级 API 自动化测试引擎**

基于 YAML 的声明式测试框架，支持复杂的 API 测试场景

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [示例](#-示例)

</div>

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
- **流程控制** - 等待、For 循环、While 循环
- **数据驱动** - 支持 CSV、JSON、数据库作为数据源
- **钩子函数** - 全局和步骤级别的 setup/teardown

### 📊 结果输出

- **详细报告** - JSON 格式的测试结果输出
- **性能指标** - 响应时间、DNS 查询、TCP 连接等性能数据
- **错误分类** - 智能错误分类和诊断信息

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
# 查看版本
sisyphus-api-engine --help

# 运行示例测试
sisyphus-api-engine --cases examples/01_最简案例.yaml
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
      url: "{{config.profiles.prod.base_url}}/get"
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

# 保存结果
sisyphus-api-engine --cases my_first_test.yaml -o result.json
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

### ⭐ 入门级

- **[01_最简案例.yaml](examples/01_最简案例.yaml)** - 最简单的 GET 请求
- **[02_HTTP请求测试.yaml](examples/02_HTTP请求测试.yaml)** - GET/POST、验证和提取

### ⭐⭐⭐ 进阶级

- **[03_完整流程测试.yaml](examples/03_完整流程测试.yaml)** - 登录流程、环境配置
- **[04_数据库操作.yaml](examples/04_数据库操作.yaml)** - 数据库 CRUD 操作

### ⭐⭐⭐⭐ 高级

- **[05_步骤控制.yaml](examples/05_步骤控制.yaml)** - 条件执行、依赖管理
- **[06_等待和循环.yaml](examples/06_等待和循环.yaml)** - 等待、循环控制

### ⭐⭐⭐⭐⭐ 专家级

- **[07_数据驱动测试.yaml](examples/07_数据驱动测试.yaml)** - CSV 数据驱动

### 🐍 Python 演示脚本

- **[08_重试机制演示.py](examples/08_重试机制演示.py)** - 展示各种重试策略
- **[09_等待循环演示.py](examples/09_等待循环演示.py)** - 展示等待和循环功能

<details>
<summary>查看完整示例列表</summary>

#### 运行 YAML 测试用例

```bash
# 验证所有 YAML 示例
for file in examples/*.yaml; do
    sisyphus-api-engine --validate "$file"
done

# 运行所有 YAML 示例
for file in examples/*.yaml; do
    sisyphus-api-engine --cases "$file"
done

# 运行 Python 演示脚本
python examples/08_重试机制演示.py
python examples/09_等待循环演示.py
```

#### 学习路径

1. 从 `01_最简案例.yaml` 开始理解基本结构
2. 学习 `02_HTTP请求测试.yaml` 掌握 HTTP 测试
3. 通过 `03_完整流程测试.yaml` 学习环境配置
4. 实践 `04_数据库操作.yaml` 掌握数据库集成
5. 进阶 `05_步骤控制.yaml` 学习流程控制
6. 掌握 `06_等待和循环.yaml` 处理异步场景
7. 精通 `07_数据驱动测试.yaml` 实现数据驱动
8. 运行 `08_重试机制演示.py` 深入理解重试机制
9. 运行 `09_等待循环演示.py` 深入理解等待和循环

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
    file_path: "test_data.csv"
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

### 开发文档

- **[CLAUDE.md](CLAUDE.md)** - 代码架构和开发指南
- **[开发计划](docs/开发计划任务列表.md)** - 功能开发路线图
- **[任务进度](docs/任务进度列表.md)** - 当前任务进度

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
      username: "user_{{now().strftime('%Y%m%d%H%M%S')}}"
      email: "{{random_string(10)}}@example.com"
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

### v1.0.0 (2026-01-28)

**首次发布**
- 🎉 企业级 API 自动化测试引擎
- ✨ YAML 声明式测试语法
- ✨ 多环境配置管理
- ✨ HTTP/HTTPS 请求支持
- ✨ 数据库操作支持（MySQL/PostgreSQL/SQLite）
- ✨ 强大的变量系统（Jinja2 模板）
- ✨ 多种验证器（JSONPath、正则、类型检查等）
- ✨ 变量提取（JSONPath、正则、Header、Cookie）
- ✨ 增强的重试机制（固定/指数退避/线性策略）
- ✨ 步骤控制（条件执行、依赖管理）
- ✨ 流程控制（等待、For循环、While循环）
- ✨ 数据驱动测试（CSV/JSON/数据库）
- ✨ 钩子函数（setup/teardown）
- 📚 完整的文档和示例

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

<div align="center">
**如果这个项目对你有帮助，请给个 ⭐️ Star！**

Made with ❤️ by koco-co

</div>
