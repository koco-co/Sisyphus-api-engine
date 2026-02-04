# WebSocket 实时推送

> 学习如何接收测试执行的实时进度推送。

---

## 📖 概述

WebSocket 模块提供测试执行的实时进度推送，可用于构建测试监控面板。

---

## ⚙️ 关键字参考

| 关键字 | 类型 | 描述 |
|-------|------|------|
| websocket | object | WebSocket 配置 |
| enabled | boolean | 是否启用 |
| port | number | WebSocket 端口 |

---

## 💡 使用示例

```yaml
config:
  websocket:
    enabled: true
    port: 9000
```

### 客户端订阅示例

```javascript
const ws = new WebSocket('ws://localhost:9000');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('进度:', data.progress);
  console.log('当前步骤:', data.current_step);
};
```

---

## 🔗 相关资源

- [上一章：Mock服务器](./13_Mock服务器.md)
- [下一章：性能测试](./15_性能测试.md)
