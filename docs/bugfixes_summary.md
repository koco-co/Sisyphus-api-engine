# Bug Fixes Summary

本文档总结了 Sisyphus API Engine 框架中修复的主要问题。

## 修复的问题

### 1. JSONPath Extractor 不支持复杂表达式 ✅

**问题描述**：
- 不支持过滤表达式 `$.array[?(@.field == 'value')]`
- 数组索引 `$.array[1]` 不稳定

**根本原因**：
使用的基础 `jsonpath` 库功能有限，不支持完整的 JSONPath 标准。

**解决方案**：
- 将依赖从 `jsonpath` 升级到 `jsonpath-ng>=1.6.0`
- 完全重写 `enhanced_jsonpath.py` 以支持完整的 JSONPath 功能

**支持的新功能**：
- 过滤表达式：`$.data[?(@.roleName != '项目所有者')].id`
- 数组索引：`$.data[1].id`
- 通配符：`$.users[*].name`
- 数值比较：`$.items[?(@.price > 100)]`
- 布尔值过滤：`$.items[?(@.active == true)]`

**注意事项**：
- 过滤表达式中布尔值使用小写 `true`/`false`，而非 Python 的 `True`/`False`
- 复杂的 AND/OR 条件需要使用 `&` 和 `|` 运算符

---

### 2. 变量嵌套引用无法渲染 ✅

**问题描述**：
```yaml
config:
  variables:
    test_suffix: "0129"
    param_name: "test_param_${test_suffix}"  # 定义时嵌套

steps:
  - body:
      paramName: "${param_name}"  # ❌ 渲染结果: "test_param_" (test_suffix被丢弃)
```

**根本原因**：
`VariableManager.render_string()` 只执行一次渲染，不处理嵌套引用。

**解决方案**：
在 `VariableManager.render_string()` 中添加递归渲染逻辑：
- 最多迭代 10 次（防止循环引用）
- 每次迭代后检查值是否变化
- 直到没有模板引用或达到最大迭代次数

**新功能**：
```yaml
config:
  variables:
    base: "api"
    env: "dev"
    version: "v1"
    url1: "${base}.${env}.com"
    url2: "${url1}/${version}"

steps:
  - url: "${url2}"  # ✅ 渲染结果: "api.dev.com/v1"
```

---

### 3. Contains 验证器对数组验证不稳定 ✅

**问题描述**：
```yaml
validations:
  - type: contains
    path: "$.data[*].paramName"
    expect: "test_param_0131174706"
    # ❌ 即使值存在于数组中也可能报告不存在
```

**根本原因**：
`Comparators.contains()` 对 `None` 值和特殊类型处理不当。

**解决方案**：
改进 `contains` 比较器的逻辑：
- 正确处理 `None` 值
- 对列表进行逐元素比较
- 对字符串进行类型转换后比较
- 支持字典键检查

**改进后**：
```python
@staticmethod
def contains(actual: Any, expected: Any) -> bool:
    # Handle None case
    if actual is None:
        return expected is None

    if isinstance(actual, str):
        if expected is None:
            return False
        return str(expected) in actual

    if isinstance(actual, (list, tuple)):
        for item in actual:
            if item == expected:
                return True
        return False

    if isinstance(actual, dict):
        if expected is None:
            return False
        return expected in actual.keys()

    return False
```

---

### 4. 时间戳微秒级格式支持 ✅

**问题描述**：
```yaml
variables:
  # ❌ 不支持
  test_suffix: "${now().strftime('%Y%m%d%H%M%S%f')}"
  # Error: 渲染后test_suffix为空
```

**解决方案**：
添加专门的微秒级时间戳函数：

| 函数 | 返回值 | 示例 |
|------|--------|------|
| `timestamp_us()` | 微秒级时间戳（整数） | `1706508000000000` |
| `now_us()` | 格式化微秒时间字符串 | `"20260129133045123456"` |
| `now().strftime('%f')` | 微秒部分（6位） | `"123456"` |

**使用示例**：
```yaml
config:
  variables:
    # 方式 1: 使用专用函数
    test_suffix: "${now_us()}"

    # 方式 2: 使用 now().strftime('%f')
    test_suffix_2: "${now().strftime('%Y%m%d%H%M%S%f')}"

    # 方式 3: 使用微秒时间戳
    timestamp: "${timestamp_us()}"
```

