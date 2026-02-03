---
description: 启动 Sisyphus API Engine 项目重构任务，显示当前进度和下一步工作
---

# Sisyphus API Engine 项目重构任务

## 📊 项目概览

**项目名称**: Sisyphus API Engine - 企业级 API 自动化测试引擎

**重构目标**:
1. 系统化 review 所有代码，将 Google 规范的英文注释改为中文
2. 为每个功能模块补充完整的单元测试（覆盖率 80%+）
3. 创建 YAML 使用示例案例
4. 更新详细文档
5. 清理不需要的测试文件和报告

**项目结构**:
```
Sisyphus-api-engine/
├── apirun/              # 核心代码 (60个Python文件)
│   ├── core/           # 核心模块
│   ├── executor/       # 执行器
│   ├── parser/         # 解析器
│   ├── validation/     # 验证引擎
│   ├── extractor/      # 变量提取器
│   ├── data_driven/    # 数据驱动测试
│   ├── result/         # 结果收集
│   ├── utils/          # 实用工具
│   └── cli.py          # 命令行接口
├── tests/              # 单元测试
├── examples/           # YAML 示例
└── docs/               # 文档
```

---

## 🎯 学习路径（14个阶段）

| 阶段 | 功能 | 涉及文件 | 状态 |
|-----|------|---------|------|
| 01 | 核心数据模型 | `apirun/core/models.py` | ⏳ 待开始 |
| 02 | 配置管理 | `apirun/core/global_config_manager.py` | ⏳ 待开始 |
| 03 | 变量系统 | `variable_manager.py`, `template_functions.py`, `condition_evaluator.py` | ⏳ 待开始 |
| 04 | 解析器 | `v2_yaml_parser.py`, `yaml_validator.py` | ⏳ 待开始 |
| 05 | 执行器基础 | `step_executor.py`, `retry.py` | ⏳ 待开始 |
| 06 | HTTP请求执行 | `api_executor.py` | ⏳ 待开始 |
| 07 | 验证系统 | `validation/` 目录 | ⏳ 待开始 |
| 08 | 变量提取 | `extractor/` 目录 | ⏳ 待开始 |
| 09 | 步骤执行类型 | wait/loop/concurrent/poll/database/script 执行器 | ⏳ 待开始 |
| 10 | 测试用例执行 | `test_case_executor.py`, `dependency_analyzer.py` | ⏳ 待开始 |
| 11 | 数据驱动测试 | `data_driven/` 目录 | ⏳ 待开始 |
| 12 | 结果收集和输出 | `result/` 目录 | ⏳ 待开始 |
| 13 | 实用工具 | `utils/` 目录 | ⏳ 待开始 |
| 14 | 命令行接口 | `cli.py` | ⏳ 待开始 |

---

## 📋 当前工作流程（每个阶段）

### 8步标准化流程

```bash
# 步骤1: 代码 Review 和中文注释
# - 阅读并理解代码逻辑
# - 将 Google 规范的英文注释改为中文
# - 识别不合理设计并质疑
# - 确认后重写逻辑

# 步骤2: 删除旧的测试文件
rm -rf tests/<module>/*.py
rm -f examples/<old_files>.yaml

# 步骤3: 编写单元测试（从零，不参考旧文件）
# - 使用 Google 规范的中文注释
# - 充分考虑测试场景（正常、边界、异常）
# - 目标覆盖率：80%+

# 步骤4: 创建 YAML 案例
# - 位置: examples/yaml/<序号>_<功能名称>_<场景>.yaml
# - 覆盖所有关键字和使用场景

# 步骤5: 自测
pytest tests/<module>/ -v
sisyphus --cases examples/yaml/<test_case>.yaml

# 步骤6: 更新详细文档
# - 按照 docs/template_docs.md 模板规范
# - 更新 docs/<序号>_<阶段名称>.md

# 步骤7: 更新其他文档
# - 更新 README.md（引用路径要正确）
# - 更新 CHANGELOG.md（记录变更）
# - 更新 pyproject.toml（如需要）

# 步骤8: 原子化提交
git add apirun/<module>/<file>.py
git commit -m "refactor(<module>): 📝 将<功能>注释改为中文"

git add tests/<module>/test_<file>.py
git commit -m "test(<module>): ✅ 新增<功能>单元测试"

git add examples/yaml/<test_case>.yaml
git commit -m "docs(examples): 📝 新增<功能>YAML示例"

git add docs/<序号>_<阶段名称>.md
git commit -m "docs: 📝 更新<功能>详细文档"
```

