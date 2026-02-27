# Changelog

## [2.2.2] - 2026-02-27

### 新增

- HTTP 执行器：`RequestStepParams.files` 支持 MinIO 路径，自动通过 HTTP 下载为临时文件并作为 multipart 上传（REQ-018）。
- CLI：在 `-O json` 模式下，针对 YAML 解析与校验等引擎级错误输出符合《JSON 输出规范》的 `status=error` 顶层结构，复用 `to_json_engine_error`（ERR-004, RPT-004）。

### 变更

- 错误处理：`apirun.core.runner.load_case` 统一委托 `parser.yaml_parser.parse_yaml`，对外始终抛出 `EngineError`，测试用例同步对齐错误码断言。
- 发布脚本：`pypi_publish.sh` 新增 `PYPI_REPOSITORY` / `PYPI_REPOSITORY_URL` 支持，可方便地将构建包发布到 TestPyPI 进行流程验证，并在 README 中补充了发布流程示例（PUB-002）。

## [2.2.1] - 2026-02-27

### 新增

- 报告：Allure 结果文件生成（RPT-008～010），步骤与断言映射；HTML 自包含报告（RPT-011～012）。
- CLI：`-O allure` / `-O html` 集成，支持 `--allure-dir`、`--html-dir`（CLI-013～014）。
- WebSocket：EventPublisher 协议与 NoOp/WsPublisher 实现，runner 可选注入（WS-001～004）。
- 发布准备：CHANGELOG 维护、LICENSE(MIT)、版本与 pyproject 同步、examples 示例用例（PUB-001～005）。

### 变更

- 无破坏性变更。

## [2.2.0] - 2026-02-26

### 变更

- 发布：将核心执行器重构线作为 PyPI 新版本 `2.2.0` 发布，对应当前仓库代码。
- 文档：更新 README 中的版本说明与发布策略，标记 2.2.0 为最新稳定版，并保留历史 2.1.0 信息。
- 版本管理：`pyproject.toml` 中版本号由 `0.2.0` 升级为 `2.2.0`，用于对齐现有 PyPI 版本序列。

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
