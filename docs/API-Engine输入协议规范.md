# API-Engine 输入协议规范 v1.0

> **变更说明**: 相比 v1.0，新增了测试步骤控制、数据驱动、钩子函数、Mock支持等企业级特性。

---

## 目录

- [1. 完整示例](#1-完整示例)
- [2. 配置结构详解](#2-配置结构详解)
- [3. 测试步骤类型](#3-测试步骤类型)
- [4. 变量系统](#4-变量系统)
- [5. 断言系统](#5-断言系统)
- [6. 高级特性](#6-高级特性)
- [7. 枚举与常量](#7-枚举与常量)

---

## 1. 完整示例

```yaml
# ==============================================================================
# 适用引擎: api-engine
# 版本: 2.0
# 描述: 电商全流程测试示例（包含所有核心特性）
# ==============================================================================

config:
  # ==================== 基础配置 ====================
  name: "电商下单全流程测试_V2.0"
  version: "1.0.0"
  author: "QA Team"

  # ==================== 环境配置 ====================
  base_url: "https://api.example.com"
  timeout: 30
  retries: 2
  retry_delay: 1000  # 重试延迟(ms)

  # ==================== 环境切换 ====================
  profiles:
    dev:
      base_url: "http://dev-api.example.com"
      variables:
        env_mode: "dev"
    staging:
      base_url: "http://staging-api.example.com"
      variables:
        env_mode: "staging"
    prod:
      base_url: "https://api.example.com"
      variables:
        env_mode: "production"

  active_profile: "dev"  # 当前激活的环境

  # ==================== 全局变量 ====================
  variables:
    # 环境变量引用
    api_base: "${base_url}"
    env_mode: "${config.profiles.${active_profile}.variables.env_mode}"

    # 数据库连接别名（引用后端配置）
    db_main: "mysql_main"
    db_cache: "redis_cache"

    # 业务变量
    default_sku: "SKU_123456"
    test_user: "test_user_01"

  # ==================== 全局钩子 ====================
  setup:
    - name: "清理测试数据"
      type: "database"
      connection: "${db_main}"
      sql_type: "mysql"
      command: "execute"
      sql: "DELETE FROM orders WHERE user_id = 10086 AND status = 'PENDING';"

    - name: "初始化测试环境"
      type: "api"
      request:
        method: "POST"
        url: "/test-env/init"
        json:
          mode: "${env_mode}"

  teardown:
    - name: "恢复测试环境"
      type: "api"
      request:
        method: "POST"
        url: "/test-env/cleanup"

  # ==================== 日志配置 ====================
  log_level: "normal"  # [minimal, normal, verbose]
  save_response: true  # 是否保存完整响应

# ==================== 测试步骤 ====================
teststeps:
  # ============================================================================
  # 场景1: 数据驱动测试（批量验证）
  # ============================================================================
  - name: "批量验证用户登录"
    id: "step_01"
    type: "api"
    tags: ["smoke", "auth", "critical"]
    priority: "P0"

    # 数据驱动：从CSV/JSON文件读取多组数据
    data_provider: "test_data/login_users.csv"

    # 或内联数据
    # data_provider:
    #   - { username: "user1", password: "pass1", expected: 200 }
    #   - { username: "user2", password: "pass2", expected: 200 }

    request:
      method: "POST"
      url: "/auth/login"
      json:
        username: "${username}"  # 引用 data_provider 中的变量
        password: "${password}"

    extract:
      access_token: "body.data.token"
      user_id: "body.data.user_info.id"

    validate:
      - eq: ["status_code", "${expected}"]
      - eq: ["body.code", 0]
      - len_gt: ["body.data.token", 20]

    # 钩子：步骤级前置/后置
    before_step:
      - type: "wait"
        duration_ms: 100

    after_step:
      - type: "script"
        source: "save_token_to_cache.py"
        args:
          token: "${access_token}"

  # ============================================================================
  # 场景2: 条件执行（生产环境跳过）
  # ============================================================================
  - name: "调用测试专用接口"
    id: "step_02"
    type: "api"
    tags: ["test-only"]
    priority: "P1"

    # 条件控制
    skip_if: "${env_mode} == 'production'"
    only_if: "${feature_enabled} == true"

    request:
      method: "POST"
      url: "/test/debug"
      json:
        action: "reset_cache"

  # ============================================================================
  # 场景3: 依赖关系管理
  # ============================================================================
  - name: "查询订单详情（依赖登录）"
    id: "step_03"
    type: "api"
    tags: ["order"]
    priority: "P0"

    # 依赖上一步提取的变量
    depends_on: ["step_01"]

    request:
      method: "GET"
      url: "/orders/detail"
      headers:
        Authorization: "Bearer ${access_token}"
      params:
        order_id: "ORDER_001"

    validate:
      - eq: ["status_code", 200]
      - eq: ["body.data.user_id", "${user_id}"]

  # ============================================================================
  # 场景4: Mock第三方服务
  # ============================================================================
  - name: "调用支付接口（Mock响应）"
    id: "step_04"
    type: "api"
    tags: ["payment", "mock"]
    priority: "P0"

    request:
      method: "POST"
      url: "/payment/create"
      json:
        order_id: "ORDER_001"
        amount: 99.00

    # Mock配置
    mock:
      enabled: true
      response:
        status_code: 200
        headers:
          X-Mocked: "true"
        body:
          code: 0
          msg: "success"
          data:
            payment_id: "MOCK_PAYMENT_123"
            status: "success"

    validate:
      - eq: ["body.code", 0]
      - contains: ["body.data.payment_id", "MOCK"]

  # ============================================================================
  # 场景5: 并发压测
  # ============================================================================
  - name: "并发压测：商品搜索"
    id: "step_05"
    type: "api"
    tags: ["performance"]
    priority: "P1"

    # 并发配置
    parallel:
      enabled: true
      threads: 10  # 10个并发线程
      ramp_up: 5   # 5秒内启动所有线程
      iterations: 100  # 每个线程执行100次

    request:
      method: "GET"
      url: "/products/search"
      params:
        keyword: "手机"

    validate:
      - eq: ["status_code", 200]
      - lt: ["elapsed", 1.0]  # 响应时间小于1秒

  # ============================================================================
  # 场景6: 数据库操作+断言
  # ============================================================================
  - name: "验证订单入库"
    id: "step_06"
    type: "database"
    tags: ["database"]
    priority: "P0"

    connection: "${db_main}"
    sql_type: "mysql"
    command: "query"
    sql: "SELECT * FROM orders WHERE order_id = 'ORDER_001'"

    # 数据库断言
    validate:
      - eq: ["rows[0].status", "PENDING"]
      - eq: ["rows[0].amount", 99.00]
      - len_eq: ["rows", 1]

    extract:
      order_create_time: "rows[0].create_time"

  # ============================================================================
  # 场景7: 文件上传
  # ============================================================================
  - name: "上传用户头像"
    id: "step_07"
    type: "api"
    tags: ["upload"]
    priority: "P1"

    request:
      method: "POST"
      url: "/user/avatar"
      headers:
        Authorization: "Bearer ${access_token}"

      # Multipart上传
      upload:
        file: "test_data/avatar.jpg"
        form_fields:
          type: "avatar"
          user_id: "${user_id}"

    validate:
      - eq: ["status_code", 200]
      - contains: ["body.data.url", "avatar"]

  # ============================================================================
  # 场景8: 自定义脚本钩子
  # ============================================================================
  - name: "执行自定义Python脚本"
    id: "step_08"
    type: "script"
    tags: ["custom"]
    priority: "P2"

    # 脚本路径（相对于项目根目录）
    source: "scripts/custom_validator.py"

    # 传递参数
    args:
      api_response: "${response.body}"
      threshold: 100

    # 提取脚本返回值
    extract:
      custom_result: "return_value"

  # ============================================================================
  # 场景9: 等待/延迟
  # ============================================================================
  - name: "等待异步任务完成"
    id: "step_09"
    type: "wait"
    tags: ["async"]
    priority: "P1"

    duration_ms: 2000

    # 或等待条件
    # wait_condition:
    #   type: "api"
    #   request: { url: "/jobs/status" }
    #   check: "body.data.status == 'completed'"
    #   timeout: 30
    #   interval: 2

  # ============================================================================
  # 场景10: 循环测试
  # ============================================================================
  - name: "批量创建订单"
    id: "step_10"
    type: "api"
    tags: ["batch"]
    priority: "P1"

    # 循环配置
    loop:
      type: "for"  # [for, while]
      times: 10
      variable: "index"  # 当前循环索引变量名

    request:
      method: "POST"
      url: "/orders/create"
      json:
        sku_id: "${default_sku}"
        quantity: 1
        remark: "自动创建订单 #${index}"

    validate:
      - eq: ["status_code", 201]

  # ============================================================================
  # 场景11: 复杂断言示例
  # ============================================================================
  - name: "验证复杂响应结构"
    id: "step_11"
    type: "api"
    tags: ["validation"]
    priority: "P0"

    request:
      method: "GET"
      url: "/products/detail"
      params:
        sku_id: "${default_sku}"

    validate:
      # 基础断言
      - eq: ["status_code", 200]
      - eq: ["body.code", 0]

      # 类型断言
      - type: ["body.data.price", "number"]
      - type: ["body.data.tags", "array"]

      # 数组索引断言
      - eq: ["body.data.tags[0]", "hot"]

      # JSONPath过滤断言
      - contains: ["body.data.reviews[?rating==5].comment", "excellent"]

      # 对象包含断言
      - contains: ["body.data", { "in_stock": true, "free_shipping": true }]

      # 数据库联查断言
      - eq: ["body.data.price", "${db_query(SELECT price FROM product WHERE sku='${default_sku}')}"]

      # 逻辑运算
      - and:
          - eq: ["body.data.stock", 100]
          - gt: ["body.data.sales", 50]

      - or:
          - eq: ["body.data.status", "available"]
          - eq: ["body.data.status", "low_stock"]
```

---

## 2. 配置结构详解

### 2.1 Config 基础配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 测试用例名称 |
| `version` | string | ❌ | 用例版本号 |
| `author` | string | ❌ | 作者 |
| `base_url` | string | ❌ | 基础URL（会被环境配置覆盖） |
| `timeout` | integer | ❌ | 全局超时时间（秒），默认30 |
| `retries` | integer | ❌ | 全局重试次数，默认0 |
| `retry_delay` | integer | ❌ | 重试延迟（毫秒），默认1000 |
| `log_level` | string | ❌ | 日志级别：[minimal, normal, verbose] |
| `save_response` | boolean | ❌ | 是否保存完整响应，默认true |

### 2.2 环境配置（profiles）

```yaml
config:
  profiles:
    dev:
      base_url: "http://dev-api.example.com"
      variables:
        env_mode: "dev"
        db_alias: "mysql_dev"

    staging:
      base_url: "http://staging-api.example.com"
      variables:
        env_mode: "staging"
        db_alias: "mysql_staging"

  active_profile: "dev"  # 或通过环境变量指定
```

**切换方式**：
1. YAML中直接指定 `active_profile`
2. 后端API传入参数覆盖 `?profile=staging`
3. 环境变量 `export TEST_PROFILE=staging`

### 2.3 全局变量（variables）

```yaml
config:
  variables:
    # 静态变量
    api_key: "sk_test_123456"

    # 引用其他变量
    api_url: "${base_url}/v1"

    # 引用环境配置
    env_mode: "${config.profiles.${active_profile}.variables.env_mode}"

    # 引用数据库连接别名（后端管理）
    db_main: "mysql_main"
```

### 2.4 全局钩子（setup/teardown）

```yaml
config:
  setup:
    - name: "初始化测试数据"
      type: "database"
      connection: "mysql_main"
      sql: "DELETE FROM temp_table;"

    - name: "启动Mock服务"
      type: "script"
      source: "scripts/start_mock.py"

  teardown:
    - name: "清理测试数据"
      type: "api"
      request:
        method: "POST"
        url: "/test/cleanup"
```

---

## 3. 测试步骤类型

### 3.1 API请求步骤

```yaml
teststeps:
  - name: "API请求示例"
    type: "api"
    id: "step_01"

    # 步骤级配置
    timeout: 10  # 覆盖全局配置
    retries: 3

    # 请求配置
    request:
      method: "POST"
      url: "/users/login"
      headers:
        Content-Type: "application/json"
        User-Agent: "ApiEngine/2.0"

      # Query参数
      params:
        debug: "true"

      # 请求体（JSON）
      json:
        username: "test_user"
        password: "pass123"

      # 或表单提交
      # data:
      #   username: "test_user"
      #   password: "pass123"

      # 或文件上传
      # upload:
      #   file: "test_data/avatar.jpg"
      #   form_fields:
      #     type: "avatar"

    # 变量提取
    extract:
      token: "body.data.token"
      user_id: "body.data.user.id"

    # 断言验证
    validate:
      - eq: ["status_code", 200]
      - eq: ["body.code", 0]

    # 钩子
    before_step:
      - type: "wait"
        duration_ms: 100

    after_step:
      - type: "script"
        source: "log_request.py"
```

### 3.2 数据库操作步骤

```yaml
teststeps:
  - name: "数据库操作示例"
    type: "database"
    id: "step_01"

    # 连接配置（引用后端配置的别名）
    connection: "mysql_main"

    # 数据库类型
    sql_type: "mysql"  # [mysql, postgresql, oracle, sqlserver]

    # 命令类型
    command: "execute"  # [execute, query]

    # SQL语句
    sql: "INSERT INTO users (name, email) VALUES ('test', 'test@example.com');"

    # 预编译语句（防止SQL注入）
    # sql: "INSERT INTO users (name, email) VALUES (%s, %s);"
    # params: ["test", "test@example.com"]

    # 断言（仅query类型）
    validate:
      - len_eq: ["rows", 1]
      - eq: ["rows[0].id", 123]

    # 提取数据
    extract:
      user_id: "rows[0].id"
      created_at: "rows[0].created_at"
```

### 3.3 等待步骤

```yaml
teststeps:
  - name: "等待示例"
    type: "wait"
    id: "step_01"

    # 固定延迟
    duration_ms: 2000

    # 或条件等待
    # wait_condition:
    #   type: "api"  # [api, database, custom]
    #   request:
    #     method: "GET"
    #     url: "/jobs/status"
    #   check: "body.data.status == 'completed'"
    #   timeout: 30
    #   interval: 2
```

### 3.4 脚本步骤

```yaml
teststeps:
  - name: "执行自定义脚本"
    type: "script"
    id: "step_01"

    # 脚本路径（支持.py, .js）
    source: "scripts/custom_validator.py"

    # 传递参数（JSON格式）
    args:
      api_response: "${response.body}"
      threshold: 100

    # 超时时间
    timeout: 60
```

---

## 4. 变量系统

### 4.1 变量引用语法

```yaml
variables:
  # 引用全局变量
  base: "${base_url}"

  # 引用环境变量
  env: "${ENV_MODE}"

  # 引用上一步提取的变量
  token: "${access_token}"

  # 引用嵌套对象
  value: "${config.profiles.dev.variables.api_key}"

  # 默认值
  optional: "${optional_var|default_value}"
```

### 4.2 变量提取（extract）

```yaml
extract:
  # 从响应体提取（JSONPath）
  token: "body.data.token"
  user_id: "body.data.user_info.id"
  first_tag: "body.data.tags[0]"

  # 从响应头提取
  server: "headers.Server"
  set_cookie: "headers.Set-Cookie"

  # 从Cookies提取
  session_id: "cookies.sessionid"

  # 提取完整响应
  full_response: "response"

  # 性能指标
  response_time: "elapsed"
```

### 4.3 内置函数

```yaml
variables:
  # 数据库查询函数
  product_price: "${db_query(SELECT price FROM product WHERE sku='SKU123')}"

  # 时间函数
  current_time: "${now()}"
  timestamp: "${timestamp()}"
  formatted_date: "${date_format('%Y-%m-%d')}"

  # 随机函数
  random_id: "${random_int(1000, 9999)}"
  random_uuid: "${uuid()}"
  random_string: "${random_string(10)}"

  # 字符串函数
  upper: "${upper(test)}"
  lower: "${lower(TEST)}"
  md5: "${md5('password123')}"
```

---

## 5. 断言系统

### 5.1 基础比较器

| 比较器 | 说明 | 示例 |
|--------|------|------|
| `eq` | 等于 | `- eq: ["status_code", 200]` |
| `ne` | 不等于 | `- ne: ["body.error", null]` |
| `gt` | 大于 | `- gt: ["body.data.count", 0]` |
| `ge` | 大于等于 | `- ge: ["body.data.age", 18]` |
| `lt` | 小于 | `- lt: ["elapsed", 1.0]` |
| `le` | 小于等于 | `- le: ["body.data.stock", 100]` |
| `contains` | 包含 | `- contains: ["body.data.tags", "hot"]` |
| `not_contains` | 不包含 | `- not_contains: ["body.msg", "error"]` |
| `len_eq` | 长度等于 | `- len_eq: ["body.data.items", 10]` |
| `len_gt` | 长度大于 | `- len_gt: ["body.data.token", 20]` |
| `len_lt` | 长度小于 | `- len_lt: ["body.data.errors", 1]` |
| `startswith` | 以...开头 | `- startswith: ["body.data.url", "https"]` |
| `endswith` | 以...结尾 | `- endswith: ["body.data.email", "@example.com"]` |
| `type` | 类型检查 | `- type: ["body.data.price", "number"]` |
| `regex` | 正则匹配 | `- regex: ["body.data.phone", "^1[3-9]\\d{9}$"]` |
| `in` | 在范围内 | `- in: ["body.data.status", ["pending", "processing"]]` |
| `not_in` | 不在范围内 | `- not_in: ["body.data.type", ["deleted", "banned"]]` |

### 5.2 复杂断言

```yaml
validate:
  # 逻辑与
  - and:
      - eq: ["status_code", 200]
      - eq: ["body.code", 0]
      - gt: ["body.data.count", 0]

  # 逻辑或
  - or:
      - eq: ["body.data.status", "available"]
      - eq: ["body.data.status", "low_stock"]

  # 逻辑非
  - not:
      - eq: ["body.error", "timeout"]

  # 嵌套组合
  - and:
      - or:
          - eq: ["body.data.type", "A"]
          - eq: ["body.data.type", "B"]
      - gt: ["body.data.value", 100]
```

### 5.3 提取目标

| 目标 | 说明 | 示例 |
|------|------|------|
| `status_code` | HTTP状态码 | `status_code` |
| `body` | 响应体（JSON） | `body.data.user.id` |
| `headers` | 响应头 | `headers.Content-Type` |
| `cookies` | 响应Cookies | `cookies.sessionid` |
| `elapsed` | 响应时间（秒） | `elapsed` |
| `response` | 完整响应对象 | `response` |

---

## 6. 高级特性

### 6.1 测试步骤控制

```yaml
teststeps:
  # 条件跳过
  - name: "测试专用接口"
    skip_if: "${env_mode} == 'production'"

  # 条件执行
  - name: "新功能测试"
    only_if: "${feature_enabled} == true"

  # 依赖关系
  - name: "查询订单"
    depends_on: ["step_login", "step_create_order"]

  # 标签和优先级
  - name: "核心接口"
    tags: ["smoke", "critical", "auth"]
    priority: "P0"  # [P0, P1, P2, P3]
```

### 6.2 数据驱动测试

```yaml
teststeps:
  # 从文件读取
  - name: "批量登录测试"
    data_provider: "test_data/login_users.csv"
    # CSV格式：
    # username,password,expected
    # user1,pass1,200
    # user2,pass2,200

  # 内联数据
  - name: "批量创建订单"
    data_provider:
      - { sku: "SKU001", qty: 1, expected: 201 }
      - { sku: "SKU002", qty: 2, expected: 201 }

  # 从数据库读取
  - name: "从数据库读取测试数据"
    data_provider:
      type: "database"
      connection: "mysql_main"
      sql: "SELECT username, password FROM test_users WHERE active = 1"
```

### 6.3 并发测试

```yaml
teststeps:
  - name: "并发压测"
    type: "api"
    parallel:
      enabled: true
      threads: 10      # 并发线程数
      ramp_up: 5       # 启动时间（秒）
      iterations: 100  # 每个线程执行次数
      think_time: 1    # 每次执行间隔（秒）

    request:
      method: "GET"
      url: "/products/search"
```

### 6.4 循环测试

```yaml
teststeps:
  # 固定次数循环
  - name: "批量创建"
    loop:
      type: "for"
      times: 10
      variable: "index"  # 当前索引变量名

    request:
      json:
        remark: "第${index}次创建"

  # 条件循环
  - name: "轮询等待"
    loop:
      type: "while"
      condition: "${response.body.data.status} != 'completed'"
      max_iterations: 30
      interval: 2  # 每次循环间隔（秒）

    request:
      url: "/jobs/status"
```

### 6.5 Mock支持

```yaml
teststeps:
  - name: "调用第三方支付"
    mock:
      enabled: true
      # 简单Mock
      response:
        status_code: 200
        body:
          code: 0
          data:
            payment_id: "MOCK_123"

      # 或动态Mock（使用脚本）
      # script: "scripts/mock_payment.py"

      # 或条件Mock
      # conditions:
      #   - if: "${request.body.amount} > 100"
      #     response: { body: { code: 1, msg: "金额超限" } }
      #   - else:
      #     response: { body: { code: 0, msg: "success" } }
```

### 6.6 钩子函数

```yaml
teststeps:
  - name: "带钩子的步骤"

    # 前置钩子
    before_step:
      - type: "api"
        request: { url: "/before" }
      - type: "wait"
        duration_ms: 100

    # 后置钩子
    after_step:
      - type: "script"
        source: "scripts/cleanup.py"
      - type: "api"
        request: { url: "/after" }
```

---

## 7. 枚举与常量

### 7.1 步骤类型（type）

| 值 | 说明 |
|----|------|
| `api` | HTTP请求 |
| `database` | 数据库操作 |
| `wait` | 等待/延迟 |
| `script` | 自定义脚本 |

### 7.2 数据库类型（sql_type）

| 值 | 说明 |
|----|------|
| `mysql` | MySQL |
| `postgresql` | PostgreSQL |
| `oracle` | Oracle |
| `sqlserver` | SQL Server |
| `mongodb` | MongoDB |

### 7.3 数据库命令（command）

| 值 | 说明 |
|----|------|
| `execute` | 执行（INSERT/UPDATE/DELETE） |
| `query` | 查询（SELECT） |

### 7.4 HTTP方法（method）

| 值 | 说明 |
|----|------|
| `GET` | 查询 |
| `POST` | 创建 |
| `PUT` | 更新（全量） |
| `PATCH` | 更新（部分） |
| `DELETE` | 删除 |
| `HEAD` | 获取头信息 |
| `OPTIONS` | 获取支持的方法 |

### 7.5 优先级（priority）

| 值 | 说明 |
|----|------|
| `P0` | 核心功能，必须通过 |
| `P1` | 重要功能 |
| `P2` | 一般功能 |
| `P3` | 可选功能 |

### 7.6 状态（status）

| 值 | 说明 |
|----|------|
| `success` | 成功 |
| `failed` | 失败（断言不通过） |
| `error` | 错误（执行异常） |
| `skipped` | 跳过 |
| `running` | 运行中 |

### 7.7 日志级别（log_level）

| 值 | 说明 |
|----|------|
| `minimal` | 最小（仅关键信息） |
| `normal` | 正常（默认） |
| `verbose` | 详细（包含请求/响应完整信息） |

---

## 附录：安全最佳实践

### A.1 敏感信息处理

```yaml
# ❌ 错误：直接硬编码密码
config:
  variables:
    db_password: "Aa9999!"

# ✅ 正确：使用环境变量
config:
  variables:
    db_password: "${DB_PASSWORD}"  # 从环境变量读取

# ✅ 正确：使用连接别名
config:
  variables:
    db_alias: "mysql_main"  # 引用后端配置的连接
```

### A.2 SQL注入防护

```yaml
# ❌ 错误：字符串拼接
sql: "SELECT * FROM users WHERE name = '${user_name}'"

# ✅ 正确：使用预编译语句
sql: "SELECT * FROM users WHERE name = %s"
params: ["${user_name}"]
```

### A.3 响应脱敏

```yaml
config:
  # 自动脱敏敏感字段
  sensitive_fields:
    - "password"
    - "token"
    - "credit_card"
    - "id_card"

  # 脱敏策略
  masking_strategy: "partial"  # [none, partial, full]
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2026-01-27 | 新增：测试步骤控制、数据驱动、并发测试、Mock支持等 |
| 1.0 | 2026-01-20 | 初始版本 |
