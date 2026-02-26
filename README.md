# Sisyphus-api-engine

[![Python](https://img.shields.io/badge/python-3.12%2B-brightgreen)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-core--engine--beta-blue)](./CHANGELOG.md)

YAML 驱动的接口自动化测试引擎，为 Sisyphus-X 平台提供 **核心执行器** 能力。  
当前仓库是面向 Python 3.12+ 的「轻量核心版」，聚焦：

- YAML 用例 → Pydantic 数据模型
- 场景运行器（Runner）
- HTTP 请求执行
- JSON 结果输出（对齐内部输出规范）

> 完整功能版（含 Mock、WebSocket、多格式报告等）请参考已发布的 PyPI 包  
> [Sisyphus-api-engine](https://pypi.org/project/Sisyphus-api-engine/)。

---

## 目录

- [Sisyphus-api-engine](#sisyphus-api-engine)
  - [目录](#目录)
  - [简介](#简介)
  - [特性概览](#特性概览)
  - [技术栈与约束](#技术栈与约束)
  - [安装](#安装)
    - [使用 uv（推荐）](#使用-uv推荐)
    - [使用 pip](#使用-pip)
  - [快速开始](#快速开始)
    - [编写最小 YAML 用例](#编写最小-yaml-用例)
    - [通过 CLI 执行](#通过-cli-执行)
  - [配置管理（.sisyphus）](#配置管理sisyphus)
  - [项目结构](#项目结构)
  - [运行与调试](#运行与调试)
    - [单元测试](#单元测试)
    - [代码质量与类型检查](#代码质量与类型检查)
  - [版本与发布策略](#版本与发布策略)
  - [开发规范](#开发规范)
  - [关联文档](#关联文档)
  - [许可证](#许可证)

---

## 简介

`Sisyphus-api-engine` 是 Sisyphus-X 自动化测试管理平台的 **核心执行器**：

- 解析 YAML 格式的接口测试用例
- 按步骤执行 HTTP 请求
- 组合变量系统与模板渲染
- 输出标准化 JSON 结果给平台消费

本仓库对应的是「核心执行器重构线」，优先保证核心链路稳定：

> YAML → Pydantic 模型 → 场景运行器 → HTTP 请求 → JSON 输出

高级特性（数据库、数据驱动、断言引擎、WebSocket 推送等）会按照内部开发任务清单逐步补齐。

---

## 特性概览

- **YAML 驱动**：用例以 YAML 描述，结构清晰、易读易维护
- **强类型模型**：基于 Pydantic v2 构建核心数据模型，保证输入合法性
- **变量系统**：
  - 内置函数（随机串、时间戳等），见 `apirun/utils/functions.py`
  - 递归模板渲染，见 `apirun/utils/variables.py`
- **HTTP 请求执行**：
  - 基于 `requests`，支持常见 HTTP 方法
  - 支持 base_url + 相对路径拼接
  - 支持 URL / headers / params / body 的变量渲染
- **JSON 输出**：
  - 执行结果统一输出为 JSON
  - 输出结构与内部《JSON 输出规范》文档对齐（逐步完善中）

---

## 技术栈与约束

- **语言**：Python **3.12+**
- **包管理器**：`uv`
- **代码风格**：Google Python Style，**注释统一使用中文**
- **静态检查**：`Ruff` + `Pyright`
- **测试框架**：`pytest`
- **构建系统**：`hatchling`（由 `pyproject.toml` 管理）

详细技术约束与架构说明参见：

- `docs/Sisyphus-api-engine需求文档.md`
- `docs/开发任务清单.md`

---

## 安装

### 使用 uv（推荐）

```bash
# 1. 创建虚拟环境（Python 3.12+）
uv venv -p 3.12 .venv
source .venv/bin/activate  # macOS / Linux

# 2. 安装依赖
uv sync

# 或开发模式安装（包含 dev 依赖）
uv pip install -e ".[dev]"
```

### 使用 pip

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux

pip install -e ".[dev]"
```

> `pyproject.toml` 中 `requires-python = ">=3.12"`，低于 3.12 的 Python 版本不支持。

---

## 快速开始

> 当前核心能力为 **HTTP 请求 + JSON 输出**，高级特性按任务清单逐步实现。

### 编写最小 YAML 用例

示例：`tests/yaml/simple_get.yaml`（可自行创建）：

```yaml
config:
  name: "简单 GET 示例"
  environment:
    name: "dev"
    base_url: "https://httpbin.org"

teststeps:
  - name: "GET /get"
    keyword_type: "request"
    request:
      method: "GET"
      url: "/get"
```

### 通过 CLI 执行

```bash
# 执行单个 YAML 用例，并输出 JSON
sisyphus --case tests/yaml/simple_get.yaml -O json

# 批量执行目录下所有 YAML 用例
sisyphus --cases tests/yaml/ -O json
```

> CLI 的参数设计与完整引擎版本保持一致，详细说明见 `apirun/cli.py` 以及需求文档中「CLI 命令行接口」章节。

---

## 配置管理（.sisyphus）

项目根目录下的 `.sisyphus/config.yaml` 用于统一环境配置：

```yaml
profiles:
  dev:
    base_url: "http://dev.example.com"
    variables:
      api_key: "dev-key-please-change"

  prod:
    base_url: "https://api.example.com"
    variables:
      api_key: "prod-key-please-change"

active_profile: "dev"

variables:
  common_headers:
    User-Agent: "sisyphus-api-engine/0.2.0"
```

- 用例中可通过 `config.profiles.{profile}.base_url` 访问环境配置
- `active_profile` 控制默认环境
- `variables` 下可定义公共变量/头信息

---

## 项目结构

```text
Sisyphus-api-engine/
├── .sisyphus/              # 统一环境配置
│   └── config.yaml
├── apirun/                 # 主 Python 包
│   ├── __init__.py         # 导出 __version__ / 公共 API（预留）
│   ├── cli.py              # CLI 入口 (sisyphus)
│   ├── core/
│   │   ├── models.py       # CaseModel / Config / StepDefinition 等
│   │   └── runner.py       # 场景运行器
│   ├── executor/
│   │   └── request.py      # HTTP 请求执行器
│   ├── utils/
│   │   ├── functions.py    # 内置函数
│   │   └── variables.py    # 变量渲染引擎
│   ├── parser/             # YAML 解析（预留）
│   ├── validation/         # 断言引擎（预留）
│   ├── extractor/          # 变量提取器（预留）
│   ├── data_driven/        # 数据驱动（预留）
│   ├── result/             # 结果模型与导出（预留）
│   └── websocket/          # WebSocket 推送（预留）
├── docs/                   # 需求 & 规范 & 任务清单
├── tests/
│   ├── unit/               # Python 单元测试（pytest）
│   └── yaml/               # YAML 集成用例（通过 CLI 执行）
├── CHANGELOG.md
├── LICENSE
├── MANIFEST.in
├── pyproject.toml
├── pypi_publish.sh         # PyPI 发布脚本
└── uv.lock
```

---

## 运行与调试

### 单元测试

```bash
# 运行所有单元测试
uv run python -m pytest tests/unit -v
```

### 代码质量与类型检查

```bash
# 代码格式化（Ruff）
uv run ruff format .

# 静态检查（Ruff）
uv run ruff check .

# 类型检查（Pyright）
uv run pyright
```

> 推荐安装 `pre-commit` 钩子（已在 `.pre-commit-config.yaml` 中配置）：

```bash
pre-commit install
```

---

## 版本与发布策略

> 当前仓库版本号仅针对「核心执行器重构线」，与历史完整引擎版本解耦。

- **内部版本（本仓库）**
  - 当前版本：`2.2.0`
  - 历史内部版本：`0.1.0` / `0.2.0`（未作为独立 PyPI 版本发布）
  - 版本变更记录：见 `CHANGELOG.md`
- **PyPI 已发布版本（完整引擎）**
  - 包名：`Sisyphus-api-engine`
  - 最新稳定版：`2.2.0`
  - 页面：<https://pypi.org/project/Sisyphus-api-engine/>

未来规划：

- 先在本仓库完成核心执行器的重构与简化
- 与需求文档和任务清单对齐后，再规划下一代主线版本（例如 3.x）

---

## 开发规范

- 代码风格：Google Python Style
- 注释：统一使用中文，解释「意图」而非「语法」
- 类型：尽量补全类型注解，保持 Pyright 通过
- 测试：新增/修改功能时应补充或更新 `tests/unit` 与 `tests/yaml` 中的用例
- 提交信息：建议使用前缀（如 `feat:`, `fix:`, `chore:`, `docs:`, `refactor:` 等）

---

## 关联文档

- 需求规格说明：`docs/Sisyphus-api-engine需求文档.md`
- YAML 输入规范：`docs/Sisyphus-api-engine YAML 输入规范.md`
- JSON 输出规范：`docs/Sisyphus-api-engine JSON 输出规范.md`
- 开发任务清单：`docs/开发任务清单.md`

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎在遵守协议的前提下自由使用、修改和分发。
