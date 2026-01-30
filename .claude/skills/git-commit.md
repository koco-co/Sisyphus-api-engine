# Git 智能分批提交

当用户要求提交代码到 GitHub 时，使用此 skill 智能地将更改分批提交，而不是一次性提交所有更改。

## 触发方式

用户说以下任一短语时触发：
- "提交到 github"
- "提交代码"
- "commit to github"
- "git commit"
- "提交"

## 技能说明

此技能会分析当前的 Git 更改，并根据以下规则进行智能分组：

### 1. 核心功能修复 (Critical Fixes)
**优先级**: 最高
**包含**:
- `apirun/core/` - 核心数据模型
- `apirun/parser/` - 解析器
- `apirun/executor/` - 执行器
- `apirun/validation/` - 验证引擎
**提交前缀**: `fix:` 或 `feat:`
**示例**: `fix: 修复 YAML 验证器对 !include 标签的支持`

### 2. 文档更新 (Documentation)
**优先级**: 中等
**包含**:
- `*.md` 文件
- `docs/` 目录
- `README.md`, `CHANGELOG.md`
**提交前缀**: `docs:`
**示例**: `docs: 完善 README.md 使用示例`

### 3. 测试文件 (Tests)
**优先级**: 中等
**包含**:
- `tests/` 目录
- `test_*.py` 文件
**提交前缀**: `test:` 或 `chore:`
**示例**: `test: 添加验证器单元测试`

### 4. 配置和工具 (Configuration & Tools)
**优先级**: 低
**包含**:
- `*.toml`, `*.yaml`, `*.json`
- `.github/` 目录
- `scripts/` 目录
**提交前缀**: `chore:` 或 `ci:`
**示例**: `chore: 更新 pyproject.toml 版本号`

### 5. 示例文件 (Examples)
**优先级**: 低
**包含**:
- `examples/` 目录
**提交前缀**: `examples:` 或 `docs:`
**示例**: `examples: 添加数据库操作示例`

## 执行步骤

### 步骤 1: 分析更改
```bash
git status
git diff --stat
```

### 步骤 2: 智能分组
根据上述规则，将更改文件分配到不同的提交组中。使用以下逻辑：

- **相关联的文件放一起提交**：例如，修改了解析器，应该同时包含相关的测试文件
- **按功能模块分组**：不要将不相关的功能混在一起
- **文档独立提交**：文档更改应该与代码更改分开
- **配置独立提交**：配置文件的更改应该单独提交

### 步骤 3: 创建提交
按以下优先级顺序提交：

```bash
# 第1批：核心功能修复（最重要）
git add apirun/parser/v2_yaml_parser.py
git commit -m "fix: 修复..."

# 第2批：相关测试
git add tests/parser/test_v2_yaml_parser.py
git commit -m "test: 添加...测试"

# 第3批：文档更新
git add README.md CLAUDE.md
git commit -m "docs: 完善...文档"

# 第4批：配置文件
git add pyproject.toml
git commit -m "chore: 更新版本号"
```

### 步骤 4: 推送到远程
```bash
git push
```

## 提交信息规范

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `fix`: 修复 bug
- `feat`: 新功能
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/配置
- `perf`: 性能优化
- `examples`: 示例代码

### Subject 规则
- 使用中文（本项目为中文项目）
- 简洁明了，不超过 50 字
- 不以句号结尾
- 使用陈述语气

### Body 规则
- 详细说明"做了什么"和"为什么做"
- 列出主要变更点
- 每行不超过 72 字符

### 示例
```
fix: 修复 YAML 验证器对 !include 标签的支持

问题：
- validate_yaml() 方法使用 safe_load，不支持 !include 标签
- 使用全局配置的 YAML 文件验证失败

解决方案：
- 改用 _load_yaml_with_include() 方法
- 使用 yaml.FullLoader 替代 safe_load

影响范围：
- apirun/parser/v2_yaml_parser.py::validate_yaml()

测试：
- 所有 23 个示例文件验证通过
```

## 智能分组示例

### 示例 1: 修复 + 测试 + 文档
```bash
# 批次 1: 核心修复
git add apirun/parser/v2_yaml_parser.py
git commit -m "fix: 修复 YAML 验证器..."

# 批次 2: 测试
git add tests/parser/test_v2_yaml_parser.py
git commit -m "test: 添加验证器测试"

# 批次 3: 文档
git add README.md docs/API-Engine输入协议规范.md
git commit -m "docs: 更新文档说明"
```

### 示例 2: 新功能 + 示例 + 配置
```bash
# 批次 1: 核心功能
git add apirun/executor/my_executor.py
git commit -m "feat: 添加新的执行器类型"

# 批次 2: 示例
git add examples/my_feature_example.yaml
git commit -m "examples: 添加功能使用示例"

# 批次 3: 配置
git add pyproject.toml
git commit -m "chore: 更新版本号和依赖"
```

### 示例 3: 多个独立修复
```bash
# 批次 1: 解析器修复
git add apirun/parser/v2_yaml_parser.py
git commit -m "fix: 修复解析器..."

# 批次 2: 验证器改进
git add apirun/validation/comparators.py
git commit -m "feat: 添加新的验证器..."

# 批次 3: CLI 改进
git add apirun/cli.py apirun/cli_help_i18n.py
git commit -m "feat: 改进 CLI 帮助信息"
```

## 特殊情况处理

### 1. 重命名文件
```bash
# Git 会自动检测重命名，但要确保相关文件一起提交
git add old_file.txt new_file.txt
git commit -m "refactor: 重命名文件以..."
```

### 2. 删除文件
```bash
git add old_file.txt  # 或 git rm old_file.txt
git commit -m "chore: 移除废弃的..."
```

### 3. 新增目录
```bash
git add new_directory/
git commit -m "feat: 添加新的模块目录"
```

### 4. 临时文件
检查是否有不应该提交的文件：
```bash
# 在提交前查看状态
git status

# 如果有临时文件（如 test_results.txt），添加到 .gitignore
echo "test_results.txt" >> .gitignore
git add .gitignore
git commit -m "chore: 添加 test_results.txt 到 .gitignore"
```

## 提交前检查清单

在执行提交前，确保：

- [ ] 运行了所有测试 (`pytest tests/`)
- [ ] 检查了 git status，确认没有遗漏或多余的文件
- [ ] 查看了 git diff，确认更改内容正确
- [ ] 按照逻辑关系进行了合理分组
- [ ] 为每批提交编写了清晰的提交信息
- [ ] 遵循了项目的提交规范

## 注意事项

1. **不要打断原子性操作**：如果一个功能需要同时修改多个文件才能工作，这些文件应该在同一个提交中
2. **确保每次提交后代码可运行**：不要提交半成品代码
3. **合理控制粒度**：既不要太粗（一次提交太多），也不要太细（过度拆分）
4. **优先提交重要内容**：先提交核心功能，再提交文档和配置
5. **测试驱动**：如果可能，先提交测试，再提交实现（TDD 风格）

## 推送策略

- **方案 A**: 每批提交后立即推送
  ```bash
  git commit -m "..." && git push
  ```

- **方案 B**: 全部提交完成后再一次性推送（推荐）
  ```bash
  # 创建所有提交
  git commit -m "..."
  git commit -m "..."
  # 最后一次性推送
  git push
  ```

根据项目规模和团队协作方式选择合适的策略。
