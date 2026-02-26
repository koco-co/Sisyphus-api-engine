# sisyphus-api-engine YAML 输入规范

> **文档版本**: v1.0
> **创建日期**: 2026-02-25
> **文档性质**: 接口规范文档（供后端开发人员使用）
> **适用组件**: sisyphus-api-engine 核心执行器

---

## 目录

- [1. 概述](#1-概述)
- [2. 顶层结构](#2-顶层结构)
- [3. config — 场景配置](#3-config--场景配置)
- [4. teststeps — 测试步骤](#4-teststeps--测试步骤)
  - [4.1 发送请求 (request)](#41-发送请求-request)
  - [4.2 断言 (assertion)](#42-断言-assertion)
  - [4.3 提取变量 (extract)](#43-提取变量-extract)
  - [4.4 数据库操作 (db)](#44-数据库操作-db)
  - [4.5 自定义操作 (custom)](#45-自定义操作-custom)
- [5. ddts — 数据驱动](#5-ddts--数据驱动)
- [6. 变量引用规则](#6-变量引用规则)
- [7. 完整示例](#7-完整示例)
- [8. 字段速查表](#8-字段速查表)

---

## 1. 概述

sisyphus-api-engine 通过 YAML 文件驱动接口自动化测试。**一个 YAML 文件 = 一个完整的测试场景**。

**CLI 调用方式**:

```bash
# 默认文本报告（rich 库渲染）
sisyphus --case <yaml_file_path>

# JSON 响应输出（平台集成模式）
sisyphus --case <yaml_file_path> -O json

# Allure 报告输出
sisyphus --case <yaml_file_path> -O allure --allure-dir <output_dir>

# HTML 报告输出
sisyphus --case <yaml_file_path> -O html --html-dir <output_dir>
```

**平台集成模式**: 后端将前端参数转化为 YAML 文件，保存至 `temp/` 临时目录（UUID 命名），调用 CLI 执行后获取 JSON 响应。

---

## 2. 顶层结构

```yaml
# YAML 文件顶层结构
config:        # [必填] 场景配置信息
  ...

teststeps:     # [必填] 测试步骤列表（有序数组）
  - ...

ddts:          # [选填] 数据驱动测试数据集（YAML 内定义方式）
  ...
```

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `config` | Object | ✅ 必填 | 场景级配置，包含名称、变量、环境、SQL 等 |
| `teststeps` | Array\<Object\> | ✅ 必填 | 测试步骤列表，按数组顺序执行 |
| `ddts` | Object | ❌ 选填 | 数据驱动测试数据定义 |

---

## 3. config — 场景配置

```yaml
config:
  name: "用户注册-登录-查看个人信息"
  description: "端到端验证用户注册、登录及信息获取流程"
  project_id: "proj-uuid-001"
  scenario_id: "scen-uuid-001"
  priority: "P1"
  tags:
    - "冒烟测试"
    - "核心流程"
  environment:
    name: "测试环境"
    base_url: "https://api-test.example.com"
    variables:
      env_token: ""
      env_host: "api-test.example.com"
  variables:
    global_admin_token: "Bearer xxx"
    test_user_email: "testuser@example.com"
    random_suffix: "{{random(8)}}"
  pre_sql:
    datasource: "db_main"
    statements:
      - "CREATE TABLE IF NOT EXISTS temp_test_{{random_suffix}} (id INT PRIMARY KEY, name VARCHAR(100));"
      - "INSERT INTO temp_test_{{random_suffix}} VALUES (1, 'seed_data');"
  post_sql:
    datasource: "db_main"
    statements:
      - "DROP TABLE IF EXISTS temp_test_{{random_suffix}};"
  csv_datasource: "data/test_users.csv"
```

### 3.1 config 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 测试场景名称，最大 255 字符 |
| `description` | String | ❌ 选填 | 测试场景描述 |
| `project_id` | String (UUID) | ✅ 必填 | 所属项目 ID，平台生成时自动填入 |
| `scenario_id` | String (UUID) | ✅ 必填 | 场景唯一 ID，平台生成时自动填入 |
| `priority` | String (Enum) | ❌ 选填 | 优先级：`P0` / `P1` / `P2` / `P3`，默认 `P2` |
| `tags` | Array\<String\> | ❌ 选填 | 标签列表 |
| `environment` | Object | ❌ 选填 | 运行环境配置，见 § 3.2 |
| `variables` | Object (Dict) | ❌ 选填 | 场景级变量定义，Key-Value 形式 |
| `pre_sql` | Object | ❌ 选填 | 前置 SQL 配置，见 § 3.3 |
| `post_sql` | Object | ❌ 选填 | 后置 SQL 配置，见 § 3.3 |
| `csv_datasource` | String | ❌ 选填 | CSV 数据驱动文件路径（与 `ddts` 字段二选一） |

### 3.2 environment 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 环境名称，如"测试环境"、"预发布环境" |
| `base_url` | String (URL) | ✅ 必填 | 环境前置 URL，如 `https://api.example.com` |
| `variables` | Object (Dict) | ❌ 选填 | 环境变量，Key-Value 形式；仅当前环境可用 |

### 3.3 pre_sql / post_sql 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `datasource` | String | ✅ 必填 | 数据源引用变量名（对应项目数据库配置中的"引用变量"） |
| `statements` | Array\<String\> | ✅ 必填 | SQL 语句列表，按顺序执行；支持 `{{变量名}}` 引用 |

---

## 4. teststeps — 测试步骤

`teststeps` 是一个有序数组，每个元素代表一个测试步骤。步骤按数组顺序依次执行。

### 通用步骤字段

每个步骤都包含以下通用字段：

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 步骤名称 / 描述 |
| `keyword_type` | String (Enum) | ✅ 必填 | 关键字类型：`request` / `assertion` / `extract` / `db` / `custom` |
| `keyword_name` | String | ✅ 必填 | 关键字函数名称（内置或自定义关键字的方法名） |
| `enabled` | Boolean | ❌ 选填 | 是否启用该步骤，默认 `true` |

---

### 4.1 发送请求 (request)

适用于 `keyword_type: request`，支持所有 HTTP 请求方法。

```yaml
- name: "用户注册"
  keyword_type: "request"
  keyword_name: "http_request"
  enabled: true
  request:
    method: "POST"
    url: "/api/v1/auth/register"
    headers:
      Content-Type: "application/json"
      X-Request-ID: "{{random_uuid()}}"
    params:
      source: "web"
      version: "2.0"
    json:
      email: "{{test_user_email}}"
      password: "Test@123456"
      nickname: "测试用户_{{random(6)}}"
    timeout: 30
  extract:
    - name: "user_id"
      type: "json"
      expression: "$.data.id"
      scope: "global"
    - name: "register_token"
      type: "header"
      expression: "X-Auth-Token"
      scope: "environment"
  validate:
    - target: "status_code"
      comparator: "eq"
      expected: 200
    - target: "json"
      expression: "$.code"
      comparator: "eq"
      expected: 0
    - target: "json"
      expression: "$.data.email"
      comparator: "eq"
      expected: "{{test_user_email}}"
    - target: "response_time"
      comparator: "lt"
      expected: 3000
```

#### 4.1.1 request 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `method` | String (Enum) | ✅ 必填 | HTTP 方法：`GET` / `POST` / `PUT` / `DELETE` / `PATCH` / `HEAD` / `OPTIONS` |
| `url` | String | ✅ 必填 | 请求 URL（相对路径或完整 URL）。若配置了 `environment.base_url`，可使用相对路径 |
| `headers` | Object (Dict) | ❌ 选填 | 请求头，Key-Value 形式 |
| `params` | Object (Dict) | ❌ 选填 | URL 查询参数（Query String），Key-Value 形式 |
| `json` | Object / Array | ❌ 选填 | JSON 请求体，与 `data` / `files` 互斥 |
| `data` | Object (Dict) | ❌ 选填 | 表单请求体（application/x-www-form-urlencoded），与 `json` / `files` 互斥 |
| `files` | Object (Dict) | ❌ 选填 | 文件上传参数，Value 为 MinIO 文件路径；与 `json` / `data` 互斥 |
| `cookies` | Object (Dict) | ❌ 选填 | 请求 Cookie，Key-Value 形式 |
| `timeout` | Integer | ❌ 选填 | 请求超时时间（秒），默认 `30` |
| `allow_redirects` | Boolean | ❌ 选填 | 是否允许重定向，默认 `true` |
| `verify` | Boolean | ❌ 选填 | 是否验证 SSL 证书，默认 `true` |

#### 4.1.2 extract 字段定义（随步骤提取）

`extract` 可内嵌于 `request` 步骤中，步骤执行后立即提取变量。

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 提取后的变量名称，后续通过 `{{name}}` 引用 |
| `type` | String (Enum) | ✅ 必填 | 提取来源：`json` / `header` / `cookie` |
| `expression` | String | ✅ 必填 | 提取表达式。`json` 类型使用 JSONPath（如 `$.data.id`）；`header` / `cookie` 类型使用名称（如 `X-Auth-Token`） |
| `scope` | String (Enum) | ❌ 选填 | 变量作用域：`global`（全局变量）/ `environment`（环境变量），默认 `global` |
| `default` | Any | ❌ 选填 | 提取失败时的默认值 |

#### 4.1.3 validate 字段定义（随步骤断言）

`validate` 可内嵌于 `request` 步骤中，步骤执行后立即进行断言验证。

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `target` | String (Enum) | ✅ 必填 | 断言对象：`json` / `header` / `cookie` / `status_code` / `response_time` / `env_variable` |
| `expression` | String | 条件必填 | 提取表达式。当 `target` 为 `json` 时必填（JSONPath 表达式），`header` / `cookie` 时必填（名称），`status_code` / `response_time` 时无需填写 |
| `comparator` | String (Enum) | ✅ 必填 | 判断符号，见下方 § 4.1.4 |
| `expected` | Any | ✅ 必填 | 预期结果，支持 `{{变量名}}` 引用 |
| `message` | String | ❌ 选填 | 断言失败时的自定义提示消息 |

#### 4.1.4 comparator 判断符号枚举

| 值 | 说明 | 示例 |
|----|------|------|
| `eq` | 等于 | `expected: 200` |
| `neq` | 不等于 | `expected: 500` |
| `gt` | 大于 | `expected: 0` |
| `gte` | 大于等于 | `expected: 1` |
| `lt` | 小于 | `expected: 3000` |
| `lte` | 小于等于 | `expected: 100` |
| `contains` | 包含（字符串 / 列表） | `expected: "success"` |
| `not_contains` | 不包含 | `expected: "error"` |
| `startswith` | 以…开头 | `expected: "Bearer"` |
| `endswith` | 以…结尾 | `expected: ".com"` |
| `matches` | 正则匹配 | `expected: "^\\d{4}-\\d{2}-\\d{2}$"` |
| `type_match` | 类型匹配 | `expected: "int"` / `"str"` / `"list"` / `"dict"` / `"bool"` / `"null"` |
| `length_eq` | 长度等于 | `expected: 10` |
| `length_gt` | 长度大于 | `expected: 0` |
| `length_lt` | 长度小于 | `expected: 100` |
| `is_null` | 为 null | `expected: true` |
| `is_not_null` | 不为 null | `expected: true` |

---

### 4.2 断言 (assertion)

独立断言步骤，适用于 `keyword_type: assertion`。与内嵌 `validate` 的区别是：独立断言步骤可以作为单独的执行步骤出现在流程中。

```yaml
- name: "验证用户 ID 格式正确"
  keyword_type: "assertion"
  keyword_name: "json_assertion"
  assertion:
    target: "json"
    source_variable: "last_response"
    expression: "$.data.user_id"
    comparator: "matches"
    expected: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    message: "用户 ID 应为有效的 UUID 格式"
```

#### 4.2.1 assertion 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `target` | String (Enum) | ✅ 必填 | 断言对象：`json` / `header` / `cookie` / `status_code` / `response_time` / `env_variable` |
| `source_variable` | String | ❌ 选填 | 断言数据源变量名。默认使用上一个 `request` 步骤的响应数据；可指定已提取的变量 |
| `expression` | String | 条件必填 | 提取表达式，规则同 § 4.1.3 |
| `comparator` | String (Enum) | ✅ 必填 | 判断符号，见 § 4.1.4 |
| `expected` | Any | ✅ 必填 | 预期结果 |
| `message` | String | ❌ 选填 | 断言失败时的自定义提示消息 |

---

### 4.3 提取变量 (extract)

独立变量提取步骤，适用于 `keyword_type: extract`。

```yaml
- name: "提取登录 Token"
  keyword_type: "extract"
  keyword_name: "json_extract"
  extract:
    - name: "auth_token"
      type: "json"
      source_variable: "last_response"
      expression: "$.data.token"
      scope: "global"
      default: ""
    - name: "session_cookie"
      type: "cookie"
      expression: "SESSIONID"
      scope: "environment"
```

#### 4.3.1 extract 字段定义

`extract` 为数组，每个元素定义一个变量提取规则：

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 提取后的变量名称 |
| `type` | String (Enum) | ✅ 必填 | 提取来源：`json` / `header` / `cookie` |
| `source_variable` | String | ❌ 选填 | 数据源变量名。默认使用上一个 `request` 步骤的响应；可指定已提取的变量 |
| `expression` | String | ✅ 必填 | 提取表达式。`json` → JSONPath；`header` / `cookie` → 名称 |
| `scope` | String (Enum) | ❌ 选填 | 变量作用域：`global` / `environment`，默认 `global` |
| `default` | Any | ❌ 选填 | 提取失败时的默认值 |

---

### 4.4 数据库操作 (db)

适用于 `keyword_type: db`，支持数据库查询、断言和变量提取。

```yaml
- name: "验证数据库中用户注册记录"
  keyword_type: "db"
  keyword_name: "db_operation"
  db:
    datasource: "db_main"
    sql: "SELECT id, email, status FROM users WHERE email = '{{test_user_email}}' LIMIT 1;"
    extract:
      - name: "db_user_id"
        expression: "$[0].id"
        scope: "global"
      - name: "db_user_status"
        expression: "$[0].status"
        scope: "global"
    validate:
      - expression: "$[0].email"
        comparator: "eq"
        expected: "{{test_user_email}}"
        message: "数据库中用户邮箱应与注册邮箱一致"
      - expression: "$.length"
        comparator: "eq"
        expected: 1
        message: "应只有一条匹配的用户记录"
```

#### 4.4.1 db 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `datasource` | String | ✅ 必填 | 数据源引用变量名（对应项目数据库配置中的"引用变量"字段） |
| `sql` | String | ✅ 必填 | SQL 语句，支持 `{{变量名}}` 引用 |
| `extract` | Array\<Object\> | ❌ 选填 | 从查询结果中提取变量，见 § 4.4.2 |
| `validate` | Array\<Object\> | ❌ 选填 | 对查询结果进行断言，见 § 4.4.3 |

#### 4.4.2 db.extract 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 提取后的变量名称 |
| `expression` | String | ✅ 必填 | JSONPath 表达式，从 SQL 查询结果的 JSON 数组中提取。如 `$[0].id` 表示第一行的 `id` 字段 |
| `scope` | String (Enum) | ❌ 选填 | 变量作用域：`global` / `environment`，默认 `global` |
| `default` | Any | ❌ 选填 | 提取失败时的默认值 |

#### 4.4.3 db.validate 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `expression` | String | ✅ 必填 | JSONPath 表达式，从查询结果中提取值进行断言。`$.length` 为内置表达式，代表结果集行数 |
| `comparator` | String (Enum) | ✅ 必填 | 判断符号，同 § 4.1.4 |
| `expected` | Any | ✅ 必填 | 预期结果 |
| `message` | String | ❌ 选填 | 断言失败时的自定义提示消息 |

---

### 4.5 自定义操作 (custom)

适用于 `keyword_type: custom`，调用用户在"关键字配置"中自定义的关键字函数。

```yaml
- name: "生成唯一业务编号"
  keyword_type: "custom"
  keyword_name: "generate_business_code"
  parameters:
    prefix: "BIZ"
    length: 12
    include_timestamp: true
  extract:
    - name: "business_code"
      type: "json"
      expression: "$.result"
      scope: "global"
```

#### 4.5.1 custom 字段定义

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `parameters` | Object (Dict) | 条件必填 | 关键字函数入参，Key-Value 形式。具体参数由关键字配置中的"入参释义"定义 |
| `extract` | Array\<Object\> | ❌ 选填 | 从自定义关键字返回值中提取变量，格式同 § 4.1.2 |

---

## 5. ddts — 数据驱动

数据驱动测试支持两种方式：

### 5.1 方式一：YAML 内定义（ddts 字段）

```yaml
ddts:
  name: "多用户注册数据集"
  parameters:
    - user_email: "user_a@example.com"
      user_name: "用户A"
      expected_code: 0
    - user_email: "user_b@example.com"
      user_name: "用户B"
      expected_code: 0
    - user_email: "invalid_email"
      user_name: "异常用户"
      expected_code: 40001
```

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|----------|------|
| `name` | String | ✅ 必填 | 数据集名称 |
| `parameters` | Array\<Object\> | ✅ 必填 | 数据行列表。每个 Object 为一组测试数据；所有 Object 的 Key 应保持一致 |

**执行规则**:
- 每一行数据等价于一个独立的 YAML 文件执行
- 数据集中的字段通过 `{{字段名}}` 在测试步骤中引用
- 多行数据**并行执行**（底层通过 `pytest.mark.parametrize` 实现）

### 5.2 方式二：CSV 文件引入

在 `config` 中通过 `csv_datasource` 字段指定 CSV 文件路径：

```yaml
config:
  name: "数据驱动-CSV文件"
  csv_datasource: "data/test_users.csv"
```

对应的 CSV 文件格式：

```csv
user_email,user_name,expected_code
user_a@example.com,用户A,0
user_b@example.com,用户B,0
invalid_email,异常用户,40001
```

- CSV 第一行为表头（即变量名），后续每行为一组数据
- 变量名与 `ddts.parameters` 中的 Key 等价，通过 `{{变量名}}` 引用

---

## 6. 变量引用规则

全平台统一使用 `{{变量名称}}` 语法。变量引用支持在以下位置使用：

| 位置 | 示例 |
|------|------|
| URL | `url: "/api/v1/users/{{user_id}}"` |
| Headers | `Authorization: "Bearer {{auth_token}}"` |
| Params | `id: "{{user_id}}"` |
| 请求体 JSON | `"email": "{{test_user_email}}"` |
| SQL 语句 | `SELECT * FROM users WHERE id = '{{user_id}}'` |
| 断言预期值 | `expected: "{{expected_email}}"` |
| 提取表达式 | `expression: "$.data.items[{{index}}].id"` |

### 6.1 变量优先级（从高到低）

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | 数据驱动变量 | `ddts` / CSV 中定义的变量 |
| 2 | 步骤提取变量 | 通过 `extract` 在步骤执行后提取的变量 |
| 3 | 场景级变量 | `config.variables` 中定义的变量 |
| 4 | 环境变量 | `config.environment.variables` 中定义的变量 |
| 5 | 全局参数函数 | 系统设置中注册的全局参数工具函数 |

### 6.2 内置函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `{{random(n)}}` | 生成 n 位随机字符串 | `{{random(12)}}` → `"a3b5c7d9e1f2"` |
| `{{random_uuid()}}` | 生成 UUID | `{{random_uuid()}}` → `"550e8400-..."` |
| `{{timestamp()}}` | 当前时间戳（秒） | `{{timestamp()}}` → `1708876800` |
| `{{timestamp_ms()}}` | 当前时间戳（毫秒） | `{{timestamp_ms()}}` → `1708876800000` |
| `{{datetime(fmt)}}` | 格式化当前时间 | `{{datetime(%Y-%m-%d)}}` → `"2026-02-25"` |

### 6.3 全局参数引用

全局参数（系统设置中配置的工具函数）通过 `{{参数方法名}}` 或 `{{参数方法名(参数)}}` 引用：

```yaml
# 无参调用
url: "/api/v1/tables/{{generate_table_name}}"

# 带参调用
data:
  code: "{{generate_code(BIZ, 12)}}"
  table_name: "source_table_{{random(12)}}"
```

---

## 7. 完整示例

### 7.1 基础 HTTP 请求场景

```yaml
config:
  name: "获取用户列表"
  project_id: "proj-001"
  scenario_id: "scen-001"
  environment:
    name: "测试环境"
    base_url: "https://api-test.example.com"

teststeps:
  - name: "获取用户列表"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "GET"
      url: "/api/v1/users"
      headers:
        Authorization: "Bearer {{global_admin_token}}"
      params:
        page: 1
        page_size: 10
    validate:
      - target: "status_code"
        comparator: "eq"
        expected: 200
      - target: "json"
        expression: "$.code"
        comparator: "eq"
        expected: 0
      - target: "json"
        expression: "$.data.total"
        comparator: "gt"
        expected: 0
```

### 7.2 多步骤端到端场景（含提取、断言、数据库）

```yaml
config:
  name: "用户注册 → 登录 → 查看信息 → 数据库验证"
  project_id: "proj-001"
  scenario_id: "scen-002"
  priority: "P0"
  tags:
    - "冒烟测试"
    - "端到端"
  environment:
    name: "测试环境"
    base_url: "https://api-test.example.com"
  variables:
    test_email: "e2e_{{random(8)}}@example.com"
    test_password: "Test@123456"
  post_sql:
    datasource: "db_main"
    statements:
      - "DELETE FROM users WHERE email = '{{test_email}}';"

teststeps:
  # 步骤 1: 注册
  - name: "注册新用户"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "POST"
      url: "/api/v1/auth/register"
      json:
        email: "{{test_email}}"
        password: "{{test_password}}"
    extract:
      - name: "user_id"
        type: "json"
        expression: "$.data.id"
    validate:
      - target: "status_code"
        comparator: "eq"
        expected: 201
      - target: "json"
        expression: "$.code"
        comparator: "eq"
        expected: 0

  # 步骤 2: 登录
  - name: "用户登录"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "POST"
      url: "/api/v1/auth/login"
      json:
        email: "{{test_email}}"
        password: "{{test_password}}"
    extract:
      - name: "auth_token"
        type: "json"
        expression: "$.data.token"
    validate:
      - target: "status_code"
        comparator: "eq"
        expected: 200

  # 步骤 3: 查看个人信息
  - name: "获取个人信息"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "GET"
      url: "/api/v1/users/{{user_id}}"
      headers:
        Authorization: "Bearer {{auth_token}}"
    validate:
      - target: "json"
        expression: "$.data.email"
        comparator: "eq"
        expected: "{{test_email}}"
      - target: "json"
        expression: "$.data.id"
        comparator: "eq"
        expected: "{{user_id}}"

  # 步骤 4: 数据库验证
  - name: "数据库验证用户记录"
    keyword_type: "db"
    keyword_name: "db_operation"
    db:
      datasource: "db_main"
      sql: "SELECT id, email, status FROM users WHERE id = '{{user_id}}';"
      validate:
        - expression: "$[0].email"
          comparator: "eq"
          expected: "{{test_email}}"
        - expression: "$[0].status"
          comparator: "eq"
          expected: "active"

### 7.3 数据驱动场景

```yaml
config:
  name: "登录接口-多组数据验证"
  project_id: "proj-001"
  scenario_id: "scen-003"
  environment:
    name: "测试环境"
    base_url: "https://api-test.example.com"

teststeps:
  - name: "登录请求"
    keyword_type: "request"
    keyword_name: "http_request"
    request:
      method: "POST"
      url: "/api/v1/auth/login"
      json:
        email: "{{user_email}}"
        password: "{{user_password}}"
    validate:
      - target: "status_code"
        comparator: "eq"
        expected: "{{expected_status}}"
      - target: "json"
        expression: "$.code"
        comparator: "eq"
        expected: "{{expected_code}}"

ddts:
  name: "登录数据集"
  parameters:
    - user_email: "valid@example.com"
      user_password: "Correct@123"
      expected_status: 200
      expected_code: 0
    - user_email: "valid@example.com"
      user_password: "WrongPassword"
      expected_status: 401
      expected_code: 40101
    - user_email: ""
      user_password: ""
      expected_status: 400
      expected_code: 40001
```

---

## 8. 字段速查表

### 顶层结构

| 字段 | 路径 | 类型 | 必填 |
|------|------|------|------|
| 场景配置 | `config` | Object | ✅ |
| 测试步骤 | `teststeps` | Array | ✅ |
| 数据驱动 | `ddts` | Object | ❌ |

### config 完整字段

| 字段 | 路径 | 类型 | 必填 |
|------|------|------|------|
| 场景名称 | `config.name` | String | ✅ |
| 场景描述 | `config.description` | String | ❌ |
| 项目 ID | `config.project_id` | String (UUID) | ✅ |
| 场景 ID | `config.scenario_id` | String (UUID) | ✅ |
| 优先级 | `config.priority` | Enum | ❌ |
| 标签 | `config.tags` | Array\<String\> | ❌ |
| 环境名称 | `config.environment.name` | String | ❌ |
| 前置 URL | `config.environment.base_url` | String (URL) | ❌ |
| 环境变量 | `config.environment.variables` | Dict | ❌ |
| 场景变量 | `config.variables` | Dict | ❌ |
| 前置 SQL 数据源 | `config.pre_sql.datasource` | String | ❌ |
| 前置 SQL 语句 | `config.pre_sql.statements` | Array\<String\> | ❌ |
| 后置 SQL 数据源 | `config.post_sql.datasource` | String | ❌ |
| 后置 SQL 语句 | `config.post_sql.statements` | Array\<String\> | ❌ |
| CSV 数据源 | `config.csv_datasource` | String | ❌ |

### teststep 通用字段

| 字段 | 路径 | 类型 | 必填 |
|------|------|------|------|
| 步骤名称 | `teststeps[].name` | String | ✅ |
| 关键字类型 | `teststeps[].keyword_type` | Enum | ✅ |
| 关键字名称 | `teststeps[].keyword_name` | String | ✅ |
| 是否启用 | `teststeps[].enabled` | Boolean | ❌ |

### ddts 字段

| 字段 | 路径 | 类型 | 必填 |
|------|------|------|------|
| 数据集名称 | `ddts.name` | String | ✅ |
| 数据行列表 | `ddts.parameters` | Array\<Dict\> | ✅ |

---

> **文档结束** — sisyphus-api-engine YAML 输入规范 v1.0
