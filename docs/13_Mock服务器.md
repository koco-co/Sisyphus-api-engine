# Mock服务器

> 学习如何使用内置 Mock 服务器进行测试。

---

## 📖 概述

Mock 服务器允许模拟 API 响应，用于前端开发、第三方依赖隔离等场景。

---

## ⚙️ YAML 关键字参考

| 关键字 | 类型 | 描述 |
|-------|------|------|
| mock_server | object | Mock 服务器配置 |
| enabled | boolean | 是否启用 |
| port | number | 监听端口 |
| routes | array | 路由配置列表 |

---

## 💡 使用示例

```yaml
config:
  mock_server:
    enabled: true
    port: 8888
    routes:
      - path: "/api/users"
        method: GET
        response:
          status: 200
          body:
            users: [{"id": 1, "name": "Test"}]
      - path: "/api/users"
        method: POST
        response:
          status: 201
          body:
            id: 1
            message: "Created"
```

---

## 🔗 相关资源

- [上一章：数据库操作](./12_数据库操作.md)
- [下一章：WebSocket](./14_WebSocket.md)
