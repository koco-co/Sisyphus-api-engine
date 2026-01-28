# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Sisyphus API Engine 是一个企业级 API 自动化测试引擎，支持 YAML 定义的测试用例执行。

## 核心命令

### 安装和设置
```bash
# 安装包（开发模式）
pip install -e .

# 或安装依赖
pip install -r requirements.txt  # 如果存在
```

### 运行测试用例
```bash
# 基本运行
sisyphus-api-engine --cases <yaml_file_path>

# 详细输出
sisyphus-api-engine --cases <yaml_file_path> -v

# 保存结果到 JSON
sisyphus-api-engine --cases <yaml_file_path> -o result.json

# 验证 YAML 语法（不执行）
sisyphus-api-engine --validate <yaml_file_path>

# 切换环境配置
sisyphus-api-engine --cases <yaml_file_path> --profile staging
```

### 运行单个测试文件
```bash
# Python 直接运行
python -m apirun.cli --cases examples/test_simple.yaml
```

## 核心架构

### 分层架构

```
apirun/
├── core/           # 核心数据模型
├── parser/         # YAML 解析器（v2.0 协议）
├── executor/       # 测试执行器
├── validation/     # 断言验证引擎
├── extractor/      # 变量提取器
├── data_driven/    # 数据驱动测试
├── result/         # 结果收集器
└── utils/          # 工具函数（模板渲染、钩子）
```

### 核心数据流

1. **解析阶段**: `V2YamlParser` 解析 YAML 文件 → `TestCase` 对象
2. **变量管理**: `VariableManager` 管理全局变量、环境变量、提取变量（Jinja2 模板渲染）
3. **执行阶段**: `TestCaseExecutor` 调度步骤执行 → 各类型 `StepExecutor` (API/Database/Wait/Loop)
4. **验证阶段**: `ValidationEngine` 使用 JSONPath 提取值 → 比较器验证
5. **结果收集**: `ResultCollector` 收集结果 → v2.0 JSON 格式输出

### 步骤执行器类型

- **APIExecutor**: HTTP/HTTPS 请求（基于 requests）
- **DatabaseExecutor**: 数据库操作（MySQL/PostgreSQL/SQLite）
- **WaitExecutor**: 等待/延迟步骤
- **LoopExecutor**: 循环步骤（for/while）

### 重试机制

增强的重试系统在 `apirun/core/retry.py`：

- **策略**: fixed（固定）、exponential（指数退避）、linear（线性）、custom（自定义）
- **配置**: 通过 `retry_policy` 字段配置（max_attempts, strategy, base_delay, max_delay, backoff_multiplier, jitter）
- **历史追踪**: 记录每次重试的时间戳、错误类型、延迟时间

### 变量作用域

变量优先级（从高到低）：
1. **提取变量** (extracted_vars): 步骤中提取的变量
2. **环境变量** (profile_vars): 当前激活的 profile 变量
3. **全局变量** (global_vars): config.variables 定义的变量

变量渲染使用 Jinja2 语法：`{{variable_name}}`

## YAML 协议规范

### 基本结构

```yaml
name: "测试用例名称"
description: "测试描述"

config:
  profiles:
    dev:
      base_url: "http://dev-api.example.com"
      variables: {}
    test:
      base_url: "http://test-api.example.com"
  active_profile: "dev"
  variables: {}
  timeout: 30
  retry_times: 0

steps:
  - name: "步骤名称"
    type: request  # request/database/wait/loop
    method: GET
    url: "/api/endpoint"
    validations: []
    extractors: []
```

### 步骤类型 (type)

- `request`: HTTP 请求（GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS）
- `database`: 数据库操作（query/execute/executemany/script）
- `wait`: 等待步骤（固定延迟或条件等待）
- `loop`: 循环步骤（for/while）

### 验证器 (validations)

使用 JSONPath 提取值并比较：

```yaml
validations:
  - type: eq  # eq, ne, gt, lt, ge, le, contains, regex, type, in, etc.
    path: "$.data.user_id"
    expect: 123
    description: "验证用户ID"
```

### 变量提取 (extractors)

```yaml
extractors:
  - name: token
    type: jsonpath  # jsonpath, regex, header, cookie
    path: "$.data.token"
```

## 关键模式

### 模板渲染

所有字符串字段在执行前都会经过 `VariableManager.render_string()` 处理，支持：
- 变量引用：`{{variable_name}}`
- 嵌套对象：`{{config.profiles.dev.base_url}}`
- 条件表达式：Jinja2 的 `{% if %}` 语法

### 错误分类

`apirun/core/models.py` 定义了 `ErrorCategory`：
- ASSERTION: 断言失败
- NETWORK: 网络错误
- TIMEOUT: 超时
- PARSING: 解析错误
- BUSINESS: 业务逻辑错误
- SYSTEM: 系统错误

### 数据驱动测试

通过 `config.data_source` 配置：
- CSV 文件
- JSON 文件
- 数据库查询

## 扩展点

### 添加新的验证器

在 `apirun/validation/comparators.py` 中添加比较器函数。

### 添加新的提取器

在 `apirun/extractor/` 创建新的提取器类，在 `extractor_factory.py` 中注册。

### 添加新的步骤类型

1. 在 `apirun/core/models.py` 扩展 `TestStep`
2. 在 `apirun/executor/` 创建新的执行器（继承 `StepExecutor`）
3. 在 `TestCaseExecutor._execute_step()` 中注册新类型

## 开发指南

### 遵循的代码风格

- Google Python Style Guide
- 类型注解（typing 模块）
- Docstrings（Google 风格）

### 测试文件位置

测试示例在 `examples/` 目录，包括：
- `test_v2_example.yaml`: 完整 v2.0 协议示例
- `test_simple.yaml`: 简单 API 测试
- `test_database.yaml`: 数据库操作示例
- `test_data_driven.yaml`: 数据驱动测试
- `test_wait_and_loop.yaml`: 等待和循环步骤
- `test_step_control.yaml`: 步骤控制（skip_if, only_if, depends_on）

### 调试技巧

使用 `-v` 标志查看详细输出，包括每个步骤的：
- 执行状态
- 响应时间
- 验证结果
- 错误信息

## 协议文档

详细协议规范见：
- `docs/API-Engine输入协议规范.md`: v2.0 输入协议
- `docs/API-Engine输出协议规范.md`: 输出格式规范
- `docs/API-Engine协议升级指南.md`: v1.x 到 v2.0 迁移指南

## 常见任务

### 添加新的测试用例

创建 YAML 文件，参考 `examples/test_v2_example.yaml` 的格式。

### 修改重试策略

在步骤级别配置：

```yaml
steps:
  - name: "带重试的请求"
    retry_policy:
      max_attempts: 3
      strategy: exponential
      base_delay: 1.0
      max_delay: 10.0
      jitter: true
```

### 数据驱动测试

```yaml
config:
  data_source:
    type: csv
    file_path: test_data.csv
    delimiter: ","
    has_header: true
  data_iterations: true
  variable_prefix: "data_"
```

CSV 中的列将作为变量可用（如 `{{data_username}}`）。
