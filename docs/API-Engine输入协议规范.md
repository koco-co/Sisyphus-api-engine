# API-Engine 输入协议规范 v1.0

> **版本说明**: 这是 Sisyphus API Engine v1.0.2 的实际输入协议规范，基于代码实现编写。

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

---

## 4. 变量系统

### 4.1 变量引用语法

```yaml
variables:
  # 引用全局变量
  api_url: "${base_url}"

  # 引用环境配置
  env: "${config.profiles.dev.env_mode}"

  # 引用上一步提取的变量
  token: "${access_token}"

  # 在请求中使用
  url: "${base_url}/users/${user_id}"
```

### 4.2 变量作用域优先级

从低到高：
1. 全局变量（`config.variables`）
2. 环境变量（`config.profiles.{profile}.variables`）
3. 提取变量（从响应中提取）

### 4.3 内置模板函数

```yaml
variables:
  # 随机字符串
  random_str: "${random_string(10)}"

  # UUID
  unique_id: "${uuid()}"

  # 当前时间
  current_time: "${now()}"
  timestamp: "${timestamp()}"

  # Base64编码
  encoded: "${base64_encode('hello')}"
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

| 表达式 | 说明 |
|---------|------|
| `$.status_code` | 根对象属性 |
| `$.data.user.id` | 嵌套属性 |
| `$.data.items[0]` | 数组第一个元素 |
| `$.data.users[?id=1].name` | 过滤表达式 |
| `$..name` | 递归查找 |

#### 5.3.1.1 重要：提取器与验证器的路径差异

在编写 JSONPath 表达式时，**提取器（extractors）**和**验证器（validations）**使用不同的数据源，因此路径写法不同：

**数据源差异**：

| 组件 | 数据源 | 路径格式 | 说明 |
|------|--------|----------|------|
| **验证器** | `response.body` | `$.json.*` | 自动从响应体中提取，无需 `body.` 前缀 |
| **提取器** | `response`（完整） | `$.body.json.*` | 需要从完整响应中提取，必须加 `body.` 前缀 |

**响应结构参考**：
```json
{
  "status_code": 200,
  "headers": {...},
  "body": {
    "args": {},
    "data": "...",
    "json": {          // 请求/响应的 JSON 数据
      "username": "...",
      "token": "..."
    },
    "method": "POST",
    "origin": "...",
    "url": "..."
  }
}
```

**实际示例**：

```yaml
# 验证器：使用 $.json.*
validations:
  - type: eq
    path: "$.json.username"
    expect: "admin"
    description: "验证用户名"

# 提取器：使用 $.body.json.*
extractors:
  - name: "user_name"
    path: "$.body.json.username"    # 注意：必须加 body. 前缀
    description: "提取用户名"
```

**常见错误**：
- ❌ 提取器中使用 `$.json.username` → 无法提取
- ✅ 提取器应使用 `$.body.json.username` → 正确提取
- ✅ 验证器使用 `$.json.username` → 正确验证

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

```yaml
extractors:
  - name: "access_token"      # 变量名
    path: "$.body.data.token"      # JSONPath表达式（提取器需要 body. 前缀）
  - name: "user_id"
    path: "$.body.data.user.id"
```

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
| 1.0 | 2026-01-30 | 1.0.2 | 基于实际代码实现编写，包含完整的输入协议规范 |
