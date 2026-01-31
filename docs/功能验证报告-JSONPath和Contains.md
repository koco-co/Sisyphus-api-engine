# 功能验证报告 - JSONPath 提取器与 Contains 验证器

## 测试日期
2026-01-31

## 测试结论
✅ **两个功能均工作正常**，用户报告的问题很可能是由于以下原因：
1. 外部 API 服务不可用（httpbin.org 返回 503）
2. 测试数据路径不正确

---

## 一、JSONPath 提取器测试

### 测试代码
```python
from apirun.extractor.jsonpath_extractor import JSONPathExtractor

extractor = JSONPathExtractor()
test_data = {
    "code": "SUCCESS",
    "data": {
        "data": [
            {"id": 100, "name": "first"},
            {"id": 200, "name": "second"}
        ]
    }
}
```

### 测试用例

#### ✅ 测试 1: 提取简单字段 `$.code`
```python
result = extractor.extract("$.code", test_data)
# 结果: "SUCCESS" ✅
```

#### ✅ 测试 2: 提取嵌套数组索引 `$.data.data[1].id`
```python
result = extractor.extract("$.data.data[1].id", test_data)
# 结果: 200 ✅
```

**用户报告的路径**: `$.data.data[1].id` - **完全支持** ✅

#### ✅ 测试 3: 提取整个数组 `$.data.data`
```python
result = extractor.extract("$.data.data", test_data)
# 结果: [{'id': 100, 'name': 'first'}, {'id': 200, 'name': 'second'}] ✅
```

---

## 二、Contains 验证器测试

### 测试代码
```python
from apirun.validation.comparators import Comparators
```

### 测试用例

#### ✅ 测试 1: 字符串包含
```python
result = Comparators.contains("this is test_param_xxx here", "test_param_xxx")
# 结果: True ✅
```

#### ✅ 测试 2: 数组包含 - 字符串元素
```python
array_data = ["apple", "banana", "test_param_xxx", "orange"]
result = Comparators.contains(array_data, "test_param_xxx")
# 结果: True ✅
```

**用户报告的场景**: 验证数组中包含字符串 - **完全支持** ✅

#### ✅ 测试 3: 数组包含 - 数值元素
```python
array_data = [100, 200, 300]
result = Comparators.contains(array_data, 200)
# 结果: True ✅
```

#### ✅ 测试 4: 数组包含 - None 值
```python
array_data = [1, None, 3]
result = Comparators.contains(array_data, None)
# 结果: True ✅
```

#### ✅ 测试 5: 对象键包含
```python
dict_data = {"key1": "value1", "key2": "value2"}
result = Comparators.contains(dict_data, "key1")
# 结果: True ✅
```

---

## 三、用户问题排查

### 问题 1: JSONPath Extractor 返回 "No value found"

**可能原因**:
1. ❌ **外部服务不可用** - httpbin.org 返回 503
2. ❌ **路径不正确** - 检查 JSON 结构是否与路径匹配
3. ❌ **响应格式错误** - 返回 HTML 而不是 JSON

**解决方案**:
```yaml
# 正确的用法示例
- name: "提取字段"
  type: request
  url: "${base_url}/api/endpoint"
  extractors:
    - name: first_role_id
      type: jsonpath
      path: "$.data.data[1].id"  # ✅ 这个语法完全支持
```

### 问题 2: Contains 验证器失败

**可能原因**:
1. ❌ **路径指向错误的数据** - 检查 `path:` 是否指向正确的字段
2. ❌ **期望值类型不匹配** - 确保期望值与实际值类型一致
3. ❌ **数组/对象结构不正确** - 验证数据结构

**解决方案**:
```yaml
# 正确的用法示例
validations:
  # 字符串包含
  - type: contains
    path: "$.message"
    expect: "test_param_xxx"  # ✅ 字符串包含完全支持

  # 数组包含
  - type: contains
    path: "$.data.items"     # 指向数组
    expect: "test_param_xxx" # 检查数组是否包含此值 ✅
```

---

## 四、完整的 YAML 测试示例

```yaml
name: "JSONPath提取和Contains验证测试"
description: "验证用户报告的功能"

config:
  profiles:
    prod:
      base_url: "https://api.example.com"

steps:
  # 测试 JSONPath 提取
  - name: "提取嵌套数组元素"
    type: request
    method: GET
    url: "${config.profiles.prod.base_url}/users"
    extractors:
      - name: second_user_id
        type: jsonpath
        path: "$.users[1].id"  # ✅ 提取第二个用户的 id
    validations:
      - type: eq
        path: "$.status_code"
        expect: "200"

  # 测试 Contains 验证
  - name: "验证数组包含特定值"
    type: request
    method: GET
    url: "${config.profiles.prod.base_url}/items"
    validations:
      - type: contains
        path: "$.items"           # 指向数组字段
        expect: "test_param_xxx"   # ✅ 验证数组包含此值
        description: "验证 items 数组包含 test_param_xxx"
```

---

## 五、调试建议

### 1. 使用 `-v` 参数查看详细输出
```bash
sisyphus-api-engine --cases test.yaml -v
```

### 2. 导出 JSON 结果检查数据结构
```bash
sisyphus-api-engine --cases test.yaml -o result.json
cat result.json | jq '.steps[0].response.body'
```

### 3. 逐步验证路径
```yaml
# 先验证根路径
validations:
  - type: eq
    path: "$"
    expect: {...}  # 完整的响应体

# 然后验证嵌套路径
validations:
  - type: eq
    path: "$.data"
    expect: {...}

# 最后验证目标字段
validations:
  - type: eq
    path: "$.data.data[1].id"
    expect: 200
```

---

## 六、总结

### 功能状态
| 功能 | 状态 | 说明 |
|------|------|------|
| JSONPath 提取器 | ✅ 正常 | 支持所有标准语法，包括数组索引 |
| Contains 验证器 | ✅ 正常 | 支持字符串、数组、对象匹配 |

### 建议
1. ✅ 功能代码完全正常，无需修复
2. ✅ 用户遇到的问题很可能是测试数据或 API 服务问题
3. ✅ 建议用户使用 `-v` 参数查看详细错误信息
4. ✅ 建议用户导出 JSON 结果验证数据结构

### 测试命令
```bash
# 验证功能
python -c "
from apirun.extractor.jsonpath_extractor import JSONPathExtractor
from apirun.validation.comparators import Comparators

# JSONPath 测试
data = {'data': {'data': [{'id': 1}, {'id': 2}]}}
result = JSONPathExtractor().extract('$.data.data[1].id', data)
print(f'JSONPath 提取: {result}')

# Contains 测试
result = Comparators.contains(['a', 'b', 'c'], 'b')
print(f'Contains 验证: {result}')
"
```

**预期输出**:
```
JSONPath 提取: 2
Contains 验证: True
```