---

## 🚀 下一步工作

### 当前应该执行：第一阶段 - 核心数据模型

**目标文件**: `apirun/core/models.py`

**具体任务**:
1. 阅读 `apirun/core/models.py`，理解所有数据模型
2. 将英文注释改为中文（保留 Google 规范格式）
3. 删除 `tests/core/test_models.py`（如存在）
4. 编写新的单元测试
5. 创建 YAML 示例
6. 更新 `docs/01_第一阶段_核心数据模型.md`
7. 原子化提交

**关键模型**:
- `HttpMethod` - HTTP 方法枚举
- `ErrorCategory` - 错误分类枚举
- `ProfileConfig` - 环境配置模型
- `GlobalConfig` - 全局配置模型
- `TestCase` - 测试用例模型
- `TestStep` - 测试步骤模型
- `ValidationRule` - 验证规则模型
- `Extractor` - 提取器模型
- `StepResult` / `TestCaseResult` - 结果模型
- `PerformanceMetrics` - 性能指标模型
- `ErrorInfo` - 错误信息模型

---

## 📚 关键文档位置

### 规划文档
- **学习大纲**: `docs/00_项目重构学习大纲与任务清单.md`
- **文档模板**: `docs/template_docs.md`

### 协议规范
- **输入协议**: `docs/API-Engine输入协议规范.md`
- **输出协议**: `docs/API-Engine输出协议规范.md`

### 现有文档（待更新）
- `README.md`
- `CHANGELOG.md`
- `docs/日志系统使用指南.md`
- `docs/提取器使用指南.md`
- `docs/验证器使用指南.md`

---

## ⚠️ 重要注意事项

### 1. 注释规范
- 使用 Google Python Style Guide 的中文注释
- 所有类和函数必须有 docstring
- 最大行长度：100 字符
- 示例：
```python
class ProfileConfig:
    """环境配置模型.

    Attributes:
        base_url: 基础URL
        timeout: 超时时间（秒）
    """
    pass
```

### 2. 测试规范
- **不要参考旧测试文件**，从零编写
- 使用 Google 规范的中文注释
- 充分考虑测试场景
- 目标覆盖率：80%+

### 3. YAML 案例规范
- 文件命名：`<序号>_<功能名称>_<场景>.yaml`
- 位置：`examples/yaml/`
- 必须可实际运行

### 4. 文档规范
- 严格按照 `docs/template_docs.md` 模板
- 包含：关键字表格、YAML 示例、推荐组合用法
- 代码引用格式：`apirun/<module>/<file>.py:<line_number>`

### 5. 提交规范
- 原子化提交，不同改动分开提交
- 提交信息格式：`<type>(<scope>): <emoji> <description>`
- Types: refactor, test, docs, fix, feat, chore

---

## 📊 进度跟踪

### 完成情况
- ✅ 规划文档已创建
- ✅ 文档模板已创建
- ✅ 14个阶段占位符已创建
- ⏳ 第一阶段待开始
- ⏳ 其余阶段待开始

### 最近提交
```
bc7c0fa - docs(planning): 📋 新增项目重构学习大纲和文档模板
```

---

## 🔧 常用命令

### 查看当前进度
```bash
# 查看任务清单
cat docs/00_项目重构学习大纲与任务清单.md

# 查看Git状态
git status

# 查看最近提交
git log --oneline -5
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/core/ -v

# 查看覆盖率
pytest --cov=apirun --cov-report=html
```

### 运行 YAML 案例
```bash
# 基本运行
sisyphus --cases examples/yaml/<test_case>.yaml

# 详细输出
sisyphus --cases examples/yaml/<test_case>.yaml -v

# 验证 YAML
sisyphus-validate examples/yaml/<test_case>.yaml
```

---

## 🎓 开始工作

请从**第一阶段：核心数据模型**开始：

1. 首先阅读 `apirun/core/models.py`
2. 理解每个数据模型的作用和字段
3. 开始将注释改为中文
4. 按照上述8步流程执行

**准备好了吗？让我们开始吧！** 🚀
