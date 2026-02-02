**文档目的**:

1. 向 Sisyphus-API-Engine 社区反馈框架使用中的痛点
2. 提供具体的改进建议和实现思路
3. 促进框架功能完善，提升用户体验

---

## 🔴 高优先级改进

### 1. 变量作用域与嵌套引用增强

**问题描述**:

当前框架不支持在 YAML 顶层的 `variables` 部分嵌套引用配置变量，导致必须重复写长长的路径。

**当前限制**:
```yaml
# ❌ 不支持嵌套引用
config:
  profiles:
    ci_62:
      variables:
        test_suffix: "0202093000"

variables:
  # 无法这样写
  category_name: "test_${config.profiles.ci_62.variables.test_suffix}"

  # 必须在每个步骤中重复
```

**期望行为**:
```yaml
# ✅ 支持在 variables 中嵌套引用
variables:
  category_name: "test_${config.profiles[config.active_profile].variables.test_suffix}"
  datasource_name: "ds_${config.variables.test_suffix}"

steps:
  - name: "创建类目"
    body:
      nodeName: "${category_name}"  # 简洁引用

  - name: "创建数据源"
    body:
      dataName: "${datasource_name}"  # 简洁引用
```

**影响范围**:
- 所有需要使用配置变量的测试用例
- 代码可读性和维护性

**实现建议**:
```python
# 框架在加载 YAML 时，递归解析变量引用
class VariableResolver:
    def resolve(self, value, context):
        if isinstance(value, str) and '${' in value:
            # 支持嵌套引用: config.profiles[x].variables.y
            return self.resolve_nested(value, context)
        return value
```

**工作量评估**: 2-3 天

---

### 2. 异步轮询机制

**问题描述**:

在测试异步操作（如项目创建、元数据同步）时，需要等待操作完成后才能执行下一步。当前框架不支持轮询机制，导致测试不稳定或需要人工估算等待时间。

**实际案例**:
```yaml
# ❌ 项目刚创建无法立即删除 (error code 272)
- name: "创建项目"
  # 创建项目需要时间初始化

- name: "删除项目"
  # 失败！项目还在初始化中
  # 错误: {"code": 272, "message": "项目不能被删除"}
```

**当前变通方案** (不稳定):
```yaml
- name: "强制等待"
  type: sleep
  duration: 10000  # 等待10秒，但可能不够或太长

- name: "删除项目"
  # 希望已经初始化完成
```

**期望行为**:
```yaml
# ✅ 支持轮询等待
- name: "等待项目就绪"
  type: poll
  url: "${config.base_url}/api/rdos/batch/project/getProjectList"
  method: POST
  headers:
    Cookie: "${config.auth_cookie}"
  body:
    projectId: "${project_id}"
  poll_config:
    # 轮询条件
    condition:
      jsonpath: "$.data[?(@.projectId == ${project_id})].status"
      operator: "eq"
      expect: "ACTIVE"
    # 轮询策略
    max_attempts: 30        # 最多30次
    interval: 2000          # 每2秒一次
    timeout: 60000          # 总超时60秒
    backoff: "fixed"        # 固定间隔 / exponential 指数退避
  on_timeout:
    behavior: "fail"        # fail / continue
    message: "项目初始化超时"

- name: "删除项目"
  depends_on: "等待项目就绪"
  # 现在可以安全删除，保证项目已就绪
```

**API 设计建议**:
```yaml
# 轮询步骤定义
type: poll  # 新增步骤类型

# 轮询配置
poll_config:
  condition:
    type: "jsonpath" | "status_code" | "script"
    path: "$.data.status"
    operator: "eq" | "ne" | "gt" | "lt" | "contains" | "exists"
    expect: "ACTIVE"
  strategy:
    max_attempts: 30
    interval: 2000
    timeout: 60000
    backoff: "fixed" | "exponential"
```

**影响范围**:
- 所有涉及异步操作的测试场景
- 项目创建、任务执行、元数据同步等

**实现建议**:
```python
# 框架内置轮询执行器
class PollStepExecutor:
    def execute(self, step):
        for attempt in range(step.max_attempts):
            response = self.send_request(step)
            if self.check_condition(response, step.condition):
                return response
            time.sleep(step.get_interval(attempt))
        raise TimeoutError(f"轮询超时: {step.name}")
```

