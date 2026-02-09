# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Sisyphus API Engine 是一个企业级 API 自动化测试引擎，使用 YAML 声明式语法定义测试用例，支持 HTTP/HTTPS 请求、数据库操作、流程控制、数据驱动测试等功能。

## 常用命令

### 安装与设置
```bash
# 使用 uv 创建虚拟环境（Python 3.14）
uv venv -p 3.14 .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 安装项目（开发模式）
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 验证安装
sisyphus --help
```

### 运行测试
```bash
# 运行单个 YAML 测试用例
sisyphus --cases examples/01_HTTP请求方法.yaml

# 运行多个测试用例（支持多文件和目录）
sisyphus --cases test1.yaml test2.yaml tests/

# 指定环境运行
sisyphus --cases test.yaml --profile prod

# 详细输出模式
sisyphus --cases test.yaml -v

# 保存结果到文件
sisyphus --cases test.yaml -o result.json

# 指定输出格式
sisyphus --cases test.yaml --format json -o result.json
sisyphus --cases test.yaml --format csv -o result.csv
sisyphus --cases test.yaml --format html -o report.html
sisyphus --cases test.yaml --format junit -o junit.xml

# 生成 Allure 报告
sisyphus --cases test.yaml --allure

# 验证 YAML 文件语法
sisyphus-validate test.yaml

# 验证目录中所有 YAML 文件
sisyphus-validate examples/
```

### 单元测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/core/test_models.py

# 运行特定测试类或方法
pytest tests/core/test_models.py::TestProfileConfig::test_profile_config_creation

# 带覆盖率报告
pytest --cov=apirun --cov-report=html

# 运行集成测试
pytest tests/integration/ -v

# 跳过慢速测试
pytest -m "not slow"
```

### 代码质量检查
```bash
# Ruff 代码格式化（替代 black + isort）
ruff format apirun/ tests/

# Ruff 代码检查并自动修复（替代 flake8）
ruff check apirun/ tests/ --fix

# Pyright 类型检查（替代 mypy）
pyright .

# 运行 pre-commit 钩子（所有检查）
pre-commit run --all-files

# 安装 pre-commit 钩子
pre-commit install
```

## 核心架构

### 数据流与执行流程

```
YAML 测试用例文件
    ↓
V2YamlParser (解析 YAML → TestCase 对象)
    ↓
TestCaseExecutor (测试用例执行器)
    ↓
VariableManager (变量管理，Jinja2 渲染)
    ↓
StepExecutor (步骤执行器)
    ├── APIExecutor (HTTP/HTTPS 请求)
    ├── DatabaseExecutor (数据库操作)
    ├── WaitExecutor (等待/延迟)
    ├── LoopExecutor (循环控制)
    ├── ConcurrentExecutor (并发执行)
    └── ScriptExecutor (脚本执行)
    ↓
ValidationEngine (验证断言)
    ↓
Extractor (变量提取)
    ├── JSONPathExtractor
    ├── RegexExtractor
    ├── HeaderExtractor
    └── CookieExtractor
    ↓
ResultCollector (结果收集)
    ↓
