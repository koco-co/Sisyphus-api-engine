# WebSocket 实时推送使用指南

## 功能概述

Sisyphus API Engine 支持 WebSocket 实时推送功能，可以在测试执行过程中实时推送进度、日志和变量更新到 WebSocket 客户端。

## 配置方式

### 方式1: YAML 配置（推荐）

在测试用例 YAML 文件的 `config` 部分添加 `websocket` 配置：

```yaml
name: "示例测试"
description: "WebSocket实时推送示例"

config:
  name: "测试配置"
  timeout: 30

  # WebSocket配置
  websocket:
    enabled: true              # 是否启用WebSocket服务器
    host: "localhost"          # 服务器地址
    port: 8765                 # 服务器端口
    send_progress: true        # 发送进度事件
    send_logs: true            # 发送日志事件
    send_variables: false      # 发送变量更新事件（生产环境建议关闭）

steps:
  # ... 测试步骤
```

**优点**：
- ✅ 配置随用例保存，便于管理
- ✅ 不同用例可以有不同的WebSocket配置
- ✅ 适合长期使用的测试项目

### 方式2: CLI 命令参数

通过命令行参数启用 WebSocket：

```bash
# 基本用法
sisyphus-api-engine --cases test.yaml --ws-server

# 自定义服务器地址和端口
sisyphus-api-engine --cases test.yaml --ws-server --ws-host 0.0.0.0 --ws-port 9000
```

**优点**：
- ✅ 灵活，不需要修改YAML文件
- ✅ 可以按需开启
- ✅ 适合临时测试或调试

### 配置优先级

当同时存在 YAML 配置和 CLI 参数时，**CLI 参数优先级更高**：

```bash
# 即使YAML中配置了port: 8765，CLI参数会覆盖为9000
sisyphus-api-engine --cases test.yaml --ws-server --ws-port 9000
```

## WebSocket 事件类型

系统支持以下8种事件类型：

| 事件类型 | 说明 | 示例数据 |
|---------|------|---------|
| `test_start` | 测试执行开始 | 测试名称、步骤总数 |
| `test_complete` | 测试执行完成 | 状态、通过/失败数、耗时 |
| `step_start` | 步骤开始 | 步骤名称、类型、索引 |
| `step_complete` | 步骤完成 | 状态、耗时、重试次数 |
| `progress` | 进度更新 | 当前进度、百分比、预估剩余时间 |
| `log` | 日志消息 | 日志级别、消息内容 |
| `error` | 错误发生 | 错误类型、错误消息、建议 |
| `variable_update` | 变量更新 | 变量名、变量值、来源 |

## 客户端连接

### 使用示例客户端

项目提供了一个 WebSocket 客户端示例：

```bash
# 连接到默认地址 (localhost:8765)
python examples/websocket_client_demo.py

# 连接到自定义地址
python examples/websocket_client_demo.py --host 192.168.1.100 --port 9000
```

### 自定义客户端

使用 Python `websockets` 库：

```python
import asyncio
import websockets
import json

async def connect_to_websocket():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event['type']}")
            print(f"Data: {event['data']}")

asyncio.run(connect_to_websocket())
```

使用 JavaScript：

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type);
    console.log('Data:', data.data);
};

ws.onopen = function() {
    console.log('Connected to WebSocket server');
};

ws.onclose = function() {
    console.log('Disconnected from WebSocket server');
};
```

## 使用场景

### 1. CI/CD 集成

在 CI/CD 流程中实时查看测试进度：

```yaml
# .gitlab-ci.yml
test_api:
  script:
    - sisyphus-api-engine --cases test.yaml --ws-server --ws-host 0.0.0.0
  # 在另一个终端连接WebSocket查看实时输出
```

### 2. 远程监控

在不同机器上监控测试执行：

```bash
# 测试机器
sisyphus-api-engine --cases test.yaml --ws-server --ws-host 0.0.0.0

# 监控机器（连接到测试机器的IP）
python websocket_client_demo.py --host 192.168.1.100
```

### 3. Web界面集成

将WebSocket事件集成到自定义Web界面：

```html
<div id="progress"></div>
<div id="logs"></div>

<script>
const ws = new WebSocket('ws://localhost:8765');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
        document.getElementById('progress').textContent =
            `Progress: ${data.data.percentage}%`;
    }

    if (data.type === 'log') {
        const logDiv = document.getElementById('logs');
        logDiv.innerHTML += `<p>${data.data.message}</p>`;
    }
};
</script>
```

## 完整示例

参见 `examples/12_WebSocket实时推送.yaml` 查看完整示例。

运行示例：

```bash
# 方式1: 使用YAML配置（推荐）
sisyphus-api-engine --cases examples/12_WebSocket实时推送.yaml

# 方式2: 使用CLI参数
sisyphus-api-engine --cases examples/12_WebSocket实时推送.yaml --ws-server

# 在另一个终端连接客户端
python examples/websocket_client_demo.py
```

## 性能建议

1. **生产环境**：建议将 `send_variables` 设为 `false`，避免敏感数据泄露
2. **高频率测试**：减少日志推送频率，设置 `send_logs: false`
3. **并发测试**：WebSocket服务器可以同时服务多个客户端

## 故障排查

### 连接失败

```bash
# 错误: Connection refused
# 解决: 确认WebSocket服务器已启动，检查端口是否正确
```

### 未收到事件

```bash
# 检查YAML配置中 enabled 是否为 true
# 检查防火墙设置
# 查看服务器端日志
```

### 端口占用

```bash
# 错误: Address already in use
# 解决: 更换端口或关闭占用端口的进程
sisyphus-api-engine --cases test.yaml --ws-server --ws-port 8766
```

## 相关文档

- [任务进度列表](../docs/任务进度列表.md) - 功能开发进度
- [API-Engine输入协议规范](../docs/API-Engine输入协议规范.md) - YAML协议详细说明
- [WebSocket事件定义](../apirun/websocket/events.py) - 事件数据结构