**工作量评估**: 3-5 天

---

## 🟠 中高优先级改进

### 3. JSONPath 表达式增强

**问题描述**:

当前 JSONPath 不支持 filter 表达式，无法从数组中提取特定条件的数据。这在处理复杂响应结构时限制很大。

**实际案例**:
```python
# Python 中可以这样
params = response['data']['params']
param_id = next(p['id'] for p in params if p['paramName'] == 'specific_param')
```

```yaml
# ❌ YAML 中不支持
extractors:
  - type: jsonpath
    name: param_id
    path: "$.data.params[?(@.paramName == 'specific_param')].id"
    # 错误: 不支持 filter 表达式
```

**当前变通方案** (需要多步):
```yaml
- name: "获取所有参数"
  # 获取整个数组

- name: "手动筛选"
  # 无法在 YAML 中实现，需要用脚本
```

**期望行为**:
```yaml
# ✅ 支持 JSONPath filter 表达式
extractors:
  # 基础 filter
  - type: jsonpath
    name: param_id
    path: "$.data.params[?(@.paramName == 'specific_param')].id"
    default: null  # 找不到时使用默认值

  # 复杂 filter
  - type: jsonpath
    name: active_datasources
    path: "$.data.data[?(@.status == 1 && @.isMeta == 1)]"

  # 支持多个条件
  - type: jsonpath
    name: specific_table
    path: "$.data.tables[?(@.name == 'test_${config.test_suffix}')]"
```

**内置函数建议**:
```yaml
# 提供常用辅助函数
extractors:
  # 获取第一个匹配项
  - type: jsonpath
    name: first_item
    path: "first($$.data.params)"

  # 查找特定元素
  - type: jsonpath
    name: found_param
    path: "find($$.data.params, 'paramName', 'specific_param')"

  # 过滤数组
  - type: jsonpath
    name: active_items
    path: "filter($$.data, 'status', 1)"
```

**影响范围**:
- 复杂数据结构的提取
- 需要精确匹配的场景

**实现建议**:
```python
# 使用 jsonpath-ng 或类似库增强 JSONPath
from jsonpath_ng import parse

def enhanced_jsonpath(expression, data):
    # 支持 [?(@.field == 'value')] 语法
    parse(expression).find(data)
```

**工作量评估**: 2-3 天

---

### 4. 条件执行增强

**问题描述**:

当前 `condition` 字段语法有限，只支持简单的表达式判断，无法处理复杂的条件逻辑。

**当前限制**:
```yaml
# 只支持简单条件
condition: "${var1} != null"
condition: "${count} > 0"
```

**期望行为**:
```yaml
# ✅ 支持逻辑组合
- name: "复杂条件示例"
  condition:
    # AND 逻辑
    and:
      - "${var1} != null"
      - "${var2} > 0"
      - "${var3} == 'expected'"
    # OR 逻辑
    or:
      - "${status} == 'SUCCESS'"
      - "${status} == 'PARTIAL_SUCCESS'"
    # NOT 逻辑
    not:
      - "${error} != null"

# ✅ 支持嵌套条件
- name: "嵌套条件"
  condition:
    or:
      - and:
        - "${type} == 'MySQL'"
        - "${version} >= '5.7'"
      - and:
        - "${type} == 'Oracle'"
        - "${version} >= '11g'"

# ✅ 支持跳过原因
- name: "可选功能测试"
  condition:
    if: "${feature_enabled} == true"
    else: skip  # skip / fail / continue
    reason: "实验性功能未启用，跳过此测试"

# ✌ 支持失败标记
- name: "预期失败的步骤"
  condition:
    expect_fail: true
    reason: "验证错误处理逻辑"
```

**影响范围**:
- 需要复杂条件判断的测试场景
- 可选功能测试
- 多环境兼容测试

**工作量评估**: 1-2 天

---

## 🟠 中优先级改进

### 5. 循环支持

**问题描述**:

在需要批量处理多个对象时（如批量删除表），当前框架只能重复编写步骤，无法使用循环。

**实际案例**:
```python
# Python 中可以循环处理
for table_id in table_ids:
    delete_table(table_id)
    verify_deleted(table_id)
```

