# API-Engine 输入协议规范 v2.0

> **版本说明**: 这是 Sisyphus API Engine v2.0.0 的实际输入协议规范，基于代码实现编写。

---

## 目录

- [1. 完整示例](#1-完整示例)
- [2. 配置结构详解](#2-配置结构详解)
- [3. 测试步骤类型](#3-测试步骤类型)
- [4. 变量系统](#4-变量系统)
- [5. 断言系统](#5-断言系统)
- [6. 高级特性](#6-高级特性)

---

## 1. 完整示例

```yaml
# ==============================================================================
# Sisyphus API Engine - 示例测试用例
# ==============================================================================

name: "用户登录全流程测试"
description: "包含登录、查询、创建订单的完整流程"

config:
  name: "测试配置"
  timeout: 30
  retry_times: 0

  # 环境配置
  profiles:
    dev:
      base_url: "https://dev-api.example.com"
      env_mode: "development"
    prod:
      base_url: "https://api.example.com"
      env_mode: "production"

  active_profile: "dev"

  # 全局变量
  variables:
    api_version: "v1"
    test_user: "testuser"

# 测试步骤
steps:
  - name: "用户登录"
    description: "使用用户名和密码登录"
    type: request
    method: POST
    url: "${config.profiles.dev.base_url}/auth/login"
    headers:
      Content-Type: "application/json"
    body:
      username: "${test_user}"
      password: "testpass123"
    validations:
      - type: status_code
        path: "$.status_code"
        expect: "200"
      - type: eq
        path: "$.code"
        expect: 0
        description: "业务码应为0"
    extractors:
      - name: "access_token"
        path: "$.data.token"
      - name: "user_id"
        path: "$.data.user.id"

  - name: "查询用户信息"
    description: "使用token查询用户信息"
    type: request
    method: GET
    url: "${config.profiles.dev.base_url}/user/info"
    headers:
      Authorization: "Bearer ${access_token}"
    validations:
      - type: status_code
        path: "$.status_code"
        expect: "200"
      - type: eq
        path: "$.data.user_id"
        expect: "${user_id}"
    depends_on:
      - "用户登录"

  - name: "创建订单"
    description: "创建新订单"
    type: request
    method: POST
    url: "${config.profiles.dev.base_url}/orders/create"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${access_token}"
    body:
      product_id: "SKU_001"
      quantity: 1
    validations:
      - type: status_code
        path: "$.status_code"
        expect: "201"
    only_if: "${user_id} != null"

tags:
  - "用户"
  - "订单"

enabled: true
```

---

## 2. 配置结构详解

### 2.1 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 测试用例名称 |
| `description` | string | ❌ | 测试用例描述 |
| `config` | object | ❌ | 全局配置 |
| `steps` | array | ✅ | 测试步骤列表 |
| `tags` | array | ❌ | 标签列表 |
| `enabled` | boolean | ❌ | 是否启用，默认 true |

### 2.2 config 配置

```yaml
config:
  name: "测试配置"           # 配置名称
  timeout: 30                # 全局超时时间（秒）
  retry_times: 0             # 全局重试次数

  # 环境配置
  profiles:
    dev:
      base_url: "https://dev-api.example.com"
      variables:
        env: "dev"
    prod:
      base_url: "https://api.example.com"
      variables:
        env: "prod"

  active_profile: "dev"      # 当前激活的环境

  # 全局变量
  variables:
    api_key: "sk_test_123"
    username: "testuser"
```

#### config 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ❌ | 配置名称 |
| `timeout` | int | ❌ | 全局超时时间（秒），默认30 |
| `retry_times` | int | ❌ | 全局重试次数，默认0 |
| `profiles` | object | ❌ | 环境配置 |
| `active_profile` | string | ❌ | 激活的环境名称 |
| `variables` | object | ❌ | 全局变量 |

---

## 3. 测试步骤类型

### 3.1 Request 步骤（HTTP请求）

```yaml
- name: "发送GET请求"
  type: request                  # 可省略，默认为 request
  method: GET
  url: "https://api.example.com/users"
  params:
    page: 1
    size: 10
  headers:
    User-Agent: "API-Test"
  validations:
    - type: status_code
      path: "$.status_code"
      expect: "200"
```

#### Request 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ❌ | 步骤类型，默认 request |
| `method` | string | ✅ | HTTP方法：GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS |
| `url` | string | ✅ | 请求URL |
| `params` | object | ❌ | Query参数 |
| `headers` | object | ❌ | 请求头 |
| `body` | object | ❌ | 请求体（JSON） |
| `validations` | array | ❌ | 验证规则列表 |
| `extractors` | array | ❌ | 变量提取器列表 |
| `timeout` | int | ❌ | 超时时间（秒） |
| `retry_times` | int | ❌ | 重试次数 |
| `skip_if` | string | ❌ | 条件为真时跳过步骤 |
| `only_if` | string | ❌ | 条件为真时执行步骤 |
| `depends_on` | array | ❌ | 依赖的前置步骤列表 |

### 3.2 Database 步骤（数据库操作）

```yaml
- name: "查询数据库"
  type: database
  database: "mysql_main"       # 数据库连接别名
  operation: query             # query 或 execute
  sql: "SELECT * FROM users WHERE id = 1"
  validations:
    - type: len_eq
      path: "$.rows"
      expect: 1
```

#### Database 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值：database |
| `database` | string | ✅ | 数据库连接名称 |
| `operation` | string | ✅ | 操作类型：query/execute |
| `sql` | string | ✅ | SQL语句 |
| `validations` | array | ❌ | 验证规则列表 |
| `extractors` | array | ❌ | 变量提取器列表 |

### 3.3 Wait 步骤（等待）

```yaml
- name: "等待2秒"
  type: wait
  seconds: 2
```

或条件等待：

```yaml
- name: "等待条件满足"
  type: wait
  condition: "${response.data.status} == 'completed'"
  interval: 1                  # 检查间隔（秒）
  max_wait: 30                 # 最大等待时间（秒）
```

#### Wait 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值：wait |
| `seconds` | int | ❌ | 固定等待时间（秒） |
| `condition` | string | ❌ | 等待条件（表达式） |
| `interval` | int | ❌ | 条件检查间隔（秒），默认1 |
| `max_wait` | int | ❌ | 最大等待时间（秒），默认30 |

### 3.4 Loop 步骤（循环）

```yaml
- name: "批量创建订单"
  type: loop
  loop_type: for               # for 或 while
  loop_count: 10               # 循环次数（for类型）
  loop_variable: "index"       # 循环变量名
  loop_steps:
    - name: "创建单个订单"
      type: request
      method: POST
      url: "/orders/create"
      body:
        sku_id: "SKU_001"
        remark: "订单 #${index}"
```

#### Loop 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值：loop |
| `loop_type` | string | ✅ | 循环类型：for/while |
| `loop_count` | int | ❌ | 循环次数（for类型） |
| `loop_condition` | string | ❌ | 循环条件（while类型） |
| `loop_variable` | string | ❌ | 循环变量名 |
| `loop_steps` | array | ✅ | 循环执行的步骤列表 |

### 3.5 Script 步骤（脚本执行）

```yaml
- name: "执行Python脚本"
  type: script
  script: |
    # Python 脚本内容
    import json
    result = {"status": "ok"}
    print(json.dumps(result))
  script_type: python          # python 或 javascript
  allow_imports: true          # 是否允许导入模块
```

#### Script 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值：script |
| `script` | string | ✅ | 脚本内容 |
| `script_type` | string | ❌ | 脚本类型：python/javascript，默认python |
| `allow_imports` | boolean | ❌ | 是否允许导入模块，默认true |

### 3.6 Poll 步骤（异步轮询）⭐ v2.0.0 新增

```yaml
- name: "等待项目就绪"
  type: poll
  url: "/api/project/status"
  method: POST
  body:
    project_id: "${project_id}"
  poll_config:
    # 轮询条件
    condition:
      type: jsonpath            # 条件类型: jsonpath 或 status_code
      path: "$.data.status"
      operator: "eq"            # 比较符: eq/ne/gt/lt/ge/le/contains/exists
      expect: "ACTIVE"
    # 轮询策略
    max_attempts: 30            # 最大轮询次数
    interval: 2000              # 轮询间隔（毫秒）
    timeout: 60000              # 总超时时间（毫秒）
    backoff: "fixed"            # 退避策略: fixed/exponential/linear
  on_timeout:
    behavior: "fail"            # 超时行为: fail 或 continue
    message: "项目初始化超时"
```

#### Poll 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✅ | 固定值：poll |
| `poll_config` | object | ✅ | 轮询配置对象 |
| `poll_config.condition` | object | ✅ | 轮询条件配置 |
| `poll_config.condition.type` | string | ✅ | 条件类型：jsonpath/status_code |
| `poll_config.condition.path` | string | ✅ | JSONPath表达式或响应路径 |
| `poll_config.condition.operator` | string | ✅ | 比较运算符 |
| `poll_config.condition.expect` | any | ✅ | 期望值 |
| `poll_config.max_attempts` | int | ❌ | 最大轮询次数，默认30 |
| `poll_config.interval` | int | ❌ | 轮询间隔（毫秒），默认2000 |
| `poll_config.timeout` | int | ❌ | 总超时时间（毫秒），默认60000 |
| `poll_config.backoff` | string | ❌ | 退避策略：fixed/exponential/linear，默认fixed |
| `on_timeout` | object | ❌ | 超时处理配置 |
| `on_timeout.behavior` | string | ❌ | 超时行为：fail/continue，默认fail |
| `on_timeout.message` | string | ❌ | 超时错误消息 |

#### 支持的比较运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `eq` | 等于 | `expect: "ACTIVE"` |
| `ne` | 不等于 | `expect: "PENDING"` |
| `gt` | 大于 | `expect: 100` |
| `lt` | 小于 | `expect: 10` |
| `ge` | 大于等于 | `expect: 100` |
| `le` | 小于等于 | `expect: 10` |
| `contains` | 包含 | `expect: "target"` |
| `exists` | 存在 | 无需expect值 |

#### 退避策略说明

1. **fixed（固定间隔）** - 每次轮询间隔相同
2. **exponential（指数退避）** - 每次间隔翻倍（1s, 2s, 4s, 8s...）
3. **linear（线性增长）** - 每次间隔线性增加（1s, 2s, 3s, 4s...）

---

## 4. 变量系统

### 4.1 变量引用语法

```yaml
variables:
  # 引用全局变量
  api_url: "${base_url}"

  # 引用环境配置
  env: "${config.profiles.dev.env_mode}"

  # 🆕 嵌套引用 config 变量（v2.0.0 新增）
  category_name: "test_${config.profiles.dev.variables.test_suffix}"
  full_resource: "${config.active_profile}_${config.profiles.dev.variables.env}"

  # 引用上一步提取的变量
  token: "${access_token}"

  # 在请求中使用
  url: "${base_url}/users/${user_id}"
```

### 4.2 变量嵌套引用 ⭐ v2.0.0 新增

v2.0.0 支持在顶层 `config.variables` 中嵌套引用 `config.profiles.*` 的值：

```yaml
config:
  profiles:
    dev:
      base_url: "https://dev-api.example.com"
      variables:
        test_suffix: "001"
        env: "dev"
    prod:
      base_url: "https://api.example.com"
      variables:
        test_suffix: "PROD"
        env: "production"

  active_profile: "dev"

  # ✨ 可以在顶层嵌套引用 profile 变量
  variables:
    # 引用特定 profile 的变量
    category_name: "test_${config.profiles.dev.variables.test_suffix}"

    # 引用 active_profile
    environment: "${config.active_profile}"

    # 组合多个嵌套引用
    full_resource_name: "${config.active_profile}_${config.profiles.dev.variables.test_suffix}"

steps:
  - name: "使用嵌套变量"
    type: request
    url: "${base_url}/api/category"
    method: POST
    body:
      category: "${category_name}"  # 渲染为 "test_001"
      env: "${environment}"          # 渲染为 "dev"
```

### 4.3 变量作用域优先级

从低到高：
1. 全局变量（`config.variables`）
2. 环境变量（`config.profiles.{profile}.variables`）
3. 提取变量（从响应中提取）

### 4.4 内置模板函数

##### 4.4.1 时间函数

| 函数 | 说明 | 返回值 | 示例 |
|------|------|--------|------|
| `now()` | 当前日期时间对象 | datetime | `${now()}` |
| `timestamp()` | Unix 时间戳（秒） | 整数 | `${timestamp()}` |
| `timestamp_ms()` | Unix 时间戳（毫秒） | 整数 | `${timestamp_ms()}` |
| `timestamp_us()` | Unix 时间戳（微秒，v1.0.2+） | 整数 | `${timestamp_us()}` |
| `now_us()` | 格式化微秒时间戳 | 字符串 | `${now_us()}` |
| `date(format)` | 格式化当前时间 | 字符串 | `${date('%Y-%m-%d')}` |

**时间戳使用示例**

```yaml
variables:
  # 秒级时间戳（10位）
  ts_seconds: "${timestamp()}"  # 1706508000

  # 毫秒级时间戳（13位）
  ts_millis: "${timestamp_ms()}"  # 1706508000000

  # 微秒级时间戳（16位，v1.0.2+新增）
  ts_micros: "${timestamp_us()}"  # 1706508000000000

  # 格式化微秒时间（20位字符串，v1.0.2+新增）
  formatted_us: "${now_us()}"  # "20260129133045123456"

  # 自定义格式
  custom_date: "${date('%Y-%m-%d %H:%M:%S')}"  # "2026-01-29 13:30:45"

  # 微秒级精度（v1.0.2+新增）
  with_micros: "${now().strftime('%Y%m%d%H%M%S%f')}"  # "20260129133045123456"

  # 生成唯一ID
  request_id: "req_${now_us()}"  # "req_20260129133045123456"
  session_id: "${now_us()}_${random_str(8)}"  # "20260129133045123456_aB3dX7kL"
```

##### 4.4.2 随机函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `random_int()` | 随机整数 | `${random_int()}` |
| `random_int(min, max)` | 指定范围随机整数 | `${random_int(1, 100)}` |
| `random_str(length)` | 随机字符串 | `${random_str(10)}` |
| `uuid()` | UUID 字符串 | `${uuid()}` |
| `uuid4()` | UUID v4 | `${uuid4()}` |

##### 4.4.3 其他函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `choice(array)` | 随机选择 | `${choice(['A', 'B', 'C'])}` |
| `base64_encode(str)` | Base64 编码 | `${base64_encode('hello')}` |
| `base64_decode(str)` | Base64 解码 | `${base64_decode('aGVsbG8=')}` |

**完整示例**

```yaml
variables:
  # 时间相关
  test_suffix: "${now_us()}"  # 微秒级唯一标识
  current_date: "${date('%Y-%m-%d')}"

  # 随机数据
  username: "user_${random_str(8)}"
  user_id: "${uuid()}"
  random_score: "${random_int(1, 100)}"

  # 组合使用
  session_id: "sess_${timestamp_us()}_${random_str(6)}"
  request_header: "Bearer ${uuid()}"
```

---

## 5. 断言系统

### 5.1 验证规则格式

```yaml
validations:
  - type: status_code          # 验证类型
    path: "$.status_code"      # JSONPath表达式
    expect: "200"              # 期望值
    description: "状态码应为200"  # 描述（可选）
```

### 5.2 验证类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `status_code` | HTTP状态码 | `expect: "200"` |
| `eq` | 等于 | `expect: "value"` |
| `ne` | 不等于 | `expect: "value"` |
| `gt` | 大于 | `expect: 100` |
| `lt` | 小于 | `expect: 1000` |
| `ge` | 大于等于 | `expect: 10` |
| `le` | 小于等于 | `expect: 100` |
| `contains` | 包含 | `expect: "substring"` |
| `not_contains` | 不包含 | `expect: "error"` |
| `len_eq` | 长度等于 | `expect: 10` |
| `len_gt` | 长度大于 | `expect: 0` |
| `len_lt` | 长度小于 | `expect: 100` |
| `startswith` | 以...开头 | `expect: "prefix"` |
| `endswith` | 以...结尾 | `expect: ".com"` |
| `type` | 类型检查 | `expect: "number"` |
| `regex` | 正则匹配 | `expect: "^\\d+$"` |
| `in` | 在范围内 | `expect: ["A", "B"]` |
| `not_in` | 不在范围内 | `expect: ["X", "Y"]` |

### 5.3 JSONPath 表达式

#### 5.3.1 基础表达式

| 表达式 | 说明 | 示例 |
|---------|------|------|
| `$.field` | 根对象属性 | `$.status_code` |
| `$.data.user.id` | 嵌套属性 | `$.data.user.id` |
| `$.data.items[0]` | 数组第一个元素 | `$.data.items[0]` |
| `$.data.items[-1]` | 数组最后一个元素 | `$.data.items[-1]` |
| `$..name` | 递归查找 | `$..username` |

#### 5.3.1.1 过滤表达式（v1.0.2+ 增强）

Sisyphus API Engine 现在支持完整的 JSONPath 过滤表达式，可以基于条件筛选数组元素。

**基本过滤语法**

| 表达式 | 说明 | 示例 |
|---------|------|------|
| `$.array[?(@.field == 'value')]` | 等于 | `$.users[?(@.role == 'admin')]` |
| `$.array[?(@.field != 'value')]` | 不等于 | `$.users[?(@.status != 'deleted')]` |
| `$.array[?(@.field > 10)]` | 大于 | `$.items[?(@.price > 100)]` |
| `$.array[?(@.field < 10)]` | 小于 | `$.items[?(@.quantity < 5)]` |
| `$.array[?(@.field == true)]` | 布尔等于 | `$.users[?(@.active == true)]` |
| `$.array[*].field` | 通配符（所有元素） | `$.users[*].id` |

**组合条件**

| 表达式 | 说明 |
|---------|------|
| `[?(@.f1 == 'v1' & @.f2 == 'v2')]` | AND 条件 |
| `[?(@.f1 == 'v1' \| @.f2 == 'v2')]` | OR 条件 |

**使用示例**

```yaml
# 提取所有管理员用户
extractors:
  - name: "admin_ids"
    path: "$.body.json.users[?(@.role == 'admin')].id"

# 提取活跃用户的用户名
extractors:
  - name: "active_names"
    path: "$.body.json.users[?(@.active == true)].name"

# 提取价格大于100的商品
extractors:
  - name: "expensive_items"
    path: "$.body.json.items[?(@.price > 100)].name"

# 验证过滤后的结果
validations:
  - type: eq
    path: "$.json.users[?(@.role == 'admin')].length()"
    expect: 3
    description: "应有3个管理员"
```

**注意事项**

- 过滤表达式中的布尔值使用小写 `true`/`false`，而非 Python 的 `True`/`False`
- 复杂的 AND/OR 条件需要使用 `&` 和 `|` 运算符
- 通配符 `[*]` 可以获取所有元素的字段

#### 5.3.1.1 重要：路径使用说明

**核心原则**：`response.body` **直接就是** API 返回的 JSON 数据，不需要任何前缀！

**路径格式**：

| 组件 | 数据源 | 路径格式 | 说明 |
|------|--------|----------|------|
| **验证器** | `response.body` | `$.field` | 直接使用，无需任何前缀 |
| **提取器** | `response.body` | `$.field` | 直接使用，无需任何前缀 |

**响应结构参考**：
```json
{
  "status_code": 200,
  "headers": {...},
  "body": {  // ← API 返回的 JSON 数据直接在这里
    "code": 1,
    "message": "success",
    "data": {
      "userId": 101809,
      "userName": "testuser"
    }
  }
}
```

**实际示例**：

```yaml
# 验证器：直接使用 $.field
validations:
  - type: eq
    path: "$.data.userId"
    expect: "101809"
    description: "验证用户ID"

# 提取器：同样直接使用 $.field
extractors:
  - name: "user_id"
    type: jsonpath
    path: "$.data.userId"  # ✅ 正确：直接使用
    description: "提取用户ID"

# 从数组中提取
extractors:
  - name: "first_user_id"
    type: jsonpath
    path: "$.data.users[0].userId"  # ✅ 正确：数组索引
    description: "提取第一个用户的ID"
```

**常见错误**：
- ❌ 使用 `$.body.data.userId` → 错误：不需要 `body.` 前缀
- ❌ 使用 `$.json.data.userId` → 错误：不需要 `json.` 前缀
- ✅ 使用 `$.data.userId` → 正确：直接访问字段
- ✅ 使用 `$.data.users[0].userId` → 正确：数组元素访问

#### 5.3.2 增强函数支持

Sisyphus API Engine 支持在 JSONPath 表达式中使用函数，实现更强大的数据提取和验证能力。

**函数语法**：`$.path.function_name(arguments)`

**数组函数**

| 函数 | 说明 | 示例 |
|------|------|------|
| `length()` | 获取数组/字符串/对象长度 | `$.data.length()` |
| `size()` | length 的别名 | `$.items.size()` |
| `count()` | count 的别名 | `$.users.count()` |
| `first()` | 获取数组第一个元素 | `$.items.first()` |
| `last()` | 获取数组最后一个元素 | `$.items.last()` |
| `sum()` | 数值求和 | `$.prices.sum()` |
| `avg()` | 计算平均值 | `$.scores.avg()` |
| `min()` | 获取最小值 | `$.values.min()` |
| `max()` | 获取最大值 | `$.values.max()` |
| `reverse()` | 反转数组 | `$.items.reverse()` |
| `sort()` | 排序数组 | `$.numbers.sort()` |
| `unique()` | 获取唯一值 | `$.ids.unique()` |
| `flatten()` | 展平嵌套数组 | `$.nested.flatten()` |

**对象函数**

| 函数 | 说明 | 示例 |
|------|------|------|
| `keys()` | 获取对象的所有键 | `$.user.keys()` |
| `values()` | 获取对象的所有值 | `$.user.values()` |

**字符串函数**

| 函数 | 说明 | 示例 |
|------|------|------|
| `upper()` | 转换为大写 | `$.text.upper()` |
| `lower()` | 转换为小写 | `$.text.lower()` |
| `trim()` | 去除首尾空白 | `$.text.trim()` |
| `split(delimiter)` | 分割字符串 | `$.text.split(,)` |
| `join(delimiter)` | 数组连接为字符串 | `$.items.join(-)` |

**检查函数**

| 函数 | 说明 | 示例 |
|------|------|------|
| `contains(value)` | 检查是否包含值 | `$.text.contains(hello)` |
| `starts_with(value)` | 检查是否以...开头 | `$.text.starts_with(pre)` |
| `ends_with(value)` | 检查是否以...结尾 | `$.text.ends_with(com)` |
| `matches(pattern)` | 正则匹配 | `$.code.matches(^\d+$)` |

#### 5.3.3 实际应用示例

**验证数组不为空**
```yaml
validations:
  - type: gt
    path: "$.data.length()"
    expect: 0
    description: "返回数据不应为空"
```

**验证数值总和**
```yaml
validations:
  - type: eq
    path: "$.order_items.sum()"
    expect: 100
    description: "订单总额应为100"
```

**提取数组长度**
```yaml
extractors:
  - name: "user_count"
    path: "$.body.users.length()"    # 提取器需要 body. 前缀
```

**字符串处理验证**
```yaml
validations:
  - type: eq
    path: "$.username.upper()"
    expect: "ADMIN"
    description: "用户名应为大写"
```

**验证数组中所有元素唯一**
```yaml
validations:
  - type: eq
    path: "$.ids.unique().length()"
    expect: 10
    description: "所有ID应该唯一"
```

#### 5.3.3 函数链式调用

Sisyphus API Engine 支持函数的链式调用，即在一个 JSONPath 表达式中连续调用多个函数。

**链式调用语法**：`$.path.function1().function2().function3()`

**执行顺序**：从左到右依次执行，前一个函数的输出作为后一个函数的输入。

**常见链式调用组合**：

| 链式调用 | 说明 | 示例结果 |
|---------|------|----------|
| `$.ids.unique().length()` | 去重后计数 | 获取唯一值的数量 |
| `$.numbers.sort().first()` | 排序后取首 | 获取最小值 |
| `$.numbers.sort().last()` | 排序后取尾 | 获取最大值 |
| `$.items.flatten().length()` | 展平后计数 | 获取展平后的元素数量 |
| `$.tags.join(-).upper()` | 连接后转大写 | 获取大写的连接字符串 |
| `$.text.trim().lower()` | 去空格后转小写 | 获取小写的无空格字符串 |

**实际应用示例**：

```yaml
# 示例 1: 验证去重后的数组长度
validations:
  - type: eq
    path: "$.body.ids.unique().length()"
    expect: 10
    description: "去重后应有 10 个唯一 ID"

# 示例 2: 验证排序后的最小值
validations:
  - type: eq
    path: "$.body.scores.sort().first()"
    expect: 60
    description: "最低分应为 60"

# 示例 3: 提取并连接标签
extractors:
  - name: "tag_string"
    path: "$.body.tags.join(-)"
    description: "提取并连接标签"

# 示例 4: 复杂链式调用
validations:
  - type: eq
    path: "$.body.data.items.flatten().unique().length()"
    expect: 15
    description: "展平去重后应有 15 个元素"
```

**链式调用注意事项**：
1. **类型兼容性**：确保每个函数的输入输出类型兼容
   - ✅ `sort()` → `first()`: 数组 → 数组元素
   - ✅ `join()` → `upper()`: 字符串 → 字符串
   - ❌ `length()` → `upper()`: 数字 → 字符串（类型错误）

2. **函数顺序**：合理安排函数调用顺序
   - ✅ `$.items.unique().sort()`: 先去重再排序
   - ⚠️ `$.items.sort().unique()`: 先排序再去重（去重会打乱排序）

3. **性能考虑**：链式调用会依次执行每个函数
   - 简单链式（2-3 个函数）：性能影响小
   - 复杂链式（4+ 个函数）：考虑分步提取或简化逻辑

---

## 6. 高级特性

### 6.1 变量提取

变量提取器用于从响应中提取数据并保存为变量，供后续步骤使用。

#### 6.1.1 提取器类型

| 类型 | 说明 | 配置字段 | 示例 |
|------|------|----------|------|
| `jsonpath` | JSONPath 表达式提取 | `path` | `path: "$.data.userId"` |
| `regex` | 正则表达式提取 | `pattern`/`group` 或 `path`/`index` | `pattern: '"id":\s*(\d+)'` |
| `header` | HTTP 响应头提取 | `path` | `path: "Content-Type"` |
| `cookie` | Cookie 提取 | `path` | `path: "session_id"` |

#### 6.1.2 JSONPath 提取器

**基础语法**：

```yaml
extractors:
  - name: "access_token"      # 变量名
    type: jsonpath            # 提取器类型（可省略，默认为 jsonpath）
    path: "$.data.token"      # JSONPath 表达式（直接使用，无需前缀）
    description: "提取访问令牌"  # 描述（可选）
```

**数组元素提取**：

```yaml
extractors:
  # 提取数组第一个元素
  - name: "first_user_id"
    type: jsonpath
    path: "$.data.users[0].userId"

  # 提取数组最后一个元素
  - name: "last_user_name"
    type: jsonpath
    path: "$.data.users[-1].userName"

  # 提取所有元素的某个字段
  - name: "all_user_ids"
    type: jsonpath
    path: "$.data.users[*].userId"
```

#### 6.1.3 Regex 提取器（v1.0.3+ 增强）

**新语法（推荐）**：使用语义化的 `pattern` 和 `group` 字段

```yaml
extractors:
  - name: "user_id"
    type: regex
    pattern: '"userId":\s*(\d+)'      # 正则表达式模式
    group: 1                          # 捕获组索引
    description: "使用新语法提取用户ID"
```

**旧语法（向后兼容）**：使用 `path` 和 `index` 字段

```yaml
extractors:
  - name: "user_id"
    type: regex
    path: '"userId":\s*(\d+)'         # 正则表达式模式
    index: 1                          # 捕获组索引
    description: "使用旧语法提取用户ID"
```

**字段优先级**：
- `pattern` 字段优先于 `path` 字段
- `group` 字段优先于 `index` 字段
- 如果同时提供新旧字段，新字段生效

**正则表达式示例**：

```yaml
extractors:
  # 提取数字
  - name: "order_id"
    type: regex
    pattern: '"orderId":\s*(\d+)'
    group: 1

  # 提取字符串
  - name: "username"
    type: regex
    pattern: '"userName":\s*"([^"]+)"'
    group: 1

  # 提取多个值（使用多个捕获组）
  - name: "email"
    type: regex
    pattern: '"email":\s*"([\w.]+@[\w.]+)"'
    group: 1
```

#### 6.1.4 多提取器配置

**一个步骤可以配置多个提取器**（v1.0.3+ Bug 修复）：

```yaml
extractors:
  # 提取器 1: JSONPath 提取订单 ID
  - name: order_id
    type: jsonpath
    path: "$.data.orderId"

  # 提取器 2: Regex 提取金额
  - name: amount
    type: regex
    pattern: '"amount":\s*([\d.]+)'
    group: 1

  # 提取器 3: Header 提取
  - name: auth_token
    type: header
    path: "Authorization"

  # 提取器 4: Cookie 提取
  - name: session_id
    type: cookie
    path: "sessionId"
```

**在后续步骤中使用提取的变量**：

```yaml
# 步骤 2: 使用提取的变量
- name: "创建订单"
  type: request
  method: POST
  url: "/api/orders"
  headers:
    Authorization: "${auth_token}"    # 使用提取的 Header
  body:
    orderId: "${order_id}"            # 使用提取的订单 ID
    amount: "${amount}"               # 使用提取的金额
```

#### 6.1.5 Header 提取器

```yaml
extractors:
  # 提取响应头
  - name: "content_type"
    type: header
    path: "Content-Type"

  # 提取自定义响应头
  - name: "request_id"
    type: header
    path: "X-Request-ID"
```

#### 6.1.6 Cookie 提取器

```yaml
extractors:
  # 提取 Cookie 值
  - name: "session_token"
    type: cookie
    path: "session_id"
```

#### 6.1.7 错误提示与调试技巧（v1.0.3+ 增强）

当变量提取失败时，框架会提供详细的中文错误提示和调试建议。

**错误提示示例**：

1. **JSONPath 路径未找到**
```
⚠️  变量提取异常: 'user_id'
   提取器类型: jsonpath
   提取路径: $.data.userId
   错误详情: ValueError: JSONPath 提取失败: 路径 '$.data.userId' 在响应中未找到数据。

   💡 JSONPath 路径建议:
      • 检查路径是否以 '$' 开头
      • 验证数组索引: $.data[0].field
      • 确认字段名称拼写正确
```

2. **Regex 捕获组索引超出范围**
```
⚠️  变量提取异常: 'order_id'
   提取器类型: regex
   提取路径: "orderId":\s*"([^"]+)"
   错误详情: ValueError: 捕获组索引 2 超出范围。正则表达式包含 1 个捕获组，但请求的是第 2 个组。

   💡 Regex 表达式建议:
      • 验证正则表达式语法
      • 检查捕获组索引 (group: 2)
      • 确保模式与响应数据匹配
```

3. **数据未匹配（返回 None）**
```
⚠️  变量提取失败: 'order_id'
   提取器类型: regex
   提取路径: "orderId":\s*"([^"]+)"
   可能原因: 响应中未找到匹配的数据
   建议: 请检查路径表达式是否正确，或确认响应数据结构
```

**常见提取错误及解决方案**：

| 错误类型 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 路径未找到 | 字段名错误或路径不存在 | 使用 `-v` 查看响应结构，检查字段名拼写 |
| 数组索引越界 | 访问超出数组范围 | 检查数组长度，使用 `$.data.length()` 验证 |
| 捕获组索引错误 | Regex 捕获组数量不足 | 调整 `group` 参数或修改正则表达式 |
| 正则语法错误 | 正则表达式格式错误 | 使用在线工具验证正则语法 |
| 响应格式不符 | API 返回格式与预期不同 | 检查 API 文档，确认响应数据结构 |

**调试技巧**：

1. **使用详细输出模式**
```bash
sisyphus --cases test.yaml -v
```
详细模式会显示完整的响应数据结构，帮助您确认字段路径。

2. **打印提取的变量**
```yaml
# 添加一个调试步骤
- name: "打印提取的变量"
  type: request
  method: POST
  url: "${base_url}/debug"
  body:
    extracted_value: "${variable_name}"  # 打印提取的变量
```

3. **逐步验证路径**
```yaml
extractors:
  # 先尝试提取父级对象
  - name: parent_data
    type: jsonpath
    path: "$.data"

  # 再尝试提取具体字段
  - name: user_id
    type: jsonpath
    path: "$.data.userId"
```

4. **使用在线工具验证**
- **正则表达式**: https://regex101.com/
- **JSONPath**: https://jsonpath.com/

### 6.2 步骤控制

```yaml
# 条件跳过
- name: "测试接口"
  skip_if: "${config.profiles.dev.env_mode} == 'production'"

# 条件执行
- name: "新功能测试"
  only_if: "${feature_enabled} == true"

# 依赖关系
- name: "查询订单"
  depends_on:
    - "用户登录"
    - "创建订单"
```

### 6.3 重试策略

```yaml
# 简单重试
- name: "可能失败的接口"
  retry_times: 3

# 高级重试策略
- name: "高级重试"
  retry_policy:
    max_attempts: 3
    strategy: exponential      # fixed/linear/exponential
    base_delay: 1.0           # 基础延迟（秒）
    max_delay: 10.0           # 最大延迟（秒）
```

### 6.4 钩子函数

```yaml
# 前置钩子
- name: "带前置钩子的步骤"
  setup:
    - name: "初始化"
      type: wait
      seconds: 1

# 后置钩子
  teardown:
    - name: "清理"
      type: request
      method: POST
      url: "/cleanup"
```

---

## 版本历史

| 版本 | 日期 | 引擎版本 | 说明 |
|------|------|----------|------|
| 1.1 | 2026-02-01 | 1.0.3 | 修正路径使用说明，增强 Regex 提取器支持 pattern/group 语法，修复多提取器 Bug |
| 1.0 | 2026-01-30 | 1.0.2 | 基于实际代码实现编写，包含完整的输入协议规范 |