输出 JSON 结果 / Allure 报告 / JUnit 报告 / HTML 报告
```

### 核心模块说明

#### 1. `apirun/core/models.py`
定义所有数据模型，是整个框架的基础：
- `TestCase`: 测试用例
- `TestStep`: 测试步骤
- `GlobalConfig`, `ProfileConfig`: 配置模型
- `ValidationRule`, `Extractor`: 验证和提取规则
- `StepResult`, `TestCaseResult`: 结果模型
- `PerformanceMetrics`: 性能指标
- `ErrorInfo`: 错误信息

**重要**: 所有模型使用 `@dataclass` 装饰器，添加新字段时需更新类型注解和文档字符串。

#### 2. `apirun/parser/v2_yaml_parser.py`
YAML 解析器，将 YAML 文件解析为 `TestCase` 对象：
- 支持 `!include` 标签引入外部文件
- 解析多环境配置（profiles）
- 解析各种步骤类型（request, database, wait, loop, concurrent, script）
- 解析验证规则和提取器

**关键方法**: `parse(yaml_file: str) -> TestCase`

#### 3. `apirun/core/variable_manager.py`
变量管理器，支持多层级变量作用域：
- 优先级（从低到高）：全局变量 → 环境变量 → Profile 变量 → 提取变量
- 使用 Jinja2 模板语法：`${variable_name}`
- 内置模板函数（在 `apirun/core/template_functions.py` 中定义）：`random_string()`, `uuid()`, `now()`, `base64_encode()` 等

**关键方法**:
- `set_variable(name, value)`: 设置变量
- `get_variable(name, default)`: 获取变量
- `render_template(template_str)`: 渲染模板字符串

#### 4. `apirun/executor/`
执行器模块，所有执行器继承自 `StepExecutor` 基类：
- `step_executor.py`: 抽象基类，定义执行流程和重试逻辑
- `api_executor.py`: HTTP/HTTPS 请求执行器
- `database_executor.py`: 数据库操作执行器（支持 MySQL、PostgreSQL、SQLite）
- `wait_executor.py`: 等待/延迟执行器（支持固定延迟和条件等待）
- `loop_executor.py`: 循环控制执行器（for/while 循环）
- `concurrent_executor.py`: 并发执行器
- `script_executor.py`: Python/JavaScript 脚本执行器
- `test_case_executor.py`: 测试用例执行调度器

**重要**: 添加新的步骤类型需要：
1. 在 `TestStep` 模型中添加新字段
2. 创建新的执行器类继承 `StepExecutor`
3. 在 `TestCaseExecutor._execute_step()` 中注册新执行器

#### 5. `apirun/validation/`
验证引擎：
- `engine.py`: `ValidationEngine` 类，执行验证规则
- `comparators.py`: 比较器函数（eq, ne, gt, lt, contains, regex, type 等）

**验证流程**:
1. 使用 JSONPath 从响应中提取实际值
2. 应用对应的比较器函数
3. 返回 `ValidationResult` 对象

#### 6. `apirun/extractor/`
变量提取器：
- `jsonpath_extractor.py`: JSONPath 提取
- `regex_extractor.py`: 正则表达式提取
- `header_extractor.py`: HTTP Header 提取
- `cookie_extractor.py`: Cookie 提取
- `extractor_factory.py`: 工厂模式创建提取器

#### 7. `apirun/result/`
结果收集和导出：
- `collector.py`: `ResultCollector` 类，收集执行结果
- `allure_collector.py`: 生成 Allure 报告
- `junit_exporter.py`: 导出 JUnit 格式
- `html_exporter.py`: 导出 HTML 格式

#### 8. `apirun/data_driven/`
数据驱动测试：
- `data_source.py`: 数据源加载器（CSV、JSON、数据库）
- `iterator.py`: 数据迭代器

#### 9. `apirun/websocket/`
WebSocket 实时推送：
- `server.py`: WebSocket 服务器
- `notifier.py`: 推送通知器
- `progress.py`: 进度事件
- `broadcaster.py`: 广播器

#### 10. `apirun/mock/`
Mock 服务：
- `server.py`: Mock 服务器
- `models.py`: Mock 配置模型

#### 11. `apirun/cli.py`
命令行接口，支持中英文双语帮助：
- 主命令：`sisyphus`
- 验证命令：`sisyphus-validate`

### 变量渲染机制

使用 Jinja2 模板引擎，自定义分隔符为 `${}`：

```yaml
# 引用变量
url: "${base_url}/api/users"

# 引用嵌套变量
token: "${config.profiles.dev.variables.api_key}"

# 使用内置函数
username: "${random_string(8)}"
timestamp: "${now().strftime('%Y-%m-%d')}"
```

内置函数定义在 `apirun/core/template_functions.py`，添加新函数时需在 `get_template_functions()` 中注册。

### 重试机制

支持两种重试配置方式：

**方式一：简单重试（已废弃，但仍支持）**
```yaml
retry_times: 3
```

**方式二：增强重试策略（推荐）**
```yaml
retry_policy:
  max_attempts: 3
  strategy: exponential  # fixed/exponential/linear
  base_delay: 1.0       # 秒
  max_delay: 10.0       # 秒
  backoff_multiplier: 2.0
  jitter: true
  retry_on:
    - network
    - timeout
  stop_on:
    - assertion
```

重试管理器实现：`apirun/core/retry.py`

### 步骤控制

- `skip_if`: 条件为真时跳过步骤
- `only_if`: 条件为真时执行步骤
- `depends_on`: 依赖的前置步骤列表
- `setup`: 步骤前置钩子
- `teardown`: 步骤后置钩子

### 测试用例结构

```yaml
name: "测试用例名称"          # 必填
description: "测试描述"       # 可选