```yaml
# ❌ YAML 中只能重复编写
- name: "删除表1"
  body:
    tableId: "${table_ids[0]}"

- name: "删除表2"
  body:
    tableId: "${table_ids[1]}"

# ... 无法动态处理任意数量的表
```

**期望行为**:
```yaml
# ✅ 支持 foreach 循环
- name: "批量删除表"
  type: foreach
  items: "${table_ids}"  # 数组变量或 JSONPath
  item_name: "table_id"
  item_index: "index"   # 可选的索引变量
  steps:
    - name: "删除表 ${table_id} (索引: ${index})"
      type: request
      url: "/api/deleteTable"
      body:
        tableId: "${table_id}"
      validations:
        - type: eq
          path: "$.code"
          expect: 1

    - name: "验证删除 ${table_id}"
      type: request
      url: "/api/getTable"
      body:
        tableId: "${table_id}"
      # 期望返回 404 或特定错误码
      validations:
        - type: eq
          path: "$.code"
          expect: 404

# ✅ 支持字典遍历
- name: "处理多个数据源"
  type: foreach
  items: "${datasources}"  # 字典对象
  item_key: "ds_type"
  item_value: "ds_config"
  steps:
    - name: "创建 ${ds_type} 数据源"
      body:
        type: "${ds_type}"
        config: "${ds_config}"

# ✅ 支持循环控制
- name: "有限循环"
  type: foreach
  items: "${large_array}"
  max_iterations: 10  # 最多处理10个
  break_on_error: true  # 遇错停止
  steps:
    - name: "处理项"
      # ...
```

**循环场景**:
- 批量创建/删除资源
- 批量验证
- 数据驱动测试

**影响范围**:
- 批量操作场景
- 需要处理可变数量对象的测试

**实现建议**:
```python
class ForeachStepExecutor:
    def execute(self, step):
        items = self.resolve_items(step.items)
        for index, item in enumerate(items):
            context = {
                step.item_name: item,
                step.item_index: index
            }
            self.execute_substeps(step.steps, context)
```

**工作量评估**: 3-4 天

---

### 6. 错误处理与重试机制

**问题描述**:

网络不稳定或服务临时不可用时，测试可能失败。支持自动重试和错误处理可以提升测试稳定性。

**实际案例**:
```yaml
# ❌ 偶发性网络错误导致测试失败
- name: "调用外部API"
  # 可能因为 500/502/503 失败
  # 测试不稳定，需要手动重试
```

**期望行为**:
```yaml
# ✅ 支持自动重试
- name: "创建资源"
  type: request
  url: "/api/createResource"
  retry:
    max_attempts: 3
    backoff: "exponential"  # 指数退避: 1s, 2s, 4s
    initial_interval: 1000
    on_errors:
      - code: 500
      - code: 502
      - code: 503
      - code: 504
    on_network_error: true  # 网络错误也重试

# ✅ 支持错误处理分支
- name: "主操作"
  type: request
  url: "/api/mainOperation"
  on_failure:
    # 失败时执行回滚
    - name: "回滚操作"
      type: request
      url: "/api/rollback"
      body:
        operation_id: "${main_operation_id}"

  on_success:
    # 成功时执行后续
    - name: "记录日志"
      type: log
      message: "操作成功: ${operation_id}"

# ✅ 支持条件重试
- name: "条件重试示例"
  type: request
  url: "/api/checkStatus"
  retry:
    max_attempts: 5
    condition:
      jsonpath: "$.data.status"
      operator: "ne"
      expect: "COMPLETED"
```

**重试策略**:
```yaml
retry:
  # 策略类型
  strategy: "fixed" | "exponential" | "linear"

  # fixed: 固定间隔
  interval: 2000  # 每次间隔2秒

  # exponential: 指数退避
  initial_interval: 1000  # 初始1秒
  multiplier: 2           # 每次翻倍
  max_interval: 30000     # 最大30秒

  # linear: 线性增长
  initial_interval: 1000
  increment: 1000         # 每次增加1秒
```

**影响范围**:
- 网络不稳定环境
- 调用外部服务的测试
- 需要回滚机制的测试

**工作量评估**: 2-3 天

---

### 7. 验证断言增强

**问题描述**:

