# Sisyphus API Engine - YAML测试用例示例

本目录包含41个YAML测试用例示例，涵盖了Sisyphus API Engine的所有主要功能。

## 📋 示例列表

### 基础功能 (01-11)

| 文件 | 功能描述 |
|------|----------|
| `01_HTTP请求方法.yaml` | 演示所有HTTP请求方法的使用（GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS） |
| `02_请求参数配置.yaml` | 演示各种请求参数的配置方式（Query参数/Headers/Body/Cookies） |
| `03_变量基础语法.yaml` | 演示变量系统的基本语法和用法（全局变量/Profile变量/提取变量） |
| `04_内置模板函数.yaml` | 演示内置模板函数的使用（random/uuid/timestamp/base64等） |
| `05_基础断言验证.yaml` | 演示基础比较器的使用（eq/ne/gt/lt/contains/regex/type） |
| `06_环境配置切换.yaml` | 演示多环境配置和环境切换功能（dev/test/prod） |
| `07_使用全局配置.yaml` | 演示使用!include标签引入全局配置文件 |
| `08_输出格式配置.yaml` | 演示各种输出报告格式的配置（JSON/CSV/HTML/JUnit/Allure） |
| `09_变量提取器.yaml` | 演示从响应中提取变量（JSONPath/Regex/Header/Cookie提取器） |
| `10_高级断言验证.yaml` | 演示高级比较器和逻辑运算符的使用 |
| `11_JSONPath函数演示.yaml` | 演示增强JSONPath函数功能（20+种函数） |

### 流程控制 (12-16)

| 文件 | 功能描述 |
|------|----------|
| `12_步骤控制.yaml` | 演示步骤控制功能（skip_if/only_if/depends_on/setup/teardown） |
| `13_重试机制.yaml` | 演示简单重试和增强重试策略的使用 |
| `14_等待机制.yaml` | 演示等待机制（固定延迟/条件等待） |
| `15_循环控制.yaml` | 演示循环控制功能（for循环/while循环） |
| `16_并发执行.yaml` | 演示并发执行功能（并发请求/并发控制） |

### 高级功能 (17-24)

| 文件 | 功能描述 |
|------|----------|
| `17_数据驱动测试.yaml` | 演示数据驱动测试功能（CSV/JSON/内联数据） |
| `18_脚本执行.yaml` | 演示脚本执行功能（Python/JavaScript脚本） |
| `19_完整流程测试.yaml` | 演示完整测试流程（多个步骤的端到端测试） |
| `20_Mock服务器测试.yaml` | 演示Mock服务器的使用 |
| `21_WebSocket实时推送.yaml` | 演示WebSocket实时推送功能 |
| `22_性能测试.yaml` | 演示性能测试和性能指标收集 |
| `23_数据库操作.yaml` | 演示数据库操作（MySQL/PostgreSQL/SQLite） |
| `24_最佳实践.yaml` | 演示测试用例编写的最佳实践 |

### 新增功能 (25-38)

| 文件 | 功能描述 |
|------|----------|
| `25_字符串验证器.yaml` | 演示字符串验证器的使用 |
| `26_增强功能测试.yaml` | 演示v2.0.0新增的增强功能 |
| `27_已发现功能验证.yaml` | 验证已实现的功能 |
| `28_多值提取功能.yaml` | 演示提取所有匹配值的功能 |
| `29_条件提取简化版.yaml` | 演示条件提取功能的简化语法 |
| `30_增强条件语法.yaml` | 演示增强的条件语法 |
| `31_重试机制增强.yaml` | 演示增强的retry_policy配置 |
| `32_重试机制验证.yaml` | 验证重试机制的多种配置 |
| `33_详细日志功能.yaml` | 演示详细日志功能 |
| `34_脚本封装增强.yaml` | 演示脚本封装的增强功能 |
| `35_条件语法增强.yaml` | 演示条件语法的增强版本 |
| `36_重试机制增强.yaml` | 演示多种重试策略（与31类似但有差异） |
| `37_详细执行日志.yaml` | 演示--log-level和--log-file参数的使用 |
| `38_并行执行优化.yaml` | 演示并行执行的优化配置 |

### 特殊示例