config:                       # 可选：全局配置
  profiles: {}               # 环境配置
  variables: {}              # 全局变量
  timeout: 30                # 超时时间
  data_source: {}            # 数据驱动配置
  websocket: {}              # WebSocket 配置
  output: {}                 # 输出配置

steps: []                     # 必填：测试步骤列表
```

### 全局配置管理 (v2.0.5+)

支持项目级别的全局配置文件，实现配置的统一管理和继承：

**配置文件位置**：`.sisyphus/config.yaml`

**配置优先级**（从高到低）：
1. 测试用例文件中的 `config` 配置
2. 全局配置文件 `.sisyphus/config.yaml`
3. 系统默认值

**全局配置示例**：

```yaml
# .sisyphus/config.yaml
profiles:
  prod:
    base_url: "https://api.production.com"
    timeout: 30
  dev:
    base_url: "https://api.dev.com"
    timeout: 60
    variables:
      api_key: "dev-key-123"

variables:
  common_headers:
    User-Agent: "Sisyphus/2.0"

active_profile: "dev"
timeout: 30
retry_times: 2
```

**使用方式**：

1. **仅使用全局配置**（测试文件无 config 部分）：
```yaml
name: "使用全局配置的测试"
# 无 config 部分，自动使用 .sisyphus/config.yaml
steps:
  - name: "调用API"
    url: "${config.profiles.dev.base_url}/api/users"
```

2. **覆盖全局配置**（测试文件有 config 部分）：
```yaml
name: "覆盖全局配置的测试"
config:
  profiles:
    dev:
      base_url: "https://override.com"  # 覆盖全局配置
      timeout: 120  # 覆盖全局配置
steps:
  - name: "调用API"
    url: "${config.profiles.dev.base_url}/api/users"
```

**实现模块**：
- `apirun/core/global_config_manager.py`: 全局配置管理器
- `apirun/parser/v2_yaml_parser.py`: 解析器中集成全局配置加载

## 开发指南

### 🆕 使用提取器默认值（v2.0.1+）

提取器支持 `default` 参数，当提取的字段不存在时使用默认值：

**YAML 示例**：

```yaml
steps:
  - name: "提取用户信息"
    type: request
    url: "${base_url}/api/user"
    extractors:
      # 字段不存在时使用默认值
      - type: jsonpath
        name: user_id
        path: "$.user.id"
        default: "anonymous"
        description: "提取用户ID，不存在时使用anonymous"

      # 正则匹配失败时使用默认值
      - type: regex
        name: order_id
        path: "$.response"
        pattern: "Order ID: (\\d+)"
        default: "N/A"
        description: "提取订单号，不存在时使用N/A"
```

**代码实现**：

```python
# apirun/extractor/jsonpath_extractor.py

def extract(self, path: str, data: Any, index: int = 0, default: Any = None) -> Any:
    """Extract value using JSONPath.

    Args:
        path: JSONPath expression
        data: Data to extract from
        index: Index for multiple matches
        default: Default value if extraction fails (NEW in v2.0.1)
    """
    try:
        return extract_value(path, data, index)
    except Exception:
        if default is not None:
            return default
        raise
```

### 🆕 使用自定义错误消息（v2.0.1+）

验证器支持 `error_message` 参数，验证失败时显示自定义错误消息：

**YAML 示例**：

```yaml
steps:
  - name: "验证响应状态"
    type: request
    url: "${base_url}/api/status"
    validations:
      # 自定义错误消息
      - type: eq
        path: "$.status"
        expect: "success"
        error_message: "❌ 状态错误: 响应状态必须为'success'，请检查后端服务"
        description: "验证状态为success"

      # 逻辑运算符 - 统一错误消息
      - type: and
        error_message: "❌ 业务验证失败: 状态必须为success且码为1"
        sub_validations:
          - type: eq
            path: "$.status"
            expect: "success"
          - type: eq
            path: "$.code"
            expect: 1
```

**代码实现**：

```python
# apirun/validation/engine.py

