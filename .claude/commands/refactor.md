---
description: 执行项目重构工作流程（代码review、中文注释、测试、文档）
---

# 1. 阶段识别
- 查看 `docs/00_项目重构学习大纲与任务清单.md` 确定当前执行阶段
- 识别当前阶段涉及的核心文件（如 `apirun/core/models.py`）

# 2. 代码 Review 与中文注释
- 阅读并理解代码逻辑
- 将 Google 规范的英文注释改为中文
- 识别不合理设计并质疑，确认后重写逻辑

# 3. 删除旧测试文件
```bash
rm -rf tests/<module>/*.py
rm -f examples/<old_files>.yaml
```

# 4. 编写单元测试
- **从零编写**，不参考旧文件
- 使用 Google 规范的中文注释
- 充分考虑测试场景（正常、边界、异常）
- 目标覆盖率：80%+

# 5. 创建 YAML 案例
- 位置：`examples/yaml/<序号>_<功能名称>_<场景>.yaml`
- 覆盖所有关键字和使用场景

# 6. 自测
```bash
pytest tests/<module>/ -v
sisyphus --cases examples/yaml/<test_case>.yaml
```

# 7. 更新详细文档
- 按照 `docs/template_docs.md` 模板规范
- 更新 `docs/<序号>_<阶段名称>.md`

# 8. 更新其他文档
- 更新 `README.md`（引用路径正确性）
- 更新 `CHANGELOG.md`（记录变更）
- 更新 `pyproject.toml`（如需要）

# 9. 原子化提交
按改动点分批提交，格式：`<type>(<scope>): <emoji> <description>`
- refactor: 代码重构
- test: 测试相关
- docs: 文档更新
- fix: Bug修复
- feat: 新功能
- chore: 构建/工具
