# Changelog

## [2.2.3] - 2026-02-27

### 修复

- **last_response 变量**：修复独立 `extract` / `assertion` 步骤中使用 `source_variable: "last_response"` 时无法获取响应的问题（RUN-015）。每次 HTTP 请求成功后，自动将 `last_response` 存储到全局变量池。
- **CLI 命令别名**：添加 `sisyphus` 命令别名，与 `sisyphus-api-engine` 同时可用（CLI-016）。
- **测试环境配置**：更新 `.sisyphus/config.yaml`，将 `dev` 环境指向本地 Mock 服务器 `http://localhost:8888`，解决测试用例因不可用域名导致全部失败的问题。
- **Mock 服务器**：新增 `tests/mock_server.py` 简易 HTTP 服务器，支持所有测试用例所需的 API 端点。
- **JSONPath 修复**：修正 `tests/yaml/full_step_types.yaml` 中的变量提取表达式，从 `$.data.items[0].id` 改为 `$.data[0].id` 以匹配实际响应结构。

### 新增

- **测试指南**：添加 `docs/测试指南.md`，详细说明测试执行方法、Mock 服务器使用、环境配置等。

### 测试结果

当前测试套件状态（9 个用例）：
- ✅ **通过**: 8/9 (88.9%)
- ⚠️ **错误**: 1/9 (预期错误，测试错误处理)
- ❌ **失败**: 0/9

## [2.2.2] - 2026-02-27

### 新增

- HTTP 执行器：`RequestStepParams.files` 支持 MinIO 路径，自动通过 HTTP 下载为临时文件并作为 multipart 上传（REQ-018）。
- CLI：在 `-O json` 模式下，针对 YAML 解析与校验等引擎级错误输出符合《JSON 输出规范》的 `status=error` 顶层结构，复用 `to_json_engine_error`（ERR-004, RPT-004）。

### 变更

- 错误处理：`apirun.core.runner.load_case` 统一委托 `parser.yaml_parser.parse_yaml`，对外始终抛出 `EngineError`，测试用例同步对齐错误码断言。
- 发布脚本：`pypi_publish.sh` 新增 `PYPI_REPOSITORY` / `PYPI_REPOSITORY_URL` 支持，可方便地将构建包发布到 TestPyPI 进行流程验证，并在 README 中补充了发布流程示例（PUB-002）。
- CLI：新增 `.sisyphus/config.yaml` 的 `active_profile` 自动注入能力；当 YAML 未显式配置 `config.environment` 时，自动回填 `base_url` 与 profile 变量以支持相对 URL 执行。

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
