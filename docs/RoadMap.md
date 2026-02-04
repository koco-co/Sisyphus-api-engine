# Sisyphus API Engine 学习路线图

> 本文档为 Sisyphus API Engine 的学习路径规划，帮助你从零开始掌握 YAML 声明式 API 测试。

---

## 📚 学习路线概览

```mermaid
graph LR
    A[快速入门] --> B[HTTP请求]
    B --> C[变量系统]
    C --> D[验证断言]
    D --> E[提取器]
    E --> F[环境配置]
    F --> G[流程控制]
    G --> H[重试与等待]
    H --> I[循环控制]
    I --> J[并发执行]
    J --> K[数据驱动]
    K --> L[脚本执行]
    L --> M[数据库操作]
    M --> N[Mock服务器]
    N --> O[WebSocket]
    O --> P[性能测试]
    P --> Q[最佳实践]
```

---

## 🎯 学习阶段

### 阶段 0：快速入门

**目标**：了解框架基本概念，运行第一个测试

**核心内容**：
- 安装 Sisyphus API Engine
- YAML 测试用例基本结构
- 使用命令行运行测试

**简单示例**：
```yaml
name: "我的第一个测试"
description: "Hello World 示例"

steps:
  - 发起GET请求:
      type: request
      method: GET
      url: "https://httpbin.org/get"
      validations:
        - type: status_code
          expect: 200
```

**运行命令**：
```bash
sisyphus --cases my_first_test.yaml
```

📖 **详细文档**：[00_快速入门.md](./00_快速入门.md)

---

### 阶段 1：HTTP 请求

**目标**：掌握各种 HTTP 请求方法和参数配置

**核心内容**：
- HTTP 方法（GET/POST/PUT/DELETE/PATCH）
- 请求参数（params/headers/body/cookies）
- 请求体格式（JSON/Form/Multipart）

**简单示例**：
```yaml
steps:
  - POST请求示例:
      type: request
      method: POST
      url: "https://api.example.com/users"
      headers:
        Content-Type: "application/json"
        Authorization: "Bearer token123"
      body:
        name: "张三"
        email: "zhangsan@example.com"
```

📖 **详细文档**：[01_HTTP请求.md](./01_HTTP请求.md)

---

### 阶段 2：变量系统

**目标**：掌握变量定义、引用和模板函数

**核心内容**：
- 全局变量定义（config.variables）
- 变量引用语法（`${变量名}`）
- 内置模板函数（random_string/uuid/now 等）
- 变量嵌套引用

**简单示例**：
```yaml
config:
  variables:
    base_url: "https://api.example.com"
    user_id: "${uuid()}"

steps:
  - 使用变量:
      type: request
      url: "${base_url}/users/${user_id}"
```

📖 **详细文档**：[02_变量系统.md](./02_变量系统.md)

---

### 阶段 3：验证断言

**目标**：掌握响应验证和断言语法

**核心内容**：
- 状态码验证（status_code）
- 基础验证器（eq/ne/gt/lt/contains）
- 高级验证器（regex/type/between/and/or）
- JSONPath 增强函数
- 自定义错误消息

**简单示例**：
```yaml
validations:
  - type: status_code
    expect: 200
  - type: eq
    path: "$.code"
    expect: 0
    error_message: "业务状态码错误"
  - type: contains
    path: "$.data.name"
    expect: "张"
```

📖 **详细文档**：[03_验证断言.md](./03_验证断言.md)

---

### 阶段 4：提取器

**目标**：掌握从响应中提取变量

**核心内容**：
- JSONPath 提取器
- 正则表达式提取器
- Header 提取器
- Cookie 提取器
- 提取器默认值

**简单示例**：
```yaml
extractors:
  - type: jsonpath
    name: user_id
    path: "$.data.id"
    default: "unknown"
  - type: regex
    name: token
    path: "$.response"
    pattern: "token=(\\w+)"
```

📖 **详细文档**：[04_提取器.md](./04_提取器.md)

---

### 阶段 5：环境配置

**目标**：掌握多环境管理和配置切换

**核心内容**：
- Profiles 环境配置
- 全局配置文件（.sisyphus/config.yaml）
- !include 引入外部配置
- 配置优先级

**简单示例**：
```yaml
config:
  profiles:
    dev:
      base_url: "http://dev.example.com"
    prod:
      base_url: "https://api.example.com"
  active_profile: "dev"
```

**切换环境**：
```bash
sisyphus --cases test.yaml --profile prod
```

📖 **详细文档**：[05_环境配置.md](./05_环境配置.md)

---

### 阶段 6：流程控制

**目标**：掌握步骤执行的条件控制

**核心内容**：
- 条件执行（skip_if/only_if）
- 步骤依赖（depends_on）
- Setup/Teardown 钩子

**简单示例**：
```yaml
steps:
  - 登录:
      type: request
      url: "/login"
      extractors:
        - type: jsonpath
          name: token
          path: "$.token"

  - 获取用户信息:
      type: request
      url: "/user"
      depends_on: ["登录"]
      skip_if: "${token} == ''"
```