---

## 修改的文件

### 核心修改

1. **pyproject.toml**
   - 依赖更新：`jsonpath` → `jsonpath-ng>=1.6.0`

2. **apirun/utils/enhanced_jsonpath.py**（完全重写）
   - 使用 `jsonpath-ng` 库
   - 支持过滤表达式、通配符等高级功能
   - 添加哨兵值 `_NO_MATCH` 区分"无匹配"和"值为 None"
   - 改进数组索引越界检查

3. **apirun/core/variable_manager.py**
   - `render_string()` 添加递归渲染支持（最多 10 次迭代）

4. **apirun/validation/comparators.py**
   - 改进 `contains()` 比较器的类型处理
   - 移除对旧 `jsonpath` 库的依赖

5. **apirun/core/template_functions.py**
   - 添加 `timestamp_us()` 函数
   - 添加 `now_us()` 函数

6. **apirun/extractor/jsonpath_extractor.py**
   - 无代码修改，仅依赖更新

### 测试文件

7. **tests/test_bugfixes.py**（新增）
   - JSONPath 过滤表达式测试
   - 变量嵌套引用测试
   - Contains 验证器测试
   - 微秒时间戳测试

---

## 测试结果

```
======================= 563 passed, 16 warnings in 7.72s =======================
```

所有现有测试通过，新功能测试覆盖：
- 22 个新测试用例（tests/test_bugfixes.py）
- JSONPath 功能测试（32 个测试）
- 变量管理器测试（包括递归渲染）

---

## 向后兼容性

### 破坏性变更

**JSONPath 布尔值语法**：
过滤表达式中必须使用小写 `true`/`false`：

```yaml
# ❌ 错误
$.users[?(@.active == True)].name

# ✅ 正确
$.users[?(@.active == true)].name
```

### 新增功能（向后兼容）

所有新功能都是增量的，不影响现有用例：
- 过滤表达式是可选的
- 递归变量渲染有最大迭代限制保护
- 新的时间戳函数是额外选项

---

## 使用建议

### JSONPath 最佳实践

1. **过滤表达式**：使用小写布尔值
   ```yaml
   $.items[?(@.status == 'active' & @.price > 100)].id
   ```

2. **数组索引**：使用标准索引语法
   ```yaml
   $.data.items[0].name
   $.data.items[*].id  # 通配符获取所有
   ```

3. **提取器路径**：记住响应结构差异
   ```yaml
   # Validator: 使用 response.body
   validations:
     - path: $.json.username

   # Extractor: 使用完整响应路径
   extractors:
     - path: $.body.json.username
   ```

### 变量嵌套引用

1. **避免循环引用**：系统会在 10 次迭代后停止
   ```yaml
   # ⚠️ 循环引用（会停止）
   var1: "${var2}"
   var2: "${var1}"
   ```

2. **多级引用**：支持任意深度
   ```yaml
   base: "api"
   env: "${base}"
   url: "${env}.example.com"  # ✅ 渲染为 "api.example.com"
   ```

### 时间戳选择

| 场景 | 推荐函数 | 精度 |
|------|---------|------|
| 秒级时间戳 | `timestamp()` | 10 位 |
| 毫秒级时间戳 | `timestamp_ms()` | 13 位 |
| 微秒级时间戳 | `timestamp_us()` | 16 位 |
| 格式化日期+微秒 | `now_us()` | "20260129133045123456" |
| 自定义格式 | `now().strftime('%Y%m%d%H%M%S%f')` | 任意 |

---

## 已知限制

1. **复杂 AND/OR 条件**：`jsonpath-ng` 对嵌套逻辑表达式的支持有限，建议使用链式过滤
2. **性能考虑**：过滤表达式在大数据集上可能较慢
3. **循环引用检测**：只通过最大迭代次数限制，不会显式报错

---

## 后续改进建议

1. 添加循环引用检测算法（如访问标记）
2. 支持更多 JSONPath 扩展功能（如自定义函数）
3. 性能优化：缓存 JSONPath 解析结果
4. 更好的错误提示：指出 JSONPath 表达式的具体错误位置