当前验证只支持简单的单一条件判断，无法处理"或逻辑"、"范围判断"等复杂验证场景。

**实际案例**:
```yaml
# ❌ 无法验证"业务码为1或130都可接受"
validations:
  - type: eq
    path: "$.code"
    expect: 1
  # 如果返回 130 也会失败，但实际 130 也是可接受的
```

**期望行为**:
```yaml
# ✅ 支持复合验证
- name: "验证业务码或特定错误码"
  type: or
  conditions:
    - type: eq
      path: "$.code"
      expect: 1
      description: "成功"
    - type: eq
      path: "$.code"
      expect: 130
      description: "目录非空（可接受）"
  description: "业务码为1或130都可接受"

# ✅ 支持 AND 验证
- name: "多条件验证"
  type: and
  conditions:
    - type: eq
      path: "$.code"
      expect: 1
    - type: gt
      path: "$.data.count"
      expect: 0
    - type: contains
      path: "$.data.message"
      expect: "成功"

# ✅ 支持范围验证
- name: "数值范围验证"
  type: range
  path: "$.data.count"
  min: 1
  max: 100
  inclusive: true  # 包含边界值

# ✅ 支持集合验证
- name: "验证元素在集合中"
  type: in
  path: "$.data.status"
  values: ["SUCCESS", "PARTIAL_SUCCESS", "PENDING"]

# ✌ 支持自定义脚本验证
- name: "复杂逻辑验证"
  type: script
  language: "python"  # 或 javascript
  expression: |
    # 验证所有期望的表都在结果中
    expected_tables = ['table1', 'table2', 'table3']
    actual_tables = [item['tableName'] for item in data
                     if item.get('isMeta') == 1]
    return all(table in actual_tables for table in expected_tables)
  description: "验证所有期望的表都已同步"

# ✅ 支持正则表达式验证
- name: "格式验证"
  type: regex
  path: "$.data.email"
  pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  description: "验证邮箱格式"
```

**验证类型汇总**:
```yaml
# 基础类型
type: eq | ne | gt | lt | ge | le | contains | exists | regex

# 逻辑类型
type: and | or | not

# 高级类型
type: range | in | script | length | empty
```

**影响范围**:
- 复杂业务逻辑验证
- 需要多种可接受结果的场景

**工作量评估**: 2-3 天

---

## 🟢 低优先级改进

### 8. 数据驱动测试改进

**期望行为**:
```yaml
# ✅ 更清晰的数据驱动语法
data:
  - name: "测试MySQL数据源"
    datasource_type: "MySQL"
    expected_count: 5
    tags: ["smoke", "mysql"]

  - name: "测试Oracle数据源"
    datasource_type: "Oracle"
    expected_count: 3
    tags: ["smoke", "oracle"]

# 在步骤中引用数据变量
steps:
  - name: "创建 ${datasource_type} 数据源"
    body:
      type: "${datasource_type}"

  - name: "验证数量"
    validations:
      - type: eq
        path: "$.data.totalCount"
        expect: "${expected_count}"
```

---

### 9. 内置辅助函数

**期望行为**:
```yaml
variables:
  # 随机字符串
  test_suffix: "${random_string(8)}"
  test_suffix_alpha: "${random_string(8, 'alpha')}"  # 仅字母
  test_suffix_numeric: "${random_numeric(6)}"  # 仅数字

  # 时间函数
  timestamp: "${now()}"
  formatted_time: "${now('%Y%m%d%H%M%S')}"
  future_time: "${now('+1h')}"  # 1小时后

  # 数组操作
  first_item: "${first(array_var)}"
  last_item: "${last(array_var)}"
  item_at: "${at(array_var, 2)}"
  array_length: "${length(array_var)}"

  # 字符串操作
  upper_case: "${upper(text_var)}"
  lower_case: "${lower(text_var)}"
  substring: "${substring(text_var, 0, 10)}"
  replace: "${replace(text_var, 'old', 'new')}"

  # 数值操作
  add: "${add(var1, var2)}"
  subtract: "${subtract(var1, var2)}"
  format_number: "${format(number, '#.00')}"
```

---

### 10. 性能监控与分析

