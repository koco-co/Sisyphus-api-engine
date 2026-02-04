# HTTP请求

> 掌握 Sisyphus API Engine 中 HTTP 请求的完整配置方法。

---

## 📖 概述

HTTP 请求是 API 测试的核心。Sisyphus 支持所有标准 HTTP 方法（GET、POST、PUT、PATCH、DELETE、HEAD、OPTIONS），并提供灵活的请求配置选项，包括请求头、查询参数、请求体等。

---

## 🎯 学习目标

完成本章后，你将能够：
- 使用各种 HTTP 方法发送请求
- 配置请求头（Headers）
- 配置查询参数（Query Parameters）
- 配置请求体（Body）

---

## 📚 核心概念

### HTTP 方法

| 方法 | 用途 | 是否有请求体 |
|------|------|-------------|
| GET | 获取资源 | 通常无 |
| POST | 创建资源 | 是 |
| PUT | 完整更新资源 | 是 |
| PATCH | 部分更新资源 | 是 |
| DELETE | 删除资源 | 可选 |
| HEAD | 获取响应头 | 无 |
| OPTIONS | 获取支持的方法 | 无 |

### 请求步骤类型

当 `type` 为 `request` 或省略时，表示 HTTP 请求步骤：

```yaml
steps:
  - name: "请求步骤"
    type: request  # 可省略，默认为 request
    method: GET
    url: "https://api.example.com/users"
```

---

## ⚙️ YAML 关键字参考

| 关键字 | 类型 | 必填 | 默认值 | 描述 |
|-------|------|------|--------|------|
| name | string | ✅ | - | 步骤名称 |
| type | string | ❌ | request | 步骤类型 |
| method | string | ✅ | GET | HTTP 方法 |
| url | string | ✅ | - | 请求 URL |
| headers | object | ❌ | {} | 请求头 |
| params | object | ❌ | {} | 查询参数 |
| body | object/string | ❌ | null | 请求体 |
| timeout | number | ❌ | 30 | 超时时间（秒） |

---

## 💡 使用示例

### 示例1：GET 请求（带查询参数）

```yaml
- name: "查询用户列表"
  method: GET
  url: "https://httpbin.org/get"
  params:
    page: 1
    limit: 10
    status: "active"
  validations:
    - type: status_code
      path: "$.status_code"
      expect: "200"
```

### 示例2：POST 请求（JSON 请求体）

```yaml
- name: "创建新用户"
  method: POST
  url: "https://httpbin.org/post"
  headers:
    Content-Type: "application/json"
    Authorization: "Bearer ${token}"
  body:
    username: "newuser"
    email: "user@example.com"
    age: 25
  validations:
    - type: status_code
      path: "$.status_code"
      expect: "200"
    - type: eq
      path: "$.json.username"
      expect: "newuser"
```

### 示例3：PUT 请求（完整更新）

```yaml
- name: "更新用户信息"
  method: PUT
  url: "https://httpbin.org/put"
  headers:
    Content-Type: "application/json"
  body:
    id: 123
    username: "updateduser"
    email: "updated@example.com"
    status: "active"
```

### 示例4：DELETE 请求

```yaml
- name: "删除用户"
  method: DELETE
  url: "https://httpbin.org/delete"
  headers:
    Authorization: "Bearer ${token}"
  body:
    user_id: 123
    reason: "用户请求删除"
```

---

## 🔧 推荐组合

### 与变量提取组合

```yaml
- name: "登录获取Token"
  method: POST
  url: "${base_url}/login"
  body:
    username: "admin"
    password: "password"
  extractors:
    - name: token
      type: jsonpath
      path: "$.data.token"

- name: "使用Token访问API"
  method: GET
  url: "${base_url}/profile"
  headers:
    Authorization: "Bearer ${token}"
```

### 与验证断言组合

```yaml
- name: "完整请求验证"
  method: POST
  url: "${base_url}/api/users"
  body:
    name: "测试用户"
  validations:
    - type: status_code
      path: "$.status_code"
      expect: "201"
    - type: eq
      path: "$.data.name"
      expect: "测试用户"
    - type: type
      path: "$.data.id"
      expect: "int"
```

---

## ⚠️ 注意事项

1. **URL 编码**：特殊字符需要正确编码
2. **Content-Type**：POST/PUT/PATCH 请求需要设置正确的 Content-Type
3. **超时设置**：外网请求建议增加超时时间

---

## 🔗 相关资源

- [上一章：快速入门](./00_快速入门.md)
- [下一章：变量系统](./02_变量系统.md)
- [示例文件](../examples/01_HTTP请求方法.yaml)
- [示例文件](../examples/02_请求参数配置.yaml)
