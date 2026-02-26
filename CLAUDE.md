# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

sisyphus-api-engine 是 YAML 驱动的接口自动化测试引擎，为 Sisyphus-X 平台提供核心执行器能力。当前仓库是「轻量核心版」，聚焦核心链路：

**YAML → Pydantic 模型 → 场景运行器 → HTTP 请求 → JSON 输出**

高级特性（数据库、数据驱动、断言引擎、WebSocket 推送等）按任务清单逐步实现。

## 常用命令

### 环境管理
```bash
# 创建虚拟环境（Python 3.12+）
uv venv -p 3.12 .venv
source .venv/bin/activate  # macOS / Linux

# 安装依赖
uv sync

# 开发模式安装（含 dev 依赖）
uv pip install -e ".[dev]"
```

### 代码质量检查
```bash
# 代码格式化（Ruff）
uv run ruff format .

# 静态检查（Ruff）
uv run ruff check .

# 类型检查（Pyright）
uv run pyright
```

### 测试执行
```bash
# 运行所有单元测试
uv run python -m pytest tests/unit -v

# 运行单个 YAML 用例并输出 JSON
sisyphus --case tests/yaml/simple_get.yaml -O json

# 批量执行目录下所有 YAML 用例
sisyphus --cases tests/yaml/ -O json
```

### Pre-commit 钩子
```bash
# 安装 pre-commit 钩子（推荐）
pre-commit install
```

## 核心架构

### 数据流

```
YAML 用例
  ↓
load_case() → Pydantic 模型校验
  ↓
run_case() → 场景运行器
  ↓
execute_request_step() → HTTP 请求执行
  ↓
JSON 输出（符合内部规范）
```

### 关键模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **数据模型** | `apirun/core/models.py` | 所有 YAML 结构的 Pydantic 模型定义 |
| **场景运行器** | `apirun/core/runner.py` | `load_case()` 加载 YAML，`run_case()` 执行用例 |
| **请求执行器** | `apirun/executor/request.py` | HTTP 请求发送与响应处理 |
| **变量渲染** | `apirun/utils/variables.py` | `{{var}}` / `{{func()}}` 模板递归渲染 |
| **内置函数** | `apirun/utils/functions.py` | `random()`, `timestamp()` 等模板函数 |
| **CLI 入口** | `apirun/cli.py` | `sisyphus` 命令实现 |

### 变量系统

**渲染规则**（`apirun/utils/variables.py`）：
- `{{var_name}}` → 从 `variables` 字典读取
- `{{func_name(arg1, arg2)}}` → 调用内置函数（见 `BUILTIN_FUNCTIONS`）
- 支持递归渲染 dict / list / str 结构

**变量优先级**：
1. `config.variables`（场景级）
2. `config.environment.variables`（环境级，覆盖场景级）

### 关键类型设计

**`StepDefinition.keyword_type`** 决定步骤类型：
- `request` → HTTP 请求（当前已实现）
- `assertion` → 独立断言步骤（预留）
- `extract` → 变量提取步骤（预留）
- `db` → 数据库操作（预留）
- `custom` → 自定义关键字（预留）

**YAML 模型字段别名**：
- `RequestStepParams.json` 使用 `alias="json"`（避免与 Python 内置冲突）

## 开发约定

### 代码风格
- **Python 版本**: 3.12+
- **代码风格**: Google Python Style（Ruff 配置）
- **注释语言**: 统一使用中文，解释「意图」而非「语法」
- **类型注解**: 尽量补全，保持 Pyright 通过
- **行长度**: 100 字符（`ruff.line-length = 100`）

### 测试要求
- 单元测试位于 `tests/unit/`
- YAML 集成用例位于 `tests/yaml/`
- 新增/修改功能时需同步补充测试

### 提交规范
建议使用前缀：
- `feat:` - 新功能
- `fix:` - Bug 修复
- `refactor:` - 重构
- `docs:` - 文档更新
- `test:` - 测试相关
- `chore:` - 构建/工具链

## 配置文件

### `.sisyphus/config.yaml`
统一环境配置：
```yaml
profiles:
  dev:
    base_url: "http://dev.example.com"
    variables:
      api_key: "dev-key"
  prod:
    base_url: "https://api.example.com"
    variables:
      api_key: "prod-key"

active_profile: "dev"

variables:
  common_headers:
    User-Agent: "sisyphus-api-engine/0.2.0"
```

### CLI 输出格式
- `-O text`（默认）：人类可读文本输出
- `-O json`：机器可读 JSON（符合 `docs/Sisyphus-api-engine JSON 输出规范.md`）
- `-O allure` / `-O html`：预留

## 版本说明

- **当前版本**: `0.2.0`（核心执行器重构线）
- **PyPI 已发布版本**: `2.1.0`（完整引擎，与当前仓库解耦）
- **版本变更记录**: 见 `CHANGELOG.md`

## 扩展点

### 添加新的内置函数
在 `apirun/utils/functions.py` 中：
1. 实现函数（签名参考现有函数）
2. 注册到 `BUILTIN_FUNCTIONS` 字典

### 自定义关键字
继承 `apirun/keyword.Keyword` 基类：
```python
from apirun.keyword import Keyword

class MyKeyword(Keyword):
    name = "my_keyword"

    def execute(self, **kwargs):
        # 实现逻辑
        return result
```

## 重要文档

- 需求规格说明：`docs/Sisyphus-api-engine需求文档.md`
- YAML 输入规范：`docs/Sisyphus-api-engine YAML 输入规范.md`
- JSON 输出规范：`docs/Sisyphus-api-engine JSON 输出规范.md`
- 开发任务清单：`docs/开发任务清单.md`
