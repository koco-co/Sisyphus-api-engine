# 更新日志

本文件记录 Sisyphus API Engine 的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 规范，
项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html) 规范。

## [1.0.3] - 2026-01-31

### ✨ 新增
- 微秒级时间戳支持
  - 新增 `timestamp_us()` 函数：返回微秒级 Unix 时间戳
  - 新增 `now_us()` 函数：返回格式化的微秒时间字符串（YYYYMMDDHHMMSS%f）
  - 支持 `now().strftime('%f')` 获取微秒部分（6位数字）

### 🔧 变更
- **依赖升级**：`jsonpath` → `jsonpath-ng>=1.6.0`
  - 完整支持 JSONPath 标准语法
  - 支持过滤表达式、通配符、数组切片等高级功能

- **变量渲染**：`VariableManager.render_string()` 添加递归渲染支持
  - 支持多级嵌套变量引用（如 `${var1_${var2}}`）
  - 最多迭代 10 次（防止循环引用）
  - 自动检测渲染完成状态

- **Contains 验证器**：改进类型处理和边界情况
  - 正确处理 `None` 值
  - 支持列表、字符串、字典类型的包含检查
  - 修复数值类型比较问题

### 🐛 修复
- **JSONPath 复杂表达式支持**
  - 修复过滤表达式不工作的问题（`$.array[?(@.field == 'value')]`）
  - 修复数组索引不稳定的问题（`$.array[1]`）
  - 支持通配符访问（`$.array[*].field`）
  - 支持数值比较过滤（`$.array[?(@.price > 100)]`）
  - 支持布尔值过滤（`$.array[?(@.active == true)]`）

- **变量嵌套引用渲染**
  - 修复嵌套变量引用无法正确展开的问题
  - 支持多级嵌套（如 `${base}.${env}.com`）
  - 添加循环引用保护机制

- **Contains 验证器稳定性**
  - 修复对数组验证时偶尔报告不存在的问题
  - 修复包含 `None` 值的列表验证失败问题
  - 修复字典键检查的类型错误

- **时间戳精度支持**
  - 修复微秒格式 `%f` 不生效的问题
  - 提供专用函数避免快速运行时的重复问题

### 🗑️ 废弃
- 无

### ❌ 移除
- 无

### 🔒 安全
- 无

---

## [1.0.2] - 2026-01-29

### ✨ 新增
- JSONPath 函数支持（20+ 种内置函数）
  - 数组函数：length(), first(), last(), reverse(), sort(), unique(), flatten()
  - 数值函数：sum(), avg(), min(), max()
  - 字符串函数：upper(), lower(), trim(), split(), join()
  - 检查函数：contains(), starts_with(), ends_with(), matches()
  - 对象函数：keys(), values()

- 步骤控制功能
  - `skip_if`：条件为真时跳过步骤
  - `only_if`：条件为真时执行步骤
  - `depends_on`：步骤依赖关系
  - `setup`/`teardown`：步骤前后钩子

- 增强重试机制
  - 支持多种重试策略（fixed/exponential/linear）
  - 可配置重试条件（network/timeout/assertion）
  - 支持延迟和抖动（jitter）

### 🔧 变更
- 改进错误提示信息
- 优化变量渲染性能

### 🐛 修复
- 修复模板函数在某些情况下渲染失败的问题
- 修复验证器路径解析的边界情况

---

## [1.0.0] - 2026-01-27

### ✨ 新增
- 🎉 初始版本发布
- HTTP/HTTPS 请求支持（GET/POST/PUT/DELETE/PATCH）
- 数据库操作（MySQL/PostgreSQL/SQLite）
- 变量提取器（JSONPath/正则表达式/Header/Cookie）
- 断言验证器（20+ 种验证类型）
- 环境配置切换（profiles）
- 数据驱动测试（CSV/JSON/数据库）
- 循环控制（for/while）
- 并发执行
- 脚本执行（Python/JavaScript）
- 等待机制（固定延迟/条件等待）
- Mock 服务器
- WebSocket 实时推送
- 性能测试
- 多种输出格式（JSON/CSV/HTML/JUnit/Allure）

---

## 版本说明

### 版本号规则
- **主版本号（Major）**：不兼容的 API 变更
- **次版本号（Minor）**：向后兼容的功能新增
- **修订号（Patch）**：向后兼容的问题修复

### 变更类型说明
- **✨ 新增**：新功能
- **🔧 变更**：功能变更
- **🗑️ 废弃**：即将废弃的功能
- **❌ 移除**：已移除的功能
- **🐛 修复**：问题修复
- **🔒 安全**：安全相关修复

---

## 相关文档
- [API 输入协议规范](docs/API-Engine输入协议规范.md)
- [API 输出协议规范](docs/API-Engine输出协议规范.md)