def _validate_single(self, validation: Dict[str, Any], response_data: Dict[str, Any]) -> ValidationResult:
    """Execute a single validation."""
    val_type = validation.get("type", "eq")
    path = validation.get("path", "$")
    expect = validation.get("expect")
    description = validation.get("description", "")
    error_message = validation.get("error_message", "")  # NEW in v2.0.1

    # ... validation logic ...

    # Generate error message if failed
    error = ""
    if not passed:
        # Use custom error message if provided, otherwise generate default
        error = error_message if error_message else self._generate_error_message(val_type, path, actual, expect)

    return ValidationResult(
        passed=passed,
        type=val_type,
        path=path,
        actual=actual,
        expected=expect,
        description=description,
        error=error,
    )
```

### 添加新的验证器

在 `apirun/validation/comparators.py` 中添加：

```python
def custom_comparator(actual: Any, expected: Any) -> bool:
    """自定义比较器."""
    # 实现比较逻辑
    return actual == expected

# 注册比较器
COMPARATORS = {
    # ... 其他比较器
    "custom": custom_comparator,
}
```

### 添加新的模板函数

在 `apirun/core/template_functions.py` 中添加：

```python
def my_custom_function(**kwargs) -> Any:
    """自定义模板函数."""
    # 实现函数逻辑
    return result

# 在 get_template_functions() 中注册
def get_template_functions() -> Dict[str, Callable]:
    return {
        # ... 其他函数
        "my_custom_function": my_custom_function,
    }
```

### 添加新的步骤类型

1. 在 `apirun/core/models.py::TestStep` 中添加新字段
2. 创建执行器类（继承 `StepExecutor`）：

```python
# apirun/executor/my_executor.py
from apirun.executor.step_executor import StepExecutor

class MyExecutor(StepExecutor):
    def _execute_step(self, rendered_step):
        # 实现执行逻辑
        pass
```

3. 在 `apirun/executor/test_case_executor.py::_execute_step()` 中注册：

```python
if step.type == "my_type":
    executor = MyExecutor(...)
```

### 输出协议规范

测试执行结果遵循 v2.0 输出协议，详细格式参考 `docs/API-Engine输出协议规范.md`。

核心结构：
```json
{
  "test_case": {
    "name": "测试用例名称",
    "status": "passed/failed/skipped/error",
    "start_time": "ISO 8601 格式",
    "end_time": "ISO 8601 格式",
    "duration": 1.234
  },
  "statistics": {
    "total_steps": 10,
    "passed_steps": 8,
    "failed_steps": 1,
    "skipped_steps": 1
  },
  "steps": [...],
  "final_variables": {...}
}
```

### 代码规范

项目使用现代化 Python 开发工具链，遵循 Google Python Style Guide：

#### 工具链

- **uv** - 极速包管理器
- **Ruff** - 代码格式化和检查（替代 black + isort + flake8）
- **Pyright** - 静态类型检查（strict mode）
- **pre-commit** - Git 钩子自动化
- **pytest** - 单元测试框架
- **rich** - 终端美化输出

#### 代码风格

- 使用类型注解（Type Hints）
- 所有类和函数需有中文文档字符串（Docstrings）
- 最大行长度：88 字符（Ruff 默认）
- 使用 Ruff 格式化代码
- Pyright strict mode 类型检查
- 单引号字符串（Ruff 默认）
- 所有注释使用中文

### 测试策略

- `tests/core/`: 核心模块单元测试
- `tests/parser/`: 解析器测试
- `tests/executor/`: 执行器测试
- `tests/validation/`: 验证引擎测试
- `tests/extractor/`: 提取器测试
- `tests/integration/`: 端到端集成测试

运行集成测试前确保：
1. 所有依赖已安装
2. 测试数据库已配置（如需要）
3. Mock 服务可用（如需要）

### 常见问题

**Q: 如何调试模板渲染错误？**
A: 启用详细输出模式 `-v`，查看变量快照和错误堆栈。

**Q: 变量未生效怎么办？**
A: 检查变量名拼写、作用域优先级、模板语法（使用 `${}` 而非 `{{}}`）。

**Q: 步骤执行失败但测试继续？**
A: 检查 `depends_on` 配置，默认情况下测试会在第一个失败步骤后停止。

**Q: 如何处理动态数据？**
A: 使用内置模板函数（如 `random_string()`、`uuid()`、`now()`）生成动态数据。

### 文档参考

- `docs/API-Engine输入协议规范.md`: YAML 测试用例完整语法
- `docs/API-Engine输出协议规范.md`: 测试结果输出格式
- `docs/开发计划.md`: 功能开发路线图
- `docs/任务进度列表.md`: 当前任务进度
- `README.md`: 项目概述和快速开始
