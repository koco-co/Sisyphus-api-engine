# Changelog

## [0.2.0] - 2026-02-26

### 变更

- 文档：根据《sisyphus-api-engine 需求规格说明书》与《开发任务清单》重写 `README.md`，明确技术栈（Python 3.12 + uv + Ruff + Pyright）与当前功能边界。
- 基础设施：补充 `.gitignore`、`.sisyphus/config.yaml`、`LICENSE`、`MANIFEST.in`、`.pre-commit-config.yaml` 等项目必需文件。
- 工具链：更新 `pyproject.toml` 中的 Python 版本约束与开发依赖，统一使用 uv + Ruff + Pyright 的现代化开发流程。
- 版本管理：将内部版本号从 `0.1.0` 提升到 `0.2.0`，为后续核心能力与高级特性开发预留演进空间。

## [0.1.0] - 2026-02-26

### 新增

- 项目初始化，从 Sisyphus-X 主项目中独立
- 核心数据模型 (CaseModel, Config, StepDefinition)
- YAML 用例加载与校验
- HTTP 请求执行器
- CLI 入口 (`sisyphus` 命令)
- 支持 text / json / allure / html 输出格式
- 项目目录结构重组为 `apirun/` 包