📖 **详细文档**：[06_流程控制.md](./06_流程控制.md)

---

### 阶段 7：重试与等待

**目标**：掌握失败重试和等待机制

**核心内容**：
- 重试策略（fixed/exponential/linear）
- 重试条件配置
- 固定等待（wait）
- 条件等待

**简单示例**：
```yaml
steps:
  - 带重试的请求:
      type: request
      url: "/api/unstable"
      retry_policy:
        max_attempts: 3
        strategy: exponential
        base_delay: 1.0

  - 等待2秒:
      type: wait
      seconds: 2
```

📖 **详细文档**：[07_重试与等待.md](./07_重试与等待.md)

---

### 阶段 8：循环控制

**目标**：掌握循环执行步骤

**核心内容**：
- For 循环（遍历列表）
- While 循环（条件循环）
- 循环变量

**简单示例**：
```yaml
steps:
  - 批量创建用户:
      type: loop
      loop_type: for
      items: ["Alice", "Bob", "Charlie"]
      steps:
        - 创建用户:
            type: request
            method: POST
            url: "/users"
            body:
              name: "${item}"
```

📖 **详细文档**：[08_循环控制.md](./08_循环控制.md)

---

### 阶段 9：并发执行

**目标**：掌握并发测试和性能测试基础

**核心内容**：
- 并发步骤配置
- 并发数控制
- 结果聚合

**简单示例**：
```yaml
steps:
  - 并发请求:
      type: concurrent
      concurrency: 10
      steps:
        - 发送请求:
            type: request
            url: "/api/test"
```

📖 **详细文档**：[09_并发执行.md](./09_并发执行.md)

---

### 阶段 10：数据驱动

**目标**：掌握数据驱动测试

**核心内容**：
- CSV 数据源
- JSON 数据源
- 数据库数据源
- 变量前缀配置

**简单示例**：
```yaml
config:
  data_source:
    type: csv
    file_path: "users.csv"
    has_header: true
  data_iterations: true

steps:
  - 测试用户登录:
      type: request
      url: "/login"
      body:
        username: "${username}"
        password: "${password}"
```

📖 **详细文档**：[10_数据驱动.md](./10_数据驱动.md)

---

### 阶段 11：脚本执行

**目标**：掌握自定义脚本执行

**核心内容**：
- Python 脚本执行
- 安全沙箱机制
- 脚本内变量操作
- 脚本返回值

**简单示例**：
```yaml
steps:
  - 执行Python脚本:
      type: script
      script_type: python
      script: |
        import hashlib
        data = get_var("raw_data")
        signature = hashlib.md5(data.encode()).hexdigest()
        set_var("signature", signature)
```

📖 **详细文档**：[11_脚本执行.md](./11_脚本执行.md)

---

### 阶段 12：数据库操作

**目标**：掌握数据库集成测试

**核心内容**：
- MySQL/PostgreSQL/SQLite 支持
- 查询操作（query）
- 执行操作（exec）
- 参数化查询

**简单示例**：
```yaml
steps:
  - 查询用户:
      type: database
      database:
        type: sqlite
        path: "test.db"
      operation: query
      sql: "SELECT * FROM users WHERE id = ?"
      params: [1]
      extractors:
        - type: jsonpath
          name: user_name
          path: "$[0].name"
```

📖 **详细文档**：[12_数据库操作.md](./12_数据库操作.md)

---

### 阶段 13：Mock 服务器

**目标**：掌握 Mock 服务器的使用

**核心内容**：
- 启动 Mock 服务器
- 配置 Mock 响应
- 动态响应

**简单示例**：
```yaml
mock:
  enabled: true
  port: 8888
  routes:
    - path: "/api/users"
      method: GET
      response:
        status: 200
        body:
          users: []
```

📖 **详细文档**：[13_Mock服务器.md](./13_Mock服务器.md)

---

### 阶段 14：WebSocket

**目标**：掌握 WebSocket 实时推送

**核心内容**：
- WebSocket 服务器配置
- 实时测试进度推送
- 事件订阅

📖 **详细文档**：[14_WebSocket.md](./14_WebSocket.md)

---

### 阶段 15：性能测试

**目标**：掌握性能测试功能

**核心内容**：
- 性能指标收集
- 压力测试配置
- 性能报告

📖 **详细文档**：[15_性能测试.md](./15_性能测试.md)

---

### 阶段 16：最佳实践

**目标**：掌握项目组织和最佳实践

**核心内容**：
- 项目目录结构
- 配置分层管理
- 测试用例组织
- CI/CD 集成

📖 **详细文档**：[16_最佳实践.md](./16_最佳实践.md)

---

## 🔗 相关资源

- [README.md](../README.md) - 项目说明
- [CHANGELOG.md](../CHANGELOG.md) - 更新日志
- [examples/](../examples/) - 示例用例
