# sisyphus-api-engine JSON 输出规范

> **文档版本**: v1.0
> **创建日期**: 2026-02-25
> **文档性质**: 接口规范文档（供后端 & 前端开发人员使用）
> **适用组件**: sisyphus-api-engine 核心执行器

---

## 目录

- [1. 概述](#1-概述)
- [2. 顶层响应结构](#2-顶层响应结构)
- [3. summary — 执行摘要](#3-summary--执行摘要)
- [4. environment — 环境信息](#4-environment--环境信息)
- [5. steps — 步骤执行详情](#5-steps--步骤执行详情)
  - [5.1 request 步骤详情](#51-request-步骤详情)
  - [5.2 assertion 步骤详情](#52-assertion-步骤详情)
  - [5.3 extract 步骤详情](#53-extract-步骤详情)
  - [5.4 db 步骤详情](#54-db-步骤详情)
  - [5.5 custom 步骤详情](#55-custom-步骤详情)
- [6. data_driven — 数据驱动结果](#6-data_driven--数据驱动结果)
- [7. logs — 执行日志](#7-logs--执行日志)
- [8. 完整响应示例](#8-完整响应示例)
- [9. 字段速查表](#9-字段速查表)
- [10. 错误码定义](#10-错误码定义)

---

## 1. 概述

当通过 `-O json` 模式调用 sisyphus-api-engine 时，引擎将执行结果以 JSON 格式输出至标准输出（stdout），供后端服务捕获并返回前端展示。

**调用方式**:

```bash
sisyphus --case temp/<uuid>.yaml -O json
```

**输出方式**: 标准输出（stdout），一次性完整 JSON 输出。

---

## 2. 顶层响应结构

```json
{
  "execution_id": "exec-uuid-001",
  "scenario_id": "scen-uuid-001",
  "scenario_name": "用户注册 → 登录 → 查看信息",
  "project_id": "proj-uuid-001",
  "status": "passed",
  "start_time": "2026-02-25T22:30:00.000+08:00",
  "end_time": "2026-02-25T22:30:05.320+08:00",
  "duration": 5320,
  "summary": { ... },
  "environment": { ... },
  "steps": [ ... ],
  "data_driven": { ... },
  "variables": { ... },
  "logs": [ ... ],
  "error": null
}
```

### 顶层字段定义

| 字段 | 类型 | 是否必返 | 说明 |
|------|------|----------|------|
| `execution_id` | String (UUID) | ✅ 必返 | 本次执行的唯一 ID，由引擎自动生成 |
| `scenario_id` | String (UUID) | ✅ 必返 | 场景 ID（来源于 YAML `config.scenario_id`） |
| `scenario_name` | String | ✅ 必返 | 场景名称（来源于 YAML `config.name`） |
| `project_id` | String (UUID) | ✅ 必返 | 项目 ID（来源于 YAML `config.project_id`） |
| `status` | String (Enum) | ✅ 必返 | 场景整体执行状态，见 § 2.1 |
| `start_time` | String (ISO 8601) | ✅ 必返 | 执行开始时间，含时区偏移 |
| `end_time` | String (ISO 8601) | ✅ 必返 | 执行结束时间，含时区偏移 |
| `duration` | Integer | ✅ 必返 | 总执行耗时（毫秒） |
| `summary` | Object | ✅ 必返 | 执行摘要统计，见 § 3 |
| `environment` | Object | ✅ 必返 | 运行环境信息，见 § 4 |
| `steps` | Array\<Object\> | ✅ 必返 | 步骤执行详情列表，见 § 5 |
| `data_driven` | Object \| null | ✅ 必返 | 数据驱动运行结果。非数据驱动场景返回 `null`，见 § 6 |
| `variables` | Object (Dict) | ✅ 必返 | 执行结束后的变量快照（所有提取 / 设置的变量最终值） |
| `logs` | Array\<Object\> | ✅ 必返 | 执行日志（按时间顺序），见 § 7 |
| `error` | Object \| null | ✅ 必返 | 顶层错误信息。正常执行时为 `null`；发生引擎级异常时返回错误对象 |

### 2.1 status 枚举值

| 值 | 说明 |
|----|------|
| `passed` | 所有步骤和断言均通过 |
| `failed` | 存在步骤执行失败或断言未通过 |
| `error` | 引擎执行过程中发生异常（如 YAML 解析错误、网络不可达等） |
| `skipped` | 场景被跳过（数据驱动中某组数据被标记跳过等） |

### 2.2 error 对象定义

当 `status` 为 `error` 时，`error` 字段返回以下结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | String | 错误码，见 § 10 |
| `message` | String | 错误描述信息 |
| `detail` | String \| null | 详细错误堆栈（仅调试模式） |

---

## 3. summary — 执行摘要

```json
{
  "summary": {
    "total_steps": 4,
    "passed_steps": 3,
    "failed_steps": 1,
    "skipped_steps": 0,
    "error_steps": 0,
    "total_assertions": 8,
    "passed_assertions": 7,
    "failed_assertions": 1,
    "pass_rate": 87.5,
    "total_requests": 3,
    "total_db_operations": 1,
    "total_extractions": 2,
    "avg_response_time": 256,
    "max_response_time": 520,
    "min_response_time": 85,
    "total_data_driven_runs": 0
  }
}
```

### 3.1 summary 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_steps` | Integer | 步骤总数 |
| `passed_steps` | Integer | 通过的步骤数 |
| `failed_steps` | Integer | 失败的步骤数 |
| `skipped_steps` | Integer | 跳过的步骤数 |
| `error_steps` | Integer | 异常的步骤数 |
| `total_assertions` | Integer | 断言总数（含内嵌 validate + 独立 assertion 步骤） |
| `passed_assertions` | Integer | 通过的断言数 |
| `failed_assertions` | Integer | 失败的断言数 |
| `pass_rate` | Float | 断言通过率（百分比，保留 1 位小数） |
| `total_requests` | Integer | HTTP 请求总数 |
| `total_db_operations` | Integer | 数据库操作总数 |
| `total_extractions` | Integer | 变量提取总数 |
| `avg_response_time` | Integer | 平均响应时间（毫秒），仅统计 HTTP 请求 |
| `max_response_time` | Integer | 最大响应时间（毫秒） |
| `min_response_time` | Integer | 最小响应时间（毫秒） |
| `total_data_driven_runs` | Integer | 数据驱动轮次总数，非数据驱动时为 `0` |

---

## 4. environment — 环境信息

```json
{
  "environment": {
    "name": "测试环境",
    "base_url": "https://api-test.example.com",
    "variables": {
      "env_token": "",
      "env_host": "api-test.example.com"
    }
  }
}
```

### 4.1 environment 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | String | 环境名称 |
| `base_url` | String | 前置 URL |
| `variables` | Object (Dict) | 环境变量快照（执行结束后的最终值） |

---

## 5. steps — 步骤执行详情

`steps` 是一个数组，每个元素代表一个步骤的执行结果。所有步骤共享以下**通用字段**：

| 字段 | 类型 | 是否必返 | 说明 |
|------|------|----------|------|
| `step_index` | Integer | ✅ 必返 | 步骤序号，从 `0` 开始 |
| `name` | String | ✅ 必返 | 步骤名称 |
| `keyword_type` | String (Enum) | ✅ 必返 | 关键字类型：`request` / `assertion` / `extract` / `db` / `custom` |
| `keyword_name` | String | ✅ 必返 | 关键字函数名称 |
| `status` | String (Enum) | ✅ 必返 | 步骤执行状态：`passed` / `failed` / `error` / `skipped` |
| `start_time` | String (ISO 8601) | ✅ 必返 | 步骤开始时间 |
| `end_time` | String (ISO 8601) | ✅ 必返 | 步骤结束时间 |
| `duration` | Integer | ✅ 必返 | 步骤耗时（毫秒） |
| `error` | Object \| null | ✅ 必返 | 步骤级错误信息（同 § 2.2），正常时为 `null` |
| `request_detail` | Object \| null | 条件必返 | HTTP 请求详情，仅 `keyword_type: request` 时返回 |
| `response_detail` | Object \| null | 条件必返 | HTTP 响应详情，仅 `keyword_type: request` 时返回 |
| `assertion_results` | Array\<Object\> \| null | 条件必返 | 断言结果列表，含 validate 的步骤返回 |
| `extract_results` | Array\<Object\> \| null | 条件必返 | 提取结果列表，含 extract 的步骤返回 |
| `db_detail` | Object \| null | 条件必返 | 数据库操作详情，仅 `keyword_type: db` 时返回 |
| `custom_detail` | Object \| null | 条件必返 | 自定义操作详情，仅 `keyword_type: custom` 时返回 |

---

### 5.1 request 步骤详情

```json
{
  "step_index": 0,
  "name": "用户注册",
  "keyword_type": "request",
  "keyword_name": "http_request",
  "status": "passed",
  "start_time": "2026-02-25T22:30:00.000+08:00",
  "end_time": "2026-02-25T22:30:00.320+08:00",
  "duration": 320,
  "error": null,
  "request_detail": {
    "method": "POST",
    "url": "https://api-test.example.com/api/v1/auth/register",
    "headers": {
      "Content-Type": "application/json",
      "User-Agent": "sisyphus-api-engine/1.0"
    },
    "params": null,
    "body": {
      "email": "testuser@example.com",
      "password": "Test@123456",
      "nickname": "测试用户_a3b5c7"
    },
    "body_type": "json",
    "timeout": 30,
    "allow_redirects": true,
    "verify_ssl": true
  },
  "response_detail": {
    "status_code": 201,
    "headers": {
      "Content-Type": "application/json",
      "X-Request-ID": "req-uuid-001"
    },
    "body": {
      "code": 0,
      "message": "注册成功",
      "data": {
        "id": "user-uuid-001",
        "email": "testuser@example.com",
        "nickname": "测试用户_a3b5c7"
      }
    },
    "body_size": 256,
    "response_time": 315,
    "cookies": {
      "SESSIONID": "sess-uuid-001"
    }
  },
  "extract_results": [
    {
      "name": "user_id",
      "type": "json",
      "expression": "$.data.id",
      "scope": "global",
      "value": "user-uuid-001",
      "status": "success"
    }
  ],
  "assertion_results": [
    {
      "target": "status_code",
      "expression": null,
      "comparator": "eq",
      "expected": 201,
      "actual": 201,
      "status": "passed",
      "message": null
    },
    {
      "target": "json",
      "expression": "$.code",
      "comparator": "eq",
      "expected": 0,
      "actual": 0,
      "status": "passed",
      "message": null
    }
  ],
  "db_detail": null,
  "custom_detail": null
}
```

#### 5.1.1 request_detail 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `method` | String | HTTP 请求方法 |
| `url` | String | 完整请求 URL（已拼接 `base_url`，已替换变量） |
| `headers` | Object (Dict) | 实际发送的请求头（已替换变量） |
| `params` | Object (Dict) \| null | URL 查询参数 |
| `body` | Any | 实际发送的请求体（已替换变量）。根据 `body_type` 不同，类型为 Object / String / null |
| `body_type` | String (Enum) | 请求体类型：`json` / `form` / `multipart` / `raw` / `none` |
| `timeout` | Integer | 请求超时时间（秒） |
| `allow_redirects` | Boolean | 是否允许重定向 |
| `verify_ssl` | Boolean | 是否验证 SSL |

#### 5.1.2 response_detail 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `status_code` | Integer | HTTP 响应状态码 |
| `headers` | Object (Dict) | 响应头 |
| `body` | Any | 响应体。JSON 响应解析为 Object；非 JSON 时为 String |
| `body_size` | Integer | 响应体大小（字节） |
| `response_time` | Integer | 响应耗时（毫秒） |
| `cookies` | Object (Dict) | 响应中设置的 Cookie |

#### 5.1.3 assertion_results 字段定义

每个断言结果包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `target` | String (Enum) | 断言对象：`json` / `header` / `cookie` / `status_code` / `response_time` / `env_variable` |
| `expression` | String \| null | 提取表达式。`status_code` / `response_time` 时为 `null` |
| `comparator` | String (Enum) | 判断符号 |
| `expected` | Any | 预期值（已替换变量后的值） |
| `actual` | Any | 实际值 |
| `status` | String (Enum) | 断言结果：`passed` / `failed` |
| `message` | String \| null | 断言失败时的提示消息。成功时为 `null`；失败时返回自定义消息或默认消息 |

#### 5.1.4 extract_results 字段定义

每个提取结果包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | String | 提取的变量名称 |
| `type` | String (Enum) | 提取来源：`json` / `header` / `cookie` |
| `expression` | String | 提取表达式 |
| `scope` | String (Enum) | 变量作用域：`global` / `environment` |
| `value` | Any | 提取到的值 |
| `status` | String (Enum) | 提取结果：`success` / `failed` |

---

### 5.2 assertion 步骤详情

独立断言步骤的响应结构：

```json
{
  "step_index": 2,
  "name": "验证用户 ID 格式",
  "keyword_type": "assertion",
  "keyword_name": "json_assertion",
  "status": "passed",
  "start_time": "2026-02-25T22:30:01.200+08:00",
  "end_time": "2026-02-25T22:30:01.201+08:00",
  "duration": 1,
  "error": null,
  "request_detail": null,
  "response_detail": null,
  "assertion_results": [
    {
      "target": "json",
      "expression": "$.data.user_id",
      "comparator": "matches",
      "expected": "^[0-9a-f]{8}-.*$",
      "actual": "user-uuid-001",
      "status": "passed",
      "message": null
    }
  ],
  "extract_results": null,
  "db_detail": null,
  "custom_detail": null
}
```

---

### 5.3 extract 步骤详情

独立变量提取步骤的响应结构：

```json
{
  "step_index": 1,
  "name": "提取登录 Token",
  "keyword_type": "extract",
  "keyword_name": "json_extract",
  "status": "passed",
  "start_time": "2026-02-25T22:30:00.800+08:00",
  "end_time": "2026-02-25T22:30:00.801+08:00",
  "duration": 1,
  "error": null,
  "request_detail": null,
  "response_detail": null,
  "assertion_results": null,
  "extract_results": [
    {
      "name": "auth_token",
      "type": "json",
      "expression": "$.data.token",
      "scope": "global",
      "value": "eyJhbGciOiJIUzI1NiIs...",
      "status": "success"
    },
    {
      "name": "session_cookie",
      "type": "cookie",
      "expression": "SESSIONID",
      "scope": "environment",
      "value": "sess-uuid-001",
      "status": "success"
    }
  ],
  "db_detail": null,
  "custom_detail": null
}
```

---

### 5.4 db 步骤详情

```json
{
  "step_index": 3,
  "name": "数据库验证用户记录",
  "keyword_type": "db",
  "keyword_name": "db_operation",
  "status": "passed",
  "start_time": "2026-02-25T22:30:02.000+08:00",
  "end_time": "2026-02-25T22:30:02.150+08:00",
  "duration": 150,
  "error": null,
  "request_detail": null,
  "response_detail": null,
  "assertion_results": [
    {
      "target": "db_result",
      "expression": "$[0].email",
      "comparator": "eq",
      "expected": "testuser@example.com",
      "actual": "testuser@example.com",
      "status": "passed",
      "message": null
    },
    {
      "target": "db_result",
      "expression": "$.length",
      "comparator": "eq",
      "expected": 1,
      "actual": 1,
      "status": "passed",
      "message": null
    }
  ],
  "extract_results": [
    {
      "name": "db_user_id",
      "type": "db_result",
      "expression": "$[0].id",
      "scope": "global",
      "value": "user-uuid-001",
      "status": "success"
    }
  ],
  "db_detail": {
    "datasource": "db_main",
    "sql": "SELECT id, email, status FROM users WHERE email = 'testuser@example.com' LIMIT 1;",
    "sql_rendered": "SELECT id, email, status FROM users WHERE email = 'testuser@example.com' LIMIT 1;",
    "row_count": 1,
    "columns": ["id", "email", "status"],
    "rows": [
      {
        "id": "user-uuid-001",
        "email": "testuser@example.com",
        "status": "active"
      }
    ],
    "execution_time": 45
  },
  "custom_detail": null
}
```

#### 5.4.1 db_detail 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `datasource` | String | 数据源引用变量名 |
| `sql` | String | 原始 SQL 语句（含 `{{变量名}}` 占位符） |
| `sql_rendered` | String | 渲染后的 SQL 语句（变量已替换为实际值） |
| `row_count` | Integer | 查询结果行数 |
| `columns` | Array\<String\> | 查询结果列名列表 |
| `rows` | Array\<Object\> | 查询结果行数据（JSON 数组） |
| `execution_time` | Integer | SQL 执行耗时（毫秒） |

---

### 5.5 custom 步骤详情

```json
{
  "step_index": 4,
  "name": "生成唯一业务编号",
  "keyword_type": "custom",
  "keyword_name": "generate_business_code",
  "status": "passed",
  "start_time": "2026-02-25T22:30:03.000+08:00",
  "end_time": "2026-02-25T22:30:03.005+08:00",
  "duration": 5,
  "error": null,
  "request_detail": null,
  "response_detail": null,
  "assertion_results": null,
  "extract_results": [
    {
      "name": "business_code",
      "type": "json",
      "expression": "$.result",
      "scope": "global",
      "value": "BIZ202602251230",
      "status": "success"
    }
  ],
  "db_detail": null,
  "custom_detail": {
    "keyword_name": "generate_business_code",
    "parameters_input": {
      "prefix": "BIZ",
      "length": 12,
      "include_timestamp": true
    },
    "return_value": {
      "result": "BIZ202602251230",
      "generated_at": "2026-02-25T22:30:03.003+08:00"
    },
    "execution_time": 3
  }
}
```

#### 5.5.1 custom_detail 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `keyword_name` | String | 关键字方法名 |
| `parameters_input` | Object (Dict) | 实际传入的参数（已替换变量后的值） |
| `return_value` | Any | 关键字函数返回值 |
| `execution_time` | Integer | 函数执行耗时（毫秒） |

---

## 6. data_driven — 数据驱动结果

当 YAML 中配置了 `ddts` 或 `csv_datasource` 时，`data_driven` 字段返回数据驱动测试结果。

```json
{
  "data_driven": {
    "enabled": true,
    "source": "yaml_inline",
    "dataset_name": "登录数据集",
    "total_runs": 3,
    "passed_runs": 2,
    "failed_runs": 1,
    "pass_rate": 66.7,
    "runs": [
      {
        "run_index": 0,
        "parameters": {
          "user_email": "valid@example.com",
          "user_password": "Correct@123",
          "expected_status": 200,
          "expected_code": 0
        },
        "status": "passed",
        "duration": 320,
        "summary": {
          "total_steps": 1,
          "passed_steps": 1,
          "failed_steps": 0,
          "total_assertions": 2,
          "passed_assertions": 2,
          "failed_assertions": 0
        },
        "steps": [ ... ]
      },
      {
        "run_index": 1,
        "parameters": {
          "user_email": "valid@example.com",
          "user_password": "WrongPassword",
          "expected_status": 401,
          "expected_code": 40101
        },
        "status": "passed",
        "duration": 280,
        "summary": { ... },
        "steps": [ ... ]
      },
      {
        "run_index": 2,
        "parameters": {
          "user_email": "",
          "user_password": "",
          "expected_status": 400,
          "expected_code": 40001
        },
        "status": "failed",
        "duration": 150,
        "summary": {
          "total_steps": 1,
          "passed_steps": 0,
          "failed_steps": 1,
          "total_assertions": 2,
          "passed_assertions": 1,
          "failed_assertions": 1
        },
        "steps": [ ... ]
      }
    ]
  }
}
```

### 6.1 data_driven 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | Boolean | 是否启用数据驱动，`true` 时以下字段有效 |
| `source` | String (Enum) | 数据来源：`yaml_inline`（YAML 内 `ddts` 字段）/ `csv_file`（CSV 文件引入） |
| `dataset_name` | String | 数据集名称 |
| `total_runs` | Integer | 数据驱动总轮次数（= 数据行数） |
| `passed_runs` | Integer | 通过轮次数 |
| `failed_runs` | Integer | 失败轮次数 |
| `pass_rate` | Float | 轮次通过率（百分比，保留 1 位小数） |
| `runs` | Array\<Object\> | 每轮执行结果列表，见 § 6.2 |

### 6.2 runs[] 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_index` | Integer | 轮次序号，从 `0` 开始 |
| `parameters` | Object (Dict) | 本轮使用的参数 Key-Value |
| `status` | String (Enum) | 本轮执行状态：`passed` / `failed` / `error` / `skipped` |
| `duration` | Integer | 本轮总耗时（毫秒） |
| `summary` | Object | 本轮执行摘要（结构同 § 3，但仅包含本轮数据） |
| `steps` | Array\<Object\> | 本轮步骤执行详情（结构同 § 5） |

---

## 7. logs — 执行日志

```json
{
  "logs": [
    {
      "timestamp": "2026-02-25T22:30:00.001+08:00",
      "level": "INFO",
      "message": "开始执行场景: 用户注册 → 登录 → 查看信息",
      "step_index": null
    },
    {
      "timestamp": "2026-02-25T22:30:00.002+08:00",
      "level": "INFO",
      "message": "执行前置 SQL: db_main",
      "step_index": null
    },
    {
      "timestamp": "2026-02-25T22:30:00.100+08:00",
      "level": "INFO",
      "message": "[步骤 0] 开始执行: 用户注册",
      "step_index": 0
    },
    {
      "timestamp": "2026-02-25T22:30:00.101+08:00",
      "level": "DEBUG",
      "message": "[步骤 0] 发送 POST 请求 → https://api-test.example.com/api/v1/auth/register",
      "step_index": 0
    },
    {
      "timestamp": "2026-02-25T22:30:00.320+08:00",
      "level": "INFO",
      "message": "[步骤 0] 完成: passed (320ms)",
      "step_index": 0
    },
    {
      "timestamp": "2026-02-25T22:30:05.320+08:00",
      "level": "INFO",
      "message": "场景执行完毕: passed (5320ms)",
      "step_index": null
    }
  ]
}
```

### 7.1 logs 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | String (ISO 8601) | 日志时间戳 |
| `level` | String (Enum) | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `message` | String | 日志内容 |
| `step_index` | Integer \| null | 关联的步骤序号。引擎级日志为 `null`，步骤级日志为对应的 `step_index` |

---

## 8. 完整响应示例

### 8.1 简单通过场景

```json
{
  "execution_id": "exec-001",
  "scenario_id": "scen-001",
  "scenario_name": "获取用户列表",
  "project_id": "proj-001",
  "status": "passed",
  "start_time": "2026-02-25T22:30:00.000+08:00",
  "end_time": "2026-02-25T22:30:00.500+08:00",
  "duration": 500,
  "summary": {
    "total_steps": 1,
    "passed_steps": 1,
    "failed_steps": 0,
    "skipped_steps": 0,
    "error_steps": 0,
    "total_assertions": 3,
    "passed_assertions": 3,
    "failed_assertions": 0,
    "pass_rate": 100.0,
    "total_requests": 1,
    "total_db_operations": 0,
    "total_extractions": 0,
    "avg_response_time": 450,
    "max_response_time": 450,
    "min_response_time": 450,
    "total_data_driven_runs": 0
  },
  "environment": {
    "name": "测试环境",
    "base_url": "https://api-test.example.com",
    "variables": {}
  },
  "steps": [
    {
      "step_index": 0,
      "name": "获取用户列表",
      "keyword_type": "request",
      "keyword_name": "http_request",
      "status": "passed",
      "start_time": "2026-02-25T22:30:00.010+08:00",
      "end_time": "2026-02-25T22:30:00.460+08:00",
      "duration": 450,
      "error": null,
      "request_detail": {
        "method": "GET",
        "url": "https://api-test.example.com/api/v1/users",
        "headers": {
          "Authorization": "Bearer admin-token-xxx"
        },
        "params": { "page": 1, "page_size": 10 },
        "body": null,
        "body_type": "none",
        "timeout": 30,
        "allow_redirects": true,
        "verify_ssl": true
      },
      "response_detail": {
        "status_code": 200,
        "headers": { "Content-Type": "application/json" },
        "body": {
          "code": 0,
          "data": { "total": 25, "items": [] }
        },
        "body_size": 1024,
        "response_time": 445,
        "cookies": {}
      },
      "assertion_results": [
        {
          "target": "status_code",
          "expression": null,
          "comparator": "eq",
          "expected": 200,
          "actual": 200,
          "status": "passed",
          "message": null
        },
        {
          "target": "json",
          "expression": "$.code",
          "comparator": "eq",
          "expected": 0,
          "actual": 0,
          "status": "passed",
          "message": null
        },
        {
          "target": "json",
          "expression": "$.data.total",
          "comparator": "gt",
          "expected": 0,
          "actual": 25,
          "status": "passed",
          "message": null
        }
      ],
      "extract_results": null,
      "db_detail": null,
      "custom_detail": null
    }
  ],
  "data_driven": null,
  "variables": {},
  "logs": [
    {
      "timestamp": "2026-02-25T22:30:00.001+08:00",
      "level": "INFO",
      "message": "开始执行场景: 获取用户列表",
      "step_index": null
    },
    {
      "timestamp": "2026-02-25T22:30:00.460+08:00",
      "level": "INFO",
      "message": "[步骤 0] 完成: passed (450ms)",
      "step_index": 0
    },
    {
      "timestamp": "2026-02-25T22:30:00.500+08:00",
      "level": "INFO",
      "message": "场景执行完毕: passed (500ms)",
      "step_index": null
    }
  ],
  "error": null
}
```

### 8.2 引擎级错误场景

```json
{
  "execution_id": "exec-err-001",
  "scenario_id": "",
  "scenario_name": "",
  "project_id": "",
  "status": "error",
  "start_time": "2026-02-25T22:30:00.000+08:00",
  "end_time": "2026-02-25T22:30:00.050+08:00",
  "duration": 50,
  "summary": {
    "total_steps": 0,
    "passed_steps": 0,
    "failed_steps": 0,
    "skipped_steps": 0,
    "error_steps": 0,
    "total_assertions": 0,
    "passed_assertions": 0,
    "failed_assertions": 0,
    "pass_rate": 0,
    "total_requests": 0,
    "total_db_operations": 0,
    "total_extractions": 0,
    "avg_response_time": 0,
    "max_response_time": 0,
    "min_response_time": 0,
    "total_data_driven_runs": 0
  },
  "environment": null,
  "steps": [],
  "data_driven": null,
  "variables": {},
  "logs": [
    {
      "timestamp": "2026-02-25T22:30:00.001+08:00",
      "level": "ERROR",
      "message": "YAML 文件解析失败: invalid syntax at line 15",
      "step_index": null
    }
  ],
  "error": {
    "code": "YAML_PARSE_ERROR",
    "message": "YAML 文件解析失败: invalid syntax at line 15",
    "detail": "yaml.scanner.ScannerError: while scanning a quoted scalar..."
  }
}
```

---

## 9. 字段速查表

### 顶层字段

| 字段 | 类型 | 必返 | 备注 |
|------|------|------|------|
| `execution_id` | UUID | ✅ | 执行唯一 ID |
| `scenario_id` | UUID | ✅ | 场景 ID |
| `scenario_name` | String | ✅ | 场景名称 |
| `project_id` | UUID | ✅ | 项目 ID |
| `status` | Enum | ✅ | `passed` / `failed` / `error` / `skipped` |
| `start_time` | ISO 8601 | ✅ | 开始时间 |
| `end_time` | ISO 8601 | ✅ | 结束时间 |
| `duration` | Integer (ms) | ✅ | 总耗时 |
| `summary` | Object | ✅ | 执行摘要 |
| `environment` | Object / null | ✅ | 环境信息 |
| `steps` | Array | ✅ | 步骤详情 |
| `data_driven` | Object / null | ✅ | 数据驱动结果 |
| `variables` | Dict | ✅ | 变量快照 |
| `logs` | Array | ✅ | 执行日志 |
| `error` | Object / null | ✅ | 错误信息 |

### summary 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_steps` | Integer | 步骤总数 |
| `passed_steps` | Integer | 通过步骤数 |
| `failed_steps` | Integer | 失败步骤数 |
| `skipped_steps` | Integer | 跳过步骤数 |
| `error_steps` | Integer | 异常步骤数 |
| `total_assertions` | Integer | 断言总数 |
| `passed_assertions` | Integer | 通过断言数 |
| `failed_assertions` | Integer | 失败断言数 |
| `pass_rate` | Float | 通过率 (%) |
| `total_requests` | Integer | HTTP 请求数 |
| `total_db_operations` | Integer | 数据库操作数 |
| `total_extractions` | Integer | 变量提取数 |
| `avg_response_time` | Integer (ms) | 平均响应时间 |
| `max_response_time` | Integer (ms) | 最大响应时间 |
| `min_response_time` | Integer (ms) | 最小响应时间 |
| `total_data_driven_runs` | Integer | 数据驱动轮次 |

---

## 10. 错误码定义

### 10.1 引擎级错误

| 错误码 | 说明 |
|--------|------|
| `YAML_PARSE_ERROR` | YAML 文件解析失败 |
| `YAML_VALIDATION_ERROR` | YAML 结构校验失败（缺少必填字段等） |
| `FILE_NOT_FOUND` | YAML 文件不存在 |
| `CSV_PARSE_ERROR` | CSV 数据源文件解析失败 |
| `CSV_FILE_NOT_FOUND` | CSV 数据源文件不存在 |
| `ENGINE_INTERNAL_ERROR` | 引擎内部错误 |
| `TIMEOUT_ERROR` | 引擎执行整体超时 |

### 10.2 步骤级错误

| 错误码 | 说明 |
|--------|------|
| `REQUEST_TIMEOUT` | HTTP 请求超时 |
| `REQUEST_CONNECTION_ERROR` | HTTP 连接错误（目标不可达） |
| `REQUEST_SSL_ERROR` | SSL 证书验证失败 |
| `ASSERTION_FAILED` | 断言失败 |
| `EXTRACT_FAILED` | 变量提取失败（JSONPath 未匹配到值等） |
| `DB_CONNECTION_ERROR` | 数据库连接失败 |
| `DB_QUERY_ERROR` | SQL 执行错误 |
| `DB_DATASOURCE_NOT_FOUND` | 数据源引用未找到 |
| `KEYWORD_NOT_FOUND` | 关键字未找到 |
| `KEYWORD_EXECUTION_ERROR` | 自定义关键字执行异常 |
| `VARIABLE_NOT_FOUND` | 变量引用未找到 |
| `VARIABLE_RENDER_ERROR` | 变量渲染失败 |

---

> **文档结束** — sisyphus-api-engine JSON 输出规范 v1.0
