# sisyphus-api-engine 需求规格说明书

> **文档版本**: v1.0
> **创建日期**: 2026-02-26
> **文档性质**: 功能需求规格说明书（供开发 & 测试人员使用）
> **适用组件**: sisyphus-api-engine 核心执行器
> **关联文档**: [YAML 输入规范](./Sisyphus-api-engine%20YAML%20输入规范.md)、[JSON 输出规范](./Sisyphus-api-engine%20JSON%20输出规范.md)

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 技术架构](#2-技术架构)
- [3. 模块功能需求](#3-模块功能需求)
  - [3.1 核心数据模型 (apirun/core)](#31-核心数据模型-apiruncore)
  - [3.2 YAML 解析器 (apirun/parser)](#32-yaml-解析器-apirunparser)
  - [3.3 测试执行器 (apirun/executor)](#33-测试执行器-apirunexecutor)
  - [3.4 断言验证引擎 (apirun/validation)](#34-断言验证引擎-apirunvalidation)
  - [3.5 变量提取器 (apirun/extractor)](#35-变量提取器-apirunextractor)
  - [3.6 数据驱动测试 (apirun/data_driven)](#36-数据驱动测试-apirundata_driven)
  - [3.7 结果收集器 (apirun/result)](#37-结果收集器-apirunresult)
  - [3.8 WebSocket 实时推送 (apirun/websocket)](#38-websocket-实时推送-apirunwebsocket)
  - [3.9 CLI 命令行接口 (apirun/cli)](#39-cli-命令行接口-apiruncli)
  - [3.10 工具函数 (apirun/utils)](#310-工具函数-apirunutils)
  - [3.11 安全与防护 (apirun/security)](#311-安全与防护-apirunsecurity)
  - [3.12 健壮性机制 (Robustness)](#312-健壮性机制-robustness)
- [4. 变量系统](#4-变量系统)
- [5. 错误处理规范](#5-错误处理规范)
- [6. 开发任务清单](#6-开发任务清单)
- [附录 A: 枚举值定义](#附录-a-枚举值定义)
- [附录 B: 错误码定义](#附录-b-错误码定义)

---

## 1. 项目概述

### 1.1 产品定位

sisyphus-api-engine 是 Sisyphus-X 自动化测试管理平台的**核心执行器**，负责解析 YAML 格式的测试用例文件并执行接口自动化测试。引擎以 CLI 工具形式提供，支持多种报告格式输出，可作为独立 PyPI 包安装使用。

### 1.2 核心能力

| 能力域 | 说明 |
|--------|------|
| YAML 解析 | 解析并校验 YAML 测试用例文件，将其转换为内部数据模型 |
| HTTP 请求执行 | 支持所有 HTTP 方法，处理 headers/params/body/cookies/timeout 等参数 |
| 断言验证 | 支持 17 种比较器，支持 JSON/Header/Cookie/StatusCode/ResponseTime 等断言目标 |
| 变量提取 | 从响应中通过 JSONPath / Header / Cookie 提取变量，支持全局和环境级作用域 |
| 数据驱动 | 支持 YAML 内联定义和 CSV 文件两种数据驱动方式 |
| 数据库操作 | 支持 MySQL/PostgreSQL 数据库查询、提取、断言 |
| 自定义关键字 | 调用用户自定义的关键字函数 |
| 多格式报告 | 支持 text/json/allure/html 四种输出格式 |
| 实时推送 | 通过 WebSocket 实时推送执行进度（平台集成模式） |

### 1.3 运行模式

| 模式 | 说明 |
|------|------|
| 独立 CLI 模式 | 开发者直接通过 `sisyphus` 命令执行 YAML 用例 |
| 平台集成模式 | Sisyphus-X 后端通过 subprocess 调用 CLI，获取 JSON 输出 |
| PyPI 包模式 | 作为 Python 包被第三方项目引入调用 |

### 1.4 技术约束

| 约束项 | 说明 |
|--------|------|
| Python 版本 | >= 3.12 |
| 包管理器 | uv |
| 代码规范 | Google 开发范式 |
| 注释语言 | 中文 |
| 代码检查 | Ruff + Pyright |
| 测试框架 | pytest |

---

## 2. 技术架构

### 2.1 项目目录结构

```
Sisyphus-api-engine/
├── .sisyphus/              # 统一环境配置
│   └── config.yaml
├── apirun/                 # 主 Python 包
│   ├── __init__.py
│   ├── cli.py              # CLI 入口
│   ├── core/               # 核心数据模型
│   │   ├── models.py       # Pydantic 数据模型
│   │   └── runner.py       # 场景运行器
│   ├── parser/             # YAML 解析器
│   ├── executor/           # 测试执行器
│   │   └── request.py      # HTTP 请求执行器
│   ├── validation/         # 断言验证引擎
│   ├── extractor/          # 变量提取器
│   ├── data_driven/        # 数据驱动测试
│   ├── result/             # 结果收集器
│   ├── websocket/          # WebSocket 实时推送
│   └── utils/              # 工具函数
├── examples/               # 示例 YAML 用例
├── docs/                   # 项目文档
├── tests/                  # 单元测试
├── pyproject.toml
├── pypi_publish.sh
├── CHANGELOG.md
└── README.md
```

### 2.2 核心数据流

```
YAML 文件 → Parser(解析+校验) → CaseModel(数据模型) → Runner(编排执行)
                                                          │
                                    ┌──────────────────────┤
                                    ▼                      ▼
                              Executor(请求)          DataDriven(数据驱动)
                                    │                      │
                              ┌─────┼─────┐                ▼
                              ▼     ▼     ▼          循环执行每组数据
                          Extractor  Validator  DB       │
                              │     │     │            │
                              ▼     ▼     ▼            ▼
                          变量池 ← 提取结果          合并结果
                                    │
                                    ▼
                              ResultCollector(结果收集)
                                    │
                              ┌─────┼─────┐
                              ▼     ▼     ▼
                            JSON  HTML  Allure  Text
```

### 2.3 依赖库

| 库名 | 用途 |
|------|------|
| click | CLI 框架 |
| pyyaml | YAML 解析 |
| pydantic | 数据模型校验 |
| requests | HTTP 请求 |
| jsonpath-ng | JSONPath 表达式求值 |
| rich | 终端美化输出 (text 报告) |
| pymysql | MySQL 数据库连接 |
| psycopg2-binary | PostgreSQL 数据库连接 |
| allure-pytest | Allure 报告生成 |

---

## 3. 模块功能需求

### 3.1 核心数据模型 (apirun/core)

#### 3.1.1 YAML 顶层数据模型 - CaseModel

**文件**: `apirun/core/models.py`

基于 YAML 输入规范，定义以下 Pydantic 数据模型：

| 模型类 | 说明 | 关联规范 |
|--------|------|----------|
| `CaseModel` | YAML 文件顶层结构（config + teststeps + ddts） | YAML § 2 |
| `Config` | 场景配置（name/project_id/scenario_id/environment/variables/pre_sql/post_sql/csv_datasource） | YAML § 3 |
| `EnvironmentConfig` | 环境配置（name/base_url/variables） | YAML § 3.2 |
| `PrePostSql` | 前置/后置 SQL 配置（datasource/statements） | YAML § 3.3 |
| `StepDefinition` | 测试步骤通用结构（name/keyword_type/keyword_name/enabled） | YAML § 4 |
| `RequestStepParams` | HTTP 请求参数（method/url/headers/params/json/data/files/cookies/timeout） | YAML § 4.1.1 |
| `ExtractRule` | 变量提取规则（name/type/expression/scope/default/source_variable） | YAML § 4.1.2/4.3.1 |
| `ValidateRule` | 断言规则（target/expression/comparator/expected/message） | YAML § 4.1.3 |
| `AssertionParams` | 独立断言步骤参数（target/source_variable/expression/comparator/expected/message） | YAML § 4.2.1 |
| `DbParams` | 数据库操作参数（datasource/sql/extract/validate） | YAML § 4.4.1 |
| `CustomParams` | 自定义操作参数（parameters/extract） | YAML § 4.5.1 |
| `Ddts` | 数据驱动测试数据（name/parameters） | YAML § 5 |

**功能需求**:

- [x] FR-CORE-001: CaseModel 包含 config(必填)、teststeps(必填)、ddts(选填) 三个顶层字段
- [ ] FR-CORE-002: StepDefinition 需支持 5 种 keyword_type: request/assertion/extract/db/custom
- [ ] FR-CORE-003: StepDefinition 根据 keyword_type 关联不同的参数模型（request/assertion/extract/db/parameters）
- [ ] FR-CORE-004: StepDefinition 中 request 步骤可内嵌 extract 和 validate 字段
- [ ] FR-CORE-005: RequestStepParams 中 json/data/files 三者互斥
- [ ] FR-CORE-006: Config 中 csv_datasource 与 ddts 二选一

#### 3.1.2 JSON 输出数据模型

**文件**: `apirun/core/models.py` 或 `apirun/result/models.py`

基于 JSON 输出规范，定义以下输出数据模型：

| 模型类 | 说明 | 关联规范 |
|--------|------|----------|
| `ExecutionResult` | 顶层执行结果 | JSON § 2 |
| `ExecutionSummary` | 执行摘要统计 | JSON § 3 |
| `EnvironmentInfo` | 环境信息快照 | JSON § 4 |
| `StepResult` | 步骤执行结果（通用字段） | JSON § 5 |
| `RequestDetail` | HTTP 请求详情 | JSON § 5.1.1 |
| `ResponseDetail` | HTTP 响应详情 | JSON § 5.1.2 |
| `AssertionResult` | 断言结果 | JSON § 5.1.3 |
| `ExtractResult` | 提取结果 | JSON § 5.1.4 |
| `DbDetail` | 数据库操作详情 | JSON § 5.4.1 |
| `CustomDetail` | 自定义操作详情 | JSON § 5.5.1 |
| `DataDrivenResult` | 数据驱动整体结果 | JSON § 6.1 |
| `DataDrivenRun` | 单轮数据驱动结果 | JSON § 6.2 |
| `LogEntry` | 执行日志条目 | JSON § 7.1 |
| `ErrorInfo` | 错误信息 | JSON § 2.2 |

**功能需求**:

- [ ] FR-CORE-007: ExecutionResult 必须包含规范定义的全部 14 个顶层字段
- [ ] FR-CORE-008: ExecutionSummary 必须包含规范定义的全部 16 个统计字段
- [ ] FR-CORE-009: StepResult 必须包含 12 个通用字段，按 keyword_type 条件返回详情字段
- [ ] FR-CORE-010: 所有模型均可通过 `model_dump()` 生成可 JSON 序列化的字典

#### 3.1.3 场景运行器

**文件**: `apirun/core/runner.py`

场景运行器是引擎的核心编排模块，负责按顺序执行测试步骤。

**功能需求**:

- [x] FR-RUNNER-001: `load_case(yaml_path)` 加载并校验 YAML 文件，返回 CaseModel
- [x] FR-RUNNER-002: `run_case(case)` 按 teststeps 数组顺序依次执行步骤
- [ ] FR-RUNNER-003: 步骤 `enabled=false` 时跳过该步骤，status 标记为 `skipped`
- [ ] FR-RUNNER-004: 执行前运行 `pre_sql`，执行后运行 `post_sql`
- [ ] FR-RUNNER-005: 步骤执行异常时捕获错误，设置 status 为 `error`，不中断后续步骤
- [ ] FR-RUNNER-006: 根据所有步骤和断言结果计算场景整体 status（passed/failed/error）
- [ ] FR-RUNNER-007: 生成完整的 ExecutionResult 输出结构
- [ ] FR-RUNNER-008: 支持数据驱动模式（检测 ddts 或 csv_datasource 后循环执行）

---

### 3.2 YAML 解析器 (apirun/parser)

**文件**: `apirun/parser/yaml_parser.py`、`apirun/parser/csv_parser.py`

**功能需求**:

- [ ] FR-PARSER-001: 读取 YAML 文件并解析为 Python 字典
- [ ] FR-PARSER-002: 文件不存在时抛出 `FileNotFoundError`，错误码 `FILE_NOT_FOUND`
- [ ] FR-PARSER-003: YAML 语法错误时抛出 `ValueError`，错误码 `YAML_PARSE_ERROR`
- [ ] FR-PARSER-004: 通过 Pydantic 校验字典结构，校验失败时错误码 `YAML_VALIDATION_ERROR`
- [ ] FR-PARSER-005: 解析 CSV 数据驱动文件，第一行为表头，后续行为数据
- [ ] FR-PARSER-006: CSV 文件不存在时错误码 `CSV_FILE_NOT_FOUND`
- [ ] FR-PARSER-007: CSV 格式错误时错误码 `CSV_PARSE_ERROR`

---

### 3.3 测试执行器 (apirun/executor)

#### 3.3.1 HTTP 请求执行器

**文件**: `apirun/executor/request.py`

**功能需求**:

- [x] FR-EXEC-001: 支持 GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS 全部 HTTP 方法
- [x] FR-EXEC-002: 相对路径 URL 自动拼接 `environment.base_url`
- [x] FR-EXEC-003: 请求参数中的 `{{变量名}}` 替换为实际值
- [x] FR-EXEC-004: 支持 headers/params/json/data/files/cookies 全部参数类型
- [x] FR-EXEC-005: 支持 timeout/allow_redirects/verify 请求选项
- [x] FR-EXEC-006: 返回完整的 response 信息（status_code/headers/body/body_size/response_time/cookies）
- [x] FR-EXEC-007: 请求超时时返回错误码 `REQUEST_TIMEOUT`
- [x] FR-EXEC-008: 连接错误时返回错误码 `REQUEST_CONNECTION_ERROR`
- [ ] FR-EXEC-009: SSL 错误时返回错误码 `REQUEST_SSL_ERROR`
- [ ] FR-EXEC-010: 响应体为 JSON 时自动解析为 dict/list，非 JSON 时保留为字符串
- [ ] FR-EXEC-011: 变量替换需递归处理 headers/params/json/data 中的所有值

#### 3.3.2 数据库执行器

**文件**: `apirun/executor/db.py`

**功能需求**:

- [ ] FR-EXEC-DB-001: 通过 datasource 引用变量名查找数据库连接配置
- [ ] FR-EXEC-DB-002: 支持 MySQL (pymysql) 和 PostgreSQL (psycopg2) 两种数据库
- [ ] FR-EXEC-DB-003: SQL 语句中的 `{{变量名}}` 替换为实际值
- [ ] FR-EXEC-DB-004: 执行 SQL 查询并返回结果集（JSON 数组格式）
- [ ] FR-EXEC-DB-005: 返回 db_detail 信息（datasource/sql/sql_rendered/row_count/columns/rows/execution_time）
- [ ] FR-EXEC-DB-006: 数据库连接失败时错误码 `DB_CONNECTION_ERROR`
- [ ] FR-EXEC-DB-007: SQL 执行错误时错误码 `DB_QUERY_ERROR`
- [ ] FR-EXEC-DB-008: 数据源未找到时错误码 `DB_DATASOURCE_NOT_FOUND`

#### 3.3.3 自定义关键字执行器

**文件**: `apirun/executor/custom.py`

**功能需求**:

- [ ] FR-EXEC-CUSTOM-001: 根据 keyword_name 查找自定义关键字函数
- [ ] FR-EXEC-CUSTOM-002: 将 parameters 作为参数传入关键字函数
- [ ] FR-EXEC-CUSTOM-003: 返回 custom_detail 信息（keyword_name/parameters_input/return_value/execution_time）
- [ ] FR-EXEC-CUSTOM-004: 关键字未找到时错误码 `KEYWORD_NOT_FOUND`
- [ ] FR-EXEC-CUSTOM-005: 关键字执行异常时错误码 `KEYWORD_EXECUTION_ERROR`

---

### 3.4 断言验证引擎 (apirun/validation)

**文件**: `apirun/validation/validator.py`、`apirun/validation/comparators.py`

**功能需求**:

- [ ] FR-VALID-001: 支持 6 种断言目标 (target): json/header/cookie/status_code/response_time/env_variable
- [ ] FR-VALID-002: 支持 17 种比较器 (comparator):

| 比较器 | 说明 |
|--------|------|
| `eq` | 等于 |
| `neq` | 不等于 |
| `gt` | 大于 |
| `gte` | 大于等于 |
| `lt` | 小于 |
| `lte` | 小于等于 |
| `contains` | 包含（字符串/列表） |
| `not_contains` | 不包含 |
| `startswith` | 以...开头 |
| `endswith` | 以...结尾 |
| `matches` | 正则匹配 |
| `type_match` | 类型匹配（int/str/list/dict/bool/null） |
| `length_eq` | 长度等于 |
| `length_gt` | 长度大于 |
| `length_lt` | 长度小于 |
| `is_null` | 为 null |
| `is_not_null` | 不为 null |

- [ ] FR-VALID-003: 根据 target 类型从不同数据源提取实际值:
  - `json`: 通过 JSONPath 从响应体中提取
  - `header`: 从响应头中按名称提取
  - `cookie`: 从响应 Cookie 中按名称提取
  - `status_code`: 直接取响应状态码
  - `response_time`: 直接取响应耗时（毫秒）
  - `env_variable`: 从变量池中按名称提取
- [ ] FR-VALID-004: 返回 AssertionResult 结构（target/expression/comparator/expected/actual/status/message）
- [ ] FR-VALID-005: 断言失败时 status 为 `failed`，成功时为 `passed`
- [ ] FR-VALID-006: 支持 expected 中的 `{{变量名}}` 引用替换
- [ ] FR-VALID-007: 断言失败时返回自定义 message 或默认消息
- [ ] FR-VALID-008: 数据库查询结果使用 JSONPath 进行断言（`$.length` 代表结果集行数）

---

### 3.5 变量提取器 (apirun/extractor)

**文件**: `apirun/extractor/extractor.py`

**功能需求**:

- [ ] FR-EXTRACT-001: 支持 3 种提取来源 (type): json/header/cookie
- [ ] FR-EXTRACT-002: `json` 类型使用 JSONPath 表达式从响应体中提取值
- [ ] FR-EXTRACT-003: `header` 类型按名称从响应头中提取值
- [ ] FR-EXTRACT-004: `cookie` 类型按名称从响应 Cookie 中提取值
- [ ] FR-EXTRACT-005: 支持 `scope` 作用域: global（全局变量）/ environment（环境变量）
- [ ] FR-EXTRACT-006: 提取失败时使用 `default` 默认值，无默认值时错误码 `EXTRACT_FAILED`
- [ ] FR-EXTRACT-007: 返回 ExtractResult 结构（name/type/expression/scope/value/status）
- [ ] FR-EXTRACT-008: 提取的变量写入变量池，后续步骤可通过 `{{变量名}}` 引用
- [ ] FR-EXTRACT-009: 支持 source_variable 指定数据源（默认为上一个 request 步骤的响应）
- [ ] FR-EXTRACT-010: 支持从数据库查询结果中提取变量（db_result 类型）

---

### 3.6 数据驱动测试 (apirun/data_driven)

**文件**: `apirun/data_driven/driver.py`

**功能需求**:

- [ ] FR-DDT-001: 支持 YAML 内联数据驱动（ddts 字段）
- [ ] FR-DDT-002: 支持 CSV 文件数据驱动（csv_datasource 字段）
- [ ] FR-DDT-003: 每一行数据等价于一个独立的用例执行
- [ ] FR-DDT-004: 数据集中的字段通过 `{{字段名}}` 在测试步骤中引用
- [ ] FR-DDT-005: 返回 DataDrivenResult 结构（enabled/source/dataset_name/total_runs/passed_runs/failed_runs/pass_rate/runs）
- [ ] FR-DDT-006: 每轮 runs 包含 run_index/parameters/status/duration/summary/steps
- [ ] FR-DDT-007: source 标识数据来源: `yaml_inline` 或 `csv_file`
- [ ] FR-DDT-008: 汇总所有轮次的结果到顶层 summary 和 status

---

### 3.7 结果收集器 (apirun/result)

**文件**: `apirun/result/json_reporter.py`、`apirun/result/text_reporter.py`、`apirun/result/allure_reporter.py`、`apirun/result/html_reporter.py`

#### 3.7.1 JSON 报告 (-O json)

**功能需求**:

- [ ] FR-RESULT-001: 输出完整的 JSON 结构至 stdout，格式符合 JSON 输出规范
- [ ] FR-RESULT-002: 输出必须可被 `json.loads()` 解析
- [ ] FR-RESULT-003: 时间字段使用 ISO 8601 格式，含时区偏移
- [ ] FR-RESULT-004: ensure_ascii=False，支持中文字符
- [ ] FR-RESULT-005: 引擎级异常时输出 error 对象，status 为 `error`

#### 3.7.2 Text 报告 (-O text)

**功能需求**:

- [ ] FR-RESULT-006: 使用 rich 库渲染终端美化输出
- [ ] FR-RESULT-007: 展示场景名称、执行状态、耗时、步骤概览
- [ ] FR-RESULT-008: 通过 -v/--verbose 参数控制详细程度

#### 3.7.3 Allure 报告 (-O allure)

**功能需求**:

- [ ] FR-RESULT-009: 生成 Allure 兼容的 JSON 结果文件到 --allure-dir 目录
- [ ] FR-RESULT-010: 每个步骤映射为 Allure 的 Step
- [ ] FR-RESULT-011: 断言结果映射为 Allure 的 Attachment

#### 3.7.4 HTML 报告 (-O html)

**功能需求**:

- [ ] FR-RESULT-012: 生成自包含的 HTML 报告文件到 --html-dir 目录
- [ ] FR-RESULT-013: 报告包含执行摘要、步骤详情、断言结果、响应数据

---

### 3.8 WebSocket 实时推送 (apirun/websocket)

**文件**: `apirun/websocket/publisher.py`

**功能需求**:

- [ ] FR-WS-001: 支持在平台集成模式下通过 WebSocket 实时推送执行进度
- [ ] FR-WS-002: 推送事件包括: 场景开始、步骤开始、步骤完成、断言结果、场景完成
- [ ] FR-WS-003: 推送消息格式包含 event_type、step_index、status、timestamp 等字段
- [ ] FR-WS-004: WebSocket 连接失败时不影响用例执行（降级为无推送模式）

---

### 3.9 CLI 命令行接口 (apirun/cli)

**文件**: `apirun/cli.py`

**功能需求**:

- [x] FR-CLI-001: 命令名为 `sisyphus`
- [x] FR-CLI-002: `--case` 参数指定 YAML 文件路径（必填）
- [x] FR-CLI-003: `-O / --output-format` 参数指定输出格式: text/json/allure/html（默认 text）
- [x] FR-CLI-004: `--allure-dir` 参数指定 Allure 报告输出目录
- [x] FR-CLI-005: `--html-dir` 参数指定 HTML 报告输出目录
- [x] FR-CLI-006: `-v / --verbose` 参数启用详细输出
- [ ] FR-CLI-007: YAML 文件不存在时 exit code 1，stderr 输出错误信息
- [ ] FR-CLI-008: 执行成功时 exit code 0
- [ ] FR-CLI-009: 执行失败（有断言失败）时 exit code 0，status 字段体现失败
- [ ] FR-CLI-010: 引擎异常时 exit code 1

---

### 3.10 工具函数 (apirun/utils)

**文件**: `apirun/utils/variables.py`、`apirun/utils/functions.py`

#### 3.10.1 变量替换工具

**功能需求**:

- [ ] FR-UTIL-001: `render_template(template, variables)` 替换字符串中的 `{{变量名}}`
- [ ] FR-UTIL-002: 递归替换 dict/list/str 中的所有变量引用
- [ ] FR-UTIL-003: 变量未找到时错误码 `VARIABLE_NOT_FOUND`
- [ ] FR-UTIL-004: 变量渲染失败时错误码 `VARIABLE_RENDER_ERROR`

#### 3.10.2 内置函数

**功能需求**:

- [ ] FR-UTIL-005: `{{random(n)}}` 生成 n 位随机字符串
- [ ] FR-UTIL-006: `{{random_uuid()}}` 生成 UUID
- [ ] FR-UTIL-007: `{{timestamp()}}` 返回当前时间戳（秒）
- [ ] FR-UTIL-008: `{{timestamp_ms()}}` 返回当前时间戳（毫秒）
- [ ] FR-UTIL-009: `{{datetime(fmt)}}` 返回格式化的当前时间

---

### 3.11 安全与防护 (apirun/security)

**文件**: `apirun/security/`

**功能需求**:

- [x] FR-SEC-001: 提供 SQL 防注入机制 (`sql_validator.py`)，自动拦截针对数据库层的恶意 Payload 攻击
- [x] FR-SEC-002: 提供正则表达的安全性检验 (`regex_validator.py`)，避免 ReDoS (正则表达式拒绝服务)
- [x] FR-SEC-003: 大体积 Payload 防护 (`size_limiter.py`)，当响应体体积超过安全阈值自动截断或丢弃，保护引擎内存
- [x] FR-SEC-004: 敏感日志自动脱敏功能 (`log_sanitizer.py`)，保障输出报告或日志信息内涉及如认证信息的安全

---

### 3.12 健壮性机制 (Robustness)

**文件**: `apirun/utils/retry.py`、`apirun/utils/timeout.py` 等

**功能需求**:

- [x] FR-ROB-001: 请求容错重试，建立基础重试 (`retry.py`)，采用指数退避算法控制请求重做
- [x] FR-ROB-002: 全局级发包超时 (`timeout.py`)，应对外部服务极慢带来的挂起或假死，保障引擎整体释放资源
- [x] FR-ROB-003: 并发与多线程处理健壮性，引入相关压测模块支撑评估

---

## 4. 变量系统

### 4.1 变量池

引擎运行时维护一个变量池（dict），按以下优先级（从高到低）解析变量引用:

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | 数据驱动变量 | ddts / CSV 中定义的变量 |
| 2 | 步骤提取变量 | 通过 extract 在步骤执行后提取的变量 |
| 3 | 场景级变量 | config.variables 中定义的变量 |
| 4 | 环境变量 | config.environment.variables 中定义的变量 |
| 5 | 全局参数函数 | 系统设置中注册的全局参数工具函数 |

### 4.2 变量作用域

| 作用域 | 说明 |
|--------|------|
| `global` | 全局变量，在整个场景执行过程中可用 |
| `environment` | 环境变量，仅在当前环境中可用 |

### 4.3 变量引用位置

变量 `{{变量名}}` 可在以下位置使用:

- URL 路径
- 请求 Headers
- 请求 Params (Query String)
- 请求体 JSON/Form Data
- SQL 语句
- 断言预期值 (expected)
- 提取表达式

---

## 5. 错误处理规范

### 5.1 错误传播策略

| 错误级别 | 处理方式 |
|----------|----------|
| 引擎级错误 | 立即终止执行，返回 error 对象，status 为 `error` |
| 步骤级错误 | 记录错误，步骤 status 为 `error`，继续执行后续步骤 |
| 断言失败 | 记录失败，步骤 status 为 `failed`，继续执行后续步骤 |
| 提取失败 | 使用默认值或记录失败，继续执行 |

### 5.2 错误输出格式

所有错误统一使用以下结构:

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读的错误描述",
  "detail": "详细堆栈信息（仅调试模式）"
}
```

---

## 6. 开发任务清单

### 6.1 核心模块

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-001 | 完善 CaseModel 数据模型（支持全部 5 种 keyword_type） | `[ ]` | P0 |
| EG-002 | 完善 CLI 入口（集成所有 Reporter） | `[~]` | P0 |
| EG-003 | 定义 JSON 输出数据模型（ExecutionResult/StepResult 等） | `[ ]` | P0 |

### 6.2 解析器

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-004 | YAML 解析器（文件读取 + Pydantic 校验） | `[~]` | P0 |
| EG-005 | CSV 数据驱动文件解析器 | `[ ]` | P1 |

### 6.3 执行器

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-006 | HTTP 请求执行器（全参数支持） | `[~]` | P0 |
| EG-007 | 变量替换引擎（递归替换 + 内置函数） | `[ ]` | P0 |
| EG-008 | 数据库执行器（MySQL + PostgreSQL） | `[ ]` | P1 |
| EG-009 | 自定义关键字执行器 | `[ ]` | P1 |

### 6.4 断言验证

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-010 | 断言验证引擎（17 种 comparator） | `[ ]` | P0 |
| EG-011 | JSONPath 表达式求值 | `[ ]` | P0 |
| EG-012 | 数据库结果断言 | `[ ]` | P1 |

### 6.5 变量提取

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-013 | 变量提取器（json/header/cookie） | `[ ]` | P0 |
| EG-014 | 变量池管理（优先级 + 作用域） | `[ ]` | P0 |

### 6.6 数据驱动

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-015 | YAML 内联数据驱动执行 | `[ ]` | P1 |
| EG-016 | CSV 文件数据驱动执行 | `[ ]` | P1 |

### 6.7 结果收集

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-017 | JSON 报告输出 | `[~]` | P0 |
| EG-018 | Text 报告输出（rich 美化） | `[ ]` | P1 |
| EG-019 | Allure 报告输出 | `[ ]` | P2 |
| EG-020 | HTML 报告输出 | `[ ]` | P2 |

### 6.8 WebSocket

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-021 | WebSocket 实时推送（平台集成模式） | `[ ]` | P2 |

### 6.9 场景运行器

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-022 | 场景运行器重构（集成所有模块） | `[ ]` | P0 |
| EG-023 | 前置/后置 SQL 执行 | `[ ]` | P1 |
| EG-024 | 执行日志收集 (logs) | `[ ]` | P1 |

### 6.10 工具函数

| 编号 | 任务 | 状态 | 优先级 |
|------|------|------|--------|
| EG-025 | 变量替换工具（递归模板渲染） | `[ ]` | P0 |
| EG-026 | 内置函数实现（random/uuid/timestamp/datetime） | `[ ]` | P0 |
| EG-027 | 全局参数函数调用 | `[ ]` | P1 |

---

## 附录 A: 枚举值定义

### keyword_type

| 值 | 说明 |
|----|------|
| `request` | HTTP 请求 |
| `assertion` | 独立断言 |
| `extract` | 独立变量提取 |
| `db` | 数据库操作 |
| `custom` | 自定义关键字 |

### status (场景/步骤)

| 值 | 说明 |
|----|------|
| `passed` | 全部通过 |
| `failed` | 存在失败 |
| `error` | 发生异常 |
| `skipped` | 被跳过 |

### comparator

| 值 | 说明 |
|----|------|
| `eq` | 等于 |
| `neq` | 不等于 |
| `gt` | 大于 |
| `gte` | 大于等于 |
| `lt` | 小于 |
| `lte` | 小于等于 |
| `contains` | 包含 |
| `not_contains` | 不包含 |
| `startswith` | 以...开头 |
| `endswith` | 以...结尾 |
| `matches` | 正则匹配 |
| `type_match` | 类型匹配 |
| `length_eq` | 长度等于 |
| `length_gt` | 长度大于 |
| `length_lt` | 长度小于 |
| `is_null` | 为 null |
| `is_not_null` | 不为 null |

### priority

| 值 | 说明 |
|----|------|
| `P0` | 最高优先级 |
| `P1` | 高优先级 |
| `P2` | 中优先级（默认） |
| `P3` | 低优先级 |

### extract.type

| 值 | 说明 |
|----|------|
| `json` | 从 JSON 响应体提取（JSONPath） |
| `header` | 从响应头提取 |
| `cookie` | 从响应 Cookie 提取 |

### extract.scope

| 值 | 说明 |
|----|------|
| `global` | 全局变量（默认） |
| `environment` | 环境变量 |

---

## 附录 B: 错误码定义

### 引擎级错误

| 错误码 | 说明 |
|--------|------|
| `YAML_PARSE_ERROR` | YAML 文件解析失败 |
| `YAML_VALIDATION_ERROR` | YAML 结构校验失败 |
| `FILE_NOT_FOUND` | YAML 文件不存在 |
| `CSV_PARSE_ERROR` | CSV 数据源文件解析失败 |
| `CSV_FILE_NOT_FOUND` | CSV 数据源文件不存在 |
| `ENGINE_INTERNAL_ERROR` | 引擎内部错误 |
| `TIMEOUT_ERROR` | 引擎执行整体超时 |

### 步骤级错误

| 错误码 | 说明 |
|--------|------|
| `REQUEST_TIMEOUT` | HTTP 请求超时 |
| `REQUEST_CONNECTION_ERROR` | HTTP 连接错误 |
| `REQUEST_SSL_ERROR` | SSL 证书验证失败 |
| `ASSERTION_FAILED` | 断言失败 |
| `EXTRACT_FAILED` | 变量提取失败 |
| `DB_CONNECTION_ERROR` | 数据库连接失败 |
| `DB_QUERY_ERROR` | SQL 执行错误 |
| `DB_DATASOURCE_NOT_FOUND` | 数据源引用未找到 |
| `KEYWORD_NOT_FOUND` | 关键字未找到 |
| `KEYWORD_EXECUTION_ERROR` | 自定义关键字执行异常 |
| `VARIABLE_NOT_FOUND` | 变量引用未找到 |
| `VARIABLE_RENDER_ERROR` | 变量渲染失败 |

---

> **文档结束** — sisyphus-api-engine 需求规格说明书 v1.0
