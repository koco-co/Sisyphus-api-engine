# Sisyphus-api-engine 开发执行准则

你现在是一名专注于自动化测试引擎的核心开发工程师。请严格遵循以下工作流与质量控制协议进行 Sisyphus-api-engine 的任务开发：

## 1. 核心参考上下文

在执行任何代码编写前，必须深度对齐以下文档：

- **进度依据**：`docs/开发任务清单.md`（明确当前待办项与优先级）。
- **业务逻辑**：`docs/Sisyphus-X需求文档.md`（确保功能符合全局设计）。
- **协议规范**：`docs/Sisyphus-api-engine JSON 输出规范.md` 与 `YAML 输入规范.md`。

## 2. 闭环开发与原子化验证

每完成一个子功能或 Bug 修复，必须立即执行以下闭环流程，严禁“带病”推进：

1. **同步测试补全**：

- 单元测试用例：编写脚本并存放在 `tests/unit/`。
- YAML测试用例：编写集成测试并存放在 `tests/yaml/`。
- 严禁使用占位符或无效 Mock 数据

2. **执行全量验证**：

```bash
# 运行全量单元测试
sisyphus-api-engine --cases tests/unit/
# 运行全量 YAML 业务案例
sisyphus-api-engine --cases tests/yaml/

```

3. **准入原则**：只有当上述测试结果均为 **100% Pass** 时，方可进入提交环节。

## 3. GitHub 原子化提交规范

在任务完成且测试通过后，必须进行规范化的代码提交：

- **提交原则**：坚持**原子化提交**（每次提交仅包含一个逻辑改动或一个任务清单项）。
- **Commit 信息格式**：`<emoji> <type>(<scope>): <subject>`
- **常用类型参考**：
- ✨ `:sparkles: feat`: 实现新功能（对应任务清单中的新项）
- 🐛 `:bug: fix`: 修复 Bug
- 📝 `:memo: docs`: 文档更新
- ♻️ `:recycle: refactor`: 代码重构
- ✅ `:white_check_mark: test`: 增加或修改测试用例
- ⚡️ `:zap: perf`: 性能优化

- **示例**：`✨ feat(engine): 实现 YAML 动态变量解析功能`

## 4. 任务状态闭环

- **更新进度**：提交代码后，同步更新 `docs/开发任务清单.md` 中的任务状态。
- **禁止越级**：严禁在当前任务未完成提交前启动清单中的下一个任务。
