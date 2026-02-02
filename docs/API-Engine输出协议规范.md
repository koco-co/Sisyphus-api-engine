# API-Engine 输出协议规范 v1.0

> **版本说明**: 这是 Sisyphus API Engine v1.0.2 的实际输出协议规范，基于代码实现编写。

---

## 目录

- [1. 完整示例](#1-完整示例)
- [2. 结构详解](#2-结构详解)
- [3. 字段说明](#3-字段说明)
- [4. 状态码与错误类型](#4-状态码与错误类型)
- [5. 输出格式](#5-输出格式)

---

## 1. 完整示例

### 1.1 Verbose 模式完整输出

```json
{
  "test_case": {
    "name": "变量基础语法测试",
    "status": "passed",
    "start_time": "2026-01-30T20:30:36.663852",
    "end_time": "2026-01-30T20:30:44.201488",
    "duration": 7.537636
  },
  "statistics": {
    "total_steps": 7,
    "passed_steps": 7,
    "failed_steps": 0,
    "skipped_steps": 0,
    "pass_rate": 100.0
  },
  "steps": [
    {
      "name": "使用全局变量",
      "status": "success",
      "start_time": "2026-01-30T20:30:36.663852",
      "end_time": "2026-01-30T20:30:37.716795",
      "retry_count": 0,
      "performance": {
        "total_time": 1048.72,
        "dns_time": 100,
        "tcp_time": 100,
        "tls_time": 150,
        "server_time": 419.49,
        "download_time": 0,
        "size": 396
      },
      "response": {
        "status_code": 200,
        "headers": {
          "Date": "Fri, 30 Jan 2026 12:30:37 GMT",
          "Content-Type": "application/json",
          "Content-Length": "396",
          "Connection": "keep-alive",
          "Server": "gunicorn/19.9.0",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Credentials": "true"
        },
        "cookies": {},
        "url": "https://httpbin.org/get?username=testuser&env=development",
        "request": {
          "method": "GET",
          "url": "https://httpbin.org/get?username=testuser&env=development",
          "headers": {
            "User-Agent": "python-requests/2.32.5",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive"
          }
        },
        "body": {
          "args": {
            "env": "development",
            "username": "testuser"
          },
          "headers": {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Host": "httpbin.org",
            "User-Agent": "python-requests/2.32.5",
            "X-Amzn-Trace-Id": "Root=1-697ca46d-79761a4539e9b67a42504a6e"
          },
          "origin": "5.34.218.79",
          "url": "https://httpbin.org/get?username=testuser&env=development"
        },
        "response_time": 1048.738,
        "size": 396
      },
      "extracted_vars": {
        "origin": "5.34.218.79"
      },
      "validations": [
        {
          "passed": true,
          "type": "status_code",
          "path": "$.status_code",
          "actual": 200,
          "expected": "200",
          "description": "",
          "error": ""
        },
        {
          "passed": true,
          "type": "eq",
          "path": "$.args.username",
          "actual": "testuser",
          "expected": "testuser",
          "description": "验证username参数使用了全局变量",
          "error": ""
        }
      ],
      "variables_snapshot": {
        "before": {},
        "extracted": {
          "origin": "5.34.218.79"
        }
      }
    }
  ],
  "final_variables": {
    "base_url": "https://httpbin.org",
    "username": "testuser",
    "env": "development",
    "origin": "5.34.218.79"
  }
}
```

### 1.2 失败示例

```json
{
  "test_case": {
    "name": "断言失败测试",
    "status": "failed",
    "start_time": "2026-01-30T20:30:36.663852",
    "end_time": "2026-01-30T20:30:38.201488",
    "duration": 1.537636
  },
  "statistics": {
    "total_steps": 2,
    "passed_steps": 1,
    "failed_steps": 1,
    "skipped_steps": 0,
    "pass_rate": 50.0
  },
  "steps": [
    {
      "name": "成功步骤",
      "status": "success",
      "start_time": "2026-01-30T20:30:36.663852",
      "end_time": "2026-01-30T20:30:37.716795",
      "retry_count": 0,
      "performance": {
        "total_time": 1048.72,
        "dns_time": 100,
        "tcp_time": 100,
        "tls_time": 150,
        "server_time": 419.49,
        "download_time": 0,
        "size": 396
      },
      "response": {
        "status_code": 200,
        "body": {
          "code": 0,
          "message": "success"
        }
      },
      "validations": [
        {
          "passed": true,
          "type": "eq",
          "path": "$.code",
          "actual": 0,
          "expected": 0,
          "description": "",
          "error": ""
        }
      ]
    },
    {
      "name": "失败步骤",
      "status": "failed",
      "start_time": "2026-01-30T20:30:37.717389",
      "end_time": "2026-01-30T20:30:38.833390",
      "retry_count": 0,
      "performance": {
        "total_time": 1115.18,
        "dns_time": 100,
        "tcp_time": 100,
        "tls_time": 150,
        "server_time": 446.07,
        "download_time": 0,
        "size": 305
      },
      "response": {
        "status_code": 200,
        "body": {
          "code": 1001,
          "message": "参数错误"
        }
      },
      "validations": [
        {
          "passed": false,
          "type": "eq",
          "path": "$.code",
          "actual": 1001,
          "expected": 0,
          "description": "业务码应为0",
          "error": "Expected 0, but got 1001"
        }
      ],
      "error_info": {
        "type": "AssertionError",
        "category": "assertion",
        "message": "Expected 0, but got 1001",
        "suggestion": null
      }
    }
  ],
  "final_variables": {},
  "error_info": {
    "type": "AssertionError",
    "category": "assertion",
    "message": "Expected 0, but got 1001",
    "suggestion": null
  }
}
```

### 1.3 超紧凑模式输出（默认 JSON 格式）

```json
[
  {
    "step": "GET请求示例",
    "response": {
      "status_code": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "args": {},
        "url": "https://httpbin.org/get"
      },
      "response_time": 1053.1029999999998,
      "size": 305
    }
  },
  {
    "step": "POST请求示例",
    "response": {
      "status_code": 200,
      "body": {
        "data": "{\"username\": \"testuser\"}",
        "json": {
          "username": "testuser",
          "password": "***"
        }
      },
      "response_time": 2505.683,
      "size": 646
    }
  }
]
```

---

## 2. 结构详解

### 2.1 顶层结构

```json
{
  "test_case": { ... },      // 测试用例信息
  "statistics": { ... },     // 统计信息
  "steps": [ ... ],          // 步骤列表
  "final_variables": { ... },// 最终变量
  "error_info": { ... }      // 错误信息（可选）
}
```

### 2.2 test_case（测试用例信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 测试用例名称 |
| `status` | string | 测试状态：passed/failed/skipped |
| `start_time` | string | 开始时间（ISO 8601格式） |
| `end_time` | string | 结束时间（ISO 8601格式） |
| `duration` | float | 总耗时（秒） |

### 2.3 statistics（统计信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_steps` | int | 总步骤数 |
| `passed_steps` | int | 通过的步骤数 |
| `failed_steps` | int | 失败的步骤数 |
| `skipped_steps` | int | 跳过的步骤数 |
| `pass_rate` | float | 通过率（百分比，0-100） |

### 2.4 steps（步骤列表）

每个步骤包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 步骤名称 |
| `status` | string | ✅ | 步骤状态：success/failed/skipped/error |
| `start_time` | string | ✅ | 开始时间（ISO 8601） |
| `end_time` | string | ✅ | 结束时间（ISO 8601） |
| `retry_count` | int | ✅ | 重试次数 |
| `performance` | object | ❌ | 性能指标 |
| `response` | object | ❌ | 响应数据 |
| `extracted_vars` | object | ❌ | 提取的变量 |
| `validations` | array | ❌ | 断言结果列表 |
| `variables_snapshot` | object | ❌ | 变量快照 |
| `error_info` | object | ❌ | 错误信息（失败时） |

---

## 3. 字段说明

### 3.1 performance（性能指标）

```json
{
  "total_time": 1048.72,     // 总耗时（毫秒）
  "dns_time": 100,           // DNS解析耗时（毫秒）
  "tcp_time": 100,           // TCP连接耗时（毫秒）
  "tls_time": 150,           // TLS握手耗时（毫秒）
  "server_time": 419.49,     // 服务器处理耗时（毫秒）
  "download_time": 0,        // 下载耗时（毫秒）
  "size": 396                // 响应大小（字节）
}
```

### 3.2 response（响应数据）

```json
{
  "status_code": 200,                    // HTTP状态码
  "headers": { ... },                     // 响应头
  "cookies": { ... },                     // Cookies
  "url": "https://...",                  // 实际请求URL
  "request": { ... },                     // 请求信息（仅verbose模式）
  "body": { ... },                        // 响应体
  "response_time": 1048.738,             // 响应时间（毫秒）
  "size": 396                            // 响应大小（字节）
}
```

### 3.3 validations（断言结果）

```json
{
  "passed": true,              // 是否通过
  "type": "eq",                // 断言类型
  "path": "$.args.username",   // JSONPath表达式
  "actual": "testuser",        // 实际值
  "expected": "testuser",      // 期望值
  "description": "验证...",    // 描述
  "error": ""                  // 错误信息（失败时）
}
```

### 3.4 error_info（错误信息）

```json
{
  "type": "AssertionError",    // 错误类型
  "category": "assertion",     // 错误分类
  "message": "Expected...",    // 错误消息
  "suggestion": null           // 修复建议（可选）
}
```

### 3.5 variables_snapshot（变量快照）

```json
{
  "before": { ... },           // 步骤执行前的变量
  "extracted": { ... }         // 步骤执行后提取的变量
}
```

---

## 4. 状态码与错误类型

### 4.1 测试用例状态（test_case.status）

| 状态 | 说明 |
|------|------|
| `passed` | 所有步骤通过 |
| `failed` | 至少一个步骤失败 |
| `skipped` | 所有步骤跳过 |

### 4.2 步骤状态（step.status）

| 状态 | 说明 |
|------|------|
| `success` | 步骤成功执行，所有断言通过 |
| `failed` | 断言不通过 |
| `skipped` | 步骤被跳过（条件不满足等） |
| `error` | 执行出错（网络错误、超时等） |

### 4.3 错误类型（error_info.type）

| 类型 | 说明 |
|------|------|
| `AssertionError` | 断言错误 |
| `TimeoutError` | 超时错误 |
| `ConnectionError` | 连接错误 |
| `HTTPError` | HTTP错误 |
| `ValidationError` | 验证错误 |
| `DatabaseError` | 数据库错误 |
| `ScriptError` | 脚本错误 |
| `ConfigError` | 配置错误 |
| `NetworkError` | 网络错误 |

### 4.4 错误分类（error_info.category）

| 分类 | 说明 |
|------|------|
| `assertion` | 断言错误 |
| `network` | 网络错误 |
| `timeout` | 超时错误 |
| `parsing` | 解析错误 |
| `business` | 业务错误 |
| `system` | 系统错误 |

---

## 5. 输出格式

### 5.1 JSON 格式

**完整模式（verbose）**：包含所有测试信息

```bash
sisyphus --cases test.yaml --format json -v
```

**超紧凑模式（默认）**：仅包含步骤名称和响应

```bash
sisyphus --cases test.yaml --format json
```

### 5.2 CSV 格式

**详细模式（verbose）**：包含所有性能指标

```bash
sisyphus --cases test.yaml --format csv -v
```

输出列：
- Test Name
- Step Name
- Step Index
- Status
- Start Time
- End Time
- Duration (s)
- HTTP Status Code
- Response Size (bytes)
- Total Time (ms)
- DNS Time (ms)
- TCP Time (ms)
- TLS Time (ms)
- Server Time (ms)
- Download Time (ms)
- Error Type
- Error Message

**紧凑模式（默认）**：仅包含步骤基本信息

```bash
sisyphus --cases test.yaml --format csv
```

输出列：
- Step
- Status Code
- Status

### 5.3 HTML 格式

HTML 格式支持中英文双语，通过 `--report-lang` 参数指定语言：

```bash
# 生成中文报告
sisyphus --cases test.yaml --format html --report-lang zh -o report.html

# 生成英文报告
sisyphus --cases test.yaml --format html --report-lang en -o report.html
```

**特性：**
- 完整的中英文双语支持
- 响应式设计，美观易读
- 交互式步骤详情（可展开/折叠）
- 彩色状态标识（绿色成功、红色失败、橙色跳过）
- 进度条展示
- 统计数据卡片
- 性能指标可视化
- 错误信息和建议提示

### 5.4 JUnit 格式

```bash
sisyphus --cases test.yaml --format junit -o junit.xml
```

### 5.5 Allure 报告

```bash
sisyphus --cases test.yaml --allure
allure generate allure-results -o allure-report
```

---

## 版本历史

| 版本 | 日期 | 引擎版本 | 说明 |
|------|------|----------|------|
| 1.0 | 2026-01-30 | 1.0.2 | 基于实际代码实现编写，包含完整的输出协议规范 |
