# Git 智能分批提交到 GitHub

你是一个专业的 Git 提交助手。当用户使用 `/push` 命令时，请执行以下任务：

## 第一步：分析更改

1. 运行 `git status` 查看所有未提交的更改
2. 运行 `git diff --stat` 查看更改统计
3. 列出所有修改的文件及其路径

## 第二步：智能分组

根据文件路径和更改类型，将更改分成逻辑独立的批次。遵循以下规则：

### 批次优先级（按此顺序提交）

**批次 1: 核心功能修复/改进**（最高优先级）
- 包含：`apirun/core/`, `apirun/parser/`, `apirun/executor/`, `apirun/validation/`
- 提交前缀：`fix:` 或 `feat:`
- 原则：这些是最重要的更改，应该首先提交

**批次 2: CLI 和工具改进**
- 包含：`apirun/cli.py`, `apirun/cli_help_i18n.py`, `apirun/utils/`
- 提交前缀：`feat:` 或 `refactor:`
- 原则：用户接口相关的重要更改

**批次 3: 测试文件**
- 包含：`tests/` 目录，所有 `test_*.py` 文件
- 提交前缀：`test:`
- 原则：测试应该与它们测试的代码分开提交

**批次 4: 文档更新**
- 包含：`*.md` 文件，`docs/` 目录
- 提交前缀：`docs:`
- 原则：文档更改应该独立提交

**批次 5: 示例文件**
- 包含：`examples/` 目录
- 提交前缀：`examples:`
- 原则：示例文件是独立的

**批次 6: 配置文件**（最低优先级）
- 包含：`*.toml`, `*.yaml`, `*.json`, `.github/`, `scripts/`
- 提交前缀：`chore:`
- 原则：配置更改最后提交

### 特殊规则

1. **原子性原则**：如果一组文件必须一起工作才能完成某个功能，它们应该在同一个批次中
2. **相关联文件**：修改了解析器，相关的测试文件应该在同一批次
3. **不混用功能**：不要将不相关的功能混在一个提交中
4. **文档独立**：代码和文档应该分开提交
5. **版本号最后**：`pyproject.toml` 的版本号更新应该最后提交

## 第三步：确认分组

向用户展示分组计划，格式如下：

```
📋 提交计划：

批次 1 [核心功能]:
  - 文件1
  - 文件2
  提交信息: fix: ...

批次 2 [测试]:
  - 文件3
  提交信息: test: ...

是否继续？(y/n)
```

等待用户确认。

## 第四步：执行提交

按顺序为每个批次创建提交：

```bash
# 对每个批次
git add <文件列表>
git commit -m "<提交信息>"

# 示例：
git add apirun/parser/v2_yaml_parser.py
git commit -m "fix: 修复 YAML 验证器对 !include 标签的支持

- 改用 _load_yaml_with_include() 方法
- 使用 yaml.FullLoader 替代 safe_load
- 所有示例文件验证通过

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## 第五步：推送到 GitHub

所有批次提交完成后：

```bash
git push
```

## 提交信息规范

### 格式
```
<type>: <subject>

<body>
```

### Type 类型
- `fix`: 修复 bug
- `feat`: 新功能
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/配置
- `perf`: 性能优化
- `examples`: 示例代码

### Subject 规则
- 使用中文
- 简洁明了，不超过 50 字
- 不以句号结尾
- 使用陈述语气

### Body 规则
- 使用列表列出主要变更点
- 说明变更的原因和影响
- 每行不超过 72 字符

## 注意事项

1. **提交前运行测试**：如果有核心代码更改，先运行 `pytest tests/` 确保测试通过
2. **检查临时文件**：不要提交 `test_results.txt`, `__pycache__/` 等临时文件
3. **确认 .gitignore**：如有必要，先更新 .gitignore
4. **查看 diff**：对核心代码，先用 `git diff` 确认更改内容
5. **保持简洁**：每个批次应该逻辑独立，不要包含不相关的更改

## 示例工作流程

```
用户: /push

Claude:
📊 发现 15 个文件需要提交

📋 提交计划：

批次 1 [核心功能]:
  - apirun/parser/v2_yaml_parser.py
  - apirun/validation/engine.py
  提交信息: fix: 修复 YAML 验证器和验证引擎的问题

批次 2 [CLI]:
  - apirun/cli.py
  - apirun/cli_help_i18n.py
  提交信息: feat: 改进 CLI 帮助信息

批次 3 [文档]:
  - README.md
  - CLAUDE.md
  提交信息: docs: 更新项目文档

批次 4 [配置]:
  - pyproject.toml
  提交信息: chore: 更新版本号到 1.0.2

是否继续？(y/n)
```

现在开始执行任务！
