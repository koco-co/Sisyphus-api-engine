# sisyphus-api-engine

YAML 驱动的接口自动化测试引擎，供 Sisyphus-X 平台调用。

## 项目结构

```
Sisyphus-api-engine/
├── .sisyphus/          # 统一环境配置
│   └── config.yaml
├── apirun/             # 主 Python 包
│   ├── core/           # 核心数据模型
│   ├── parser/         # YAML 解析器
│   ├── executor/       # 测试执行器
│   ├── validation/     # 断言验证引擎
│   ├── extractor/      # 变量提取器
│   ├── data_driven/    # 数据驱动测试
│   ├── result/         # 结果收集器 (json/html/allure/custom)
│   ├── websocket/      # WebSocket 实时推送
│   ├── utils/          # 工具函数
│   └── cli.py          # CLI 入口
├── examples/           # 示例 YAML 用例
├── docs/               # 项目文档
├── tests/
│   ├── unit/           # Python 单元测试 (pytest)
│   └── yaml/           # YAML 测试用例 (sisyphus --cases)
├── CHANGELOG.md
├── pyproject.toml
└── pypi_publish.sh     # PyPI 发布脚本
```

## 使用

```bash
# 默认文本输出
sisyphus --case case.yaml

# JSON 输出（平台集成）
sisyphus --case case.yaml -O json

# Allure 报告
sisyphus --case case.yaml -O allure --allure-dir ./allure-results

# HTML 报告
sisyphus --case case.yaml -O html --html-dir ./html-report
```

## 开发

```bash
uv sync
# Python 单元测试
uv run python -m pytest tests/unit -v

# 批量执行 tests/yaml/ 下所有 YAML 用例
sisyphus --cases tests/yaml/

# 批量执行 examples/ 下所有示例 YAML 用例
sisyphus --cases examples/
```

## 发布

```bash
./pypi_publish.sh
```