| 文件 | 功能描述 |
|------|----------|
| `变量嵌套引用示例.yaml` | 演示变量间的嵌套引用功能 |
| `异步轮询示例.yaml` | 演示异步轮询功能的使用 |
| `综合功能测试.yaml` | 综合演示多个功能的联合使用 |

## 🚀 快速开始

### 运行单个测试用例

```bash
# 运行HTTP请求方法测试
sisyphus --cases examples/01_HTTP请求方法.yaml

# 运行数据驱动测试
sisyphus --cases examples/17_数据驱动测试.yaml

# 运行完整流程测试
sisyphus --cases examples/19_完整流程测试.yaml
```

### 运行多个测试用例

```bash
# 运行基础功能测试
sisyphus --cases examples/01*.yaml examples/02*.yaml examples/03*.yaml

# 运行所有YAML示例
sisyphus --cases examples/*.yaml

# 运行指定目录
sisyphus --cases examples/
```

### 指定环境运行

```bash
# 使用dev环境
sisyphus --cases examples/06_环境配置切换.yaml --profile dev

# 使用prod环境
sisyphus --cases examples/06_环境配置切换.yaml --profile prod
```

### 验证YAML语法

```bash
# 验证单个文件
sisyphus-validate examples/01_HTTP请求方法.yaml

# 验证所有文件
sisyphus-validate examples/*.yaml

# 验证整个目录
sisyphus-validate examples/
```

### 生成测试报告

```bash
# JSON格式
sisyphus --cases examples/01_HTTP请求方法.yaml -o result.json

# HTML报告（中文）
sisyphus --cases examples/01_HTTP请求方法.yaml --format html --report-lang zh -o report.html

# HTML报告（英文）
sisyphus --cases examples/01_HTTP请求方法.yaml --format html --report-lang en -o report.html

# Allure报告
sisyphus --cases examples/01_HTTP请求方法.yaml --allure
allure open allure-results
```

## 📊 功能覆盖

本示例集覆盖了以下核心功能：

- ✅ **HTTP测试**：所有HTTP方法、请求参数、响应验证
- ✅ **变量系统**：全局变量、Profile变量、嵌套引用、提取变量
- ✅ **模板渲染**：内置模板函数（20+函数）
- ✅ **数据驱动**：CSV、JSON、数据库、内联数据
- ✅ **流程控制**：条件、循环、并发、依赖、重试、等待
- ✅ **断言验证**：基础比较器、高级比较器、逻辑运算符
- ✅ **变量提取**：JSONPath、正则表达式、Header、Cookie提取
- ✅ **数据库操作**：MySQL、PostgreSQL、SQLite
- ✅ **脚本执行**：Python、JavaScript脚本
- ✅ **Mock服务**：内置Mock服务器
- ✅ **WebSocket推送**：实时测试进度推送
- ✅ **性能测试**：性能指标收集和分析

## 🔧 使用建议

### 学习路径

1. **初学者**：从01-11号示例开始，学习基础功能
2. **进阶用户**：学习12-24号示例，掌握流程控制和高级功能
3. **高级用户**：研究25-38号示例，了解最新特性和最佳实践

### 自定义示例

建议以现有示例为模板，根据实际需求进行修改：

```bash
# 复制示例作为起点
cp examples/24_最佳实践.yaml my_test.yaml

# 编辑创建自己的测试用例
vim my_test.yaml

# 运行测试
sisyphus --cases my_test.yaml
```

## 📖 相关文档

- [输入协议规范](../docs/API-Engine输入协议规范.md) - YAML测试用例完整语法
- [输出协议规范](../docs/API-Engine输出协议规范.md) - 测试结果输出格式
- [提取器使用指南](../docs/提取器使用指南.md) - 变量提取器详细说明
- [验证器使用指南](../docs/验证器使用指南.md) - 断言验证器详细说明
- [日志系统使用指南](../docs/日志系统使用指南.md) - 日志配置和使用

## 💡 提示

- 所有示例都经过`sisyphus-validate`验证，确保语法正确
- 示例使用httpbin.org作为测试端点，无需本地服务
- 部分示例需要Mock服务器或数据库支持，请参考具体示例说明
- 建议按照示例编号顺序学习，由浅入深

---

**最后更新**：2026-02-02
**示例版本**：v2.0.0
**维护状态**：✅ 活跃维护