**期望行为**:
```yaml
# 自动记录性能数据
{
  "steps": [
    {
      "name": "获取数据源列表",
      "performance": {
        "total_time": 252.68,
        "dns_time": 25.27,
        "tcp_time": 25.27,
        "server_time": 101.07,
        "download_time": 101.07,
        "size": 6303,
        "slow": true,  # 标记慢步骤
        "threshold": 100  # 慢步骤阈值
      }
    }
  ],
  "summary": {
    "total_time": 1500,
    "slowest_step": "获取数据源列表",
    "performance_score": "C"  # A/B/C/D 评级
  }
}

# 命令行支持
sisyphus test.yaml --performance-report
```

---

### 11. 测试依赖可视化

**期望行为**:
```bash
# 生成依赖关系图
sisyphus test.yaml --graph-deps

# 输出 Mermaid 图表
graph TD
    A[获取数据源列表] --> B[获取表类目]
    A --> C[创建数据源]
    B --> D[同步元数据]
    C --> D
```

**功能**:
- 自动生成测试步骤依赖图
- 识别循环依赖
- 并行执行优化建议

---

### 12. Mock/Stub 支持

**期望行为**:
```yaml
# Mock 外部依赖
- name: "测试步骤"
  mock:
    - url: "/api/external/service"
      method: GET
      response:
        code: 1
        data:
          mocked: true
    - url: "/api/external/config"
      method: POST
      response:
        code: 1
        data:
          config_key: "test_value"

  type: request
  url: "/api/internal/call-external"
  # 实际调用会被 mock 拦截
```

---

## 📊 改进优先级总结

| 优先级 | 功能 | 影响 | 工作量 | 价值 |
|-------|------|------|--------|------|
| 🔴 **高** | 变量作用域增强 | 代码可读性 | 2-3天 | ⭐⭐⭐⭐⭐ |
| 🔴 **高** | 异步轮询机制 | 异步场景测试 | 3-5天 | ⭐⭐⭐⭐⭐ |
| 🟠 **中高** | JSONPath 增强 | 复杂数据提取 | 2-3天 | ⭐⭐⭐⭐ |
| 🟠 **中高** | 条件执行增强 | 测试灵活性 | 1-2天 | ⭐⭐⭐⭐ |
| 🟠 **中** | 循环支持 | 批量操作 | 3-4天 | ⭐⭐⭐ |
| 🟠 **中** | 错误处理与重试 | 测试稳定性 | 2-3天 | ⭐⭐⭐ |
| 🟠 **中** | 验证断言增强 | 验证能力 | 2-3天 | ⭐⭐⭐ |
| 🟢 **低** | 数据驱动改进 | 可读性 | 1-2天 | ⭐⭐ |
| 🟢 **低** | 内置辅助函数 | 便利性 | 2-3天 | ⭐⭐ |
| 🟢 **低** | 性能监控 | 性能优化 | 2-3天 | ⭐ |
| 🟢 **低** | 依赖可视化 | 调试辅助 | 2-3天 | ⭐ |
| 🟢 **低** | Mock/Stub 支持 | 隔离测试 | 3-4天 | ⭐ |

---

## 🤝 社区贡献

### 如何贡献

1. **讨论建议**: 在 GitHub Issues 中讨论这些改进建议
2. **实现功能**: 选择感兴趣的功能提交 Pull Request
3. **编写文档**: 完善功能文档和使用示例
4. **分享经验**: 分享实际使用中的最佳实践

### 提交流程

```bash
# 1. Fork 项目
git clone https://github.com/YOUR_USERNAME/Sisyphus-api-engine.git

# 2. 创建功能分支
git checkout -b feature/variable-scope-enhancement

# 3. 实现功能
# ... 编写代码 ...

# 4. 提交代码
git commit -m "feat: 支持变量嵌套引用"

# 5. 推送到远程
git push origin feature/variable-scope-enhancement

# 6. 创建 Pull Request
# 在 GitHub 上创建 PR，引用本文档
```

### 实现建议优先级

**第一阶段** (高优先级):
1. 变量作用域增强
2. 异步轮询机制

**第二阶段** (中高优先级):
3. JSONPath 增强
4. 条件执行增强

**第三阶段** (中优先级):
5. 循环支持
6. 错误处理与重试
7. 验证断言增强
