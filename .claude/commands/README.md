# Claude Code 自定义命令使用说明

本项目配置了自定义的 Claude Code 斜杠命令，用于提高开发效率。

## /push 命令

### 功能
智能地将代码更改分批提交到 GitHub，而不是一次性提交所有更改。

### 使用方法
在 Claude Code 对话框中输入：
```
/push
```

### 工作流程

1. **分析更改**：自动运行 `git status` 和 `git diff` 分析所有未提交的更改

2. **智能分组**：将更改按优先级分为 6 个批次：
   - **批次 1**: 核心功能（`apirun/core/`, `apirun/parser/`, `apirun/executor/`, `apirun/validation/`）
   - **批次 2**: CLI 和工具（`apirun/cli.py`, `apirun/utils/`）
   - **批次 3**: 测试文件（`tests/`）
   - **批次 4**: 文档更新（`*.md`, `docs/`）
   - **批次 5**: 示例文件（`examples/`）
   - **批次 6**: 配置文件（`*.toml`, `*.yaml`, `*.json`）

3. **确认计划**：展示分组计划，等待你确认

4. **执行提交**：按顺序为每个批次创建提交，每批都有清晰的提交信息

5. **推送到 GitHub**：所有批次提交完成后自动推送

### 示例输出

```
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

### 优势

✅ **逻辑清晰**：每个提交都是独立的功能单元
✅ **易于追溯**：提交历史清晰，便于代码审查
✅ **专业规范**：遵循项目的提交信息规范
✅ **智能分组**：自动识别文件类型和优先级
✅ **交互式**：执行前展示计划，可以确认或调整

### 提交信息规范

/push 命令遵循以下提交信息规范：

| Type | 说明 | 示例 |
|------|------|------|
| `fix` | 修复 bug | `fix: 修复 YAML 验证器对 !include 标签的支持` |
| `feat` | 新功能 | `feat: 添加新的验证器类型` |
| `docs` | 文档更新 | `docs: 完善 README.md 使用示例` |
| `refactor` | 重构 | `refactor: 优化变量管理器结构` |
| `test` | 测试相关 | `test: 添加验证器单元测试` |
| `chore` | 构建/工具/配置 | `chore: 更新版本号到 1.0.2` |
| `perf` | 性能优化 | `perf: 优化模板渲染性能` |
| `examples` | 示例代码 | `examples: 添加数据库操作示例` |

## 添加更多命令

要添加更多自定义命令，在 `.claude/commands/` 目录下创建 `<命令名>.md` 文件即可。

例如，创建 `/test` 命令：
```bash
# 创建命令文件
cat > .claude/commands/test.md << 'EOF'
# 运行测试命令

运行所有测试并生成覆盖率报告。
EOF
```

然后在 Claude Code 中输入 `/test` 即可使用。

## 相关资源

- **提交记录**: https://github.com/koco-co/Sisyphus-api-engine/commit/2041b5c
- **项目文档**: https://github.com/koco-co/Sisyphus-api-engine
