# API-Engine 输出协议规范 v1.0

> **变更说明**: 这是首个正式版本，包含完整的错误分类、性能指标、重试历史、测试套件层级、变量追踪等企业级特性。

---

## 目录

- [1. 完整示例](#1-完整示例)
- [2. 结构详解](#2-结构详解)
- [3. 状态码与错误类型](#3-状态码与错误类型)
- [4. 性能指标说明](#4-性能指标说明)
- [5. 实时推送协议](#5-实时推送协议websocket)

---

## 1. 完整示例

```json
{
  "meta": {
    "protocol_version": "1.0",
    "engine_version": "1.0.0",
    "generated_at": "2026-01-27T10:30:00Z",
    "generator": "api-engine"
  },

  "summary": {
    "task_id": "task_20260127_abc123",
    "task_name": "电商下单全流程测试_V2.0",
    "status": "failed",
    "start_time": "2026-01-27T10:00:00Z",
    "end_time": "2026-01-27T10:01:30.500Z",
    "duration": 90.5,
    "total_steps": 11,
    "stat": {
      "total": 11,
      "success": 8,
      "failed": 2,
      "error": 1,
      "skipped": 0
    },

    "pass_rate": 0.727,
    "retry_count": 3,

    "environment": {
      "profile": "dev",
      "base_url": "http://dev-api.example.com",
      "server": "linux-docker-node-01",
      "agent_version": "1.0.0"
    },

    "tags": {
      "smoke": { "total": 3, "passed": 3, "failed": 0 },
      "critical": { "total": 5, "passed": 4, "failed": 1 },
      "performance": { "total": 1, "passed": 1, "failed": 0 }
    }
  },

  "suites": [
    {
      "id": "suite_001",
      "name": "用户认证模块",
      "description": "登录、注册、token验证",
      "status": "success",
      "start_time": "2026-01-27T10:00:00Z",
      "duration": 5.2,
      "stat": {
        "total": 3,
        "success": 3,
        "failed": 0,
        "error": 0
      },
      "steps": ["step_01", "step_02", "step_03"]
    },
    {
      "id": "suite_002",
      "name": "订单模块",
      "description": "创建订单、支付、查询",
      "status": "failed",
      "start_time": "2026-01-27T10:00:05.2Z",
      "duration": 85.3,
      "stat": {
        "total": 8,
        "success": 5,
        "failed": 2,
        "error": 1
      },
      "steps": ["step_04", "step_05", "step_06", "step_07", "step_08", "step_09", "step_10", "step_11"]
    }
  ],

  "details": [
    {
      "id": "step_01",
      "name": "批量验证用户登录",
      "suite_id": "suite_001",
      "type": "api",
      "tags": ["smoke", "auth", "critical"],
      "priority": "P0",
      "status": "success",
      "iteration": 0,

      "start_time": "2026-01-27T10:00:00.100Z",
      "end_time": "2026-01-27T10:00:00.300Z",
      "duration": 0.2,

      "data_provider": {
        "type": "csv",
        "source": "demo_data/login_users.csv",
        "total_iterations": 3,
        "current_data": {
          "username": "user1",
          "password": "***",
          "expected": 200
        }
      },

      "retry_history": [],

      "request": {
        "method": "POST",
        "url": "http://dev-api.example.com/auth/login",
        "headers": {
          "Content-Type": "application/json",
          "User-Agent": "ApiEngine/2.0"
        },
        "body": {
          "username": "user1",
          "password": "***"
        }
      },

      "response": {
        "status_code": 200,
        "headers": {
          "Content-Type": "application/json",
          "Date": "Mon, 27 Jan 2026 10:00:00 GMT",
          "Server": "nginx/1.18.0"
        },
        "body": {
          "code": 0,
          "msg": "success",
          "data": {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "user": {
              "id": 10086,
              "username": "user1",
              "email": "user1@example.com"
            }
          }
        },
        "size_bytes": 1024
      },

      "performance": {
        "total_time_ms": 200,
        "dns_time_ms": 20,
        "tcp_time_ms": 15,
        "tls_time_ms": 30,
        "server_time_ms": 120,
        "transfer_time_ms": 15
      },

      "extract_result": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_id": 10086
      },

      "variables_snapshot": {
        "before": {
          "access_token": null,
          "user_id": null
        },
        "after": {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "user_id": 10086
        }
      },

      "validate_result": [
        {
          "check": "status_code == 200",
          "comparator": "eq",
          "expect": 200,
          "actual": 200,
          "result": "pass"
        },
        {
          "check": "body.code == 0",
          "comparator": "eq",
          "expect": 0,
          "actual": 0,
          "result": "pass"
        },
        {
          "check": "len_gt(body.data.token, 20)",
          "comparator": "len_gt",
          "expect": "> 20",
          "actual": 156,
          "result": "pass"
        }
      ],

      "attachments": [],
      "logs": [],
      "metadata": {
        "executed_on_worker": "worker-01",
        "thread_id": "thread-01"
      }
    },

    {
      "id": "step_03",
      "name": "查询订单详情（依赖登录）",
      "suite_id": "suite_001",
      "type": "api",
      "tags": ["order"],
      "priority": "P0",
      "status": "failed",

      "depends_on": ["step_01"],
      "dependencies_satisfied": true,

      "start_time": "2026-01-27T10:00:02.000Z",
      "end_time": "2026-01-27T10:00:02.150Z",
      "duration": 0.15,

      "request": {
        "method": "GET",
        "url": "http://dev-api.example.com/orders/detail",
        "headers": {
          "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        },
        "params": {
          "order_id": "ORDER_001"
        }
      },

      "response": {
        "status_code": 200,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "code": 1001,
          "msg": "订单不存在",
          "data": null
        },
        "size_bytes": 89
      },

      "performance": {
        "total_time_ms": 150,
        "dns_time_ms": 0,
        "tcp_time_ms": 0,
        "tls_time_ms": 0,
        "server_time_ms": 140,
        "transfer_time_ms": 10
      },

      "validate_result": [
        {
          "check": "status_code == 200",
          "comparator": "eq",
          "expect": 200,
          "actual": 200,
          "result": "pass"
        },
        {
          "check": "body.code == 0",
          "comparator": "eq",
          "expect": 0,
          "actual": 1001,
          "result": "fail",
          "error_msg": "Expected body.code to be 0, but got 1001",
          "error_type": "AssertionError",
          "error_category": "business"
        }
      ],

      "error_info": {
        "type": "AssertionError",
        "category": "business",
        "message": "业务码校验失败: 期望 0, 实际 1001",
        "stack_trace": "File \"executor.py\", line 156, in validate_step\n    raise AssertionError(f\"Expected {expect}, but got {actual}\")"
      },

      "attachments": [
        {
          "type": "screenshot",
          "name": "error_screenshot.png",
          "path": "/uploads/task_20260127_abc123/step_03_error.png",
          "size_bytes": 45678,
          "content_type": "image/png"
        },
        {
          "type": "har",
          "name": "request.har",
          "path": "/har/task_20260127_abc123/step_03.har",
          "size_bytes": 12345,
          "content_type": "application/json"
        }
      ],

      "logs": [
        {
          "level": "error",
          "timestamp": "2026-01-27T10:00:02.150Z",
          "message": "[AssertionError] 业务码校验失败: 期望 0, 实际 1001"
        }
      ]
    },

    {
      "id": "step_06",
      "name": "验证订单入库",
      "suite_id": "suite_002",
      "type": "database",
      "tags": ["database"],
      "priority": "P0",
      "status": "success",

      "start_time": "2026-01-27T10:00:30.000Z",
      "end_time": "2026-01-27T10:00:30.050Z",
      "duration": 0.05,

      "database": {
        "connection": "mysql_main",
        "sql_type": "mysql",
        "command": "query",
        "sql": "SELECT * FROM orders WHERE order_id = 'ORDER_001'",
        "rows_affected": 1
      },

      "query_result": {
        "rows": [
          {
            "id": 12345,
            "order_id": "ORDER_001",
            "user_id": 10086,
            "status": "PENDING",
            "amount": 99.00,
            "create_time": "2026-01-27T10:00:25Z"
          }
        ],
        "total_rows": 1
      },

      "extract_result": {
        "order_create_time": "2026-01-27T10:00:25Z"
      },

      "validate_result": [
        {
          "check": "rows[0].status == 'PENDING'",
          "comparator": "eq",
          "expect": "PENDING",
          "actual": "PENDING",
          "result": "pass"
        },
        {
          "check": "rows[0].amount == 99.00",
          "comparator": "eq",
          "expect": 99.00,
          "actual": 99.00,
          "result": "pass"
        }
      ]
    },

    {
      "id": "step_08",
      "name": "执行自定义Python脚本",
      "suite_id": "suite_002",
      "type": "script",
      "tags": ["custom"],
      "priority": "P2",
      "status": "error",

      "start_time": "2026-01-27T10:00:45.000Z",
      "end_time": "2026-01-27T10:00:47.000Z",
      "duration": 2.0,

      "script": {
        "source": "scripts/custom_validator.py",
        "args": {
          "api_response": "{...}",
          "threshold": 100
        }
      },

      "error_info": {
        "type": "ScriptError",
        "category": "system",
        "message": "脚本执行失败: ModuleNotFoundError: No module named 'pandas'",
        "stack_trace": "Traceback (most recent call last):\n  File \"executor.py\", line 230, in execute_script\n    exec(script_content, globals)\n  File \"custom_validator.py\", line 5, in <module>\n    import pandas\nModuleNotFoundError: No module named 'pandas'"
      },

      "attachments": [
        {
          "type": "log",
          "name": "script_error.log",
          "path": "/logs/task_20260127_abc123/step_08_script_error.log"
        }
      ]
    },

    {
      "id": "step_09",
      "name": "等待异步任务完成",
      "suite_id": "suite_002",
      "type": "wait",
      "tags": ["async"],
      "priority": "P1",
      "status": "success",

      "start_time": "2026-01-27T10:00:50.000Z",
      "end_time": "2026-01-27T10:00:52.000Z",
      "duration": 2.0,

      "wait": {
        "type": "fixed",
        "duration_ms": 2000
      }
    },

    {
      "id": "step_10",
      "name": "批量创建订单（并发测试）",
      "suite_id": "suite_002",
      "type": "api",
      "tags": ["batch", "performance"],
      "priority": "P1",
      "status": "success",

      "start_time": "2026-01-27T10:00:55.000Z",
      "end_time": "2026-01-27T10:01:25.000Z",
      "duration": 30.0,

      "parallel": {
        "enabled": true,
        "threads": 10,
        "ramp_up": 5,
        "total_iterations": 100,
        "successful_iterations": 98,
        "failed_iterations": 2
      },

      "iterations": [
        {
          "index": 0,
          "thread_id": 0,
          "data": { "index": 0 },
          "status": "success",
          "duration": 0.3
        },
        {
          "index": 1,
          "thread_id": 1,
          "data": { "index": 1 },
          "status": "success",
          "duration": 0.25
        },
        {
          "index": 15,
          "thread_id": 5,
          "data": { "index": 15 },
          "status": "failed",
          "duration": 2.5,
          "error": "timeout"
        }
      ],

      "performance_summary": {
        "avg_response_time_ms": 280,
        "min_response_time_ms": 150,
        "max_response_time_ms": 2500,
        "p50_response_time_ms": 250,
        "p90_response_time_ms": 400,
        "p95_response_time_ms": 600,
        "p99_response_time_ms": 1200,
        "throughput_per_second": 3.33,
        "error_rate": 0.02
      }
    },

    {
      "id": "step_11",
      "name": "超时重试示例",
      "suite_id": "suite_002",
      "type": "api",
      "tags": ["retry"],
      "priority": "P0",
      "status": "success",

      "start_time": "2026-01-27T10:01:25.000Z",
      "end_time": "2026-01-27T10:01:30.500Z",
      "duration": 5.5,

      "retry_history": [
        {
          "attempt": 1,
          "status": "error",
          "error_type": "TimeoutError",
          "error_category": "system",
          "duration": 3.0,
          "timestamp": "2026-01-27T10:01:25.000Z",
          "error_msg": "Request timeout after 3000ms"
        },
        {
          "attempt": 2,
          "status": "success",
          "duration": 2.5,
          "timestamp": "2026-01-27T10:01:28.000Z"
        }
      ],

      "request": {
        "method": "GET",
        "url": "http://dev-api.example.com/slow-api"
      },

      "response": {
        "status_code": 200,
        "body": { "code": 0, "msg": "success" }
      }
    }
  ],

  "report_urls": {
    "html": "http://frontend.com/reports/task_20260127_abc123.html",
    "json": "http://frontend.com/reports/task_20260127_abc123.json",
    "junit": "http://frontend.com/reports/task_20260127_abc123.junit.xml"
  },

  "artifacts": {
    "logs": [
      {
        "name": "execution.log",
        "path": "/logs/task_20260127_abc123/execution.log",
        "size_bytes": 12345
      }
    ],
    "screenshots": [
      {
        "name": "failed_steps.png",
        "path": "/uploads/task_20260127_abc123/screenshots.zip"
      }
    ],
    "har": [
      {
        "name": "http_archive.har",
        "path": "/har/task_20260127_abc123/archive.har"
      }
    ]
  }
}
```

---

## 2. 结构详解

### 2.1 元数据（meta）

```json
{
  "meta": {
    "protocol_version": "2.0",           // 协议版本
    "engine_version": "2.0.0",           // 引擎版本
    "generated_at": "2026-01-27T10:30:00Z",  // 生成时间（ISO 8601）
    "generator": "api-engine"            // 生成器标识
  }
}
```

### 2.2 汇总信息（summary）

```json
{
  "summary": {
    "task_id": "task_20260127_abc123",    // 任务唯一标识
    "task_name": "电商下单全流程测试_V2.0",  // 任务名称
    "status": "failed",                    // 总体状态: [success, failed, error]
    "start_time": "2026-01-27T10:00:00Z",  // 开始时间
    "end_time": "2026-01-27T10:01:30.500Z", // 结束时间
    "duration": 90.5,                      // 总耗时（秒）
    "total_steps": 11,                     // 总步骤数

    "stat": {
      "total": 11,                         // 总数
      "success": 8,                        // 成功数
      "failed": 2,                         // 失败数（断言不通过）
      "error": 1,                          // 错误数（执行异常）
      "skipped": 0                         // 跳过数
    },

    "pass_rate": 0.727,                    // 通过率（success / total）
    "retry_count": 3,                      // 总重试次数

    "environment": {
      "profile": "dev",                    // 环境配置名
      "base_url": "http://dev-api.example.com",  // 基础URL
      "server": "linux-docker-node-01",    // 执行服务器
      "agent_version": "1.0.0"             // Agent版本
    },

    "tags": {
      "smoke": {
        "total": 3,
        "passed": 3,
        "failed": 0
      },
      "critical": {
        "total": 5,
        "passed": 4,
        "failed": 1
      }
    }
  }
}
```

### 2.3 测试套件（suites）

**可选字段**：用于组织复杂测试场景的层级结构。

```json
{
  "suites": [
    {
      "id": "suite_001",                   // 套件唯一标识
      "name": "用户认证模块",              // 套件名称
      "description": "登录、注册、token验证",  // 套件描述
      "status": "success",                 // 套件状态
      "start_time": "2026-01-27T10:00:00Z",
      "duration": 5.2,
      "stat": {
        "total": 3,
        "success": 3,
        "failed": 0,
        "error": 0
      },
      "steps": ["step_01", "step_02", "step_03"]  // 包含的步骤ID列表
    }
  ]
}
```

### 2.4 测试步骤详情（details）

#### 2.4.1 基础字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 步骤唯一标识 |
| `name` | string | ✅ | 步骤名称 |
| `suite_id` | string | ❌ | 所属套件ID |
| `type` | string | ✅ | 步骤类型: [api, database, wait, script] |
| `tags` | array | ❌ | 标签列表 |
| `priority` | string | ❌ | 优先级: [P0, P1, P2, P3] |
| `status` | string | ✅ | 状态: [success, failed, error, skipped] |
| `start_time` | string | ✅ | 开始时间（ISO 8601） |
| `end_time` | string | ✅ | 结束时间（ISO 8601） |
| `duration` | float | ✅ | 耗时（秒） |

#### 2.4.2 API步骤字段

```json
{
  "request": {
    "method": "POST",
    "url": "http://api.example.com/login",
    "headers": {
      "Content-Type": "application/json"
    },
    "params": {},                          // Query参数
    "body": {},                            // 请求体（敏感字段自动脱敏）
    "upload": {                            // 文件上传信息
      "file": "avatar.jpg",
      "form_fields": {}
    }
  },

  "response": {
    "status_code": 200,
    "headers": {},
    "body": {},                            // 响应体
    "size_bytes": 1024,                    // 响应大小（字节）
    "encoding": "utf-8"                    // 编码
  },

  "performance": {
    "total_time_ms": 200,                  // 总耗时
    "dns_time_ms": 20,                     // DNS解析耗时
    "tcp_time_ms": 15,                     // TCP连接耗时
    "tls_time_ms": 30,                     // TLS握手耗时
    "server_time_ms": 120,                 // 服务器处理耗时
    "transfer_time_ms": 15,                // 数据传输耗时
    "download_bytes": 1024,                // 下载字节数
    "upload_bytes": 256                    // 上传字节数
  }
}
```

#### 2.4.3 数据库步骤字段

```json
{
  "database": {
    "connection": "mysql_main",            // 连接别名
    "sql_type": "mysql",                   // 数据库类型
    "command": "query",                    // 命令类型
    "sql": "SELECT * FROM users WHERE id = 1",
    "rows_affected": 1                     // 影响行数（execute类型）
  },

  "query_result": {
    "rows": [                              // 查询结果（query类型）
      {
        "id": 1,
        "name": "test"
      }
    ],
    "total_rows": 1
  }
}
```

#### 2.4.4 脚本步骤字段

```json
{
  "script": {
    "source": "scripts/custom.py",         // 脚本路径
    "args": {},                            // 传入参数
    "return_value": {}                     // 返回值
  }
}
```

#### 2.4.5 等待步骤字段

```json
{
  "wait": {
    "type": "fixed",                       // [fixed, condition]
    "duration_ms": 2000,                   // 固定延迟（fixed类型）
    "condition": "",                       // 等待条件（condition类型）
    "timeout": 30,                         // 超时时间（condition类型）
    "check_interval": 2                    // 检查间隔（condition类型）
  }
}
```

#### 2.4.6 变量提取结果（extract_result）

```json
{
  "extract_result": {
    "access_token": "eyJhbG...",
    "user_id": 10086,
    "order_id": "ORDER_001"
  }
}
```

#### 2.4.7 变量快照（variables_snapshot）

```json
{
  "variables_snapshot": {
    "before": {                            // 执行前的变量值
      "access_token": null,
      "user_id": null
    },
    "after": {                             // 执行后的变量值
      "access_token": "eyJhbG...",
      "user_id": 10086
    }
  }
}
```

#### 2.4.8 断言结果（validate_result）

```json
{
  "validate_result": [
    {
      "check": "status_code == 200",       // 断言描述
      "comparator": "eq",                  // 比较器
      "expect": 200,                       // 期望值
      "actual": 200,                       // 实际值
      "result": "pass"                     // 结果: [pass, fail]
    },
    {
      "check": "body.code == 0",
      "comparator": "eq",
      "expect": 0,
      "actual": 1001,
      "result": "fail",
      "error_msg": "Expected body.code to be 0, but got 1001",
      "error_type": "AssertionError",
      "error_category": "business"
    }
  ]
}
```

#### 2.4.9 错误信息（error_info）

**失败（failed）和错误（error）步骤必填**。

```json
{
  "error_info": {
    "type": "AssertionError",              // 错误类型
    "category": "business",                // 错误分类: [business, system, data]
    "message": "业务码校验失败",           // 错误消息
    "stack_trace": "Traceback (most recent call last):\n...",  // 堆栈信息
    "suggestion": "请检查测试数据是否正确"  // 修复建议（可选）
  }
}
```

#### 2.4.10 重试历史（retry_history）

**发生重试时必填**。

```json
{
  "retry_history": [
    {
      "attempt": 1,                        // 第几次尝试
      "status": "error",                   // 该次尝试的状态
      "error_type": "TimeoutError",
      "error_category": "system",
      "duration": 3.0,
      "timestamp": "2026-01-27T10:00:00Z",
      "error_msg": "Request timeout after 3000ms"
    },
    {
      "attempt": 2,
      "status": "success",
      "duration": 2.5,
      "timestamp": "2026-01-27T10:00:03Z"
    }
  ]
}
```

#### 2.4.11 数据驱动信息（data_provider）

**使用数据驱动时必填**。

```json
{
  "data_provider": {
    "type": "csv",                         // [csv, json, database, inline]
    "source": "demo_data/login_users.csv",
    "total_iterations": 10,
    "current_iteration": 0,
    "current_data": {
      "username": "user1",
      "password": "***",                   // 自动脱敏
      "expected": 200
    }
  }
}
```

#### 2.4.12 并发测试信息（parallel）

**使用并发测试时必填**。

```json
{
  "parallel": {
    "enabled": true,
    "threads": 10,
    "ramp_up": 5,
    "total_iterations": 100,
    "successful_iterations": 98,
    "failed_iterations": 2
  },

  "iterations": [
    {
      "index": 0,
      "thread_id": 0,
      "data": { "index": 0 },
      "status": "success",
      "duration": 0.3
    }
  ],

  "performance_summary": {
    "avg_response_time_ms": 280,
    "min_response_time_ms": 150,
    "max_response_time_ms": 2500,
    "p50_response_time_ms": 250,
    "p90_response_time_ms": 400,
    "p95_response_time_ms": 600,
    "p99_response_time_ms": 1200,
    "throughput_per_second": 3.33,
    "error_rate": 0.02
  }
}
```

#### 2.4.13 附件（attachments）

```json
{
  "attachments": [
    {
      "type": "screenshot",                // [screenshot, log, har, video]
      "name": "error_screenshot.png",
      "path": "/uploads/task_20260127_abc123/step_03_error.png",
      "url": "http://storage/uploads/...",  // 可访问的URL
      "size_bytes": 45678,
      "content_type": "image/png"
    },
    {
      "type": "har",
      "name": "request.har",
      "path": "/har/task_20260127_abc123/step_03.har",
      "size_bytes": 12345,
      "content_type": "application/json"
    }
  ]
}
```

#### 2.4.14 日志（logs）

```json
{
  "logs": [
    {
      "level": "error",                    // [debug, info, warn, error]
      "timestamp": "2026-01-27T10:00:02.150Z",
      "message": "[AssertionError] 业务码校验失败",
      "source": "executor.py",             // 日志来源（可选）
      "line_number": 156                   // 行号（可选）
    }
  ]
}
```

#### 2.4.15 元数据（metadata）

```json
{
  "metadata": {
    "executed_on_worker": "worker-01",     // 执行的工作节点
    "thread_id": "thread-01",              // 线程ID（并发测试时）
    "hostname": "test-machine-01",         // 主机名
    "ip_address": "192.168.1.100"          // IP地址
  }
}
```

---

## 3. 状态码与错误类型

### 3.1 步骤状态（status）

| 状态 | 说明 | 适用场景 |
|------|------|----------|
| `success` | 成功 | 所有断言通过 |
| `failed` | 失败 | 断言不通过（业务逻辑错误） |
| `error` | 错误 | 执行异常（系统错误、网络错误、超时等） |
| `skipped` | 跳过 | 条件不满足或前置步骤失败 |
| `running` | 运行中 | 实时推送时使用 |

### 3.2 错误类型（error_type）

| 类型 | 说明 | 示例 |
|------|------|------|
| `AssertionError` | 断言错误 | 业务码校验失败、字段值不匹配 |
| `TimeoutError` | 超时错误 | 请求超过设定时间未响应 |
| `ConnectionError` | 连接错误 | DNS解析失败、TCP连接失败 |
| `HTTPError` | HTTP错误 | 5xx服务器错误、4xx客户端错误 |
| `ValidationError` | 验证错误 | JSON解析失败、参数验证失败 |
| `DatabaseError` | 数据库错误 | SQL语法错误、连接失败 |
| `ScriptError` | 脚本错误 | Python脚本执行异常 |
| `ConfigError` | 配置错误 | YAML格式错误、参数缺失 |
| `NetworkError` | 网络错误 | 丢包、连接中断 |

### 3.3 错误分类（error_category）

| 分类 | 说明 | 严重程度 |
|------|------|----------|
| `business` | 业务错误 | 断言不通过、业务逻辑错误 | 中
| `system` | 系统错误 | 超时、连接失败、服务器错误 | 高
| `data` | 数据错误 | 测试数据缺失、数据库异常 | 中
| `config` | 配置错误 | YAML错误、参数配置错误 | 高 |

### 3.4 错误处理建议

```json
{
  "error_info": {
    "type": "AssertionError",
    "category": "business",
    "message": "业务码校验失败",
    "suggestion": "建议检查：\n1. 测试数据是否正确\n2. 环境配置是否匹配\n3. 接口逻辑是否变更",
    "related_docs": [
      {
        "title": "接口文档",
        "url": "http://docs.example.com/api/login"
      },
      {
        "title": "故障排查指南",
        "url": "http://wiki.example.com/troubleshooting"
      }
    ]
  }
}
```

---

## 4. 性能指标说明

### 4.1 API请求性能分解

```
total_time_ms = dns_time_ms + tcp_time_ms + tls_time_ms + server_time_ms + transfer_time_ms
```

| 指标 | 说明 | 优化建议 |
|------|------|----------|
| `dns_time_ms` | DNS解析耗时 | 使用长连接、配置DNS缓存 |
| `tcp_time_ms` | TCP连接耗时 | 启用HTTP/2、使用连接池 |
| `tls_time_ms` | TLS握手耗时 | 启用TLS会话复用 |
| `server_time_ms` | 服务器处理耗时 | 优化后端性能、添加缓存 |
| `transfer_time_ms` | 数据传输耗时 | 启用压缩、减少响应大小 |

### 4.2 并发测试性能指标

```json
{
  "performance_summary": {
    "avg_response_time_ms": 280,           // 平均响应时间
    "min_response_time_ms": 150,           // 最小响应时间
    "max_response_time_ms": 2500,          // 最大响应时间
    "p50_response_time_ms": 250,           // 中位数（50%请求）
    "p90_response_time_ms": 400,           // 90分位（90%请求）
    "p95_response_time_ms": 600,           // 95分位
    "p99_response_time_ms": 1200,          // 99分位
    "throughput_per_second": 3.33,         // 吞吐量（请求/秒）
    "error_rate": 0.02                     // 错误率（2%）
  }
}
```

### 4.3 性能阈值建议

| 场景 | P50 | P90 | P95 | P99 | 错误率 |
|------|-----|-----|-----|-----|--------|
| 普通API | < 200ms | < 500ms | < 800ms | < 1500ms | < 1% |
| 核心API | < 100ms | < 300ms | < 500ms | < 1000ms | < 0.1% |
| 批处理 | < 1s | < 3s | < 5s | < 10s | < 5% |

---

## 5. 实时推送协议（WebSocket）

### 5.1 连接

```
WS /api/v1/test-suite/execute/stream?task_id=task_20260127_abc123
```

### 5.2 消息格式

#### 5.2.1 任务开始

```json
{
  "event": "task_started",
  "timestamp": "2026-01-27T10:00:00Z",
  "data": {
    "task_id": "task_20260127_abc123",
    "task_name": "电商下单全流程测试",
    "total_steps": 11
  }
}
```

#### 5.2.2 步骤开始

```json
{
  "event": "step_started",
  "timestamp": "2026-01-27T10:00:00.100Z",
  "data": {
    "step_id": "step_01",
    "step_name": "批量验证用户登录",
    "step_type": "api",
    "iteration": 0
  }
}
```

#### 5.2.3 步骤进度（用于长时间运行的操作）

```json
{
  "event": "step_progress",
  "timestamp": "2026-01-27T10:00:00.200Z",
  "data": {
    "step_id": "step_10",
    "progress": 0.5,                      // 进度百分比（0-1）
    "current_iteration": 50,
    "total_iterations": 100,
    "message": "正在执行第50次迭代..."
  }
}
```

#### 5.2.4 步骤完成

```json
{
  "event": "step_completed",
  "timestamp": "2026-01-27T10:00:00.300Z",
  "data": {
    "step_id": "step_01",
    "step_name": "批量验证用户登录",
    "status": "success",
    "duration": 0.2,
    "retry_count": 0,
    "summary": {
      "assertions": {
        "total": 3,
        "passed": 3,
        "failed": 0
      }
    }
  }
}
```

#### 5.2.5 步骤失败

```json
{
  "event": "step_failed",
  "timestamp": "2026-01-27T10:00:02.150Z",
  "data": {
    "step_id": "step_03",
    "step_name": "查询订单详情",
    "status": "failed",
    "duration": 0.15,
    "error_info": {
      "type": "AssertionError",
      "category": "business",
      "message": "业务码校验失败: 期望 0, 实际 1001"
    },
    "failed_assertions": [
      {
        "check": "body.code == 0",
        "expect": 0,
        "actual": 1001
      }
    ]
  }
}
```

#### 5.2.6 任务完成

```json
{
  "event": "task_completed",
  "timestamp": "2026-01-27T10:01:30.500Z",
  "data": {
    "task_id": "task_20260127_abc123",
    "task_name": "电商下单全流程测试",
    "status": "failed",
    "duration": 90.5,
    "summary": {
      "total": 11,
      "success": 8,
      "failed": 2,
      "error": 1,
      "skipped": 0
    },
    "report_url": "http://frontend.com/reports/task_20260127_abc123.html"
  }
}
```

#### 5.2.7 心跳

```json
{
  "event": "heartbeat",
  "timestamp": "2026-01-27T10:00:30Z",
  "data": {
    "message": "Task is still running..."
  }
}
```

### 5.3 事件类型列表

| 事件 | 说明 | 数据内容 |
|------|------|----------|
| `task_started` | 任务开始 | task_id, task_name, total_steps |
| `step_started` | 步骤开始 | step_id, step_name, step_type |
| `step_progress` | 步骤进度 | progress, current_iteration |
| `step_completed` | 步骤完成 | step_id, status, duration |
| `step_failed` | 步骤失败 | step_id, error_info, failed_assertions |
| `step_retried` | 步骤重试 | step_id, attempt, error |
| `task_completed` | 任务完成 | status, summary, report_url |
| `heartbeat` | 心跳 | timestamp |
| `error` | 错误 | error_type, message |

---

## 附录：前端渲染建议

### A.1 敏感信息脱敏规则

```javascript
// 自动脱敏字段列表
const SENSITIVE_FIELDS = [
  'password', 'passwd', 'pwd',
  'token', 'access_token', 'refresh_token',
  'secret', 'api_key', 'apikey',
  'credit_card', 'id_card', 'ssn',
  'authorization'
];

// 脱敏函数
function maskValue(key, value) {
  if (SENSITIVE_FIELDS.includes(key.toLowerCase())) {
    return '***';
  }
  if (typeof value === 'string' && value.length > 20) {
    return value.substring(0, 10) + '...';
  }
  return value;
}
```

### A.2 时间格式化

```javascript
// ISO 8601 → 本地时间
function formatTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// 毫秒 → 人类可读
function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  return `${(ms / 60000).toFixed(2)}m`;
}
```

### A.3 状态颜色映射

```css
:root {
  --color-success: #52c41a;
  --color-failed: #ff4d4f;
  --color-error: #faad14;
  --color-skipped: #d9d9d9;
  --color-running: #1890ff;
}

.status-success { color: var(--color-success); }
.status-failed { color: var(--color-failed); }
.status-error { color: var(--color-error); }
.status-skipped { color: var(--color-skipped); }
.status-running { color: var(--color-running); }
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2026-01-27 | 新增：测试套件、错误分类、性能指标、重试历史、变量追踪等 |
| 1.0 | 2026-01-20 | 初始版本 |
