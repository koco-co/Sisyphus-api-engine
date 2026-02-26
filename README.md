# sisyphus-api-engine

YAML 驱动的接口自动化测试引擎，为 Sisyphus-X 平台提供**核心执行器**能力。

当前仓库是面向 Python 3.12+ 的「轻量核心版」，围绕 YAML → Pydantic 模型 → 场景运行器 → JSON 输出这一主链路进行重构与简化。

---

## 1. 技术栈与约束

- Python: **3.12+**（推荐 3.14）
- 包管理器: **uv**
- 代码风格: Google Python Style，**全中文注释**
- 代码质量: **Ruff**（格式化 + 静态检查）、**Pyright**（类型检查）
- 测试框架: **pytest**

约束与需求文档保持一致，详细见 `docs/Sisyphus-api-engine需求文档.md` 与 `docs/开发任务清单.md`。

---

## 2. 项目结构

```text
Sisyphus-api-engine/
├── .sisyphus/              # 统一环境配置（.sisyphus/config.yaml）
├── apirun/                 # 主 Python 包
│   ├── __init__.py         # 导出 __version__、核心对外接口（预留）
│   ├── cli.py              # CLI 入口 (sisyphus 命令)
│   ├── core/               # 核心数据模型 & 场景运行器
│   │   ├── models.py       # CaseModel / Config / StepDefinition 等
│   │   └── runner.py       # 场景运行器：加载 YAML + 顺序执行步骤
│   ├── parser/             # YAML 解析器（预留）
│   ├── executor/           # 执行器
│   │   └── request.py      # HTTP 请求执行器（requests）
│   ├── validation/         # 断言引擎（预留）
│   ├── extractor/          # 变量提取器（预留）
│   ├── data_driven/        # 数据驱动（预留）
│   ├── result/             # 结果收集与输出（预留）
│   ├── websocket/          # WebSocket 推送（预留）
│   └── utils/              # 内置函数与变量渲染
├── docs/                   # 需求文档 / 输入输出协议 / 开发任务清单
├── tests/
│   ├── unit/               # Python 单元测试
│   └── yaml/               # YAML 用例（通过 CLI 执行）
├── CHANGELOG.md
├── pyproject.toml
├── pypi_publish.sh         # PyPI 发布脚本
└── uv.lock                 # uv 生成的锁文件
```

---

## 3. 安装与环境

### 3.1 使用 uv（推荐）

```bash
# 创建虚拟环境（Python 3.12+）
uv venv -p 3.12 .venv
source .venv/bin/activate  # macOS/Linux

# 同步依赖
uv sync

# 开发模式安装（包含 dev 依赖）
uv pip install -e ".[dev]"
```

### 3.2 使用 pip

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

pip install -e ".[dev]"
```

> 提示：`pyproject.toml` 中 `requires-python = ">=3.12"`，低版本 Python 不受支持。

---

## 4. 快速开始（当前能力）

> 当前核心能力：**YAML 输入模型 + 变量系统 + HTTP 请求执行 + JSON 输出**。  
> 数据库 / WebSocket / 多格式报告等高级能力按开发任务清单逐步补齐。

### 4.1 编写最小 YAML 用例

```yaml
# tests/yaml/simple_get.yaml
config:
  name: "简单 GET 示例"
  environment:
    name: "dev"
    base_url: "https://httpbin.org"

teststeps:
  - name: "GET /get"
    keyword_type: "request"
    request:
      method: "GET"
      url: "/get"
```

### 4.2 通过 CLI 执行

```bash
# 执行单个用例
sisyphus --case tests/yaml/simple_get.yaml -O json

# 批量执行目录下所有 YAML 用例
sisyphus --cases tests/yaml/ -O json
```

引擎会按照 `docs/Sisyphus-api-engine JSON 输出规范.md` 定义的结构返回 JSON（当前实现为最小可用结构，后续会向规范靠拢）。

---

## 5. 开发与测试

### 5.1 开发工作流

```bash
# 1. 安装依赖
uv sync

# 2. 运行单元测试
uv run python -m pytest tests/unit -v

# 3. 代码格式化 & 静态检查
uv run ruff format .
uv run ruff check .

# 4. 类型检查（Pyright）
uv run pyright
```

> 建议开启 `pre-commit`：
>
> ```bash
> pre-commit install
> ```

### 5.2 YAML 用例回归

```bash
# 执行内置 YAML 回归用例
sisyphus --cases tests/yaml/
```

---

## 6. 需求与任务跟踪

- 需求规格说明：`docs/Sisyphus-api-engine需求文档.md`
- YAML 输入规范：`docs/Sisyphus-api-engine YAML 输入规范.md`
- JSON 输出规范：`docs/Sisyphus-api-engine JSON 输出规范.md`
- 开发任务清单：`docs/开发任务清单.md`

`docs/开发任务清单.md` 中维护了详细的功能项与完成度统计（当前整体约 37%），README 仅做高层概览。

---

## 7. 版本与发布策略

### 7.1 本仓库（核心执行器重构线）

- 当前内部版本：**0.2.0**
- 初始版本：0.1.0（从 Sisyphus-X 主项目中拆分）
- 版本变更记录：详见 `CHANGELOG.md`

当前版本尚处于核心能力搭建阶段，主要面向 **Sisyphus-X 平台内部集成与验证**，不直接对应已发布的 PyPI 版本。

### 7.2 已发布 PyPI 包（历史稳定版）

- PyPI 包名：`Sisyphus-api-engine`
- 最新稳定版本：**2.1.0**
- PyPI 页面：`https://pypi.org/project/Sisyphus-api-engine/`

2.x 系列为「完整功能版」引擎，当前仓库则是面向未来 3.x 的**核心执行器重构线**。两者的功能覆盖范围不同，请以各自版本的 README 与 CHANGELOG 为准。

---

## 8. 贡献指南（简要）

1. Fork 仓库并创建特性分支：

   ```bash
   git checkout -b feature/my-feature
   ```

2. 按「开发与测试」章节运行格式化、检查与测试。
3. 提交代码并创建 Pull Request，说明变更点与对应的需求/任务编号（如 `MDL-001`、`RUN-006`）。

更详细的贡献规范后续会补充到 `docs/开发指南.md` 中。

